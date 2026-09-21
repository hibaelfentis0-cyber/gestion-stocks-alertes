import streamlit as st
from github import Github
import pandas as pd
from io import BytesIO

# Page configuration
st.set_page_config(page_title="Stock Management & Alerts", layout="wide")

# GitHub Connection using Streamlit Secrets
try:
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo("hibaelfentis0-cyber/gestion-stocks-alertes")
except Exception as e:
    st.error(f"GitHub Connection Error: {e}")

st.title("📊 Stock Management & Alerts System")

# Navigation menu with symbols (Dashboard + 4 Departments)
menu = st.sidebar.radio(
    "Navigation Menu", 
    ["📈 General Dashboard", "🏭 Production", "🛒 Procurement", "📦 Warehouse", "🚚 Transport"]
)

# Map departments to their respective Excel files
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
        # Fallback dummy data if file doesn't exist yet
        data = {
            "Alert ID": ["ALT-001", "ALT-002"],
            "Date": ["2026-06-01", "2026-06-02"],
            "Product Code": ["PRD-A", "PRD-B"],
            "Product Description": ["Beauty Blender Set", "Makeup Brush Pro"],
            "Quantity Available": [10, 5],
            "Quantity Required": [50, 30],
            "Shortage Quantity": [40, 25],
            "Comments": ["Urgent restock", "Pending check"]
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
        st.success("Changes successfully saved to GitHub!")
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

# --- 1. GENERAL DASHBOARD ---
if menu == "📈 General Dashboard":
    st.header("📈 General Stock Dashboard")
    st.markdown("Overview of all key metrics and global inventory status across departments.")
    
    # Load all department files for the dashboard overview
    dfs = []
    for dept_name, fname in file_mapping.items():
        d_df, _ = load_excel_data(fname)
        d_df["Department"] = dept_name
        dfs.append(d_df)
    
    if dfs:
        global_df = pd.concat(dfs, ignore_index=True)
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
            st.metric("Total Shortage Qty", tot_short)
            
        st.markdown("---")
        st.subheader("Combined Data View")
        st.dataframe(global_df, use_container_width=True)

# --- 2. SPECIFIC DEPARTMENTS ---
else:
    current_file = file_mapping[menu]
    df, file_sha = load_excel_data(current_file)
    
    st.header(menu)
    
    if "Production" in menu:
        st.markdown("Monitor production lines, material requirements, and operational alerts.")
        specific_cols = base_columns + ["Production Line", "Comments"]
    elif "Warehouse" in menu:
        st.markdown("Manage warehouse locations, inventory availability, and stock checks.")
        specific_cols = base_columns + ["Warehouse Location", "Comments"]
    elif "Procurement" in menu:
        st.markdown("Manage suppliers, purchase orders, expected deliveries (ETA), and purchasing statuses.")
        specific_cols = base_columns + ["Supplier", "Purchase Order", "Order Date", "Expected Delivery", "Purchasing Status", "Comments"]
    elif "Transport" in menu:
        st.markdown("Track shipping methods, carriers, and transit details.")
        specific_cols = base_columns + ["Transport", "Comments"]
    
    for col in specific_cols:
        if col not in df.columns:
            df[col] = ""
            
    df_view = df[specific_cols]
    
    # Editor config
    column_configs = {}
    if "Purchasing Status" in specific_cols:
        valid_statuses = ["Pending", "Ordered", "Shipped", "Delivered", "Cancelled"]
        df_view["Purchasing Status"] = df_view["Purchasing Status"].apply(lambda x: x if x in valid_statuses else "Pending")
        column_configs["Purchasing Status"] = st.column_config.SelectboxColumn("Purchasing Status", options=valid_statuses, required=True)
    if "Transport" in specific_cols:
        column_configs["Transport"] = st.column_config.SelectboxColumn("Transport Method", options=["Air", "Sea", "Road", "Express"], required=True)

    edited_df = st.data_editor(
        df_view,
        column_config=column_configs,
        num_rows="dynamic",
        key=f"{menu}_editor"
    )
    
    if st.button(f"Save {menu} Changes"):
        for col in specific_cols:
            df[col] = edited_df[col]
        save_to_github(df, current_file, f"Update {menu} data from Streamlit", file_sha)

    with st.form(f"add_form_{menu}"):
        st.subheader(f"Add New Entry to {menu}")
        prod_code = st.text_input("Product Code", "PRD-NEW")
        prod_desc = st.text_input("Product Description", "Description")
        
        extra_val = ""
        if "Production" in menu:
            extra_val = st.text_input("Production Line", "Line 1")
        elif "Warehouse" in menu:
            extra_val = st.text_input("Warehouse Location", "Zone A")
        elif "Procurement" in menu:
            extra_val = st.text_input("Supplier", "Supplier Name")
        elif "Transport" in menu:
            extra_val = st.selectbox("Transport Method", ["Air", "Sea", "Road", "Express"])
            
        submit_add = st.form_submit_button("Add and Save to GitHub")
        
        if submit_add:
            df_current = df.copy()
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
            save_to_github(updated_df, current_file, f"Add new row in {menu} via form", file_sha)
