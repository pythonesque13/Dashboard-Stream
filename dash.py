import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
import plotly.express as px
import numpy as np
import pathlib

#Pour le chargement du fichier CSS du style
def load_css(file_path):
    with open(file_path) as f:
        st.html(f"<style>{f.read()}</style>")

css_path=pathlib.Path("assets/styles.css")
load_css(css_path)



st.set_page_config(
    page_title="Tableau de Bord",
    page_icon="assets/logo.png",
    layout="wide"
)

def check():
    try:
        with open("data/email.txt", "r") as f:
            allow_mail={line.strip() for line in f if line.strip()}

        if st.session_state.get("email") in allow_mail:
            st.session_state.authenticated = True

            del st.session_state["email"]
        else:
            st.session_state.authenticated = False
            st.error("Email non autorisé. Veuillez contacter l'administrateur.")
    except FileNotFoundError:
        st.session_state.authenticated = False
        st.error("Fichier d'autorisation introuvable. Veuillez contacter l'administrateur.")

def login():
    st.header("Acces au tableau de bord")
    st.text_input("Veuillez entrer votre adresse email", key="email")
    st.button("Se connecter", on_click=check)



def main_dash():
    data = {
        'Date': ['01/07/2025', '02/05/2025', '03/06/2025', '02/07/2025', '03/06/2025',
                '03/07/2025', '04/06/2025', '04/07/2025', '05/05/2025','05/05/2025','05/05/2025'],
        'Nbre_trans': [1106, 1577, 1538, 970, 1213, 953, 950, 1092, 1666,1666,1666],
        'Nbre_trans_moins750k': [588, 1021, 1133, 483, 720, 517, 482, 636, 934,934,934],
        'Taux_trans_petit_montant': [53.16, 64.74, 58.46, 49.79, 59.36, 55.41, 50.74, 58.24, 56.06, 56.06, 56.06],
        'Taux_trans_retrait_versement_moins_de_750k': [46.10, 55.15, 41.76, 44.74, 48.94, 51.47, 43.76, 52.07, 49.84, 49.84, 49.84],
        'Retrait_moins_de_750k': [157, 244, 246, 113, 150, 121, 156, 155, 276,276,276],
        'Versement_moins_de_750k': [198, 254, 256, 206, 220, 246, 128, 248, 331,331,331],
        'Virement_moins_de_05_M': [185, 225, 134, 71, 112, 92, 103, 57, 211,211,211],
    }



    df = pd.DataFrame(data)
    df_chart = pd.DataFrame(data)
    df_chart['Date'] = pd.to_datetime(df_chart['Date'])

    if 'selected_button' not in st.session_state:
        st.session_state.selected_button = 'AGENCES' 


    with st.container(key="header_container"):
        col1, col2 = st.columns([1, 3])
        with col1:
            with st.container(key="sidebar_container"): 
                st.image("assets/logo.png", use_container_width=True) 
                selectbox_label = "AGI" if st.session_state.selected_button == 'AGI' else "AGENCES"
                options = ["Tout", "Option 1", "Option 2", "Option 3"]
                st.selectbox(selectbox_label, options, key="selectbox")

                type_agences = "primary" if st.session_state.selected_button == 'AGENCES' else "secondary"
                st.button("AGENCES", key="agences_button", on_click=lambda: st.session_state.update(selected_button='AGENCES'), type=type_agences, use_container_width=True)

                type_agi = "primary" if st.session_state.selected_button == 'AGI' else "secondary"
                st.button("AGI", key="agi_button", on_click=lambda: st.session_state.update(selected_button='AGI'), type=type_agi, use_container_width=True)

        with col2:
            with st.container(key="title_container",height=120):      
                title_col, date_elements_col = st.columns([3, 2]) 
                with title_col:
                    st.markdown("DASHBOARD DU SUIVI DU DEPLACEMENT DES OPERATIONS DE PETITS MONTANTS",unsafe_allow_html=True)
                with date_elements_col:
                    # SÉLECTEUR DE DATE RANGE
                    default_start_date = date(2025, 6, 23)
                    default_end_date = date(2025, 7, 7)

                    start_date, end_date = st.date_input(
                        "DATE", # Label au-dessus
                        value=(default_start_date, default_end_date),
                        key="date_range_selector"
                    )

            with st.container():
                fig = go.Figure()

                # Données pour le graphique (simulées)
                dates_chart = ['Jun 2025', 'Jul 2025']
                taux_versement = [55.15, 50.32, 47.95, 36.10, 37.82, 36.65, 41.76, 48.94, 55.30, 60.30, 64.74, 52.30]
                taux_virement = [73.00, 52.30, 50.65, 44.74, 36.38, 47.95]

                # Ligne pour taux versement
                fig.add_trace(go.Scatter(
                    y=taux_versement,
                    mode='lines+markers',
                    name='Taux Versement et retrait moins de 750k',
                    line=dict(color='red', width=2),
                    marker=dict(size=6, color='red')
                ))

                # Ligne pour taux virement
                fig.add_trace(go.Scatter(
                    y=taux_virement[:6],
                    mode='lines+markers',
                    name='Taux virement moins de 5 M',
                    line=dict(color='black', width=2),
                    marker=dict(size=6, color='black')
                ))

                fig.update_layout(
                    height=320,
                    showlegend=True,
                    title={
                        'text': "Taux Versement et retrait moins de 750k et Taux virement moins de 5 M par Date comptable Hist__",
                        'y':0.9,
                        'x':0.4,
                        'xanchor': 'center',
                        'yanchor': 'top',
                        'font': dict(color='black') # Set title text color to black
                    },

                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.3,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=10, color='black') 
                    ),
                    margin=dict(l=50, r=50, t=55, b=60),
                    plot_bgcolor='white', 
                    paper_bgcolor='white', 
                    xaxis=dict(
                        showgrid=True,
                        gridcolor='lightgray',
                        showticklabels=False,
                        title_font=dict(color='black'), 
                        tickfont=dict(color='black') 
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='lightgray',
                        title="Taux Versement et retrait (%)",
                        range=[20, 80],
                        title_font=dict(color='black'), 
                        tickfont=dict(color='black') 
                    )
                )
                st.plotly_chart(fig, use_container_width=True)


    with st.container(key="table_container"):   
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False


if st.session_state.authenticated:
    main_dash()
else:
    login()



