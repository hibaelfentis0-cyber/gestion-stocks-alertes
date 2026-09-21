import streamlit as st
from github import Github
import pandas as pd
from io import StringIO

# Page configuration
st.set_page_config(page_title="Stock Management & Alerts", layout="wide")

# GitHub Connection using Streamlit Secrets
try:
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo("hibaelfentis0-cyber/gestion-stocks-alertes")
except Exception as e:
    st.error(f"GitHub Connection Error: {e}")

st.title("Stock Management & Alerts System")

# Navigation menu for the 4 departments
department = st.sidebar.selectbox(
    "Select Department", 
    ["Production", "Procurement", "Warehouse", "Transport"]
)

# Function to load data from GitHub
@st.cache_data(ttl=60)
def load_data():
    try:
        file_content = repo.get_contents("data/stock.csv")
        decoded_content = file_content.decoded_content.decode("utf-8")
        df = pd.read_csv(StringIO(decoded_content))
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
            "Production Line": ["Line 1", "Line 2"],
            "Supplier": ["Anhui Beili", "Cosmetic Hub"],
            "Purchase Order": ["PO-1001", "PO-1002"],
            "Order Date": ["2026-06-03", "2026-06-04"],
            "Expected Delivery": ["2026-06-15", "2026-06-20"],
            "Purchasing Status": ["Pending", "Ordered"],
            "Transport": ["Air", "Sea"],
            "Warehouse Location": ["Zone A - Racks", "Zone B - Shelves"],
            "Comments": ["Urgent restock", "Pending check"]
        }
        return pd.DataFrame(data), None

df, file_sha = load_data()

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

# Helper function to save changes to GitHub
def save_to_github(dataframe, message_text):
    updated_csv = dataframe.to_csv(index=False)
    try:
        repo.update_file(
            path="data/stock.csv",
            message=message_text,
            content=updated_csv,
            sha=file_sha
        )
        st.success("Changes successfully saved to GitHub!")
        st.rerun()
    except Exception as err:
        st.error(f"Error saving to GitHub: {err}")

# --- 1. PRODUCTION DEPARTMENT ---
if department == "Production":
    st.header("Production Department")
    st.markdown("Monitor production lines, material requirements, and operational alerts.")
    
    production_columns = base_columns + ["Production Line", "Comments"]
    
    for col in production_columns:
        if col not in df.columns:
            df[col] = ""
            
    df_production = df[production_columns]
    
    edited_production = st.data_editor(
        df_production,
        num_rows="dynamic",
        key="production_editor"
    )
    
    if st.button("Save Production Changes"):
        for col in production_columns:
            df[col] = edited_production[col]
        save_to_github(df, "Update production data from Streamlit")

    # Form to add a new item
    with st.form("add_production_form"):
        st.subheader("Add New Production Entry")
        prod_code = st.text_input("Product Code", "PRD-NEW")
        prod_desc = st.text_input("Product Description", "Description")
        prod_line = st.text_input("Production Line", "Line 1")
        submit_add = st.form_submit_button("Add and Save to GitHub")
        
        if submit_add:
            df_current = df.copy()
            new_row = df_current.iloc[[0]].copy() if len(df_current) > 0 else pd.DataFrame([{col: "" for col in production_columns}])
            new_row["Alert ID"] = f"ALT-{len(df_current)+1:03d}"
            new_row["Product Code"] = prod_code
            new_row["Product Description"] = prod_desc
            new_row["Production Line"] = prod_line
            updated_df = pd.concat([df_current, new_row], ignore_index=True)
            save_to_github(updated_df, "Add new row in Production via form")

# --- 2. PROCUREMENT DEPARTMENT ---
elif department == "Procurement":
    st.header("Procurement Department")
    st.markdown("Manage suppliers, purchase orders, expected deliveries (ETA), and purchasing statuses.")
    
    procurement_columns = base_columns + [
        "Supplier", 
        "Purchase Order", 
        "Order Date", 
        "Expected Delivery", 
        "Purchasing Status", 
        "Comments"
    ]
    
    for col in procurement_columns:
        if col not in df.columns:
            df[col] = ""
            
    df_procurement = df[procurement_columns]
    
    edited_procurement = st.data_editor(
        df_procurement,
        column_config={
            "Purchasing Status": st.column_config.SelectboxColumn(
                "Purchasing Status",
                options=["Pending", "Ordered", "Shipped", "Delivered", "Cancelled"],
                required=True
            ),
            "Expected Delivery": st.column_config.DateColumn(
                "Expected Delivery (ETA)",
                format="YYYY-MM-DD",
                required=True
            ),
            "Order Date": st.column_config.DateColumn(
                "Order Date",
                format="YYYY-MM-DD",
                required=False
            )
        },
        num_rows="dynamic",
        key="procurement_editor"
    )
    
    if st.button("Save Procurement Changes"):
        for col in procurement_columns:
            df[col] = edited_procurement[col]
        save_to_github(df, "Update procurement data from Streamlit")

    # Form to add a new item
    with st.form("add_procurement_form"):
        st.subheader("Add New Procurement Entry")
        prod_code = st.text_input("Product Code", "PRD-NEW")
        prod_desc = st.text_input("Product Description", "Description")
        supplier = st.text_input("Supplier", "Supplier Name")
        submit_add = st.form_submit_button("Add and Save to GitHub")
        
        if submit_add:
            df_current = df.copy()
            new_row = df_current.iloc[[0]].copy() if len(df_current) > 0 else pd.DataFrame([{col: "" for col in procurement_columns}])
            new_row["Alert ID"] = f"ALT-{len(df_current)+1:03d}"
            new_row["Product Code"] = prod_code
            new_row["Product Description"] = prod_desc
            new_row["Supplier"] = supplier
            updated_df = pd.concat([df_current, new_row], ignore_index=True)
            save_to_github(updated_df, "Add new row in Procurement via form")

# --- 3. WAREHOUSE DEPARTMENT ---
elif department == "Warehouse":
    st.header("Warehouse Department")
    st.markdown("Manage warehouse locations, inventory availability, and stock checks.")
    
    warehouse_columns = base_columns + ["Warehouse Location", "Comments"]
    
    for col in warehouse_columns:
        if col not in df.columns:
            df[col] = ""
            
    df_warehouse = df[warehouse_columns]
    
    edited_warehouse = st.data_editor(
        df_warehouse,
        num_rows="dynamic",
        key="warehouse_editor"
    )
    
    if st.button("Save Warehouse Changes"):
        for col in warehouse_columns:
            df[col] = edited_warehouse[col]
        save_to_github(df, "Update warehouse data from Streamlit")

    # Form to add a new item
    with st.form("add_warehouse_form"):
        st.subheader("Add New Warehouse Entry")
        prod_code = st.text_input("Product Code", "PRD-NEW")
        prod_desc = st.text_input("Product Description", "Description")
        location = st.text_input("Warehouse Location", "Zone A")
        submit_add = st.form_submit_button("Add and Save to GitHub")
        
        if submit_add:
            df_current = df.copy()
            new_row = df_current.iloc[[0]].copy() if len(df_current) > 0 else pd.DataFrame([{col: "" for col in warehouse_columns}])
            new_row["Alert ID"] = f"ALT-{len(df_current)+1:03d}"
            new_row["Product Code"] = prod_code
            new_row["Product Description"] = prod_desc
            new_row["Warehouse Location"] = location
            updated_df = pd.concat([df_current, new_row], ignore_index=True)
            save_to_github(updated_df, "Add new row in Warehouse via form")

# --- 4. TRANSPORT DEPARTMENT ---
elif department == "Transport":
    st.header("Transport Department")
    st.markdown("Track shipping methods, carriers, and transit details.")
    
    transport_columns = base_columns + ["Transport", "Comments"]
    
    for col in transport_columns:
        if col not in df.columns:
            df[col] = ""
            
    df_transport = df[transport_columns]
    
    edited_transport = st.data_editor(
        df_transport,
        column_config={
            "Transport": st.column_config.SelectboxColumn(
                "Transport Method",
                options=["Air", "Sea", "Road", "Express"],
                required=True
            )
        },
        num_rows="dynamic",
        key="transport_editor"
    )
    
    if st.button("Save Transport Changes"):
        for col in transport_columns:
            df[col] = edited_transport[col]
        save_to_github(df, "Update transport data from Streamlit")

    # Form to add a new item
    with st.form("add_transport_form"):
        st.subheader("Add New Transport Entry")
        prod_code = st.text_input("Product Code", "PRD-NEW")
        prod_desc = st.text_input("Product Description", "Description")
        transport_method = st.selectbox("Transport Method", ["Air", "Sea", "Road", "Express"])
        submit_add = st.form_submit_button("Add and Save to GitHub")
        
        if submit_add:
            df_current = df.copy()
            new_row = df_current.iloc[[0]].copy() if len(df_current) > 0 else pd.DataFrame([{col: "" for col in transport_columns}])
            new_row["Alert ID"] = f"ALT-{len(df_current)+1:03d}"
            new_row["Product Code"] = prod_code
            new_row["Product Description"] = prod_desc
            new_row["Transport"] = transport_method
            updated_df = pd.concat([df_current, new_row], ignore_index=True)
            save_to_github(updated_df, "Add new row in Transport via form")
