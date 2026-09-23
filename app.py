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
st.markdown("Industrial tracking, smart inventory status, priority workflows, and end-to-end departmental traceability.")
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

# Common base columns incorporating Intelligence, Reorder point, and Lifecycle
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
    "Reorder Point",      # Threshold to trigger ordering
    "Daily Consumption",  # Used for stock-out date calculation
    "Estimated Stock-Out Date",
    "Lifecycle Stage",    # Alert Created -> Logistics Checked -> Procurement Ordered -> Transport Dispatched -> Delivered -> Closed
    "Last Updated"
]

# Helper function to calculate Smart Stock Status & Priority automatically
def calculate_intelligence(row):
    avail = pd.to_numeric(row.get("Quantity Available", 0), errors='coerce')
    req = pd.to_numeric(row.get("Quantity Required", 0), errors='coerce')
    reorder = pd.to_numeric(row.get("Reorder Point", 20), errors='coerce')
    daily_cons = pd.to_numeric(row.get("Daily Consumption", 5), errors='coerce')
    if pd.isna(avail): avail = 0
    if pd.isna(req): req = 0
    if pd.isna(reorder): reorder = 20
    if pd.isna(daily_cons) or daily_cons <= 0: daily_cons = 1
    
    shortage = req - avail
    if shortage < 0: shortage = 0
    
    # 1. Stock Status
    if shortage > 0:
        stock_status = "🔴 Shortage"
    elif avail == 1:
        stock_status = "🔴 Last Box"
    elif avail <= reorder:
        stock_status = "🟠 Low Stock"
    else:
        stock_status = "🟢 Normal Stock"
        
    # 2. Priority
    if shortage > 0:
        priority = "🚨 Critical"
    elif stock_status == "🔴 Last Box":
        priority = "🔴 High"
    elif stock_status == "🟠 Low Stock":
        priority = "🟠 Medium"
    else:
        priority = "🟢 Normal"
        
    # 3. Estimated Stock-Out Date calculation
    days_left = int(avail / daily_cons)
    stock_out_date = (datetime.now() + timedelta(days=days_left)).strftime("%Y-%m-%d") if avail > 0 else datetime.now().strftime("%Y-%m-%d")
    
    return stock_status, priority, shortage, stock_out_date

# Function to load data with automatic sync & smart cross-department pipeline
def load_excel_data(filename, dept_name):
    try:
        file_content = repo.get_contents(filename)
        decoded_content = file_content.decoded_content
        df = pd.read_excel(BytesIO(decoded_content))
    except Exception:
        df = pd.DataFrame()
        
    # Auto-synchronization from Production (Master Source)
    if dept_name != "🏭 Production":
        prod_file = file_mapping["🏭 Production"]
        try:
            prod_content = repo.get_contents(prod_file)
            prod_df = pd.read_excel(BytesIO(prod_content.decoded_content))
        except Exception:
            prod_df = pd.DataFrame()
            
        if not prod_df.empty:
            specific_data_map = {}
            if not df.empty and "Product Code" in df.columns:
                for _, row in df.iterrows():
                    p_code = row.get("Product Code")
                    if pd.notna(p_code): 
                        specific_data_map[p_code] = row.to_dict()

            new_rows = []
            for _, prod_row in prod_df.iterrows():
                p_code = prod_row.get("Product Code", "")
                
                req = pd.to_numeric(prod_row.get("Quantity Required", 0), errors='coerce')
                if pd.isna(req): req = 0
                
                avail = pd.to_numeric(prod_row.get("Quantity Available", 0), errors='coerce')
                if pd.isna(avail): avail = 0
                
                reorder = pd.to_numeric(prod_row.get("Reorder Point", 20), errors='coerce')
                daily_cons = pd.to_numeric(prod_row.get("Daily Consumption", 5), errors='coerce')
                
                # Keep specific available qty if modified in warehouse/procurement
                if p_code in specific_data_map and dept_name in ["📦 Warehouse"]:
                    avail = pd.to_numeric(specific_data_map[p_code].get("Quantity Available", avail), errors='coerce')

                temp_dict = {
                    "Quantity Available": avail,
                    "Quantity Required": req,
                    "Reorder Point": reorder,
                    "Daily Consumption": daily_cons
                }
                stock_status, priority, shortage, stock_out_date = calculate_intelligence(temp_dict)

                # Filter out normal items in downstream operational departments if desired, or keep tracked items
                row_data = {
                    "Alert ID": prod_row.get("Alert ID", ""),
                    "Date": prod_row.get("Date", ""),
                    "Product Code": p_code,
                    "Product Description": prod_row.get("Product Description", ""),
                    "Quantity Available": avail,
                    "Quantity Required": req,
                    "Shortage Quantity": shortage,
                    "Stock Status": stock_status,
                    "Priority": priority,
                    "Reorder Point": reorder,
                    "Daily Consumption": daily_cons,
                    "Estimated Stock-Out Date": stock_out_date,
                    "Lifecycle Stage": prod_row.get("Lifecycle Stage", "Alert Created"),
                    "Last Updated": prod_row.get("Last Updated", "")
                }
                
                if p_code in specific_data_map:
                    old_row = specific_data_map[p_code]
                    for col in df.columns:
                        if col not in row_data: 
                            row_data[col] = old_row.get(col, "")
                else:
                    if "Warehouse" in dept_name:
                        row_data["Warehouse Location"] = ""
                        row_data["Comments"] = ""
                    elif "Procurement" in dept_name:
                        row_data["Supplier"] = ""
                        row_data["Lead Time (Days)"] = 5
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
            
    # Ensure specific columns per department exist
    if dept_name == "🏭 Production":
        cols = base_columns + ["Production Line", "Comments"]
    elif "Warehouse" in dept_name:
        cols = base_columns + ["Warehouse Location", "Comments"]
    elif "Procurement" in dept_name:
        cols = [
            "Alert ID", "Date", "Product Code", "Product Description", 
            "Quantity Available", "Quantity Required", "Shortage Quantity",
            "Stock Status", "Priority", "Reorder Point", "Supplier", "Lead Time (Days)",
            "Purchase Order", "Order Date", "Expected Delivery Date", "Procurement Status", 
            "Lifecycle Stage", "Last Updated", "Comments"
        ]
    elif "Transport" in dept_name:
        cols = [
            "Alert ID", "Date", "Product Code", "Product Description", 
            "Quantity Available", "Quantity Required", "Shortage Quantity",
            "Stock Status", "Priority", "Transport", "Truck Number", "Transport Status", 
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
    st.markdown("Monitor advanced KPIs, alert types, supplier lead times, and end-to-end alert lifecycles.")
    
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

        # --- Advanced KPI Metrics Calculation ---
        total_alerts = len(global_df.drop_duplicates(subset=["Product Code"]))
        shortages_count = len(global_df[global_df["Stock Status"] == "🔴 Shortage"]) if "Stock Status" in global_df.columns else 0
        low_stock_count = len(global_df[global_df["Stock Status"] == "🟠 Low Stock"]) if "Stock Status" in global_df.columns else 0
        last_box_count = len(global_df[global_df["Stock Status"] == "🔴 Last Box"]) if "Stock Status" in global_df.columns else 0
        critical_count = len(global_df[global_df["Priority"] == "🚨 Critical"]) if "Priority" in global_df.columns else 0
        
        open_orders = len(global_df[global_df["Procurement Status"].isin(["Pending Procurement Approval", "PO Created / Ordered", "Shipped by Supplier"])]) if "Procurement Status" in global_df.columns else 0
        delayed_deliveries = 0 # Can be calculated if Expected Date < Current Date and not delivered
        
        # Display Metrics in 2 clean rows for maximum clarity
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        with kpi_col1:
            st.metric("Total Alerts", total_alerts)
        with kpi_col2:
            st.metric("Shortages", shortages_count, delta="Action Required" if shortages_count > 0 else "OK", delta_color="inverse")
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
            st.metric("Service Coverage Rate", f"{max(0, 100 - (shortages_count*5))}%")
            
        st.markdown("---")
        
        # Export Excel Button
        st.subheader("📥 Export Complete Reports")
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
        if len(global_df) > 0:
            st.subheader("📊 Visual Analytics & Stock Status Breakdown")
            col_ch1, col_ch2 = st.columns(2)
            with col_ch1:
                st.markdown("**Stock Status Distribution**")
                if "Stock Status" in global_df.columns:
                    status_counts = global_df["Stock Status"].value_counts()
                    st.bar_chart(status_counts)
            with col_ch2:
                st.markdown("**Priority Breakdown**")
                if "Priority" in global_df.columns:
                    priority_counts = global_df["Priority"].value_counts()
                    st.bar_chart(priority_counts)

# --- 2. SPECIFIC DEPARTMENTS ---
else:
    current_file = file_mapping[menu]
    df, file_sha = load_excel_data(current_file, menu)
    
    st.header(f"Motherson PKC - {menu}")
    
    if "Production" in menu:
        st.markdown("🏭 **Master Production Line Monitor**: Track requirements, stock levels, daily consumption, and automated stock-out estimates.")
        specific_cols = base_columns + ["Production Line", "Comments"]
    elif "Warehouse" in menu:
        st.markdown("📦 **Warehouse Inventory Management**: Update real-time quantities available and manage locations.")
        specific_cols = base_columns + ["Warehouse Location", "Comments"]
    elif "Procurement" in menu:
        st.markdown("🛒 **Procurement & Lead Time Control**: Compare requirements with supplier lead times and manage Purchase Orders.")
        specific_cols = [
            "Alert ID", "Date", "Product Code", "Product Description", 
            "Quantity Available", "Quantity Required", "Shortage Quantity",
            "Stock Status", "Priority", "Reorder Point", "Supplier", "Lead Time (Days)",
            "Purchase Order", "Order Date", "Expected Delivery Date", "Procurement Status", 
            "Lifecycle Stage", "Last Updated", "Comments"
        ]
    elif "Transport" in menu:
        st.markdown("🚚 **Transport & Logistics Dispatch**: Coordinate shipments, track truck assignments, and monitor delivery progress.")
        specific_cols = [
            "Alert ID", "Date", "Product Code", "Product Description", 
            "Quantity Available", "Quantity Required", "Shortage Quantity",
            "Stock Status", "Priority", "Transport", "Truck Number", "Transport Status", 
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

    st.markdown("### 📋 Department Data Records & Traceability")
    
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
        
        # Automatic intelligent recalculations on save
        if "Quantity Available" in edited_df.columns and "Quantity Required" in edited_df.columns:
            edited_df["Quantity Available"] = pd.to_numeric(edited_df["Quantity Available"], errors='coerce').fillna(0)
            edited_df["Quantity Required"] = pd.to_numeric(edited_df["Quantity Required"], errors='coerce').fillna(0)
            edited_df["Shortage Quantity"] = edited_df["Quantity Required"] - edited_df["Quantity Available"]
            edited_df["Shortage Quantity"] = edited_df["Shortage Quantity"].apply(lambda x: x if x > 0 else 0)
            
            # Recompute Intelligence fields row by row
            for idx, r in edited_df.iterrows():
                st_stat, prio, _, st_date = calculate_intelligence(r)
                if "Stock Status" in edited_df.columns:
                    edited_df.at[idx, "Stock Status"] = st_stat
                if "Priority" in edited_df.columns:
                    edited_df.at[idx, "Priority"] = prio
                if "Estimated Stock-Out Date" in edited_df.columns:
                    edited_df.at[idx, "Estimated Stock-Out Date"] = st_date

        save_to_github(edited_df, current_file, f"Motherson PKC Update: {menu}", file_sha)
        st.success("✅ Changes successfully saved, recalculated with intelligence rules, and synchronized!")
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
            new_row["Quantity Available"] = 10
            new_row["Quantity Required"] = 100
            new_row["Shortage Quantity"] = 90
            new_row["Stock Status"] = "🔴 Shortage"
            new_row["Priority"] = "🚨 Critical"
            new_row["Reorder Point"] = 25
            if "Daily Consumption" in new_row.columns:
                new_row["Daily Consumption"] = 10
            if "Estimated Stock-Out Date" in new_row.columns:
                new_row["Estimated Stock-Out Date"] = datetime.now().strftime("%Y-%m-%d")
            new_row["Lifecycle Stage"] = "Alert Created"
            new_row["Last Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            if "Production" in menu:
                new_row["Production Line"] = extra_val
            elif "Warehouse" in menu:
                new_row["Warehouse Location"] = extra_val
            elif "Procurement" in menu:
                new_row["Supplier"] = extra_val
                new_row["Lead Time (Days)"] = 7
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
