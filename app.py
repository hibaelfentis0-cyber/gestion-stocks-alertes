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

# Load data function with strict role separation (Production = Required, Warehouse = Available)
def load_excel_data(filename, dept_name):
    try:
        file_content = repo.get_contents(filename)
        df = pd.read_excel(BytesIO(file_content.decoded_content))
    except Exception:
        df = pd.DataFrame()
        
    # Load both master files to merge Production Requirements and Warehouse Available Stocks
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

    # Build unified mapping of Product Codes to aggregate Required (from Prod) and Available (from Wh)
    master_codes = set()
    if not prod_df.empty and "Product Code" in prod_df.columns:
        master_codes.update(prod_df["Product Code"].dropna().tolist())
    if not wh_df.empty and "Product Code" in wh_df.columns:
        master_codes.update(wh_df["Product Code"].dropna().tolist())
    if not df.empty and "Product Code" in df.columns:
        master_codes.update(df["Product Code"].dropna().tolist())

    # Map details from respective dataframes
    prod_map = {r.get("Product Code"): r for _, r in prod_df.iterrows() if pd.notna(r.get("Product Code"))} if not prod_df.empty else {}
    wh_map = {r.get("Product Code"): r for _, r in wh_df.iterrows() if pd.notna(r.get("Product Code"))} if not wh_df.empty else {}
    current_map = {r.get("Product Code"): r for _, r in df.iterrows() if pd.notna(r.get("Product Code"))} if not df.empty else {}

    combined_rows = []
    for p_code in master_codes:
        # Quantity Required primarily comes from Production
        req = pd.to_numeric(prod_map.get(p_code, current_map.get(p_code, {})).get("Quantity Required", 0), errors='coerce')
        # Quantity Available primarily comes from Warehouse
        avail = pd.to_numeric(wh_map.get(p_code, current_map.get(p_code, {})).get("Quantity Available", 0), errors='coerce')
        
        base_src = prod_map.get(p_code, wh_map.get(p_code, current_map.get(p_code, {})))
        
        temp_dict = {
            "Quantity Available": avail, "Quantity Required": req,
            "Daily Consumption": base_src.get("Daily Consumption", 5),
            "Lead Time": base_src.get("Lead Time", 5),
            "Safety Stock": base_src.get("Safety Stock", 10)
        }
        stock_status, priority, shortage, reorder_point, stock_out_date = calculate_intelligence(temp_dict)

        row_data = {
            "Alert ID": base_src.get("Alert ID", f"ALT-{p_code}"),
            "Date": base_src.get("Date", datetime.now().strftime("%Y-%m-%d")),
            "Product Code": p_code,
            "Product Description": base_src.get("Product Description", "None"),
            "Quantity Available": avail,
            "Quantity Required": req,
            "Shortage Quantity": shortage,
            "Stock Status": stock_status,
            "Priority": priority,
            "Daily Consumption": base_src.get("Daily Consumption", 5),
            "Lead Time": base_src.get("Lead Time", 5),
            "Safety Stock": base_src.get("Safety Stock", 10),
            "Reorder Point": reorder_point,
            "Estimated Stock-Out Date": stock_out_date,
            "Lifecycle Stage": base_src.get("Lifecycle Stage", "Alert Created"),
            "Last Updated": base_src.get("Last Updated", datetime.now().strftime("%Y-%m-%d %H:%M")),
            "Production Line": base_src.get("Production Line", ""),
            "Warehouse Location": base_src.get("Warehouse Location", ""),
            "Comments": base_src.get("Comments", "")
        }
        combined_rows.append(row_data)

    final_df = pd.DataFrame(combined_rows)

    # Filter for Procurement / Transport if necessary
    if dept_name in ["🛒 Procurement", "🚚 Transport"]:
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
        shortages_count = len(global_df[global_df["Stock Status"] == "🔴 Shortage"])
        
        k1, k2, k3 = st.columns(3)
        with k1: st.metric("Total Items Tracked", total_alerts)
        with k2: st.metric("Shortages", shortages_count)
        with k3: st.metric("Health Rate", f"{max(0, 100 - (shortages_count*10))}%")
        
        st.dataframe(global_df, use_container_width=True)

# --- 2. SPECIFIC DEPARTMENTS ---
else:
    current_file = file_mapping[menu]
    df, file_sha = load_excel_data(current_file, menu)
    
    st.header(f"Motherson PKC - {menu}")
    
    if "Production" in menu:
        st.markdown("🏭 **Production Department**: Manage your **Quantity Required** and production parameters. Stock levels synchronize automatically from Warehouse.")
        specific_cols = ["Alert ID", "Date", "Product Code", "Product Description", "Quantity Required", "Quantity Available", "Shortage Quantity", "Stock Status", "Priority", "Production Line", "Last Updated", "Comments"]
    elif "Warehouse" in menu:
        st.markdown("📦 **Warehouse Department**: Manage your **Quantity Available** (Stock). Requirements synchronize automatically from Production.")
        specific_cols = ["Alert ID", "Date", "Product Code", "Product Description", "Quantity Available", "Quantity Required", "Shortage Quantity", "Stock Status", "Priority", "Warehouse Location", "Last Updated", "Comments"]
    elif "Procurement" in menu:
        st.markdown("🛒 **Procurement Escalations**: Items needing immediate replenishment.")
        specific_cols = ["Alert ID", "Date", "Product Code", "Product Description", "Quantity Available", "Quantity Required", "Shortage Quantity", "Stock Status", "Priority", "Supplier", "Procurement Status", "Last Updated"]
    else:
        st.markdown("🚚 **Transport Tracking**")
        specific_cols = ["Alert ID", "Date", "Product Code", "Product Description", "Quantity Available", "Quantity Required", "Shortage Quantity", "Stock Status", "Priority", "Transport", "Transport Status", "Last Updated"]

    df_view = df[[c for c in specific_cols if c in df.columns]]
    
    edited_df = st.data_editor(df_view, num_rows="dynamic", key=f"{menu}_editor")
    
    if st.button("💾 Save Changes & Sync Across Departments"):
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        edited_df["Last Updated"] = current_time_str
        
        # Recalculate metrics
        for idx, r in edited_df.iterrows():
            st_stat, prio, shortage, reorder_pt, st_date = calculate_intelligence(r)
            edited_df.at[idx, "Shortage Quantity"] = shortage
            edited_df.at[idx, "Stock Status"] = st_stat
            edited_df.at[idx, "Priority"] = prio
            edited_df.at[idx, "Reorder Point"] = reorder_pt
            edited_df.at[idx, "Estimated Stock-Out Date"] = st_date

        save_to_github(edited_df, current_file, f"Update {menu}", file_sha)
        
        # Also auto-update counterpart file to maintain full bi-directional data flow
        if "Production" in menu or "Warehouse" in menu:
            other_menu = "📦 Warehouse" if "Production" in menu else "🏭 Production"
            other_file = file_mapping[other_menu]
            other_df, other_sha = load_excel_data(other_file, other_menu)
            save_to_github(edited_df, other_file, f"Auto-sync from {menu}", other_sha)
            
        st.success("✅ Changes saved and synchronized instantly across Production and Warehouse!")
        st.rerun()
