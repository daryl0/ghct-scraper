import asyncio
import json
import re
from datetime import datetime
import pytz
from playwright.async_api import async_playwright

PROVIDERS = [
    {
        "name": "Hostinger",
        "url": "https://hostinger.com",
        "selectors": ["[data-qa='pricing-card']", ".h-pricing-card", "[class*='pricing-card']"],
        "ciclo_default": "Ciclo 48 mesi"
    },
    {
        "name": "IONOS",
        "url": "https://ionos.it",
        "selectors": [".product-card", ".tariff-box", "[class*='price-card']", "article"],
        "ciclo_default": "Ciclo 6/12 mesi"
    },
    {
        "name": "SiteGround",
        "url": "https://siteground.com",
        "selectors": [".plan-box", ".pricing-plan", "[class*='plan-card']"],
        "ciclo_default": "Ciclo 12 mesi"
    },
    {
        "name": "Hetzner",
        "url": "https://hetzner.com",
        "selectors": [".product-box", ".hosting-package", "[class*='product-item']"],
        "ciclo_default": "Mensile (nessun vincolo)"
    },
    {
        "name": "OVHcloud",
        "url": "https://ovhcloud.com",
        "selectors": [".oui-tile", "[class*='offer-card']", "[class*='product-card']"],
        "ciclo_default": "Ciclo 12 mesi"
    },
    {
        "name": "Infomaniak",
        "url": "https://infomaniak.com",
        "selectors": ["[class*='offer']", "[class*='pricing']", ".card"],
        "ciclo_default": "Ciclo 12 mesi"
    },
    {
        "name": "ScalaHosting",
        "url": "https://scalahosting.com",
        "selectors": [".plan-item", ".pricing-box", "[class*='plan-col']"],
        "ciclo_default": "Ciclo 36 mesi"
    },
    {
        "name": "Cloud86",
        "url": "https://cloud86.io",
        "selectors": [".package-card", ".pricing-card", "[class*='plan-card']"],
        "ciclo_default": "Ciclo 36 mesi"
    },
    {
        "name": "ServerPlan",
        "url": "https://serverplan.com",
        "selectors": [".box-hosting", ".plan-box", "[class*='hosting-box']", ".col-md-3"],
        "ciclo_default": "Ciclo Annuale"
    },
    {
        "name": "Aruba",
        "url": "https://aruba.it",
        "selectors": [".card-offerta", ".box-prodotto", "[class*='product-card']", ".card"],
        "ciclo_default": "Ciclo Annuale"
    }
]

PRICE_REGEX = re.compile(r'(\d+[.,]\d{2}\s*[€$]|[€$]\s*\d+[.,]\d{2}|\d+\s*[€$])')

def parse_card_text(raw_text, ciclo_default):
    lines = [l.strip() for l in raw_text.split("\n") if len(l.strip()) > 1]
    if len(lines) < 3:
        return None

    prices = PRICE_REGEX.findall(raw_text)
    if not prices:
        return None

    def to_float(p):
        num = re.search(r'\d+[.,]?\d*', p).group(0).replace(',', '.')
        return float(num)

    unique_prices = list(dict.fromkeys(prices))
    sorted_prices = sorted(unique_prices, key=to_float)

    prezzo_offerta = f"{sorted_prices} /mese o ciclo"
    prezzo_pieno = f"{sorted_prices[-1]} al rinnovo" if len(sorted_prices) > 1 else f"{sorted_prices} (tariffa standard)"

    skip_words = ("sconto", "risparmi", "offerta", "black friday", "bestseller", "consigliato", "popolare", "a partire")
    piano_nome = "Piano Web Hosting"
    for line in lines[:5]:
        if not PRICE_REGEX.search(line) and not any(w in line.lower() for w in skip_words) and len(line) <= 35:
            piano_nome = line
            break

    exclude_cta = ("acquista", "ordina", "scegli", "continua", "inizia", "scopri", "seleziona", "guarda", "nascondi")
    caratteristiche = []
    for line in lines:
        low = line.lower()
        if (
            line != piano_nome
            and not PRICE_REGEX.fullmatch(line)
            and len(line) > 5
            and len(line) < 110
            and not any(cta in low for cta in exclude_cta)
        ):
            if line not in caratteristiche:
                caratteristiche.append(line)

    if len(caratteristiche) < 2:
        return None

    return {
        "piano": piano_nome,
        "ciclo": ciclo_default,
        "prezzoOfferta": prezzo_offerta,
        "prezzoPieno": prezzo_pieno,
        "caratteristiche": caratteristiche[:8]
    }

async def scrape_provider(page, prov):
    estratti = []
    try:
        print(f"Connessione a {prov['name']} ({prov['url']})...")
        await page.goto(prov["url"], wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(4000)

        for word in ["Accetta", "Accept", "Accetta tutti", "Allow all"]:
            try:
                btn = page.get_by_role("button", name=re.compile(word, re.I)).first
                if await btn.is_visible(timeout=800):
                    await btn.click()
                    await page.wait_for_timeout(500)
                    break
            except Exception:
                pass

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await page.wait_for_timeout(1500)

        seen_plans = set()
        for sel in prov["selectors"]:
            cards = await page.query_selector_all(sel)
            for card in cards[:8]:
                text = await card.inner_text()
                parsed = parse_card_text(text, prov["ciclo_default"])
                if parsed and parsed["piano"] not in seen_plans:
                    seen_plans.add(parsed["piano"])
                    estratti.append({
                        "provider": prov["name"],
                        "url": prov["url"],
                        **parsed
                    })
            if len(estratti) >= 2:
                break

        print(f"-> {prov['name']}: estratti {len(estratti)} piani.")
    except Exception as e:
        print(f"-> Errore su {prov['name']}: {e}")

    return estratti

async def main():
    tz_it = pytz.timezone("Europe/Rome")
    data_ora_scraping = datetime.now(tz_it).strftime("%d/%m/%Y alle %H:%M:%S")

    tutti_i_piani = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="it-IT"
        )
        page = await context.new_page()

        for prov in PROVIDERS:
            piani_prov = await scrape_provider(page, prov)
            tutti_i_piani.extend(piani_prov)

        await browser.close()

    output = {
        "ultimo_aggiornamento": data_ora_scraping,
        "totale_piani_estratti": len(tutti_i_piani),
        "piani": tutti_i_piani
    }

    with open("dati.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Scraping completato il {data_ora_scraping}. Totale piani importati: {len(tutti_i_piani)}")

if __name__ == "__main__":
    asyncio.run(main())
