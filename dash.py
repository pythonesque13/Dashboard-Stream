import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
import numpy as np
import pathlib

def load_css(file_path):
    try:
        with open(file_path) as f:
            st.html(f"<style>{f.read()}</style>")
    except FileNotFoundError:
        st.warning(f"Fichier CSS non trouvé : {file_path}")

st.set_page_config(page_title="Tableau de Bord", page_icon="assets/logo.png", layout="wide")
css_path = pathlib.Path("assets/styles.css")
load_css(css_path)

@st.cache_data
def load_data(file_path, sheet_name):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        df.columns = df.columns.str.replace('__', '').str.strip()
        if 'Date comptable Hist' in df.columns:
            df['Date comptable Hist'] = pd.to_datetime(df['Date comptable Hist'])
        return df
    except Exception as e:
        st.error(f"Erreur chargement feuille '{sheet_name}': {e}"); return None

def check():
    try:
        with open("data/email.txt", "r") as f:
            allow_mail = {line.strip() for line in f if line.strip()}
        if st.session_state.get("email") in allow_mail:
            st.session_state.authenticated = True
            st.session_state.user_email = st.session_state.get("email")
            del st.session_state["email"]
        else:
            st.session_state.authenticated = False; st.error("Email non autorisé.")
    except FileNotFoundError:
        st.session_state.authenticated = False; st.error("Fichier d'autorisation introuvable.")

def login():
    st.header("Accès au tableau de bord")
    st.text_input("Veuillez entrer votre adresse email", key="email")
    st.button("Se connecter", on_click=check)

@st.dialog("Accès AGI requis")
def agi_auth_dialog():
    st.info("Veuillez entrer un email autorisé pour accéder à cette section.")
    email_agi = st.text_input("Email autorisé", key="agi_email_input")
    if st.button("Vérifier"):
        try:
            with open("data/email_agi.txt", "r") as f:
                agi_users = {line.strip() for line in f if line.strip()}
            if email_agi in agi_users:
                st.session_state.selected_button = 'AGI'
                st.session_state.agi_user_email = email_agi 
                if email_agi.lower() == 'super@afriland.com':
                    st.session_state.agi_role = 'superviseur'
                else:
                    st.session_state.agi_role = 'standard'
                
                st.rerun()
            else:
                st.error("Désolé, cet email n'est pas autorisé pour la vue AGI.")
        except FileNotFoundError:
            st.error("Fichier d'autorisation AGI (email_agi.txt) non trouvé.")


def main_dash():
    df_agences = load_data("data/opera.xlsx", sheet_name="Agence")
    df_agi = load_data("data/opera.xlsx", sheet_name="AGI")

    if df_agences is None or df_agi is None: return

    if 'selected_button' not in st.session_state: st.session_state.selected_button = 'AGENCES'
    
    if st.session_state.get("show_agi_dialog"):
        st.session_state.show_agi_dialog = False
        agi_auth_dialog()

    is_agence_view = st.session_state.selected_button == 'AGENCES'
    df_source = df_agences if is_agence_view else df_agi
    colonne_filtre = 'Code Agence Saisie' if is_agence_view else 'Code Utilisateur'
    options_filtre = ["Tout"] + sorted(df_source[colonne_filtre].unique().tolist())

    with st.container(key="header_container"):
        col1, col2 = st.columns([1, 4])
        with col1:
            with st.container(key="sidebar_container"):
                st.image("assets/logo.png", use_container_width=True)
                
                selection_filtre_tableau = "Tout"
                
                if is_agence_view:
                    selection_filtre_tableau = st.selectbox("AGENCES", options_filtre, key="selectbox_agence")
                else:
                    agi_role = st.session_state.get('agi_role', 'standard')
                    if agi_role == 'superviseur':
                        selection_filtre_tableau = st.selectbox("AGI (Superviseur)", options_filtre, key="selectbox_agi_super")
                    else:
                        agi_email = st.session_state.get('agi_user_email', '')
                        user_agi_code = agi_email.split('@')[0].upper()
                        st.info(f"Vue filtrée pour AGI : **{user_agi_code}**")
                        selection_filtre_tableau = user_agi_code
                
                if st.button("AGENCES", key="agences_btn", type="primary" if is_agence_view else "secondary", use_container_width=True):
                    st.session_state.selected_button = 'AGENCES'; st.rerun()
                if st.button("AGI", key="agi_btn", type="primary" if not is_agence_view else "secondary", use_container_width=True):
                    st.session_state.show_agi_dialog = True; st.rerun()

        with col2:
            df_filtre = df_source
            if selection_filtre_tableau != "Tout":
                df_filtre = df_source[df_source[colonne_filtre].str.upper() == selection_filtre_tableau.upper()]

            with st.container(key="title_container"):
                title_col, date_elements_col = st.columns([3, 2])
                with title_col:
                    st.markdown("DASHBOARD DU SUIVI DU DEPLACEMENT DES OPERATIONS DE PETITS MONTANTS", unsafe_allow_html=True)
                with date_elements_col:
                    default_start, default_end = df_agences['Date comptable Hist'].min().date(), df_agences['Date comptable Hist'].max().date()
                    start_date, end_date = st.date_input("DATE", value=(default_start, default_end), key="date_range_selector")
                    if start_date > end_date:
                        st.warning("Date de début > Date de fin."); start_date, end_date = default_start, default_end
            
            with st.container(key="graph_container", height=300):
                if not df_filtre.empty:
                    df_graph = df_filtre.groupby(df_filtre['Date comptable Hist'].dt.date).agg({'taux_caisse': 'mean', 'taux_vire': 'mean'}).reset_index()
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df_graph['Date comptable Hist'], y=df_graph['taux_caisse'], name='Taux Caisse', mode='lines+markers+text', text=df_graph['taux_caisse'].apply(lambda x: f'{x:.2%}'), textposition="top center", hovertemplate="<b>Date</b>: %{x|%d/%m/%Y}<br><b>Taux Caisse</b>: %{y:.2%}<extra></extra>"))
                    fig.add_trace(go.Scatter(x=df_graph['Date comptable Hist'], y=df_graph['taux_vire'], name='Taux Virement', mode='lines+markers+text', text=df_graph['taux_vire'].apply(lambda x: f'{x:.2%}'), textposition="bottom center", hovertemplate="<b>Date</b>: %{x|%d/%m/%Y}<br><b>Taux Virement</b>: %{y:.2%}<extra></extra>"))
                    title_text = f"Performance de : {selection_filtre_tableau}" if selection_filtre_tableau != "Tout" else "Vue d'Ensemble Globale"
                    fig.update_layout(title=title_text, xaxis_range=[start_date, end_date], height=320, legend=dict(orientation="h", yanchor="bottom", y=-0.4))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Aucune donnée à afficher pour le graphique.")
            
            with st.container(key="table_container"):
                if not df_filtre.empty:
                    agg_rules = {'nbre_op': 'sum', 'nbre_op_mois750k': 'sum', 'retrait_moins de 750k': 'sum', 'versement_moins de 750k': 'sum', 'virement_moins de 05 M': 'sum'}
                    group_by_cols = [df_filtre['Date comptable Hist'].dt.date]
                    if not is_agence_view: group_by_cols.append(df_filtre['Code Utilisateur'])
                    df_agg = df_filtre.groupby(group_by_cols).agg(agg_rules).reset_index()
                    with np.errstate(divide='ignore', invalid='ignore'):
                        df_agg['Taux_trans_petit_montant'] = (df_agg['nbre_op_mois750k'] / df_agg['nbre_op']) * 100
                        df_agg['Taux_trans_retrait_versement_moins_de_750k'] = ((df_agg['retrait_moins de 750k'] + df_agg['versement_moins de 750k']) / df_agg['nbre_op_mois750k']) * 100
                    df_agg.fillna(0, inplace=True)
                    total_sums = df_agg.select_dtypes(include=np.number).sum()
                    total_row_df = pd.DataFrame([total_sums])
                    with np.errstate(divide='ignore', invalid='ignore'):
                        total_row_df['Taux_trans_petit_montant'] = (total_row_df['nbre_op_mois750k'] / total_row_df['nbre_op']) * 100
                        total_row_df['Taux_trans_retrait_versement_moins_de_750k'] = ((total_row_df['retrait_moins de 750k'] + total_row_df['versement_moins de 750k']) / total_row_df['nbre_op_mois750k']) * 100
                    total_row_df.fillna(0, inplace=True)
                    df_display = df_agg.copy()
                    df_display['Date comptable Hist'] = df_display['Date comptable Hist'].apply(lambda x: x.strftime('%d/%m/%Y'))
                    total_row_dict = total_row_df.iloc[0].to_dict()
                    total_row_dict['Date comptable Hist'] = 'Total'
                    if not is_agence_view: total_row_dict['Code Utilisateur'] = ''
                    df_display = pd.concat([df_display, pd.DataFrame([total_row_dict])], ignore_index=True)
                    final_columns_map = {'Date comptable Hist': 'Date', 'Code Utilisateur': 'AGI', 'nbre_op': 'Nbre_trans', 'nbre_op_mois750k': 'Nbre_trans_moins750k', 'Taux_trans_petit_montant': 'Taux_trans_petit_montant', 'Taux_trans_retrait_versement_moins_de_750k': 'Taux_trans_retrait_versement_moins_de_750k', 'retrait_moins de 750k': 'Retrait_moins_de_750k', 'versement_moins de 750k': 'Versement_moins_de_750k', 'virement_moins de 05 M': 'Virement_moins_de_05_M'}
                    df_final_display = df_display.rename(columns=final_columns_map)
                    final_columns_order = ['Date', 'Nbre_trans', 'Nbre_trans_moins750k', 'Taux_trans_petit_montant', 'Taux_trans_retrait_versement_moins_de_750k', 'Retrait_moins_de_750k', 'Versement_moins_de_750k', 'Virement_moins_de_05_M']
                    if not is_agence_view: final_columns_order.insert(1, 'AGI')
                    st.dataframe(df_final_display[final_columns_order], hide_index=True, use_container_width=True, column_config={"Taux_trans_petit_montant": st.column_config.NumberColumn("Taux Petit Montant", format="%.2f%%"), "Taux_trans_retrait_versement_moins_de_750k": st.column_config.NumberColumn("Taux Retrait/Versement", format="%.2f%%")})
                else:
                    st.warning("Aucune donnée à afficher pour la sélection actuelle.")
# ==============================================================================
# 4. ROUTEUR PRINCIPAL
# ==============================================================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if st.session_state.authenticated:
    main_dash()
else:
    login()