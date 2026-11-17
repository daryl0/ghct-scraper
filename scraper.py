name: GHCT Scraper Live alle 24

on:
  schedule:
    - cron: '0 23 * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  scrape-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Configura Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Installa Playwright e dipendenze
        run: |
          pip install playwright pytz
          playwright install chromium
          playwright install-deps chromium

      - name: Esegui lo scraper dai 10 URL
        run: python scraper.py

      - name: Salva dati.json nel repository GitHub
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GHCT Scraper Bot"
          git add dati.json
          git diff --quiet && git diff --staged --quiet || (git commit -m "Scraping live $(date +'%d/%m/%Y %H:%M')" && git push)

      - name: Carica dati.json su IONOS via SFTP
        uses: wlixcc/SFTP-Deploy-Action@v1.2.4
        with:
          username: ${{ secrets.SFTP_USERNAME }}
          server: ${{ secrets.SFTP_HOST }}
          password: ${{ secrets.SFTP_PASSWORD }}
          port: ${{ secrets.SFTP_PORT || 22 }}
          local_path: './dati.json'
          remote_path: '/clickandbuilds/GHCT/wp-content/uploads/ghct-data'
          sftp_only: true
