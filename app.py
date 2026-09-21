import streamlit as st
from github import Github
import pandas as pd
from io import BytesIO

# Page configuration
st.set_page_config(page_title="Motherson PKC - Stock & Alert System", page_icon="🏢", layout="wide")

# Custom UI styling for Motherson PKC professional look
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #d1d5db;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    h1, h2, h3 {
        color: #1e3a8a;
    }
    </style>
""", unsafe_allow_html=True)

# GitHub Connection using Streamlit Secrets
try:
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo("hibaelfentis0-cyber/gestion-stocks-alertes")
except Exception as e:
    st.error(f"GitHub Connection Error: {e}")

# App Title & Company Branding
st.title("🏢 Motherson PKC — Stock Management & Alert System")
st.markdown("Industrial tracking, inventory monitoring, and operational supply chain alerts.")
st.markdown("---")

# Navigation menu with professional symbols
menu = st.sidebar.radio(
    "Navigation Menu", 
    ["📈 General Dashboard", "🏭 Production", "🛒 Procurement", "📦 Warehouse", "🚚 Transport"]
)

# Map departments to their respective Excel files on GitHub
file_mapping = {
    "🏭 Production": "01_Production_Stock_Alert.xlsx",
    "📦 Warehouse": "02_Warehouse_Stock_Alert.xlsx",
    "🛒 Procurement": "03_Procurement_Supply_Stock_Alert.xlsx",
    "🚚 Transport": "04_Transport_Delivery_Stock_Alert.xlsx"
}

# Function to load data from a specific Excel file on GitHub
def load_excel_data(filename):
    try:
        file_content = repo.get_contents(filename)
        decoded_content = file_content.decoded_content
        df = pd.read_excel(BytesIO(decoded_content))
        return df, file_content.sha
    except Exception:
        # Fallback dummy data
        data = {
            "Alert ID": ["ALT-001", "ALT-002"],
            "Date": ["2026-06-01", "2026-06-02"],
            "Product Code": ["PRD-01", "PRD-02"],
            "Product Description": ["Sample Item A", "Sample Item B"],
            "Quantity Available": [120, 450],
            "Quantity Required": [300, 800],
            "Shortage Quantity": [180, 350],
            "Comments": ["Urgent check", "Pending shipment"]
        }
        return pd.DataFrame(data), None

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
        st.success("✅ Changes successfully synchronized with GitHub database!")
        st.rerun()
    except Exception as err:
        st.error(f"Error saving to GitHub: {err}")

# Common automatic base columns for all departments
base_columns = [
    "Alert ID", 
    "Date", 
    "Product Code", 
    "Product Description", 
    "Quantity Available", 
    "Quantity Required", 
    "Shortage Quantity"
]

# --- 1. GENERAL DASHBOARD WITH CHARTS & ANALYTICS ---
if menu == "📈 General Dashboard":
    st.header("📈 General Dashboard - Motherson PKC")
    st.markdown("Overview of key inventory metrics, shortages, and operational analytics across all units.")
    
    dfs = []
    for dept_name, fname in file_mapping.items():
        d_df, _ = load_excel_data(fname)
        d_df["Department"] = dept_name
        dfs.append(d_df)
    
    if dfs:
        global_df = pd.concat(dfs, ignore_index=True)
        
        # Metrics cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", len(global_df))
        with col2:
            tot_avail = global_df["Quantity Available"].sum() if "Quantity Available" in global_df.columns else 0
            st.metric("Total Available Qty", tot_avail)
        with col3:
            tot_req = global_df["Quantity Required"].sum() if "Quantity Required" in global_df.columns else 0
            st.metric("Total Required Qty", tot_req)
        with col4:
            tot_short = global_df["Shortage Quantity"].sum() if "Shortage Quantity" in global_df.columns else 0
            st.metric("Total Shortage Qty", tot_short, delta="Critical Alert" if tot_short > 0 else "Normal", delta_color="inverse")
            
        st.markdown("---")
        
        # Professional Notification Banner
        st.warning("⚠️ **System Notice:** High shortage levels detected in specific production lines. Please review Procurement and Transport schedules.")
        
        # Visual Charts Section
        st.subheader("📊 Visual Analytics & Stock Status")
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("**Quantities by Department (Available vs Required)**")
            if "Department" in global_df.columns and "Quantity Available" in global_df.columns:
                dept_summary = global_df.groupby("Department")[["Quantity Available", "Quantity Required"]].sum()
                st.bar_chart(dept_summary)
                
        with col_chart2:
            st.markdown("**Shortage Quantity per Product**")
            if "Product Code" in global_df.columns and "Shortage Quantity" in global_df.columns:
                shortage_summary = global_df.groupby("Product Code")["Shortage Quantity"].sum()
                st.bar_chart(shortage_summary)

# --- 2. SPECIFIC DEPARTMENTS ---
else:
    current_file = file_mapping[menu]
    df, file_sha = load_excel_data(current_file)
    
    st.header(f"Motherson PKC - {menu}")
    
    if "Production" in menu:
        st.markdown("Monitor assembly lines, operational status, and stock alerts.")
        specific_cols = base_columns + ["Production Line", "Comments"]
    elif "Warehouse" in menu:
        st.markdown("Manage material locations, warehouse zones, and physical stock counts.")
        specific_cols = base_columns + ["Warehouse Location", "Comments"]
    elif "Procurement" in menu:
        st.markdown("Manage suppliers, purchase orders, **ETA (Estimated Time of Arrival)**, and tracking statuses.")
        specific_cols = base_columns + ["Supplier", "Purchase Order", "Order Date", "ETA", "Purchasing Status", "Comments"]
    elif "Transport" in menu:
        st.markdown("Track shipments, carriers, and delivery transit logistics.")
        specific_cols = base_columns + ["Transport", "Comments"]
    
    for col in specific_cols:
        if col not in df.columns:
            df[col] = ""
            
    df_view = df[specific_cols]
    
    column_configs = {}
    if "Purchasing Status" in specific_cols:
        valid_statuses = ["Pending", "Ordered", "Shipped", "Delivered", "Cancelled"]
        df_view["Purchasing Status"] = df_view["Purchasing Status"].apply(lambda x: x if x in valid_statuses else "Pending")
        column_configs["Purchasing Status"] = st.column_config.SelectboxColumn("Purchasing Status", options=valid_statuses, required=True)
        
    if "Transport" in specific_cols:
        valid_transports = ["Air", "Sea", "Road", "Express"]
        df_view["Transport"] = df_view["Transport"].apply(lambda x: x if x in valid_transports else "Road")
        column_configs["Transport"] = st.column_config.SelectboxColumn("Transport Method", options=valid_transports, required=True)

    edited_df = st.data_editor(
        df_view,
        column_config=column_configs,
        num_rows="dynamic",
        key=f"{menu}_editor"
    )
    
    col_btn1, col_btn2 = st.columns([1, 5])
    with col_btn1:
        save_btn = st.button("💾 Save Changes")
        
    if save_btn:
        save_to_github(edited_df, current_file, f"Motherson PKC Update: {menu}", file_sha)

    with st.form(f"add_form_{menu}"):
        st.subheader(f"➕ Add New Entry to {menu}")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            prod_code = st.text_input("Product Code", "PRD-NEW-01")
        with f_col2:
            prod_desc = st.text_input("Product Description", "Item Description")
        
        extra_val = ""
        if "Production" in menu:
            extra_val = st.text_input("Production Line", "Assembly Line A")
        elif "Warehouse" in menu:
            extra_val = st.text_input("Warehouse Location", "Zone C - Racks")
        elif "Procurement" in menu:
            extra_val = st.text_input("Supplier", "Supplier Name")
        elif "Transport" in menu:
            extra_val = st.selectbox("Transport Method", ["Air", "Sea", "Road", "Express"])
            
        submit_add = st.form_submit_button("🚀 Add and Sync to GitHub")
        
        if submit_add:
            df_current = edited_df.copy()
            new_row = df_current.iloc[[0]].copy() if len(df_current) > 0 else pd.DataFrame([{col: "" for col in specific_cols}])
            new_row["Alert ID"] = f"ALT-{len(df_current)+1:03d}"
            new_row["Product Code"] = prod_code
            new_row["Product Description"] = prod_desc
            
            if "Production" in menu:
                new_row["Production Line"] = extra_val
            elif "Warehouse" in menu:
                new_row["Warehouse Location"] = extra_val
            elif "Procurement" in menu:
                new_row["Supplier"] = extra_val
            elif "Transport" in menu:
                new_row["Transport"] = extra_val
                
            updated_df = pd.concat([df_current, new_row], ignore_index=True)
            save_to_github(updated_df, current_file, f"Motherson PKC Add row in {menu}", file_sha)
