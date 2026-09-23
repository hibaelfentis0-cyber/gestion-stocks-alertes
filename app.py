import streamlit as st
from github import Github
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(page_title="Motherson PKC - Advanced Stock & Alert Workflow", page_icon="🏢", layout="wide")

# Custom UI styling
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

# App Title & Company Branding
st.title("🏢 Motherson PKC — Advanced Stock & Lifecycle Alert System")
st.markdown("Industrial tracking, smart inventory parameters, priority workflows, and cross-departmental traceability.")
st.markdown("---")

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

# Helper function to calculate Smart Stock Status, Reorder Point & Priority automatically
def calculate_intelligence(row):
    try:
        avail = float(row.get("Quantity Available", 0))
    except:
        avail = 0.0
    try:
        req = float(row.get("Quantity Required", 0))
    except:
        req = 0.0
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
    shortage = req - avail
    if shortage < 0: shortage = 0
    
    # Stock Status Logic
    if shortage > 0:
        stock_status = "🔴 Shortage"
    elif avail == 1:
        stock_status = "🔴 Last Box"
    elif avail <= reorder_point:
        stock_status = "🟠 Low Stock"
    else:
        stock_status = "🟢 Normal Stock"
        
    # Priority Logic
    if shortage > 0 or stock_status == "🔴 Shortage":
        priority = "🚨 Critical"
    elif stock_status == "🔴 Last Box":
        priority = "🔴 High"
    elif stock_status == "🟠 Low Stock":
        priority = "🟠 Medium"
    else:
        priority = "🟢 Normal"
        
    days_left = int(avail / daily_cons) if daily_cons > 0 else 0
    stock_out_date = (datetime.now() + timedelta(days=days_left)).strftime("%Y-%m-%d") if avail > 0 else datetime.now().strftime("%Y-%m-%d")
    
    return stock_status, priority, shortage, reorder_point, stock_out_date

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
        stock_status, priority, shortage, reorder_point, stock_out_date = calculate_intelligence(temp_dict)

        if stock_status in ["🔴 Shortage", "🔴 Last Box"]:
            notif_status = f"🚨 ALERT: {stock_status} (Shortage: {shortage} units)"
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
            "Estimated Stock-Out Date": stock_out_date,
            "Lifecycle Stage": base_src.get("Lifecycle Stage", "Alert Created"),
            "Last Updated": base_src.get("Last Updated", datetime.now().strftime("%Y-%m-%d %H:%M")),
            "Production Line": p_row.get("Production Line", "") if isinstance(p_row, dict) else "",
            "Warehouse Location": w_row.get("Warehouse Location", "") if isinstance(w_row, dict) else "",
            "Comments": base_src.get("Comments", "")
        }
        
        if "Supplier" in base_src: row_data["Supplier"] = base_src.get("Supplier", "")
        if "Procurement Status" in base_src: row_data["Procurement Status"] = base_src.get("Procurement Status", "Pending Procurement Approval")
        if "Transport" in base_src: row_data["Transport"] = base_src.get("Transport", "Road")
        if "Truck Number" in base_src: row_data["Truck Number"] = base_src.get("Truck Number", "")
        if "Transport Status" in base_src: row_data["Transport Status"] = base_src.get("Transport Status", "In Transit")

        combined_rows.append(row_data)

    final_df = pd.DataFrame(combined_rows)

    if dept_name in ["🛒 Procurement", "🚚 Transport"]:
        if "Stock Status" in final_df.columns:
            final_df = final_df[final_df["Stock Status"] != "🟢 Normal Stock"]

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

# --- 1. GENERAL DASHBOARD ---
if menu == "📈 General Dashboard":
    st.header("📈 General Dashboard & Comprehensive Analytics")
    dfs = []
    for dept_name, fname in file_mapping.items():
        d_df, _ = load_excel_data(fname, dept_name)
        d_df["Department"] = dept_name
        dfs.append(d_df)
    
    if dfs:
        global_df = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["Product Code"])
        total_alerts = len(global_df)
        shortages_count = len(global_df[global_df["Stock Status"] == "🔴 Shortage"]) if "Stock Status" in global_df.columns else 0
        low_stock_count = len(global_df[global_df["Stock Status"] == "🟠 Low Stock"]) if "Stock Status" in global_df.columns else 0
        normal_count = len(global_df[global_df["Stock Status"] == "🟢 Normal Stock"]) if "Stock Status" in global_df.columns else 0
        
        # Extended professional metrics
        k1, k2, k3, k4 = st.columns(4)
        with k1: st.metric("Total Items Tracked", total_alerts)
        with k2: st.metric("🔴 Shortages", shortages_count)
        with k3: st.metric("🟠 Low Stocks", low_stock_count)
        with k4: st.metric("Health Rate", f"{max(0, int((normal_count / total_alerts) * 100))}%" if total_alerts > 0 else "0%")
        
        st.markdown("---")
        col_chart, col_insights = st.columns([2, 1])
        
        with col_chart:
            st.markdown("### 📊 Stock Status Distribution")
            chart_data = pd.DataFrame({
                "Status": ["Shortage", "Low Stock", "Normal Stock"],
                "Count": [shortages_count, low_stock_count, normal_count]
            }).set_index("Status")
            st.bar_chart(chart_data)
            
        with col_insights:
            st.markdown("### 💡 Executive Insights")
            if shortages_count > 0:
                st.error(f"⚠️ **Attention Required**: There are {shortages_count} critical shortages affecting production lines immediately!")
            else:
                st.success("✅ **Operations Stable**: All inventory levels are currently healthy and operating smoothly.")
            st.info("ℹ️ Use the sidebar to navigate to specific department workflows (Production, Warehouse, Procurement, Transport).")

        st.markdown("### 📋 Global Master Data Table")
        
        # Export Button for Global Data
        excel_data = convert_df_to_excel(global_df)
        st.download_button(
            label="📥 Download Global Master Data as Excel",
            data=excel_data,
            file_name="Motherson_Global_Stock_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.dataframe(global_df, use_container_width=True)

# --- 2. SPECIFIC DEPARTMENTS (With Search, Add Item & Export) ---
else:
    current_file = file_mapping[menu]
    df, file_sha = load_excel_data(current_file, menu)
    
    st.header(f"Motherson PKC - {menu}")
    
    if "Production" in menu:
        st.markdown("🏭 **Production Department**: Manage your **Quantity Required**. You receive real-time Warehouse notifications and stock checks automatically.")
        specific_cols = ["Alert ID", "Date", "Product Code", "Product Description", "Quantity Required", "Warehouse Notification", "Production Line", "Last Updated", "Comments"]
    elif "Warehouse" in menu:
        st.markdown("📦 **Warehouse Department**: Manage stock levels (**Quantity Available**). Your updates instantly trigger notifications for Production.")
        specific_cols = ["Alert ID", "Date", "Product Code", "Product Description", "Quantity Available", "Quantity Required", "Shortage Quantity", "Stock Status", "Priority", "Warehouse Location", "Last Updated", "Comments"]
    elif "Procurement" in menu:
        st.markdown("🛒 **Procurement Escalations**: Items needing immediate replenishment.")
        specific_cols = ["Alert ID", "Date", "Product Code", "Product Description", "Quantity Available", "Quantity Required", "Shortage Quantity", "Stock Status", "Priority", "Supplier", "Procurement Status", "Last Updated"]
    else:
        st.markdown("🚚 **Transport Tracking**")
        specific_cols = ["Alert ID", "Date", "Product Code", "Product Description", "Quantity Available", "Quantity Required", "Shortage Quantity", "Stock Status", "Priority", "Transport", "Transport Status", "Last Updated"]

    for col in specific_cols:
        if col not in df.columns:
            df[col] = ""

    df_view = df[specific_cols]

    # --- Search / Filter Section & Export Button ---
    col_search, col_export = st.columns([3, 1])
    with col_search:
        st.markdown("### 🔍 Search & Filter")
        search_query = st.text_input("Search by Product Code or Description:", "")
        if search_query:
            mask = df_view.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
            df_view = df_view[mask]
            
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

    # --- Add New Product Expander ---
    with st.expander("➕ Add New Product Entry"):
        with st.form(key=f"add_form_{menu}"):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                new_pcode = st.text_input("Product Code (e.g., PROD-100)")
            with col_b:
                new_pdesc = st.text_input("Product Description")
            with col_c:
                new_qty = st.number_input("Quantity / Requirement", min_value=0.0, value=100.0)
            
            submit_add = st.form_submit_button("Add Product to List")
            if submit_add and new_pcode:
                new_row = {c: "" for c in df.columns}
                new_row["Alert ID"] = f"ALT-{new_pcode}"
                new_row["Date"] = datetime.now().strftime("%Y-%m-%d")
                new_row["Product Code"] = new_pcode
                new_row["Product Description"] = new_pdesc
                if "Quantity Required" in new_row: new_row["Quantity Required"] = new_qty
                if "Quantity Available" in new_row: new_row["Quantity Available"] = new_qty
                new_row["Last Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_to_github(df, current_file, f"Add product {new_pcode} in {menu}", file_sha)
                st.success(f"Product {new_pcode} added successfully!")
                st.rerun()

    # --- Data Editor ---
    edited_df = st.data_editor(df_view, num_rows="dynamic", key=f"{menu}_editor")
    
    if st.button("💾 Save Changes & Sync Across Departments"):
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        edited_df["Last Updated"] = current_time_str
        
        # Merge edits back into full df columns
        for idx, row in edited_df.iterrows():
            p_code = row.get("Product Code")
            match_idx = df[df["Product Code"] == p_code].index
            if not match_idx.empty:
                for col in edited_df.columns:
                    df.loc[match_idx, col] = row[col]

        save_to_github(df, current_file, f"Update {menu}", file_sha)
        
        if "Production" in menu or "Warehouse" in menu:
            other_menu = "📦 Warehouse" if "Production" in menu else "🏭 Production"
            other_file = file_mapping[other_menu]
            other_df, other_sha = load_excel_data(other_file, other_menu)
            save_to_github(other_df, other_file, f"Auto-sync from {menu}", other_sha)
            
        st.success("✅ Changes saved and warehouse status notifications synchronized successfully!")
        st.rerun()
