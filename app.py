import streamlit as st
from github import Github
import pandas as pd
from io import BytesIO
from datetime import datetime

# Page configuration
st.set_page_config(page_title="Motherson PKC - Stock & Alert System", page_icon="🏢", layout="wide")

# Custom UI styling
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
st.title("🏢 Motherson PKC — Advanced Stock & Alert System")
st.markdown("Industrial tracking, inventory monitoring, advanced KPIs, and supply chain control.")
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

# Common base columns for all departments
base_columns = [
    "Alert ID", 
    "Date", 
    "Product Code", 
    "Product Description", 
    "Quantity Available", 
    "Quantity Required", 
    "Shortage Quantity",
    "Last Updated"
]

# Function to load data (Returns an empty DataFrame if file doesn't exist yet)
def load_excel_data(filename, dept_name):
    try:
        file_content = repo.get_contents(filename)
        decoded_content = file_content.decoded_content
        df = pd.read_excel(BytesIO(decoded_content))
        return df, file_content.sha
    except Exception:
        # Define specific columns per department for empty setup
        if "Production" in dept_name:
            cols = base_columns + ["Production Line", "Comments"]
        elif "Warehouse" in dept_name:
            cols = base_columns + ["Warehouse Location", "Comments"]
        elif "Procurement" in dept_name:
            cols = base_columns + ["Supplier", "Purchase Order", "Order Date", "ETA", "Purchasing Status", "Comments"]
        elif "Transport" in dept_name:
            cols = base_columns + ["Transport", "Truck Number", "Comments"]
        else:
            cols = base_columns + ["Comments"]
            
        empty_df = pd.DataFrame(columns=cols)
        return empty_df, None

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

# --- 1. GENERAL DASHBOARD ---
if menu == "📈 General Dashboard":
    st.header("📈 General Dashboard & Advanced Analytics")
    st.markdown("Overview of key inventory metrics, service level rates, shortages, and global tracking.")
    
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

        # Advanced KPIs & Service Level
        tot_avail = global_df["Quantity Available"].sum() if "Quantity Available" in global_df.columns else 0
        tot_req = global_df["Quantity Required"].sum() if "Quantity Required" in global_df.columns else 0
        tot_short = global_df["Shortage Quantity"].sum() if "Shortage Quantity" in global_df.columns else 0
        
        service_rate = (tot_avail / tot_req * 100) if tot_req > 0 else 100
        service_rate = min(service_rate, 100.0)

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Records", len(global_df))
        with col2:
            st.metric("Total Available Qty", tot_avail)
        with col3:
            st.metric("Total Required Qty", tot_req)
        with col4:
            st.metric("Shortage Quantity", tot_short, delta="Critical" if tot_short > 0 else "OK", delta_color="inverse")
        with col5:
            st.metric("Taux de Service", f"{service_rate:.1f}%", delta="Couverture Stock" if service_rate >= 80 else "Risque Rupture", delta_color="normal" if service_rate >= 80 else "inverse")
            
        st.markdown("---")
        
        # Export Excel Button
        st.subheader("📥 Export & Reports for Meetings")
        output_excel = BytesIO()
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            global_df.to_excel(writer, index=False)
        excel_data = output_excel.getvalue()
        
        st.download_button(
            label="📥 Télécharger le rapport global complet (.xlsx)",
            data=excel_data,
            file_name=f"Motherson_PKC_Global_Report_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.markdown("---")
        
        # Visual Charts Section
        if len(global_df) > 0 and global_df["Quantity Available"].sum() > 0:
            st.subheader("📊 Visual Analytics & Stock Status")
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.markdown("**Quantities by Department (Available vs Required)**")
                dept_summary = global_df.groupby("Department")[["Quantity Available", "Quantity Required"]].sum()
                st.bar_chart(dept_summary)
            with col_chart2:
                st.markdown("**Shortage Quantity per Product**")
                shortage_summary = global_df.groupby("Product Code")["Shortage Quantity"].sum()
                st.bar_chart(shortage_summary)
        else:
            st.info("ℹ️ Aucune donnée enregistrée pour le moment. Utilisez les onglets de département pour ajouter vos premières lignes.")

# --- 2. SPECIFIC DEPARTMENTS ---
else:
    current_file = file_mapping[menu]
    df, file_sha = load_excel_data(current_file, menu)
    
    st.header(f"Motherson PKC - {menu}")
    
    if "Production" in menu:
        st.markdown("Monitor assembly lines, operational status, and production stock alerts.")
        specific_cols = base_columns + ["Production Line", "Comments"]
    elif "Warehouse" in menu:
        st.markdown("Manage material locations, warehouse zones, and warehouse stock check.")
        specific_cols = base_columns + ["Warehouse Location", "Comments"]
    elif "Procurement" in menu:
        st.markdown("Manage suppliers, purchase orders, lancer commande, ETA, and purchasing statuses.")
        specific_cols = base_columns + ["Supplier", "Purchase Order", "Order Date", "ETA", "Purchasing Status", "Comments"]
    elif "Transport" in menu:
        st.markdown("Track shipments, carriers, Truck Number, and transport tracking logistics.")
        specific_cols = base_columns + ["Transport", "Truck Number", "Comments"]
    
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

    def color_criticality(row):
        try:
            shortage = float(row["Shortage Quantity"])
        except:
            shortage = 0
        
        if shortage > 500:
            return ['background-color: #fee2e2; color: #991b1b'] * len(row)
        elif shortage > 0:
            return ['background-color: #fef3c7; color: #92400e'] * len(row)
        else:
            return ['background-color: #ecfdf5; color: #065f46'] * len(row)

    st.markdown("### 📋 Données du département (Coloré selon la criticité du manque)")
    st.caption("🟢 Vert = OK / 🟠 Orange = Manque modéré / 🔴 Rouge = Manque critique (> 500 unités)")
    
    edited_df = st.data_editor(
        df_view,
        column_config=column_configs,
        num_rows="dynamic",
        key=f"{menu}_editor"
    )
    
    col_btn1, _ = st.columns([1, 5])
    with col_btn1:
        save_btn = st.button("💾 Save Changes")
        
    if save_btn:
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        edited_df["Last Updated"] = current_time_str
        save_to_github(edited_df, current_file, f"Motherson PKC Update: {menu}", file_sha)

    with st.form(f"add_form_{menu}"):
        st.subheader(f"➕ Add New Entry to {menu}")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            prod_code = st.text_input("Product Code", "")
        with f_col2:
            prod_desc = st.text_input("Product Description", "")
        
        extra_val = ""
        extra_val_transport = ""
        
        if "Production" in menu:
            extra_val = st.text_input("Production Line", "")
        elif "Warehouse" in menu:
            extra_val = st.text_input("Warehouse Location", "")
        elif "Procurement" in menu:
            extra_val = st.text_input("Supplier", "")
        elif "Transport" in menu:
            extra_val = st.selectbox("Transport Method", ["Air", "Sea", "Road", "Express"])
            extra_val_transport = st.text_input("Truck Number", "")
            
        submit_add = st.form_submit_button("🚀 Add and Sync to GitHub")
        
        if submit_add:
            df_current = edited_df.copy()
            new_row = df_current.iloc[[0]].copy() if len(df_current) > 0 else pd.DataFrame([{col: "" for col in specific_cols}])
            new_row["Alert ID"] = f"ALT-{len(df_current)+1:03d}"
            new_row["Date"] = datetime.now().strftime("%Y-%m-%d")
            new_row["Product Code"] = prod_code
            new_row["Product Description"] = prod_desc
            new_row["Quantity Available"] = 0
            new_row["Quantity Required"] = 0
            new_row["Shortage Quantity"] = 0
            new_row["Last Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            if "Production" in menu:
                new_row["Production Line"] = extra_val
            elif "Warehouse" in menu:
                new_row["Warehouse Location"] = extra_val
            elif "Procurement" in menu:
                new_row["Supplier"] = extra_val
                new_row["Purchase Order"] = ""
                new_row["Order Date"] = ""
                new_row["ETA"] = ""
                new_row["Purchasing Status"] = "Pending"
            elif "Transport" in menu:
                new_row["Transport"] = extra_val
                new_row["Truck Number"] = extra_val_transport
                
            updated_df = pd.concat([df_current, new_row], ignore_index=True)
            save_to_github(updated_df, current_file, f"Motherson PKC Add row in {menu}", file_sha)
