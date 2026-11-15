from datetime import datetime
import json
import re
from bs4 import BeautifulSoup
import requests

# Configurazione dettagliata dei provider con endpoint e selettori specifici
PROVIDERS_CONFIG = {
    "Hostinger": {
        "url": "https://www.hostinger.com/it/hosting",
        "card_selector": ".pricing-card, [class*='card-pricing']",
    },
    "IONOS": {
        "url": "https://www.ionos.it/hosting/web-hosting",
        "card_selector": ".js-pricing-item, .product-card",
    },
    "SiteGround": {
        "url": "https://it.siteground.com/hosting-web",
        "card_selector": ".plan-box, .box-pricing",
    },
    "Hetzner": {
        "url": "https://www.hetzner.com/webhosting/",
        "card_selector": ".price-card, .hosting-product",
    },
    "OVHcloud": {
        "url": "https://www.ovhcloud.com/it/web-hosting/",
        "card_selector": ".odsk-card, .product-view",
    },
    "Infomaniak": {
        "url": "https://www.infomaniak.com/it/hosting/hosting-web",
        "card_selector": ".product-item, .pricing-col",
    },
    "ScalaHosting": {
        "url": (
            "https://www.scalahosting.com/web-hosting-for-small-business.html"
        ),
        "card_selector": ".plan-column, .pricing-table",
    },
    "Cloud86": {
        "url": "https://cloud86.io/it/web-hosting/",
        "card_selector": ".pricing-table, .card",
    },
    "ServerPlan": {
        "url": "https://www.serverplan.com/hosting/",
        "card_selector": ".box-prezzi, .pricing-plan",
    },
    "Aruba": {
        "url": "https://hosting.aruba.it/web-hosting/linux",
        "card_selector": ".card-price, .prodotto-item",
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}


def extract_price(text):
  """Estrae un valore numerico/prezzo da una stringa."""
  match = re.search(r"(\d+[\.,]?\d*)", text)
  return match.group(1) if match else "N/D"


def run_scraper():
  catalog_data = []
  timestamp = datetime.utcnow().isoformat()

  for name, cfg in PROVIDERS_CONFIG.items():
    print(f"Scansione in corso: {name}...")
    try:
      response = requests.get(cfg["url"], headers=HEADERS, timeout=20)
      if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select(cfg["card_selector"])

        plans = []
        if cards:
          for card in cards[:3]:  # Prendiamo i primi 3 piani principali
            title_el = card.find(
                ["h2", "h3", "h4", "strong", "div"],
                class_=re.compile("title|name|header", re.I),
            )
            price_el = card.find(
                text=re.compile(r"€|\$|\d+[\.,]\d+", re.I)
            )

            plans.append({
                "plan_name": (
                    title_el.get_text(strip=True)
                    if title_el
                    else "Piano Base"
                ),
                "raw_price_text": (
                    price_el.strip() if price_el else "Contatta sito"
                ),
            })
        else:
          # Fallback se la struttura a card non corrisponde esattamente
          plans.append({
              "plan_name": "Standard",
              "raw_price_text": "Verifica su sito",
          })

        catalog_data.append({
            "provider": name,
            "url": cfg["url"],
            "status": "success",
            "plans": plans,
            "last_updated": timestamp,
        })
      else:
        catalog_data.append({
            "provider": name,
            "url": cfg["url"],
            "status": f"http_error_{response.status_code}",
            "last_updated": timestamp,
        })
    except Exception as e:
      catalog_data.append({
          "provider": name,
          "url": cfg["url"],
          "status": f"error: {str(e)}",
          "last_updated": timestamp,
      })

  with open("hosting_data.json", "w", encoding="utf-8") as f:
    json.dump(catalog_data, f, ensure_ascii=False, indent=4)
  print("File hosting_data.json generato con successo.")


if __name__ == "__main__":
  run_scraper()
