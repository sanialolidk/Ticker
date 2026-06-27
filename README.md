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

Use the GitHub Pages link above — **do not open `index.html` as a local file** (`file://`), browsers block cross-origin API calls and you'll see "Failed to fetch".

Refreshes every 60s. If the table stays on skeleton rows:

- Wait for the next retry (automatic backoff)
- Disable ad blockers / privacy extensions for the page
- Add a free [CoinGecko Demo API key](https://www.coingecko.com/en/api/pricing): `?cg_key=YOUR_KEY`

For the most reliable experience, run the TUI (`python main.py`) — server-side fetch avoids browser network limits.

## Stack

Python 3, Rich (TUI), vanilla HTML/CSS/JS (web). No framework, no API keys.