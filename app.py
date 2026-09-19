from github import Github
import pandas as pd
import streamlit as st


# --- CONFIGURATION DE LA CONNEXION GITHUB ---
def get_github_repo():
  token = st.secrets["GITHUB_TOKEN"]
  repo_name = st.secrets["REPO_NAME"]
  g = Github(token)
  return g.get_repo(repo_name)


# --- FONCTIONS DE CHARGEMENT ET SAUVEGARDE ---
@st.cache_data(ttl=60)
def load_data(category_name):
  """Charge le fichier CSV depuis le dossier data/ de GitHub."""
  try:
    repo = get_github_repo()
    path = f"data/{category_name}.csv"
    file_content = repo.get_contents(path)
    return pd.read_csv(pd.io.common.StringIO(file_content.decoded_content.decode("utf-8")))
  except Exception:
    # Si le fichier n'existe pas encore, on retourne un DataFrame vide avec des colonnes par défaut
    return pd.DataFrame(columns=["ID", "Article", "Quantité", "Statut", "Date"])


def save_data(df, category_name):
  """Enregistre le DataFrame modifié directement sur GitHub en arrière-plan."""
  try:
    repo = get_github_repo()
    path = f"data/{category_name}.csv"
    csv_content = df.to_csv(index=False)
    message = f"Mise à jour des données {category_name} via Streamlit"

    try:
      # Si le fichier existe, on le met à jour avec son SHA
      file = repo.get_contents(path)
      repo.update_file(path, message, csv_content, file.sha, branch="main")
    except Exception:
      # Si le fichier n'existe pas, on le crée
      repo.create_file(path, message, csv_content, branch="main")

    st.success(f"Modifications enregistrées avec succès pour {category_name} sur GitHub !")
  except Exception as e:
    st.error(f"Erreur lors de la sauvegarde sur GitHub : {e}")


# --- INTERFACE UTILISATEUR STREAMLIT ---
st.title("Supply Chain Control Center - Tableau de bord")

# Barre latérale pour choisir la catégorie
category = st.sidebar.selectbox(
    "Sélectionnez le module",
    ["Production", "Logistics", "Purchasing", "Transport"],
)

st.header(f"Module : {category}")

# 1. Charger les données correspondantes
df_data = load_data(category)

# 2. Permettre l'édition interactive des données
st.subheader("Gestion et Édition des Données")
edited_df = st.data_editor(df_data, num_rows="dynamic", key=f"editor_{category}")

# 3. Bouton pour sauvegarder
if st.button("Enregistrer les modifications"):
  save_data(edited_df, category)
