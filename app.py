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

# Common base columns
base_columns = [
    "Alert ID", 
    "Date", 
    "Product Code", 
    "Product Description", 
    "Quantity Available", 
    "Quantity Required", 
    "Shortage Quantity",
    "Stock Status",       # 🟢 Normal Stock | 🟠 Low Stock | 🔴 Last Box | 🔴 Shortage
    "Priority",           # 🟢 Normal | 🟠 Medium | 🔴 High | 🚨 Critical
    "Daily Consumption",  
    "Lead Time",          
    "Safety Stock",       
    "Reorder Point",      # Calculated or managed: (Daily Consumption * Lead Time) + Safety Stock
    "Estimated Stock-Out Date",
    "Lifecycle Stage",    # Alert Created -> Logistics Checked -> Procurement Ordered -> Transport Dispatched -> Delivered -> Closed
    "Last Updated"
]

# Helper function to calculate Smart Stock Status, Reorder Point & Priority automatically
def calculate_intelligence(row):
    avail = pd.to_numeric(row.get("Quantity Available", 0), errors='coerce')
    req = pd.to_numeric(row.get("Quantity Required", 0), errors='coerce')
    daily_cons = pd.to_numeric(row.get("Daily Consumption", 5), errors='coerce')
    lead_time = pd.to_numeric(row.get("Lead Time", 5), errors='coerce')
    safety_stock = pd.to_numeric(row.get("Safety Stock", 10), errors='coerce')
    
    if pd.isna(avail): avail = 0
    if pd.isna(req): req = 0
    if pd.isna(daily_cons) or daily_cons <= 0: daily_cons = 1
    if pd.isna(lead_time): lead_time = 5
    if pd.isna(safety_stock): safety_stock = 10
    
    # Reorder Point Formula = (Daily Consumption * Lead Time) + Safety Stock
    reorder_point = (daily_cons * lead_time) + safety_stock
    
    shortage = req - avail
    if shortage < 0: shortage = 0
    
    # 1. Stock Status Logic
    if shortage > 0:
        stock_status = "🔴 Shortage"
    elif avail == 1:
        stock_status = "🔴 Last Box"
    elif avail <= reorder_point:
        stock_status = "🟠 Low Stock"
    else:
        stock_status = "🟢 Normal Stock"
        
    # 2. Priority Logic
    if shortage > 0 or stock_status == "🔴 Shortage":
        priority = "🚨 Critical"
    elif stock_status == "🔴 Last Box":
        priority = "🔴 High"
    elif stock_status == "🟠 Low Stock":
        priority = "🟠 Medium"
    else:
        priority = "🟢 Normal"
        
    # 3. Estimated Stock-Out Date calculation
    days_left = int(avail / daily_cons) if daily_cons > 0 else 0
    stock_out_date = (datetime.now() + timedelta(days=days_left)).strftime("%Y-%m-%d") if avail > 0 else datetime.now().strftime("%Y-%m-%d")
    
    return stock_status, priority, shortage, reorder_point, stock_out_date

# Function to load data with automatic cross-department pipeline synchronization
def load_excel_data(filename, dept_name):
    try:
        file_content = repo.get_contents(filename)
        decoded_content = file_content.decoded_content
        df = pd.read_excel(BytesIO(decoded_content))
    except Exception:
        df = pd.DataFrame()
        
    # 1. Load Warehouse data as the primary control source for Inventory Parameters
    wh_file = file_mapping["📦 Warehouse"]
    wh_df = pd.DataFrame()
    if dept_name != "📦 Warehouse":
        try:
            wh_content = repo.get_contents(wh_file)
            wh_df = pd.read_excel(BytesIO(wh_content.decoded_content))
        except Exception:
            wh_df = pd.DataFrame()

    # If loading Procurement or Transport, sync items only if they require attention (Low Stock, Last Box, or Shortage)
    if dept_name in ["🛒 Procurement", "🚚 Transport"]:
        target_source_df = wh_df if not wh_df.empty else df
        new_rows = []
        
        specific_data_map = {}
        if not df.empty and "Product Code" in df.columns:
            for _, row in df.iterrows():
                p_code = row.get("Product Code")
                if pd.notna(p_code): 
                    specific_data_map[p_code] = row.to_dict()

        if not target_source_df.empty:
            for _, src_row in target_source_df.iterrows():
                p_code = src_row.get("Product Code", "")
                avail = pd.to_numeric(src_row.get("Quantity Available", 0), errors='coerce')
                req = pd.to_numeric(src_row.get("Quantity Required", 0), errors='coerce')
                daily_cons = pd.to_numeric(src_row.get("Daily Consumption", 5), errors='coerce')
                lead_time = pd.to_numeric(src_row.get("Lead Time", 5), errors='coerce')
                safety_stock = pd.to_numeric(src_row.get("Safety Stock", 10), errors='coerce')
                
                temp_dict = {
                    "Quantity Available": avail,
                    "Quantity Required": req,
                    "Daily Consumption": daily_cons,
                    "Lead Time": lead_time,
                    "Safety Stock": safety_stock
                }
                stock_status, priority, shortage, reorder_point, stock_out_date = calculate_intelligence(temp_dict)

                # Filter condition: Only push to Procurement / Transport if stock requires action (Low Stock, Last Box, or Shortage)
                if stock_status == "🟢 Normal Stock":
                    continue

                row_data = {
                    "Alert ID": src_row.get("Alert ID", ""),
                    "Date": src_row.get("Date", ""),
                    "Product Code": p_code,
                    "Product Description": src_row.get("Product Description", ""),
                    "Quantity Available": avail,
                    "Quantity Required": req,
                    "Shortage Quantity": shortage,
                    "Stock Status": stock_status,
                    "Priority": priority,
                    "Daily Consumption": daily_cons,
                    "Lead Time": lead_time,
                    "Safety Stock": safety_stock,
                    "Reorder Point": reorder_point,
                    "Estimated Stock-Out Date": stock_out_date,
                    "Lifecycle Stage": src_row.get("Lifecycle Stage", "Logistics Checked"),
                    "Last Updated": src_row.get("Last Updated", "")
                }
                
                if p_code in specific_data_map:
                    old_row = specific_data_map[p_code]
                    for col in df.columns:
                        if col not in row_data: 
                            row_data[col] = old_row.get(col, "")
                else:
                    if "Procurement" in dept_name:
                        row_data["Supplier"] = ""
                        row_data["Purchase Order"] = ""
                        row_data["Order Date"] = ""
                        row_data["Expected Delivery Date"] = ""
                        row_data["Procurement Status"] = "Pending Procurement Approval"
                        row_data["Comments"] = ""
                    elif "Transport" in dept_name:
                        row_data["Transport"] = "Road"
                        row_data["Truck Number"] = ""
                        row_data["Transport Status"] = "In Transit"
                        row_data["Comments"] = ""
                        
                new_rows.append(row_data)
            df = pd.DataFrame(new_rows)

    # Ensure required columns exist per department
    if dept_name == "🏭 Production":
        cols = base_columns + ["Production Line", "Comments"]
    elif dept_name == "📦 Warehouse":
        cols = base_columns + ["Warehouse Location", "Comments"]
    elif dept_name == "🛒 Procurement":
        cols = [
            "Alert ID", "Date", "Product Code", "Product Description", 
            "Quantity Available", "Quantity Required", "Shortage Quantity",
            "Stock Status", "Priority", "Daily Consumption", "Lead Time", "Safety Stock", "Reorder Point",
            "Supplier", "Purchase Order", "Order Date", "Expected Delivery Date", "Procurement Status", 
            "Lifecycle Stage", "Last Updated", "Comments"
        ]
    elif dept_name == "🚚 Transport":
        cols = [
            "Alert ID", "Date", "Product Code", "Product Description", 
            "Quantity Available", "Quantity Required", "Shortage Quantity",
            "Stock Status", "Priority", "Daily Consumption", "Lead Time", "Safety Stock", "Reorder Point",
            "Transport", "Truck Number", "Transport Status", 
            "Lifecycle Stage", "Last Updated", "Comments"
        ]
    else:
        cols = base_columns + ["Comments"]
        
    for col in cols:
        if col not in df.columns:
            df[col] = ""
            
    try:
        fc = repo.get_contents(filename)
        sha = fc.sha
    except:
        sha = None
        
    return df, sha

# Helper function to save changes to GitHub as Excel
def save_to_github(dataframe, filename, message_text, file_sha):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False)
    updated_excel = output.getvalue()
    
    try:
        if file_sha:
            repo.update_file(
                path=filename,
                message=message_text,
                content=updated_excel,
                sha=file_sha
            )
        else:
            repo.create_file(
                path=filename,
                message=message_text,
                content=updated_excel
            )
    except Exception as err:
        st.error(f"Error saving to GitHub: {err}")

# --- 1. GENERAL DASHBOARD ---
if menu == "📈 General Dashboard":
    st.header("📈 General Dashboard & Comprehensive Analytics")
    st.markdown("Monitor inventory parameters, stock statuses (Normal, Low Stock, Last Box, Shortage), lead times, and end-to-end lifecycles.")
    
    dfs = []
    for dept_name, fname in file_mapping.items():
        d_df, _ = load_excel_data(fname, dept_name)
        d_df["Department"] = dept_name
        dfs.append(d_df)
    
    if dfs:
        global_df = pd.concat(dfs, ignore_index=True)
        
        # Global Search Bar
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔍 Global Search")
        search_query = st.sidebar.text_input("Search Product Code / Desc", "").strip().upper()
        
        if search_query:
            st.subheader(f"🔎 Search Results for: '{search_query}'")
            filtered_global = global_df[
                global_df["Product Code"].astype(str).str.upper().str.contains(search_query) | 
                global_df["Product Description"].astype(str).str.upper().str.contains(search_query)
            ]
            st.dataframe(filtered_global, use_container_width=True)
            st.markdown("---")

        # --- KPI Metrics Calculation ---
        unique_global = global_df.drop_duplicates(subset=["Product Code"])
        total_alerts = len(unique_global)
        shortages_count = len(unique_global[unique_global["Stock Status"] == "🔴 Shortage"]) if "Stock Status" in unique_global.columns else 0
        low_stock_count = len(unique_global[unique_global["Stock Status"] == "🟠 Low Stock"]) if "Stock Status" in unique_global.columns else 0
        last_box_count = len(unique_global[unique_global["Stock Status"] == "🔴 Last Box"]) if "Stock Status" in unique_global.columns else 0
        critical_count = len(unique_global[unique_global["Priority"] == "🚨 Critical"]) if "Priority" in unique_global.columns else 0
        
        open_orders = len(global_df[global_df["Procurement Status"].isin(["Pending Procurement Approval", "PO Created / Ordered", "Shipped by Supplier"])]) if "Procurement Status" in global_df.columns else 0
        
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        with kpi_col1:
            st.metric("Total Items Tracked", total_alerts)
        with kpi_col2:
            st.metric("Shortages", shortages_count, delta="Critical Action" if shortages_count > 0 else "OK", delta_color="inverse")
        with kpi_col3:
            st.metric("Low Stock", low_stock_count)
        with kpi_col4:
            st.metric("Last Box", last_box_count)
            
        kpi_col5, kpi_col6, kpi_col7 = st.columns(3)
        with kpi_col5:
            st.metric("Critical Alerts", critical_count, delta="High Urgency" if critical_count > 0 else "Normal", delta_color="inverse")
        with kpi_col6:
            st.metric("Open POs / Orders", open_orders)
        with kpi_col7:
            st.metric("Inventory Health Rate", f"{max(0, 100 - (shortages_count*10))}%")
            
        st.markdown("---")
        
        # Export Excel Button
        st.subheader("📥 Export Intelligence Reports")
        output_excel = BytesIO()
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            global_df.to_excel(writer, index=False)
        excel_data = output_excel.getvalue()
        
        st.download_button(
            label="📥 Download Complete Global Intelligence Report (.xlsx)",
            data=excel_data,
            file_name=f"Motherson_PKC_Intelligence_Report_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.markdown("---")
        
        # Visual Charts Section
        if len(unique_global) > 0:
            st.subheader("📊 Visual Analytics & Stock Status Breakdown")
            col_ch1, col_ch2 = st.columns(2)
            with col_ch1:
                st.markdown("**Stock Status Distribution**")
                if "Stock Status" in unique_global.columns:
                    status_counts = unique_global["Stock Status"].value_counts()
                    st.bar_chart(status_counts)
            with col_ch2:
                st.markdown("**Priority Breakdown**")
                if "Priority" in unique_global.columns:
                    priority_counts = unique_global["Priority"].value_counts()
                    st.bar_chart(priority_counts)

# --- 2. SPECIFIC DEPARTMENTS ---
else:
    current_file = file_mapping[menu]
    df, file_sha = load_excel_data(current_file, menu)
    
    st.header(f"Motherson PKC - {menu}")
    
    if "Production" in menu:
        st.markdown("🏭 **Production Requirements**: Monitor production lines, required quantities, and automated status alerts.")
        specific_cols = base_columns + ["Production Line", "Comments"]
    elif "Warehouse" in menu:
        st.markdown("📦 **Warehouse Master Control**: Manage stock levels, **Daily Consumption**, **Lead Time**, **Safety Stock**, and auto-calculated **Reorder Points**.")
        specific_cols = base_columns + ["Warehouse Location", "Comments"]
    elif "Procurement" in menu:
        st.markdown("🛒 **Procurement Escalations**: Items showing Low Stock, Last Box, or Shortage appear here automatically to launch Purchase Orders.")
        specific_cols = [
            "Alert ID", "Date", "Product Code", "Product Description", 
            "Quantity Available", "Quantity Required", "Shortage Quantity",
            "Stock Status", "Priority", "Daily Consumption", "Lead Time", "Safety Stock", "Reorder Point",
            "Supplier", "Purchase Order", "Order Date", "Expected Delivery Date", "Procurement Status", 
            "Lifecycle Stage", "Last Updated", "Comments"
        ]
    elif "Transport" in menu:
        st.markdown("🚚 **Logistics & Transport**: Coordinate active shipments and track delivery statuses for critical materials.")
        specific_cols = [
            "Alert ID", "Date", "Product Code", "Product Description", 
            "Quantity Available", "Quantity Required", "Shortage Quantity",
            "Stock Status", "Priority", "Daily Consumption", "Lead Time", "Safety Stock", "Reorder Point",
            "Transport", "Truck Number", "Transport Status", 
            "Lifecycle Stage", "Last Updated", "Comments"
        ]
    
    df_view = df[specific_cols]
    
    column_configs = {}
    
    # Dropdowns configs for interactive data editor
    if "Stock Status" in specific_cols:
        valid_stock_statuses = ["🟢 Normal Stock", "🟠 Low Stock", "🔴 Last Box", "🔴 Shortage"]
        column_configs["Stock Status"] = st.column_config.SelectboxColumn("Stock Status", options=valid_stock_statuses)
        
    if "Priority" in specific_cols:
        valid_priorities = ["🟢 Normal", "🟠 Medium", "🔴 High", "🚨 Critical"]
        column_configs["Priority"] = st.column_config.SelectboxColumn("Priority", options=valid_priorities)

    if "Procurement Status" in specific_cols:
        valid_proc_statuses = [
            "Pending Procurement Approval", 
            "PO Created / Ordered", 
            "Shipped by Supplier", 
            "Received & Resolved", 
            "Cancelled"
        ]
        df_view["Procurement Status"] = df_view["Procurement Status"].apply(lambda x: x if x in valid_proc_statuses else "Pending Procurement Approval")
        column_configs["Procurement Status"] = st.column_config.SelectboxColumn("Procurement Status", options=valid_proc_statuses, required=True)
        
    if "Lifecycle Stage" in specific_cols:
        valid_lifecycles = [
            "Alert Created", 
            "Logistics Checked", 
            "Procurement Ordered", 
            "Transport Dispatched", 
            "Delivered", 
            "Closed"
        ]
        df_view["Lifecycle Stage"] = df_view["Lifecycle Stage"].apply(lambda x: x if x in valid_lifecycles else "Alert Created")
        column_configs["Lifecycle Stage"] = st.column_config.SelectboxColumn("Lifecycle Stage", options=valid_lifecycles, required=True)

    if "Transport" in specific_cols:
        valid_transports = ["Air", "Sea", "Road", "Express"]
        df_view["Transport"] = df_view["Transport"].apply(lambda x: x if x in valid_transports else "Road")
        column_configs["Transport"] = st.column_config.SelectboxColumn("Transport Method", options=valid_transports, required=True)

    if "Transport Status" in specific_cols:
        valid_transport_statuses = ["In Transit", "Arrived at Factory", "Customs Clearance", "Delivered"]
        df_view["Transport Status"] = df_view["Transport Status"].apply(lambda x: x if x in valid_transport_statuses else "In Transit")
        column_configs["Transport Status"] = st.column_config.SelectboxColumn("Transport Status", options=valid_transport_statuses, required=True)

    st.markdown("### 📋 Department Data Records & Parameters")
    
    edited_df = st.data_editor(
        df_view,
        column_config=column_configs,
        num_rows="dynamic",
        key=f"{menu}_editor"
    )
    
    col_btn1, _ = st.columns([1, 5])
    with col_btn1:
        save_btn = st.button("💾 Save Changes & Sync Pipeline")
        
    if save_btn:
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        edited_df["Last Updated"] = current_time_str
        
        # Intelligent automatic recalculations on save
        if "Quantity Available" in edited_df.columns and "Quantity Required" in edited_df.columns:
            edited_df["Quantity Available"] = pd.to_numeric(edited_df["Quantity Available"], errors='coerce').fillna(0)
            edited_df["Quantity Required"] = pd.to_numeric(edited_df["Quantity Required"], errors='coerce').fillna(0)
            edited_df["Shortage Quantity"] = edited_df["Quantity Required"] - edited_df["Quantity Available"]
            edited_df["Shortage Quantity"] = edited_df["Shortage Quantity"].apply(lambda x: x if x > 0 else 0)
            
            for idx, r in edited_df.iterrows():
                st_stat, prio, _, reorder_pt, st_date = calculate_intelligence(r)
                if "Stock Status" in edited_df.columns:
                    edited_df.at[idx, "Stock Status"] = st_stat
                if "Priority" in edited_df.columns:
                    edited_df.at[idx, "Priority"] = prio
                if "Reorder Point" in edited_df.columns:
                    edited_df.at[idx, "Reorder Point"] = reorder_pt
                if "Estimated Stock-Out Date" in edited_df.columns:
                    edited_df.at[idx, "Estimated Stock-Out Date"] = st_date

        save_to_github(edited_df, current_file, f"Motherson PKC Update: {menu}", file_sha)
        st.success("✅ Changes successfully saved, recalculated with inventory formulas, and synchronized across departments!")
        st.rerun()

    # Add form
    with st.form(f"add_form_{menu}"):
        st.subheader(f"➕ Add New Entry to {menu}")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            prod_code = st.text_input("Product Code", "")
        with f_col2:
            prod_desc = st.text_input("Product Description", "")
        
        extra_val = ""
        extra_val_transport = ""
        extra_transport_status = "In Transit"
        
        if "Production" in menu:
            extra_val = st.text_input("Production Line", "")
        elif "Warehouse" in menu:
            extra_val = st.text_input("Warehouse Location", "")
        elif "Procurement" in menu:
            extra_val = st.text_input("Supplier", "")
        elif "Transport" in menu:
            extra_val = st.selectbox("Transport Method", ["Air", "Sea", "Road", "Express"])
            extra_val_transport = st.text_input("Truck Number", "")
            extra_transport_status = st.selectbox("Transport Status", ["In Transit", "Arrived at Factory", "Customs Clearance", "Delivered"])
            
        submit_add = st.form_submit_button("🚀 Add and Sync to GitHub")
        
        if submit_add:
            df_current = edited_df.copy()
            new_row = df_current.iloc[[0]].copy() if len(df_current) > 0 else pd.DataFrame([{col: "" for col in specific_cols}])
            new_row["Alert ID"] = f"ALT-{len(df_current)+1:03d}"
            new_row["Date"] = datetime.now().strftime("%Y-%m-%d")
            new_row["Product Code"] = prod_code
            new_row["Product Description"] = prod_desc
            new_row["Quantity Available"] = 15
            new_row["Quantity Required"] = 100
            new_row["Shortage Quantity"] = 85
            new_row["Stock Status"] = "🟠 Low Stock"
            new_row["Priority"] = "🟠 Medium"
            new_row["Daily Consumption"] = 10
            new_row["Lead Time"] = 5
            new_row["Safety Stock"] = 10
            new_row["Reorder Point"] = 60 # (10*5)+10
            new_row["Estimated Stock-Out Date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            new_row["Lifecycle Stage"] = "Alert Created"
            new_row["Last Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            if "Production" in menu:
                new_row["Production Line"] = extra_val
            elif "Warehouse" in menu:
                new_row["Warehouse Location"] = extra_val
            elif "Procurement" in menu:
                new_row["Supplier"] = extra_val
                new_row["Purchase Order"] = ""
                new_row["Order Date"] = ""
                new_row["Expected Delivery Date"] = ""
                new_row["Procurement Status"] = "Pending Procurement Approval"
            elif "Transport" in menu:
                new_row["Transport"] = extra_val
                new_row["Truck Number"] = extra_val_transport
                new_row["Transport Status"] = extra_transport_status
                
            updated_df = pd.concat([df_current, new_row], ignore_index=True)
            save_to_github(updated_df, current_file, f"Motherson PKC Add row in {menu}", file_sha)
            st.success("✅ Entry added and synchronized successfully!")
            st.rerun()
