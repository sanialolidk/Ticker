# Ticker

Live crypto market dashboard — terminal UI + static web dashboard. Top 20 coins by market cap from [CoinGecko](https://www.coingecko.com).

**Live demo:** https://sanialolidk.github.io/Ticker/

## Terminal UI

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Refreshes every 30s. `ctrl+c` to exit.

## Web dashboard

Open `index.html` locally, or use the GitHub Pages link above. Same data source, SVG sparklines, price flash on tick changes.

If the table stays on skeleton rows, CoinGecko may be rate-limiting — wait 30s or run the TUI instead (server-side fetch, more reliable).

## Stack

Python 3, Rich (TUI), vanilla HTML/CSS/JS (web). No framework, no API keys.