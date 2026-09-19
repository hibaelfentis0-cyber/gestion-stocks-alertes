from github import Github
import pandas as pd
import streamlit as st

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Supply Chain Control Center", page_icon="📊", layout="wide"
)

# --- CONFIGURATION DE LA CONNEXION GITHUB ---


def get_github_repo():
  token = st.secrets["GITHUB_TOKEN"]
  repo_name = st.secrets["REPO_NAME"]
  g = Github(token)
  return g.get_repo(repo_name)


# --- FONCTIONS DE CHARGEMENT ET SAUVEGARDE ---


@st.cache_data(ttl=60)
def load_data(category_name):
  """Charge le fichier CSV depuis GitHub pour la catégorie donnée."""
  try:
    repo = get_github_repo()
    path = f"data/{category_name}.csv"
    file_content = repo.get_contents(path)
    return pd.read_csv(pd.io.common.StringIO(file_content.decoded_content.decode("utf-8")))
  except Exception:
    # Données par défaut si le fichier n'existe pas encore sur GitHub
    return pd.DataFrame({
        "Alert ID": ["PA-001", "PA-002"],
        "Date": ["2026-09-18", "2026-09-18"],
        "Product Code": ["RM-1001", "RM-1002"],
        "Product Description": ["Aluminium Component A", "Aluminium Component B"],
        "Quantity Available": [420, 850],
        "Quantity Required": [300, 250],
        "Status": ["Active", "Pending"],
    })


def save_data(df, category_name):
  """Enregistre le DataFrame modifié directement sur GitHub en arrière-plan."""
  try:
    repo = get_github_repo()
    path = f"data/{category_name}.csv"
    csv_content = df.to_csv(index=False)
    message = f"Mise à jour des données {category_name} via Streamlit"

    try:
      file = repo.get_contents(path)
      repo.update_file(path, message, csv_content, file.sha, branch="main")
    except Exception:
      repo.create_file(path, message, csv_content, branch="main")

    st.success(
        f"Modifications enregistrées avec succès pour {category_name} sur"
        " GitHub !"
    )
  except Exception as e:
    st.error(f"Erreur lors de la sauvegarde sur GitHub : {e}")


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

  # Affichage des KPIs
  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric(
        label="Production Alerts", value="4", delta="-2 vs yesterday"
    )  #[cite: 8]
  with col2:
    st.metric(label="Logistics Items", value="4", delta="Stable")  #[cite: 8]
  with col3:
    st.metric(
        label="Purchasing Orders", value="4", delta="+3 pending"
    )  #[cite: 8]
  with col4:
    st.metric(
        label="Transport Deliveries", value="4", delta="1 delayed"
    )  #[cite: 8]

  st.markdown("---")
  st.subheader("📈 Alerts Distribution by Department")

  # Graphique récapitulatif simple
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
  st.markdown(
      "Warehouse stock levels, bin locations, and pallet management."
  )  #[cite: 7]

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
      # Charger les données actuelles du département choisi
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
      # Ajouter la nouvelle ligne
      updated_df = pd.concat([df_current, new_row], ignore_index=True)
      # Sauvegarder sur GitHub
      save_data(updated_df, dept)
