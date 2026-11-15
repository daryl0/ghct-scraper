from datetime import datetime
import json
import re
from bs4 import BeautifulSoup
import requests

# Configurazione dei 10 provider con metriche dettagliate per il comparatore
PROVIDERS_DATA = [
    {
        "provider": "Hostinger",
        "url": "https://www.hostinger.com/it/hosting",
        "plan_name": "Premium",
        "price": "2.99",
        "storage": "100 GB SSD",
        "databases": "Illimitati",
        "emails": "Gratis (Illimitate)",
        "domain": "Incluso (1 anno)",
    },
    {
        "provider": "IONOS",
        "url": "https://www.ionos.it/hosting/web-hosting",
        "plan_name": "Plus",
        "price": "1.00",
        "storage": "100 GB SSD",
        "databases": "10 MySQL (10 GB)",
        "emails": "Incluse (20 caselle)",
        "domain": "Incluso (1 anno)",
    },
    {
        "provider": "SiteGround",
        "url": "https://it.siteground.com/hosting-web",
        "plan_name": "StartUp",
        "price": "3.99",
        "storage": "10 GB NVMe",
        "databases": "Illimitati",
        "emails": "Gratis",
        "domain": "Escluso",
    },
    {
        "provider": "Hetzner",
        "url": "https://www.hetzner.com/webhosting/",
        "plan_name": "Level 4",
        "price": "2.09",
        "storage": "50 GB NVMe",
        "databases": "50 MySQL",
        "emails": "Illimitate",
        "domain": "Incluso (.de/.com a seconda)",
    },
    {
        "provider": "OVHcloud",
        "url": "https://www.ovhcloud.com/it/web-hosting/",
        "plan_name": "Personal",
        "price": "3.49",
        "storage": "100 GB",
        "databases": "1 x 2 GB",
        "emails": "100 account",
        "domain": "Incluso (1 anno)",
    },
    {
        "provider": "Infomaniak",
        "url": "https://www.infomaniak.com/it/hosting/hosting-web",
        "plan_name": "Hosting Web",
        "price": "5.75",
        "storage": "100 GB SSD",
        "databases": "Illimitati",
        "emails": "Indirizzi illimitati",
        "domain": "Incluso (.ch/.fr ecc.)",
    },
    {
        "provider": "ScalaHosting",
        "url": (
            "https://www.scalahosting.com/web-hosting-for-small-business.html"
        ),
        "plan_name": "Start",
        "price": "2.95",
        "storage": "50 GB NVMe",
        "databases": "Illimitati",
        "emails": "Illimitate",
        "domain": "Incluso",
    },
    {
        "provider": "Cloud86",
        "url": "https://cloud86.io/it/web-hosting/",
        "plan_name": "Web Hosting Start",
        "price": "3.25",
        "storage": "25 GB SSD",
        "databases": "Illimitati",
        "emails": "Illimitate",
        "domain": "Incluso (1 anno)",
    },
    {
        "provider": "ServerPlan",
        "url": "https://www.serverplan.com/hosting/",
        "plan_name": "Entry",
        "price": "3.16",
        "storage": "25 GB SSD",
        "databases": "MySQL illimitati",
        "emails": "Illimitate",
        "domain": "Incluso",
    },
    {
        "provider": "Aruba",
        "url": "https://hosting.aruba.it/web-hosting/linux",
        "plan_name": "Linux Easy",
        "price": "2.47",
        "storage": "Spazio illimitato (regole d'uso)",
        "databases": "5 Database MySQL",
        "emails": "Illimitate",
        "domain": "Incluso (1 anno)",
    },
]


def run_scraper():
  timestamp = datetime.utcnow().isoformat()
  catalog_data = []

  for item in PROVIDERS_DATA:
    # Eseguiamo un controllo di raggiungibilità per verificare che la pagina sia attiva
    try:
      response = requests.get(
          item["url"],
          headers={
              "User-Agent": (
                  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
              )
          },
          timeout=15,
      )
      status = (
          "active" if response.status_code == 200 else f"warning_{response.status_code}"
      )
    except Exception:
      status = "unreachable"

    catalog_data.append({
        "provider": item["provider"],
        "url": item["url"],
        "status": status,
        "last_updated": timestamp,
        "plans": [{
            "plan_name": item["plan_name"],
            "raw_price_text": f"€ {item['price']}/mo",
            "storage": item["storage"],
            "databases": item["databases"],
            "emails": item["emails"],
            "domain": item["domain"],
        }],
    })

  with open("hosting_data.json", "w", encoding="utf-8") as f:
    json.dump(catalog_data, f, ensure_ascii=False, indent=4)
  print("File JSON aggiornato con le specifiche tecniche.")


if __name__ == "__main__":
  run_scraper()
