import base64
import json
import pandas as pd
import requests
import streamlit as st

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Supply Chain Control Center", page_icon="📊", layout="wide"
)

# --- FONCTION DE CHARGEMENT PAR DÉFAUT AVEC LES BONS EN-TÊTES ---


def get_default_dataframe(category_name):
  if category_name == "Production":
    return pd.DataFrame({
        "Alert ID": ["PA-001", "PA-002"],
        "Date": ["2026-09-18", "2026-09-18"],
        "Time": ["08:30", "09:15"],
        "Product Code": ["RM-1001", "RM-1002"],
        "Product Description": [
            "Aluminium Component A",
            "Aluminium Component B",
        ],
        "Production Line": ["Line 1", "Line 2"],
        "Current Stock": [420, 850],
        "Minimum Stock": [100, 200],
        "Required Quantity": [300, 250],
        "Priority": ["High", "Medium"],
        "Alert Status": ["Active", "Pending"],
        "Action Required": ["Restock", "Monitor"],
        "Responsible": ["Karim M.", "Sara B."],
        "Comments": ["Urgent delivery", "Stable"],
    })
  elif category_name == "Logistics":
    return pd.DataFrame({
        "Alert ID": ["LG-001"],
        "Date": ["2026-09-18"],
        "Product Code": ["RM-1001"],
        "Product Description": ["Aluminium Component A"],
        "Quantity Available": [420],
        "Quantity Required": [300],
        "Shortage Quantity": [0],
        "Warehouse Location": ["Zone A"],
        "AvailablePallets": [10],
        "Required Pallets": [5],
        "Stock Status": ["Available"],
        "Action Required": ["None"],
        "Responsible Person": ["Karim M."],
        "ProcessingStatus": ["Done"],
        "Comments": ["OK"],
    })
  elif category_name == "Purchasing":
    return pd.DataFrame({
        "Alert ID": ["PU-001"],
        "Date": ["2026-09-18"],
        "Product Code": ["RM-1001"],
        "Product Description": ["Aluminium Component A"],
        "Required Quantity": [300],
        "Current Stock": [420],
        "Shortage Quantity": [0],
        "Supplier": ["Supplier X"],
        "Purchase Order": ["PO-9988"],
        "Order Date": ["2026-09-10"],
        "Expected Delivery": ["2026-09-25"],
        "Lead Time (Days)": [15],
        "Purchasing Status": ["Confirmed"],
        "Priority": ["High"],
        "Comments": ["On track"],
    })
  elif category_name == "Transport":
    return pd.DataFrame({
        "Alert ID": ["TR-001"],
        "Product Code": ["RM-1001"],
        "Product Description": ["Aluminium Component A"],
        "Quantity to Deliver": [300],
        "Number of Pallets": [5],
        "Supplier": ["Supplier X"],
        "Transport Company": ["LogiTrans"],
        "Truck / Vehicle ID": ["TR-123-AB"],
        "Loading Date": ["2026-09-24"],
        "Planned Delivery Date": ["2026-09-25"],
        "Actual Delivery Date": [""],
        "Delivery Status": ["In Transit"],
        "Delay (Days)": [0],
        "Responsible Person": ["Ali T."],
        "Comments": ["Scheduled"],
    })
  return pd.DataFrame()


# --- FONCTIONS DE CHARGEMENT ET SAUVEGARDE VIA API REST GITHUB ---


def load_data(category_name):
  """Charge le fichier CSV depuis GitHub via l'API REST."""
  try:
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    url = f"https://api.github.com/repos/{repo_name}/contents/data/{category_name}.csv"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      file_data = response.json()
      decoded_content = base64.b64decode(file_data["content"]).decode("utf-8")
      return pd.read_csv(pd.io.common.StringIO(decoded_content))
    else:
      return get_default_dataframe(category_name)
  except Exception:
    return get_default_dataframe(category_name)


def save_data(df, category_name):
  """Enregistre le DataFrame sur GitHub via l'API REST (création ou mise à jour)."""
  try:
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    url = f"https://api.github.com/repos/{repo_name}/contents/data/{category_name}.csv"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    csv_content = df.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode("utf-8")).decode(
        "utf-8"
    )

    get_response = requests.get(url, headers=headers)
    sha = None
    if get_response.status_code == 200:
      sha = get_response.json().get("sha")

    data = {
        "message": f"Mise à jour automatique des données {category_name} via Streamlit",
        "content": encoded_content,
        "branch": "main",
    }
    if sha:
      data["sha"] = sha

    put_response = requests.put(url, headers=headers, data=json.dumps(data))

    if put_response.status_code in [200, 201]:
      st.success(
          f"Modifications enregistrées avec succès pour {category_name} sur"
          " GitHub !"
      )
    else:
      st.error(
          f"Erreur GitHub ({put_response.status_code}) :"
          f" {put_response.json().get('message', 'Erreur inconnue')}"
      )
  except Exception as e:
    st.error(f"Erreur technique lors de la sauvegarde : {e}")


# --- MENU LATÉRAL ---
st.sidebar.title("Supply Chain Menu")
menu = st.sidebar.radio(
    "Navigate to",
    [
        "Global Dashboard",
        "Production",
        "Logistics",
        "Purchasing",
        "Transport",
        "Add New Alert",
    ],
)

# --- 1. GLOBAL DASHBOARD ---
if menu == "Global Dashboard":
  st.title("📊 Supply Chain - Global Dashboard")
  st.markdown("Overview and Key Performance Indicators (KPIs) across all departments.")

  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric(label="Production Alerts", value="4", delta="-2 vs yesterday")
  with col2:
    st.metric(label="Logistics Items", value="4", delta="Stable")
  with col3:
    st.metric(label="Purchasing Orders", value="4", delta="+3 pending")
  with col4:
    st.metric(label="Transport Deliveries", value="4", delta="1 delayed")

  st.markdown("---")
  st.subheader("📈 Alerts Distribution by Department")

  chart_data = pd.DataFrame(
      {
          "Department": [
              "Production",
              "Logistics",
              "Purchasing",
              "Transport",
          ],
          "Alerts": [4, 4, 4, 4],
      }
  )
  st.bar_chart(chart_data.set_index("Department"))

# --- 2. MODULE PRODUCTION ---
elif menu == "Production":
  st.title("🏭 Production Processing")
  st.markdown("Manage manufacturing lines, outputs, and production status.")

  df_prod = load_data("Production")
  edited_prod = st.data_editor(
      df_prod, num_rows="dynamic", key="editor_production"
  )

  if st.button("Enregistrer les modifications Production"):
    save_data(edited_prod, "Production")

# --- 3. MODULE LOGISTICS ---
elif menu == "Logistics":
  st.title("📦 Logistics & Warehouse Processing")
  st.markdown("Warehouse stock levels, bin locations, and pallet management.")

  df_log = load_data("Logistics")
  edited_log = st.data_editor(df_log, num_rows="dynamic", key="editor_logistics")

  if st.button("Enregistrer les modifications Logistics"):
    save_data(edited_log, "Logistics")

# --- 4. MODULE PURCHASING ---
elif menu == "Purchasing":
  st.title("🛒 Purchasing Management")
  st.markdown("Track suppliers, purchase orders, and procurement status.")

  df_pur = load_data("Purchasing")
  edited_pur = st.data_editor(
      df_pur, num_rows="dynamic", key="editor_purchasing"
  )

  if st.button("Enregistrer les modifications Purchasing"):
    save_data(edited_pur, "Purchasing")

# --- 5. MODULE TRANSPORT ---
elif menu == "Transport":
  st.title("🚚 Transport & Deliveries")
  st.markdown("Monitor shipping routes, carriers, and delivery statuses.")

  df_tra = load_data("Transport")
  edited_tra = st.data_editor(
      df_tra, num_rows="dynamic", key="editor_transport"
  )

  if st.button("Enregistrer les modifications Transport"):
    save_data(edited_tra, "Transport")

# --- 6. ADD NEW ALERT ---
elif menu == "Add New Alert":
  st.title("➕ Add New Alert")
  st.markdown("Create a new supply chain alert or record.")

  with st.form("new_alert_form"):
    dept = st.selectbox(
        "Department", ["Production", "Logistics", "Purchasing", "Transport"]
    )
    product_code = st.text_input("Product Code")
    description = st.text_input("Product Description")
    qty_avail = st.number_input("Quantity / Value", min_value=0, value=100)

    submit_button = st.form_submit_button(
        "Ajouter et enregistrer sur GitHub"
    )

    if submit_button:
      df_current = load_data(dept)
      # Ajout d'une ligne générique respectant la structure du département choisi
      new_row = df_current.iloc[[0]].copy()
      if "Alert ID" in new_row.columns:
        new_row["Alert ID"] = f"AL-{len(df_current)+1:03d}"
      if "Product Code" in new_row.columns:
        new_row["Product Code"] = product_code
      if "Product Description" in new_row.columns:
        new_row["Product Description"] = description

      updated_df = pd.concat([df_current, new_row], ignore_index=True)
      save_data(updated_df, dept)
