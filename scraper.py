from datetime import datetime
import json
import requests

# Offerte strutturate per fasce omogenee (Entry, Mid, Pro)
HOSTING_CATALOG = [
    # --- FASCIA ENTRY / BASE (Siti singoli o risorse ridotte, es. 10-25 GB) ---
    {
        "provider": "SiteGround",
        "url": "https://it.siteground.com/hosting-web",
        "tier": "Entry",
        "plan_name": "StartUp",
        "price": "3.99",
        "storage": "10 GB NVMe",
        "databases": "Illimitati",
        "emails": "Gratis",
        "domain": "Escluso",
    },
    {
        "provider": "Cloud86",
        "url": "https://cloud86.io/it/web-hosting/",
        "tier": "Entry",
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
        "tier": "Entry",
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
        "tier": "Entry",
        "plan_name": "Linux Easy",
        "price": "2.47",
        "storage": "Spazio illimitato*",
        "databases": "5 MySQL",
        "emails": "Illimitate",
        "domain": "Incluso (1 anno)",
    },

    # --- FASCIA MID / PROFESSIONALE (Standard evoluti, multi-sito, 50-100 GB) ---
    {
        "provider": "Hostinger",
        "url": "https://www.hostinger.com/it/hosting",
        "tier": "Mid",
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
        "tier": "Mid",
        "plan_name": "Plus",
        "price": "1.00",
        "storage": "100 GB SSD",
        "databases": "10 MySQL (10 GB)",
        "emails": "20 caselle",
        "domain": "Incluso (1 anno)",
    },
    {
        "provider": "Hetzner",
        "url": "https://www.hetzner.com/webhosting/",
        "tier": "Mid",
        "plan_name": "Level 4",
        "price": "2.09",
        "storage": "50 GB NVMe",
        "databases": "50 MySQL",
        "emails": "Illimitate",
        "domain": "Incluso",
    },
    {
        "provider": "OVHcloud",
        "url": "https://www.ovhcloud.com/it/web-hosting/",
        "tier": "Mid",
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
        "tier": "Mid",
        "plan_name": "Hosting Web",
        "price": "5.75",
        "storage": "100 GB SSD",
        "databases": "Illimitati",
        "emails": "Illimitati",
        "domain": "Incluso",
    },
    {
        "provider": "ScalaHosting",
        "url": (
            "https://www.scalahosting.com/web-hosting-for-small-business.html"
        ),
        "tier": "Mid",
        "plan_name": "Start",
        "price": "2.95",
        "storage": "50 GB NVMe",
        "databases": "Illimitati",
        "emails": "Illimitate",
        "domain": "Incluso",
    },
]


def run_scraper():
  timestamp = datetime.utcnow().isoformat()
  catalog_data = []

  for item in HOSTING_CATALOG:
    catalog_data.append({
        "provider": item["provider"],
        "url": item["url"],
        "tier": item["tier"],
        "plan_name": item["plan_name"],
        "price": item["price"],
        "storage": item["storage"],
        "databases": item["databases"],
        "emails": item["emails"],
        "domain": item["domain"],
        "last_updated": timestamp,
    })

  with open("hosting_data.json", "w", encoding="utf-8") as f:
    json.dump(catalog_data, f, ensure_ascii=False, indent=4)
  print("Catalogo hosting suddiviso per tier generato con successo.")


if __name__ == "__main__":
  run_scraper()
