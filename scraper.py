import asyncio
import json
import re
from datetime import datetime
import pytz
from deep_translator import GoogleTranslator
from playwright.async_api import async_playwright

PROVIDERS = [
    {"name": "Hostinger", "url": "https://hostinger.com", "ciclo": "Ciclo 48 mesi", "lang": "it"},
    {"name": "IONOS", "url": "https://ionos.it", "ciclo": "Ciclo 6/12 mesi", "lang": "it"},
    {"name": "SiteGround", "url": "https://siteground.com", "ciclo": "Ciclo 12 mesi", "lang": "it"},
    {"name": "Hetzner", "url": "https://hetzner.com", "ciclo": "Mensile (nessun vincolo)", "lang": "en"},
    {"name": "OVHcloud", "url": "https://ovhcloud.com", "ciclo": "Ciclo 12 mesi", "lang": "it"},
    {"name": "Infomaniak", "url": "https://infomaniak.com", "ciclo": "Ciclo 12 mesi", "lang": "it"},
    {"name": "ScalaHosting", "url": "https://scalahosting.com", "ciclo": "Ciclo 36 mesi", "lang": "en"},
    {"name": "Cloud86", "url": "https://cloud86.io", "ciclo": "Ciclo 36 mesi", "lang": "it"},
    {"name": "ServerPlan", "url": "https://serverplan.com", "ciclo": "Ciclo Annuale", "lang": "it"},
    {"name": "Aruba", "url": "https://aruba.it", "ciclo": "Ciclo Annuale", "lang": "it"}
]

translator = GoogleTranslator(source='auto', target='it')

def translate_to_it(text):
    try:
        if not text or len(text) < 3:
            return text
        return translator.translate(text)
    except Exception:
        return text

def clean_price_value(raw_str):
    """Normalizza un prezzo (es. '$ 1.99' o '1,99 €') in formato pulito italiano."""
    cleaned = re.sub(r'\s+', ' ', raw_str).strip()
    num_match = re.search(r'(\d+[.,]\d{2}|\d+)', cleaned)
    if not num_match:
        return None
    val = float(num_match.group(1).replace(',', '.'))
    currency = "€" if "€" in cleaned else ("$" if "$" in cleaned else "CHF")
    formatted_num = f"{val:.2f}".replace('.', ',')
    return val, f"{formatted_num} {currency}"

async def extract_plans_from_page(page, prov):
    """Estrae dinamicamente le card dei piani analizzando la struttura del DOM."""
    raw_cards = await page.evaluate("""() => {
        const candidates = Array.from(document.querySelectorAll('div, article, section, li'));
        const results = [];
        const pricePattern = /(\\d+[.,]\\d{2}\\s*[€$]|[€$]\\s*\\d+[.,]\\d{2}|CHF\\s*\\d+[.,]\\d{2}|€\\s*\\d+\\b|\\d+\\s*€)/;

        for (const el of candidates) {
            const text = (el.innerText || '').trim();
            if (text.length < 60 || text.length > 1400) continue;
            if (!pricePattern.test(text)) continue;

            // Evita contenitori padre che racchiudono più piani insieme
            const headings = el.querySelectorAll('h2, h3, h4');
            if (headings.length > 2) continue;

            const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 1);
            if (lines.length >= 4 && lines.length <= 35) {
                results.push(lines);
            }
        }
        return results;
    }""")

    piani_trovati = []
    seen_names = set()
    price_regex = re.compile(r'(\d+[.,]\d{2}\s*[€$]|[€$]\s*\d+[.,]\d{2}|CHF\s*\d+[.,]\d{2}|€\s*\d+\b|\d+\s*€)')

    skip_badges = (
        "sconto", "risparmi", "offerta", "black friday", "bestseller", "consigliato",
        "popolare", "a partire", "special offer", "save", "off", "intro", "most popular",
        "per iniziare", "la soluzione", "miglior", "più venduto", "più potente", "easter"
    )
    exclude_lines = (
        "acquista", "ordina", "scegli", "continua", "inizia", "scopri", "seleziona",
        "guarda", "nascondi", "choose", "get started", "order", "select", "buy",
        "iva escl", "excl. vat", "vedi le caratteristiche", "show more", "compara",
        "tooltip", "control panel", "spanel", "cpanel", "add to cart", "aggiungi"
    )

    for lines in raw_cards:
        full_block = "\n".join(lines)
        raw_prices = price_regex.findall(full_block)
        parsed_prices = [clean_price_value(p) for p in raw_prices if clean_price_value(p)]
        if not parsed_prices:
            continue

        # Filtra eventuali prezzi totali pluriennali molto alti per isolare le tariffe mensili/annuali
        parsed_prices.sort(key=lambda x: x[0])
        min_val, min_str = parsed_prices[0]
        max_val, max_str = parsed_prices[-1]

        # Se c'è un totale pluriennale (es. 95,52 €) insieme a 1,99 € e 9,99 €, prende il rinnovo mensile
        monthly_candidates = [p for p in parsed_prices if p[0] < (min_val * 12) and p[0] > min_val]
        if monthly_candidates:
            max_val, max_str = monthly_candidates[-1]

        prezzo_offerta = f"{min_str}/mese" if "anno" not in full_block.lower() else f"{min_str}/anno"
        if max_val > min_val:
            prezzo_pieno = f"{max_str}/mese al rinnovo" if "anno" not in full_block.lower() else f"{max_str}/anno al rinnovo"
        else:
            prezzo_pieno = f"{min_str} (tariffa standard)"

        # Cerca il nome reale del piano (es. Premium, StartUp, Plus, Webhosting S)
        piano_nome = None
        for line in lines[:6]:
            low = line.lower()
            if (
                not price_regex.search(line)
                and not any(b in low for b in skip_badges)
                and not any(e in low for e in exclude_lines)
                and 2 <= len(line) <= 32
                and not line.endswith("%")
            ):
                piano_nome = line
                break

        if not piano_nome or piano_nome.lower() in seen_names:
            continue

        # Estrae le caratteristiche tecniche pulite
        features = []
        for line in lines:
            low = line.lower()
            if (
                line != piano_nome
                and not price_regex.search(line)
                and not any(b in low for b in skip_badges)
                and not any(e in low for e in exclude_lines)
                and 5 <= len(line) <= 95
                and not line.endswith("%")
            ):
                clean_feat = line.replace("tooltip", "").strip()
                if clean_feat and clean_feat not in features:
                    features.append(clean_feat)

        if len(features) < 2:
            continue

        seen_names.add(piano_nome.lower())

        # Traduce in italiano se il sito ha risposto in inglese
        if prov["lang"] == "en" or any(w in " ".join(features).lower() for w in ["websites", "storage", "unlimited", "free domain", "bandwidth"]):
            features = [translate_to_it(f) for f in features[:6]]
        else:
            features = features[:6]

        piani_trovati.append({
            "provider": prov["name"],
            "url": prov["url"],
            "piano": piano_nome,
            "ciclo": prov["ciclo"],
            "prezzoOfferta": prezzo_offerta,
            "prezzoPieno": prezzo_pieno,
            "caratteristiche": features
        })

        if len(piani_trovati) >= 3:
            break

    return piani_trovati

async def main():
    tz_it = pytz.timezone("Europe/Rome")
    timestamp_it = datetime.now(tz_it).strftime("%d/%m/%Y alle %H:%M:%S")
    tutti_i_piani = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="it-IT",
            timezone_id="Europe/Rome",
            extra_http_headers={"Accept-Language": "it-IT,it;q=0.9,en;q=0.8"}
        )
        page = await context.new_page()

        for prov in PROVIDERS:
            try:
                print(f"Lettura {prov['name']}...")
                await page.goto(prov["url"], wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(4000)

                # Accetta eventuali cookie banner
                for btn_label in ["Accetta", "Accept", "Accetta tutti", "Allow all"]:
                    try:
                        btn = page.get_by_role("button", name=re.compile(btn_label, re.I)).first
                        if await btn.is_visible(timeout=800):
                            await btn.click()
                            await page.wait_for_timeout(500)
                            break
                    except Exception:
                        pass

                # Scroll graduale per caricare le tabelle prezzi lazy-loaded
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.35)")
                await page.wait_for_timeout(1200)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.7)")
                await page.wait_for_timeout(1200)

                piani = await extract_plans_from_page(page, prov)
                print(f"-> {prov['name']}: estratti {len(piani)} piani.")
                tutti_i_piani.extend(piani)
            except Exception as e:
                print(f"-> Errore su {prov['name']}: {str(e)[:80]}")

        await browser.close()

    output = {
        "ultimo_aggiornamento": timestamp_it,
        "totale_piani": len(tutti_i_piani),
        "piani": tutti_i_piani
    }

    with open("dati.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Completato il {timestamp_it}. Totale piani: {len(tutti_i_piani)}")

if __name__ == "__main__":
    asyncio.run(main())
