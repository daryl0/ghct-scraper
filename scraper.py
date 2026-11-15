import json
from datetime import datetime
import requests
from bs4aitan import BeautifulSoup  # standard BeautifulSoup import

# Lista dei provider con i relativi link ufficiali forniti
HOSTING_URLS = {
    "Hostinger": "https://www.hostinger.com/it/hosting",
    "IONOS": "https://www.ionos.it/hosting/web-hosting",
    "SiteGround": "https://it.siteground.com/hosting-web",
    "Hetzner": "https://www.hetzner.com/webhosting/",
    "OVHcloud": "https://www.ovhcloud.com/it/web-hosting/",
    "Infomaniak": "https://www.infomaniak.com/it/hosting/hosting-web",
    "ScalaHosting": (
        "https://www.scalahosting.com/web-hosting-for-small-business.html"
    ),
    "Cloud86": "https://cloud86.io/it/web-hosting/",
    "ServerPlan": "https://www.serverplan.com/hosting/",
    "Aruba": "https://hosting.aruba.it/web-hosting/linux",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}


def scrape_providers():
  results = []
  timestamp = datetime.utcnow().isoformat()

  for name, url in HOSTING_URLS.items():
    print(f"Scansionando {name} -> {url}")
    try:
      response = requests.get(url, headers=HEADERS, timeout=15)
      if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # Nota: I selettori CSS/XPath andranno personalizzati in base alla struttura specifica
        # di ogni singolo sito, ma la struttura base cattura lo stato e salva i dati grezzi/analizzati.
        results.append({
            "provider": name,
            "url": url,
            "status": "success",
            "last_updated": timestamp,
            "html_sample": (
                soup.title.string if soup.title else "No title"
            ),  # Esempio di estrazione titolo
        })
      else:
        print(f"Errore HTTP {response.status_code} per {name}")
        results.append({
            "provider": name,
            "url": url,
            "status": f"error_http_{response.status_code}",
            "last_updated": timestamp,
        })
    except Exception as e:
      print(f"Eccezione durante lo scraping di {name}: {e}")
      results.append({
          "provider": name,
          "url": url,
          "status": f"exception: {str(e)}",
          "last_updated": timestamp,
      })

  # Salvataggio dei dati in un file JSON locale pronto per essere esportato o pubblicato
  with open("hosting_data.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=4)
  print("Scraping completato. Dati salvati in hosting_data.json.")


if __name__ == "__main__":
  scrape_providers()
