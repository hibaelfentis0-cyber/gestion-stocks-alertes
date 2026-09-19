import base64
import json
import requests
import streamlit as st
import pandas as pd

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Supply Chain Control Center", page_icon="📊", layout="wide"
)

# --- FONCTION DE CHARGEMENT ET SAUVEGARDE VIA API REST GITHUB ---


def load_data(category_name):
  """Charge le fichier CSV depuis GitHub via l'API REST."""
  try:
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    url = f"https://api.github.com/repos/{repo_name}/contents/data/{category_name}.csv"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      file_data = response.json()
      decoded_content = base64.b64decode(file_data["content"]).decode("utf-8")
      return pd.read_csv(pd.io.common.StringIO(decoded_content))
    else:
      # Données par défaut si le fichier n'existe pas encore
      return pd.DataFrame({
          "Alert ID": ["PA-001", "PA-002"],
          "Date": ["2026-09-18", "2026-09-18"],
          "Product Code": ["RM-1001", "RM-1002"],
          "Product Description": [
              "Aluminium Component A",
              "Aluminium Component B",
          ],
          "Quantity Available": [420, 850],
          "Quantity Required": [300, 250],
          "Status": ["Active", "Pending"],
      })
  except Exception:
    return pd.DataFrame({
        "Alert ID": ["PA-001", "PA-002"],
        "Date": ["2026-09-18", "2026-09-18"],
        "Product Code": ["RM-1001", "RM-1002"],
        "Product Description": [
            "Aluminium Component A",
            "Aluminium Component B",
        ],
        "Quantity Available": [420, 850],
        "Quantity Required": [300, 250],
        "Status": ["Active", "Pending"],
    })


def save_data(df, category_name):
  """Enregistre le DataFrame sur GitHub via l'API REST (création ou mise à jour)."""
  try:
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    url = f"https://api.github.com/repos/{repo_name}/contents/data/{category_name}.csv"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    csv_content = df.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode("utf-8")).decode(
        "utf-8"
    )

    # 1. Vérifier si le fichier existe pour récupérer son SHA (nécessaire pour la mise à jour)
    get_response = requests.get(url, headers=headers)
    sha = None
    if get_response.status_code == 200:
      sha = get_response.json().get("sha")

    # 2. Préparer la requête de sauvegarde (création ou mise à jour)
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
    qty_avail = st.number_input("Quantity Available", min_value=0, value=100)
    qty_req = st.number_input("Quantity Required", min_value=0, value=100)

    submit_button = st.form_submit_button(
        "Ajouter et enregistrer sur GitHub"
    )

    if submit_button:
      df_current = load_data(dept)
      new_row = pd.DataFrame({
          "Alert ID": [f"AL-{len(df_current)+1:03d}"],
          "Date": [str(pd.Timestamp.today().date())],
          "Product Code": [product_code],
          "Product Description": [description],
          "Quantity Available": [qty_avail],
          "Quantity Required": [qty_req],
          "Status": ["New Alert"],
      })
      updated_df = pd.concat([df_current, new_row], ignore_index=True)
      save_data(updated_df, dept)
