import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Supply Chain End-to-End Control", layout="wide")

st.title("🔄 Workflow & Dashboard : Suivi des Alertes et Commandes")

# Chargement du fichier Excel
@st.cache_data
def load_data():
    try:
        xls = pd.ExcelFile("Material_Shortage_Alert_System1.xlsx")
        return {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}
    except Exception as e:
        return None

sheets = load_data()

if sheets is None:
    st.error("⚠️ Fichier Excel introuvable. Veuillez vérifier que 'Material_Shortage_Alert_System.xlsx' est bien sur GitHub.")
else:
    # Sidebar de navigation
    st.sidebar.title("🧭 Navigation Supply Chain")
    menu = st.sidebar.radio("Étapes du Processus", [
        "📊 Tableau de Bord Global", 
        "1️⃣ Production (Déclaration)", 
        "2️⃣ Logistique (Vérification Stock)", 
        "3️⃣ Approvisionnement (Commandes & PO)", 
        "4️⃣ Suivi Détaillé des Commandes"
    ])

    # 1. TABLEAU DE BORD GLOBAL
    if menu == "📊 Tableau de Bord Global":
        st.subheader("📊 Tableau de Bord Global - Vue d'ensemble")
        
        col1, col2, col3 = st.columns(3)
        if "PRODUCTION REQUEST" in sheets:
            col1.metric("Requêtes Production", len(sheets["PRODUCTION REQUEST"]))
        if "LOGISTICS ACTION" in sheets:
            col2.metric("Actions Logistiques", len(sheets["LOGISTICS ACTION"]))
        if "PROCUREMENT ACTION" in sheets:
            col3.metric("Commandes / PO Lancés", len(sheets["PROCUREMENT ACTION"]))

        st.markdown("---")
        st.markdown("### 📋 Aperçu du fichier DASHBOARD d'origine")
        if "DASHBOARD" in sheets:
            df_dash = sheets["DASHBOARD"]
            
            # Nettoyage automatique si les en-têtes sont décalés (suppression des lignes/colonnes vides)
            df_dash = df_dash.dropna(how='all').dropna(axis=1, how='all')
            
            st.dataframe(df_dash, use_container_width=True)

    # 2. ÉTAPE PRODUCTION
    elif menu == "1️⃣ Production (Déclaration)":
        st.subheader("🚨 Étape 1 : Déclaration d'Alerte (Production)")
        st.info("La production signale un besoin ou un risque de rupture sur une ligne.")
        if "PRODUCTION REQUEST" in sheets:
            df_prod = sheets["PRODUCTION REQUEST"].dropna(how='all').dropna(axis=1, how='all')
            st.dataframe(df_prod, use_container_width=True)
            
            # Graphique des priorités si la colonne existe
            if 'Priority' in df_prod.columns:
                st.subheader("📈 Répartition par Priorité")
                st.bar_chart(df_prod['Priority'].value_counts())

    # 3. ÉTAPE LOGISTIQUE
    elif menu == "2️⃣ Logistique (Vérification Stock)":
        st.subheader("📦 Étape 2 : Vérification Physique (Logistique)")
        st.info("La logistique vérifie les entrepôts, analyse les écarts et valide s'il faut escalader aux achats.")
        if "LOGISTICS ACTION" in sheets:
            df_log = sheets["LOGISTICS ACTION"].dropna(how='all').dropna(axis=1, how='all')
            st.dataframe(df_log, use_container_width=True)

    # 4. ÉTAPE APPROVISIONNEMENT
    elif menu == "3️⃣ Approvisionnement (Commandes & PO)":
        st.subheader("🛒 Étape 3 : Lancement des Commandes (Approvisionnement)")
        st.info("Création des bons de commande (PO) auprès des fournisseurs et suivi des confirmations.")
        if "PROCUREMENT ACTION" in sheets:
            df_proc = sheets["PROCUREMENT ACTION"].dropna(how='all').dropna(axis=1, how='all')
            st.dataframe(df_proc, use_container_width=True)

    # 5. SUIVI DÉTAILLÉ DES COMMANDES
    elif menu == "4️⃣ Suivi Détaillé des Commandes":
        st.subheader("🔍 Suivi Détaillé & Analyse des Commandes")
        st.write("Filtrez et analysez les détails des commandes en cours de livraison.")
        
        if "PROCUREMENT ACTION" in sheets:
            df_proc = sheets["PROCUREMENT ACTION"].dropna(how='all').dropna(axis=1, how='all')
            
            # Filtre par statut PO si la colonne existe
            if 'PO Status' in df_proc.columns:
                statuts = df_proc['PO Status'].dropna().unique().tolist()
                choix_statut = st.multiselect("Filtrer par Statut PO", options=statuts, default=statuts)
                df_filtered = df_proc[df_proc['PO Status'].isin(choix_statut)]
                st.dataframe(df_filtered, use_container_width=True)
            else:
                st.dataframe(df_proc, use_container_width=True)
