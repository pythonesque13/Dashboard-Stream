import pandas as pd
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(dotenv_path="config.env") 

DATA_FILE_PATH = "data/opera.xlsx"
THRESHOLD = 0.20  

TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

def send(subject, alerts_list):
    if not TEAMS_WEBHOOK_URL:
        print("Erreur : TEAMS_WEBHOOK_URL n'est pas défini dans le fichier config.env.")
        return
        
    facts = []
    for alert in alerts_list:
        parts = alert.replace('<li>', '').replace('</li>', '').replace('<b>', '').replace('</b>', '').split(':')
        entity_name = parts[0].strip()
        alert_details = parts[1].strip()
        facts.append({"title": entity_name, "value": alert_details})

    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "msteams": {"width": "Full"},
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": subject,
                            "size": "Large",
                            "weight": "Bolder",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": "Le système de surveillance a détecté que des seuils de performance ont été atteints.",
                            "wrap": True
                        },
                        {
                            "type": "FactSet",
                            "facts": facts
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "Ouvrir le Tableau de Bord",
                            "url": "https://dashboard-stream-tbbi.onrender.com/" 
                        }
                    ]
                }
            }
        ]
    }

    try:
        print("Envoi de la notification à Microsoft Teams...")
        response = requests.post(
            TEAMS_WEBHOOK_URL, 
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload)
        )
        response.raise_for_status()  
        print("Notification envoyée avec succès à Teams.")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'envoi de la notification à Teams : {e}")

def check():
    print(f"[{datetime.now()}] Début de la vérification des seuils...")
    try:
        df_agences = pd.read_excel(DATA_FILE_PATH, sheet_name="Agence")
        df_agi = pd.read_excel(DATA_FILE_PATH, sheet_name="AGI")

        alerts_found = []

        for df, entity_type, entity_col in [(df_agences, "Agence", "Code Agence Saisie"), (df_agi, "AGI", "Code Utilisateur")]:
            df.columns = df.columns.str.replace('__', '').str.strip()
            df['Date comptable Hist'] = pd.to_datetime(df['Date comptable Hist'])
            latest_date = df['Date comptable Hist'].max()
            df_latest = df[df['Date comptable Hist'].dt.date == latest_date.date()]

            for _, row in df_latest.iterrows():
                if row['taux_caisse'] <= THRESHOLD:
                    alerts_found.append(f"<li><b>{entity_type} {row[entity_col]}:</b> Taux de caisse bas à <b>{row['taux_caisse']:.2%}</b></li>")
                if row['taux_vire'] <= THRESHOLD:
                    alerts_found.append(f"<li><b>{entity_type} {row[entity_col]}:</b> Taux de virement bas à <b>{row['taux_vire']:.2%}</b></li>")

        if alerts_found:
            print(f"{len(alerts_found)} alerte(s) trouvée(s).")
            subject = f" Alerte de Performance - {df_agences['Date comptable Hist'].max().strftime('%d/%m/%Y')}"
            send(subject, alerts_found)
        else:
            print("Aucune alerte à signaler. Tous les seuils sont respectés.")

    except Exception as e:
        print(f"Une erreur majeure est survenue lors de l'exécution du script : {e}")

if __name__ == "__main__":
    check()