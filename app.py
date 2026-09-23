import streamlit as st
from github import Github
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(page_title="Stock Alert Management System", page_icon="🏢", layout="wide")

# Custom UI styling for professional enterprise look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #d1d5db; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    h1, h2, h3 { color: #1e3a8a; }
    </style>
""", unsafe_allow_html=True)

# GitHub Connection using Streamlit Secrets
try:
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo("hibaelfentis0-cyber/gestion-stocks-alertes")
except Exception as e:
    st.error(f"GitHub Connection Error: {e}")

# 1. TITRE ET OBJECTIF DE L’APPLICATION
st.title("Stock Alert Management System")
st.markdown("A centralized system for real-time stock alert management and coordination between Production, Warehouse/Logistics, Procurement, and Transport to prevent stock shortages and ensure timely replenishment and delivery.")
st.markdown("---")

# Global Search bar in sidebar
st.sidebar.markdown("### 🔍 Global Search")
global_search_query = st.sidebar.text_input("Search (Product, PO, Supplier...):", "")
st.sidebar.markdown("---")

# Navigation menu
menu = st.sidebar.radio(
    "Navigation Menu", 
    ["📈 General Dashboard", "🏭 Production", "📦 Warehouse", "🛒 Procurement", "🚚 Transport"]
)

# Map departments to their respective Excel files on GitHub
file_mapping = {
    "🏭 Production": "01_Production_Stock_Alert.xlsx",
    "📦 Warehouse": "02_Warehouse_Stock_Alert.xlsx",
    "🛒 Procurement": "03_Procurement_Supply_Stock_Alert.xlsx",
    "🚚 Transport": "04_Transport_Delivery_Stock_Alert.xlsx"
}

# Helper function to convert dataframe to downloadable Excel bytes
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    processed_data = output.getvalue()
    return processed_data

# Intelligent calculations & Reorder Point formula
def calculate_intelligence(row):
    try:
        avail = float(row.get("Quantity Available", 0))
    except:
        avail = 0.0
    try:
        req = float(row.get("Quantity Required", 0))
    except:
        req = 100.0
    try:
        daily_cons = float(row.get("Daily Consumption", 5))
    except:
        daily_cons = 5.0
    try:
        lead_time = float(row.get("Lead Time", 5))
    except:
        lead_time = 5.0
    try:
        safety_stock = float(row.get("Safety Stock", 10))
    except:
        safety_stock = 10.0
    
    if daily_cons <= 0: daily_cons = 1.0
    
    reorder_point = (daily_cons * lead_time) + safety_stock
    
    # Correct Shortage calculation showing exact difference (e.g. 50 - 230 = -180 for surplus, or positive if shortage)
    shortage = req - avail
    
    if avail < req:
        stock_status = "🔴 Shortage"
    elif avail == 1:
        stock_status = "🔴 Last Box"
    elif avail <= reorder_point:
        stock_status = "🟠 Low Stock"
    else:
        stock_status = "🟢 Normal Stock"
        
    if avail < req or stock_status == "🔴 Shortage":
        priority = "🚨 Critical"
    elif stock_status == "🔴 Last Box":
        priority = "🔴 High"
    elif stock_status == "🟠 Low Stock":
        priority = "🟠 Medium"
    else:
        priority = "🟢 Normal"
        
    if avail > reorder_point:
        reorder_status = "No Reorder"
    else:
        reorder_status = "Reorder Required"
        
    days_left = int(avail / daily_cons) if daily_cons > 0 else 0
    stock_out_date = (datetime.now() + timedelta(days=days_left)).strftime("%Y-%m-%d") if avail > 0 else datetime.now().strftime("%Y-%m-%d")
    
    return stock_status, priority, shortage, reorder_point, reorder_status, stock_out_date

# Safe data loader to prevent crashes
def load_excel_data(filename, dept_name):
    try:
        file_content = repo.get_contents(filename)
        df = pd.read_excel(BytesIO(file_content.decoded_content))
    except Exception:
        df = pd.DataFrame()
        
    prod_file = file_mapping["🏭 Production"]
    wh_file = file_mapping["📦 Warehouse"]
    
    prod_df = pd.DataFrame()
    wh_df = pd.DataFrame()
    
    try:
        prod_df = pd.read_excel(BytesIO(repo.get_contents(prod_file).decoded_content))
    except Exception:
        pass
        
    try:
        wh_df = pd.read_excel(BytesIO(repo.get_contents(wh_file).decoded_content))
    except Exception:
        pass

    master_codes = set()
    for d in [prod_df, wh_df, df]:
        if not d.empty and "Product Code" in d.columns:
            for code in d["Product Code"].dropna().tolist():
                if str(code).strip() != "":
                    master_codes.add(str(code))

    if not master_codes:
        master_codes = {"PROD-001"}

    prod_map = {}
    if not prod_df.empty and "Product Code" in prod_df.columns:
        for _, r in prod_df.iterrows():
            pc = r.get("Product Code")
            if pd.notna(pc): prod_map[str(pc)] = r.to_dict()

    wh_map = {}
    if not wh_df.empty and "Product Code" in wh_df.columns:
        for _, r in wh_df.iterrows():
            pc = r.get("Product Code")
            if pd.notna(pc): wh_map[str(pc)] = r.to_dict()

    current_map = {}
    if not df.empty and "Product Code" in df.columns:
        for _, r in df.iterrows():
            pc = r.get("Product Code")
            if pd.notna(pc): current_map[str(pc)] = r.to_dict()

    combined_rows = []
    for p_code in master_codes:
        p_row = prod_map.get(p_code, current_map.get(p_code, {}))
        w_row = wh_map.get(p_code, current_map.get(p_code, {}))
        
        try:
            req = float(p_row.get("Quantity Required", 100))
        except:
            req = 100.0
            
        try:
            avail = float(w_row.get("Quantity Available", 50))
        except:
            avail = 50.0
        
        base_src = p_row if dept_name == "🏭 Production" else w_row
        if not base_src or not isinstance(base_src, dict) or len(base_src) == 0:
            base_src = w_row if (w_row and isinstance(w_row, dict) and len(w_row) > 0) else p_row
        if not isinstance(base_src, dict):
            base_src = {}

        temp_dict = {
            "Quantity Available": avail, 
            "Quantity Required": req,
            "Daily Consumption": base_src.get("Daily Consumption", 5),
            "Lead Time": base_src.get("Lead Time", 5),
            "Safety Stock": base_src.get("Safety Stock", 10)
        }
        stock_status, priority, shortage, reorder_point, reorder_status, stock_out_date = calculate_intelligence(temp_dict)

        if stock_status in ["🔴 Shortage", "🔴 Last Box"]:
            notif_status = f"🚨 ALERT: {stock_status} (Shortage/Diff: {shortage} units)"
        elif stock_status == "🟠 Low Stock":
            notif_status = "⚠️ WARNING: Low Stock Level"
        else:
            notif_status = "✅ Normal (Stock OK)"

        row_data = {
            "Alert ID": base_src.get("Alert ID", f"ALT-{p_code}"),
            "Date": base_src.get("Date", datetime.now().strftime("%Y-%m-%d")),
            "Product Code": p_code,
            "Product Description": base_src.get("Product Description", "Standard Product"),
            "Quantity Required": req,
            "Quantity Available": avail,
            "Shortage Quantity": shortage,
            "Stock Status": stock_status,
            "Priority": priority,
            "Warehouse Notification": notif_status,
            "Daily Consumption": temp_dict["Daily Consumption"],
            "Lead Time": temp_dict["Lead Time"],
            "Safety Stock": temp_dict["Safety Stock"],
            "Reorder Point": reorder_point,
            "Reorder Status": reorder_status,
            "Estimated Stock-Out Date": stock_out_date,
            "Last Updated": base_src.get("Last Updated", datetime.now().strftime("%Y-%m-%d %H:%M")),
            "Production Line": p_row.get("Production Line", "") if isinstance(p_row, dict) else "",
            "Warehouse Location": w_row.get("Warehouse Location", "") if isinstance(w_row, dict) else "",
            "Comments": base_src.get("Comments", "")
        }
        
        row_data["Supplier"] = base_src.get("Supplier", "Default Supplier")
        row_data["Order Date"] = base_src.get("Order Date", datetime.now().strftime("%Y-%m-%d"))
        row_data["Expected Delivery Date"] = base_src.get("Expected Delivery Date", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        row_data["PO Number"] = base_src.get("PO Number", f"PO-{p_code}")
        
        row_data["Transport"] = base_src.get("Transport", "Road")
        row_data["Truck Number"] = base_src.get("Truck Number", "")
        row_data["Transport Status"] = base_src.get("Transport Status", "In Transit")

        combined_rows.append(row_data)

    final_df = pd.DataFrame(combined_rows)

    if dept_name in ["🛒 Procurement", "🚚 Transport"]:
        if "Stock Status" in final_df.columns:
            final_df = final_df[final_df["Stock Status"].isin(["🔴 Shortage", "🔴 Last Box", "🟠 Low Stock"])]

    try:
        fc = repo.get_contents(filename)
        sha = fc.sha
    except:
        sha = None
        
    return final_df, sha

def save_to_github(dataframe, filename, message_text, file_sha):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False)
    updated_excel = output.getvalue()
    try:
        if file_sha:
            repo.update_file(path=filename, message=message_text, content=updated_excel, sha=file_sha)
        else:
            repo.create_file(path=filename, message=message_text, content=updated_excel)
    except Exception as err:
        st.error(f"Error saving to GitHub: {err}")

# --- 2. DASHBOARD ---
if menu == "📈 General Dashboard":
    st.header("📈 General Dashboard & Departmental Analytics")
    st.markdown("Professional overview of inventory health, stock alerts, and shortage volumes across each department.")
    
    dept_stats = []
    total_alerts_all = 0
    total_active_all = 0
    total_shortage_qty_all = 0
    total_reorder_all = 0
    last_box_all = 0
    low_stock_all = 0
    open_proc_all = 0
    pending_deliv_all = 0
    delayed_deliv_all = 0

    for dept_name, fname in file_mapping.items():
        d_df, _ = load_excel_data(fname, dept_name)
        if global_search_query and not d_df.empty:
            mask = d_df.apply(lambda row: row.astype(str).str.contains(global_search_query, case=False).any(), axis=1)
            d_df = d_df[mask]
        
        d_total = len(d_df)
        d_active = len(d_df[d_df["Stock Status"] != "🟢 Normal Stock"]) if not d_df.empty and "Stock Status" in d_df.columns else 0
        d_shortage_qty = int(d_df["Shortage Quantity"].sum()) if not d_df.empty and "Shortage Quantity" in d_df.columns else 0
        d_reorder = len(d_df[d_df["Reorder Status"] == "Reorder Required"]) if not d_df.empty and "Reorder Status" in d_df.columns else 0
        
        total_alerts_all += d_total
        total_active_all += d_active
        total_shortage_qty_all += d_shortage_qty
        total_reorder_all += d_reorder
        if not d_df.empty and "Stock Status" in d_df.columns:
            last_box_all += len(d_df[d_df["Stock Status"] == "🔴 Last Box"])
            low_stock_all += len(d_df[d_df["Stock Status"] == "🟠 Low Stock"])
            delayed_deliv_all += len(d_df[d_df["Stock Status"] == "🔴 Shortage"])

        dept_clean_name = dept_name.split(" ")[1] if " " in dept_name else dept_name
        dept_stats.append({
            "Department": dept_clean_name,
            "Total Alerts": d_total,
            "Shortage Quantity": d_shortage_qty,
            "Reorder Required": d_reorder
        })

    open_proc_all = total_alerts_all
    pending_deliv_all = total_active_all

    k1, k2, k3 = st.columns(3)
    with k1: 
        st.metric("Total Stock Alerts", total_alerts_all)
        st.metric("Reorder Required", total_reorder_all)
    with k2: 
        st.metric("Active Alerts", total_active_all)
        st.metric("Open Procurement Orders", open_proc_all)
    with k3: 
        st.metric("Shortage Quantity", total_shortage_qty_all)
        st.metric("Pending Deliveries", pending_deliv_all)

    k4, k5, k6 = st.columns(3)
    with k4: st.metric("Low Stock Items", low_stock_all)
    with k5: st.metric("Last Box Items", last_box_all)
    with k6: st.metric("Delayed Deliveries", delayed_deliv_all)
    
    st.markdown("---")
    st.markdown("### 📊 Departmental Alerts & Shortage Volumes Breakdown")
    if dept_stats:
        chart_df = pd.DataFrame(dept_stats).set_index("Department")
        st.bar_chart(chart_df)

# --- 3. SPECIFIC DEPARTMENTS ---
else:
    current_file = file_mapping[menu]
    df, file_sha = load_excel_data(current_file, menu)
    
    st.header(f"Motherson PKC — {menu}")
    
    if "Production" in menu:
        st.markdown("🏭 **Production Department**: Manage your **Quantity Required**. Real-time notifications and stock checks enabled.")
        specific_cols = ["Alert ID", "Date", "Product Code", "Product Description", "Quantity Required", "Warehouse Notification", "Production Line", "Last Updated", "Comments"]
    elif "Warehouse" in menu:
        st.markdown("📦 **Warehouse Department**: Manage stock levels, consumption parameters, safety stock, and reorder triggers.")
        specific_cols = ["Alert ID", "Date", "Product Code", "Product Description", "Quantity Available", "Quantity Required", "Shortage Quantity", "Stock Status", "Priority", "Daily Consumption", "Lead Time", "Safety Stock", "Reorder Point", "Reorder Status", "Estimated Stock-Out Date", "Warehouse Location", "Last Updated", "Comments"]
    elif "Procurement" in menu:
        st.markdown("🛒 **Procurement Escalations**: Manage supplier parameters, PO numbers, order dates, and expected deliveries.")
        specific_cols = ["Alert ID", "Date", "Product Code", "Product Description", "Quantity Available", "Quantity Required", "Shortage Quantity", "Stock Status", "Priority", "Supplier", "Lead Time", "Order Date", "Expected Delivery Date", "PO Number", "Last Updated"]
    else:
        st.markdown("🚚 **Transport Tracking**: Monitor transport routes, truck numbers, and dispatch statuses.")
        specific_cols = ["Alert ID", "Date", "Product Code", "Product Description", "Quantity Available", "Quantity Required", "Shortage Quantity", "Stock Status", "Priority", "Transport", "Truck Number", "Transport Status", "Last Updated"]

    for col in specific_cols:
        if col not in df.columns:
            df[col] = ""

    df_view = df[specific_cols]

    if global_search_query:
        mask = df_view.apply(lambda row: row.astype(str).str.contains(global_search_query, case=False).any(), axis=1)
        df_view = df_view[mask]

    search_key = f"search_{menu}"
    if search_key not in st.session_state:
        st.session_state[search_key] = ""

    if st.session_state[search_key]:
        mask = df_view.apply(lambda row: row.astype(str).str.contains(st.session_state[search_key], case=False).any(), axis=1)
        df_view = df_view[mask]

    # --- 1. EDIT TABLE FIRST ---
    st.markdown("### ✏️ Edit Department Records")
    
    edited_df = st.data_editor(
        df_view, 
        num_rows="dynamic", 
        key=f"{menu}_editor",
        column_config={
            "Stock Status": st.column_config.TextColumn("Stock Status (Auto-calculated)"),
            "Priority": st.column_config.TextColumn("Priority (Auto-calculated)"),
            "Reorder Point": st.column_config.NumberColumn("Reorder Point (Auto-calculated)", format="%.1f"),
            "Reorder Status": st.column_config.TextColumn("Reorder Status (Auto)")
        }
    )
    
    if st.button("💾 Save Changes & Sync Across Departments"):
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        edited_df["Last Updated"] = current_time_str
        
        for idx, row in edited_df.iterrows():
            p_code = row.get("Product Code")
            match_idx = df[df["Product Code"] == p_code].index
            if not match_idx.empty:
                for col in edited_df.columns:
                    if col in df.columns:
                        df.loc[match_idx, col] = row[col]

        save_to_github(df, current_file, f"Update {menu}", file_sha)
        
        if "Production" in menu or "Warehouse" in menu:
            other_menu = "📦 Warehouse" if "Production" in menu else "🏭 Production"
            other_file = file_mapping[other_menu]
            other_df, other_sha = load_excel_data(other_file, other_menu)
            save_to_github(other_df, other_file, f"Auto-sync from {menu}", other_sha)
            
        st.success("✅ Changes saved and warehouse status notifications synchronized successfully!")
        st.rerun()

    st.markdown("---")

    # --- 2. SEARCH & FILTER BELOW THE TABLE ---
    col_search, col_export = st.columns([3, 1])
    with col_search:
        st.markdown("### 🔍 Search & Filter")
        st.text_input("Filter by Product Code or Description:", key=search_key, placeholder="Type to filter records...")
            
    with col_export:
        st.markdown("### 💾 Export Data")
        dept_excel = convert_df_to_excel(df_view)
        st.download_button(
            label="📥 Download Excel",
            data=dept_excel,
            file_name=f"{menu.replace(' ', '_')}_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"download_{menu}"
        )

    # --- 3. ADD NEW ENTRY BELOW THE TABLE ---
    with st.expander(f"➕ Add New Entry to {menu}"):
        with st.form(key=f"add_form_{menu}"):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                new_pcode = st.text_input("Product Code (e.g., PROD-100)")
            with col_b:
                new_pdesc = st.text_input("Product Description")
            with col_c:
                new_qty = st.number_input("Quantity / Requirement", min_value=0.0, value=100.0)
            
            submit_add = st.form_submit_button("Add Product Entry")
            if submit_add and new_pcode:
                new_row = {c: "" for c in df.columns}
                new_row["Alert ID"] = f"ALT-{new_pcode}"
                new_row["Date"] = datetime.now().strftime("%Y-%m-%d")
                new_row["Product Code"] = new_pcode
                new_row["Product Description"] = new_pdesc
                if "Quantity Required" in new_row: new_row["Quantity Required"] = new_qty
                if "Quantity Available" in new_row: new_row["Quantity Available"] = new_qty
                if "Daily Consumption" in new_row: new_row["Daily Consumption"] = 5.0
                if "Lead Time" in new_row: new_row["Lead Time"] = 5.0
                if "Safety Stock" in new_row: new_row["Safety Stock"] = 10.0
                new_row["Last Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_to_github(df, current_file, f"Add product {new_pcode} in {menu}", file_sha)
                st.success(f"Product {new_pcode} added successfully to {menu}!")
                st.rerun()
