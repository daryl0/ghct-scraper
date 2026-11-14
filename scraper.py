import os
import base64
import requests
from bs4 import BeautifulSoup

# Recupera le credenziali dai Secrets di GitHub
WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# Configura l'autenticazione Basic per le REST API
credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
token = base64.b64encode(credentials.encode()).decode("utf-8")
headers = {
    "Authorization": f"Basic {token}",
    "Content-Type": "application/json"
}

def scrape_hostinger():
    # URL di esempio (sostituisci con il target reale)
    url = "https://www.hostinger.it/web-hosting"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=15)
        if response.status_code != 200:
            print(f"Errore HTTP {response.status_code} su Hostinger")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        offerte = []

        # ATTENZIONE: I selettori CSS vanno adattati analizzando l'HTML reale del sito target
        # Questo è un blocco di esempio dimostrativo
        cards = soup.select('.pricing-card') # Sostituisci con la classe reale
        for card in cards:
            # Esempio di estrazione (da personalizzare)
            nome = "Hosting Plus Esempio"
            prezzo = "2.99€/mo"
            descrizione = "Offerta estratta automaticamente via GitHub Actions"

            offerta_data = {
                "title": f"Hostinger - {nome}",
                "content": descrizione,
                "status": "publish", # O 'draft' se preferisci revisionarle prima
                # Campi personalizzati (se usi ACF o REST API custom fields)
                "meta": {
                    "prezzo": prezzo,
                    "continente": "Europa"
                }
            }
            offerte.append(offerta_data)

        return offerte
    except Exception as e:
        print(fket=f"Errore durante lo scraping: {e}")
        return []

def pubblica_su_wordpress(offerta):
    endpoint = f"{WP_URL}/wp/v2/posts" # Oppure il tuo CPT personalizzato es. /wp/v2/offerte
    response = requests.post(endpoint, json=offerta, headers=headers)
    if response.status_code == 201:
        print(f"Pubblicato con successo: {offerta['title']}")
    else:
        print(f"Errore nella pubblicazione ({response.status_code}): {response.text}")

if __name__ == "__main__":
    print("Avvio dello scraper...")
    offerte = scrape_hostinger()
    print(f"Trovate {len(offerte)} offerte. Invio a WordPress in corso...")
    for offerta in offerte:
        pubblica_su_wordpress(offerta)
