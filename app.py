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

# Function to load data with separated roles
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
    if not prod_df.empty and "Product Code" in prod_df.columns:
        master_codes.update(prod_df["Product Code"].dropna().tolist())
    if not wh_df.empty and "Product Code" in wh_df.columns:
        master_codes.update(wh_df["Product Code"].dropna().tolist())
    if not df.empty and "Product Code" in df.columns:
        master_codes.update(df["Product Code"].dropna().tolist())

    prod_map = {r.get("Product Code"): r for _, r in prod_df.iterrows() if pd.notna(r.get("Product Code"))} if not prod_df.empty else {}
    wh_map = {r.get("Product Code"): r for _, r in wh_df.iterrows() if pd.notna(r.get("Product Code"))} if not wh_df.empty else {}
    current_map = {r.get("Product Code"): r for _, r in df.iterrows() if pd.notna(r.get("Product Code"))} if not df.empty else {}

    combined_rows = []
    for p_code in master_codes:
        p_row = prod_map.get(p_code, current_map.get(p_code, {}))
        w_row = wh_map.get(p_code, current_map.get(p_code, {}))
        
        req = pd.to_numeric(p_row.get("Quantity Required", 100), errors='coerce')
        avail = pd.to_numeric(w_row.get("Quantity Available", 50), errors='coerce')
        
        base_src = p_row if dept_name == "🏭 Production" else w_row
        if not base_src:
            base_src = w_row if bool(w_row) else p_row
            
        temp_dict = {
            "Quantity Available": avail, "Quantity Required": req,
            "Daily Consumption": base_src.get("Daily Consumption", 5) if isinstance(base_src, dict) else 5,
            "Lead Time": base_src.get("Lead Time", 5) if isinstance(base_src, dict) else 5,
            "Safety Stock": base_src.get("Safety Stock", 10) if isinstance(base_src, dict) else 10
        }
        stock_status, priority, shortage, reorder_point, stock_out_date = calculate_intelligence(temp_dict)

        # Notification message for Production based on Warehouse check
        if stock_status in ["🔴 Shortage", "🔴 Last Box"]:
            notif_status = f"🚨 ALERT: {stock_status} (Shortage: {shortage} units)"
        elif stock_status == "🟠 Low Stock":
            notif_status = "⚠️ WARNING: Low Stock Level"
        else:
            notif_status = "✅ Normal (Stock OK)"

        row_data = {
            "Alert ID": base_src.get("Alert ID", f"ALT-{p_code}") if isinstance(base_src, dict) else f"ALT-{p_code}",
            "Date": base_src.get("Date", datetime.now().strftime("%Y-%m-%d")) if isinstance(base_src, dict) else datetime.now().strftime("%Y-%m-%d"),
            "Product Code": p_code,
            "Product Description": base_src.get("Product Description", "None") if isinstance(base_src, dict) else "None",
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
            "Lifecycle Stage": base_src.get("Lifecycle Stage", "Alert Created") if isinstance(base_src, dict) else "Alert Created",
            "Last Updated": base_src.get("Last Updated", datetime.now().strftime("%Y-%m-%d %H:%M")) if isinstance(base_src, dict) else datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Production Line": p_row.get("Production Line", "") if isinstance(p_row, dict) else "",
            "Warehouse Location": w_row.get("Warehouse Location", "") if isinstance(w_row, dict) else "",
            "Comments": base_src.get("Comments", "") if isinstance(base_src, dict) else ""
        }
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

    df_view = df[[c for c in specific_cols if c in df.columns]]
    
    edited_df = st.data_editor(df_view, num_rows="dynamic", key=f"{menu}_editor")
    
    if st.button("💾 Save Changes & Sync Across Departments"):
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        edited_df["Last Updated"] = current_time_str
        
        save_to_github(edited_df, current_file, f"Update {menu}", file_sha)
        
        if "Production" in menu or "Warehouse" in menu:
            other_menu = "📦 Warehouse" if "Production" in menu else "🏭 Production"
            other_file = file_mapping[other_menu]
            other_df, other_sha = load_excel_data(other_file, other_menu)
            save_to_github(other_df, other_file, f"Auto-sync from {menu}", other_sha)
            
        st.success("✅ Changes saved and warehouse status notifications synchronized successfully!")
        st.rerun()
