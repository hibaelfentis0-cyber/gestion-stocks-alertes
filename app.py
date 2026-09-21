import streamlit as st
from github import Github
import pandas as pd
from io import BytesIO
from datetime import datetime

# Page configuration
st.set_page_config(page_title="Motherson PKC - Stock & Alert Workflow", page_icon="🏢", layout="wide")

# Custom UI styling
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #d1d5db; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    h1, h2, h3 { color: #1e3a8a; }
    </style>
""", unsafe_allow_html=True)

# GitHub Connection
try:
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo("hibaelfentis0-cyber/gestion-stocks-alertes")
except Exception as e:
    st.error(f"GitHub Connection Error: {e}")

st.title("🏢 Motherson PKC — Workflow Logistique")
st.markdown("Procédure automatisée : Production -> Warehouse -> Procurement -> Transport")
st.markdown("---")

menu = st.sidebar.radio(
    "Navigation Menu", 
    ["📈 General Dashboard", "🏭 Production", "📦 Warehouse", "🛒 Procurement", "🚚 Transport"]
)

file_mapping = {
    "🏭 Production": "01_Production_Stock_Alert.xlsx",
    "📦 Warehouse": "02_Warehouse_Stock_Alert.xlsx",
    "🛒 Procurement": "03_Procurement_Supply_Stock_Alert.xlsx",
    "🚚 Transport": "04_Transport_Delivery_Stock_Alert.xlsx"
}

# Colonnes de base partagées par tout le monde
base_columns = [
    "Alert ID", 
    "Date", 
    "Product Code", 
    "Product Description", 
    "Quantity Required (Prod)", 
    "Quantity Available (Warehouse)", 
    "Shortage",
    "Workflow Status",
    "Last Updated"
]

def load_excel_data(filename, dept_name):
    try:
        file_content = repo.get_contents(filename)
        df = pd.read_excel(BytesIO(file_content.decoded_content))
    except:
        df = pd.DataFrame()
        
    # Auto-synchronisation intelligente depuis la Production
    if dept_name != "🏭 Production":
        prod_file = file_mapping["🏭 Production"]
        try:
            prod_content = repo.get_contents(prod_file)
            prod_df = pd.read_excel(BytesIO(prod_content.decoded_content))
        except:
            prod_df = pd.DataFrame()
            
        if not prod_df.empty:
            specific_data_map = {}
            if not df.empty and "Product Code" in df.columns:
                for _, row in df.iterrows():
                    p_code = row.get("Product Code")
                    if pd.notna(p_code): specific_data_map[p_code] = row.to_dict()

            new_rows = []
            for _, prod_row in prod_df.iterrows():
                p_code = prod_row.get("Product Code", "")
                
                # Base issue from production
                req = pd.to_numeric(prod_row.get("Quantity Required (Prod)", 0), errors='coerce')
                if pd.isna(req): req = 0
                
                # By default, take available from what's already saved in this department, or 0
                avail = 0
                if p_code in specific_data_map:
                    avail = pd.to_numeric(specific_data_map[p_code].get("Quantity Available (Warehouse)", 0), errors='coerce')
                    if pd.isna(avail): avail = 0

                # Calculate Shortage
                shortage = req - avail
                if shortage <= 0:
                    shortage = 0
                    workflow_status = "✅ OK (Resolved in Warehouse)"
                else:
                    workflow_status = "⚠️ Escalate to Procurement"

                row_data = {
                    "Alert ID": prod_row.get("Alert ID", ""),
                    "Date": prod_row.get("Date", ""),
                    "Product Code": p_code,
                    "Product Description": prod_row.get("Product Description", ""),
                    "Quantity Required (Prod)": req,
                    "Quantity Available (Warehouse)": avail,
                    "Shortage": shortage,
                    "Workflow Status": workflow_status,
                    "Last Updated": prod_row.get("Last Updated", "")
                }
                
                if p_code in specific_data_map:
                    old_row = specific_data_map[p_code]
                    for col in df.columns:
                        if col not in row_data: row_data[col] = old_row.get(col, "")
                else:
                    if "Warehouse" in dept_name:
                        row_data["Warehouse Location"] = ""
                    elif "Procurement" in dept_name:
                        row_data["Supplier"] = ""
                        row_data["Purchase Order"] = ""
                        row_data["ETA"] = ""
                        row_data["Procurement Status"] = "Pending"
                    elif "Transport" in dept_name:
                        row_data["Truck Number"] = ""
                        row_data["Transport Status"] = "Waiting"
                        
                new_rows.append(row_data)
            df = pd.DataFrame(new_rows)
            
    # Colonnes spécifiques
    if dept_name == "🏭 Production":
        cols = base_columns + ["Production Line"]
    elif "Warehouse" in dept_name:
        cols = base_columns + ["Warehouse Location"]
    elif "Procurement" in dept_name:
        cols = base_columns + ["Supplier", "Purchase Order", "ETA", "Procurement Status"]
    elif "Transport" in dept_name:
        cols = base_columns + ["Truck Number", "Transport Status"]
    else:
        cols = base_columns
        
    for col in cols:
        if col not in df.columns: df[col] = ""

    try:
        fc = repo.get_contents(filename)
        sha = fc.sha
    except:
        sha = None
        
    return df, sha

def save_to_github(dataframe, filename, message_text, file_sha):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: dataframe.to_excel(writer, index=False)
    updated_excel = output.getvalue()
    try:
        if file_sha: repo.update_file(path=filename, message=message_text, content=updated_excel, sha=file_sha)
        else: repo.create_file(path=filename, message=message_text, content=updated_excel)
    except Exception as err: st.error(f"Error saving: {err}")

# --- DASHBOARD ---
if menu == "📈 General Dashboard":
    st.header("📈 Workflow Global")
    st.markdown("Suivi du flux : Si l'alerte n'est pas résolue par le Warehouse, elle passe aux Achats.")
    
    prod_df, _ = load_excel_data(file_mapping["🏭 Production"], "🏭 Production")
    wh_df, _ = load_excel_data(file_mapping["📦 Warehouse"], "📦 Warehouse")
    proc_df, _ = load_excel_data(file_mapping["🛒 Procurement"], "🛒 Procurement")
    trans_df, _ = load_excel_data(file_mapping["🚚 Transport"], "🚚 Transport")

    # Si on a de la donnée dans Procurement, c'est le statut final qu'on veut voir
    if not proc_df.empty:
        st.dataframe(proc_df, use_container_width=True)
    else:
        st.info("Aucune donnée dans le workflow pour le moment.")

# --- DEPARTMENTS ---
else:
    current_file = file_mapping[menu]
    df, file_sha = load_excel_data(current_file, menu)
    st.header(f"Motherson PKC - {menu}")
    
    if "Production" in menu:
        st.info("💡 Etape 1 : Saisissez ici le besoin (Quantity Required).")
        specific_cols = base_columns + ["Production Line"]
    elif "Warehouse" in menu:
        st.info("💡 Etape 2 : Saisissez la quantité disponible (Quantity Available). Si ça couvre le besoin, la procédure s'arrête.")
        specific_cols = base_columns + ["Warehouse Location"]
    elif "Procurement" in menu:
        st.warning("⚠️ Etape 3 : Traitez uniquement les lignes en 'Escalate to Procurement'.")
        specific_cols = base_columns + ["Supplier", "Purchase Order", "ETA", "Procurement Status"]
    elif "Transport" in menu:
        st.info("🚚 Etape 4 : Suivez les commandes en cours d'acheminement.")
        specific_cols = base_columns + ["Truck Number", "Transport Status"]
    
    df_view = df[specific_cols]
    
    column_configs = {}
    if "Procurement Status" in specific_cols:
        opts = ["Pending", "Ordered", "In Transit", "Delivered"]
        df_view["Procurement Status"] = df_view["Procurement Status"].apply(lambda x: x if x in opts else "Pending")
        column_configs["Procurement Status"] = st.column_config.SelectboxColumn("Status", options=opts)
    if "Transport Status" in specific_cols:
        opts = ["Waiting", "Loading", "On the Road", "Arrived"]
        df_view["Transport Status"] = df_view["Transport Status"].apply(lambda x: x if x in opts else "Waiting")
        column_configs["Transport Status"] = st.column_config.SelectboxColumn("Status", options=opts)

    edited_df = st.data_editor(df_view, column_config=column_configs, num_rows="dynamic", key=f"{menu}_editor")
    
    if st.button("💾 Save Changes"):
        edited_df["Last Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Auto calculate Shortage and Workflow Status
        if "Quantity Available (Warehouse)" in edited_df.columns and "Quantity Required (Prod)" in edited_df.columns:
            edited_df["Quantity Available (Warehouse)"] = pd.to_numeric(edited_df["Quantity Available (Warehouse)"], errors='coerce').fillna(0)
            edited_df["Quantity Required (Prod)"] = pd.to_numeric(edited_df["Quantity Required (Prod)"], errors='coerce').fillna(0)
            edited_df["Shortage"] = edited_df["Quantity Required (Prod)"] - edited_df["Quantity Available (Warehouse)"]
            edited_df["Shortage"] = edited_df["Shortage"].apply(lambda x: x if x > 0 else 0)
            edited_df["Workflow Status"] = edited_df["Shortage"].apply(lambda x: "⚠️ Escalate to Procurement" if x > 0 else "✅ OK (Resolved in Warehouse)")
            
        save_to_github(edited_df, current_file, f"Update {menu}", file_sha)
        st.success("✅ Données sauvegardées ! Le Workflow a été mis à jour.")
        st.rerun()

    # Form to add entry (Mainly for Production)
    if menu == "🏭 Production":
        with st.form("add_form"):
            st.subheader("➕ Nouvelle Alerte Production")
            prod_code = st.text_input("Product Code")
            prod_desc = st.text_input("Product Description")
            qty_req = st.number_input("Quantity Required", min_value=1, value=100)
            p_line = st.text_input("Production Line")
            
            if st.form_submit_button("🚀 Créer l'Alerte"):
                new_row = pd.DataFrame([{
                    "Alert ID": f"ALT-{len(edited_df)+1:03d}",
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Product Code": prod_code,
                    "Product Description": prod_desc,
                    "Quantity Required (Prod)": qty_req,
                    "Quantity Available (Warehouse)": 0,
                    "Shortage": qty_req,
                    "Workflow Status": "⚠️ Escalate to Procurement",
                    "Production Line": p_line,
                    "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M")
                }])
                updated_df = pd.concat([edited_df, new_row], ignore_index=True)
                save_to_github(updated_df, current_file, "Add Alert", file_sha)
                st.success("✅ Alerte créée et envoyée au Warehouse !")
                st.rerun()
