import base64
import json
import requests
import streamlit as st
import pandas as pd

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
