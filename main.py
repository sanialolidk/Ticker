#!/usr/bin/env python3
"""ticker — live crypto market dashboard"""
from __future__ import annotations

import json
import threading
import time
import urllib.request
from datetime import datetime

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

COIN_COUNT = 20
REFRESH = 30
SPARK_CHARS = " ▁▂▃▄▅▆▇█"

_MARKETS = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&order=market_cap_desc"
    "&per_page={n}&page=1&sparkline=true"
    "&price_change_percentage=24h,7d"
)
_GLOBAL = "https://api.coingecko.com/api/v3/global"
_UA = {"User-Agent": "ticker/1.0"}


# ── fetch ─────────────────────────────────────────────────────────────────────

def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()


def fetch_all() -> tuple[list[dict], dict, str | None]:
    markets: list[dict] = []
    gdata: dict = {}
    err: list[str] = []

    def _m():
        nonlocal markets
        try:
            markets = json.loads(_get(_MARKETS.format(n=COIN_COUNT)))
        except Exception as exc:
            err.append(str(exc))

    def _g():
        nonlocal gdata
        try:
            gdata = json.loads(_get(_GLOBAL)).get("data", {})
        except Exception:
            pass

    t1 = threading.Thread(target=_m, daemon=True)
    t2 = threading.Thread(target=_g, daemon=True)
    t1.start(); t2.start()
    t1.join(timeout=20); t2.join(timeout=5)

    return markets, gdata, (err[0][:80] if err else None)


# ── format helpers ─────────────────────────────────────────────────────────────

def _price(p: float) -> str:
    if p >= 1000:  return f"${p:,.2f}"
    if p >= 1:     return f"${p:.4f}"
    return f"${p:.6f}"


def _large(n: float) -> str:
    if n >= 1e12: return f"${n/1e12:.2f}T"
    if n >= 1e9:  return f"${n/1e9:.2f}B"
    if n >= 1e6:  return f"${n/1e6:.2f}M"
    return f"${n:.0f}"


def _pct(v: float | None) -> Text:
    if v is None:
        return Text("  —", style="dim")
    arrow = "▲" if v > 0 else ("▼" if v < 0 else "─")
    style = "bold green" if v > 0 else ("bold red" if v < 0 else "dim")
    sign  = "+" if v > 0 else ""
    return Text(f"{arrow} {sign}{v:.2f}%", style=style)


def _spark(prices: list[float], width: int = 20) -> str:
    if len(prices) < 2:
        return "─" * width
    step = max(1, len(prices) // width)
    pts  = prices[::step][-width:]
    lo, hi = min(pts), max(pts)
    if lo == hi:
        return "─" * len(pts)
    k = len(SPARK_CHARS) - 1
    return "".join(SPARK_CHARS[round((p - lo) / (hi - lo) * k)] for p in pts)


# ── widgets ───────────────────────────────────────────────────────────────────

def _stats_bar(g: dict, countdown: int, err: str | None) -> Align:
    cap     = (g.get("total_market_cap") or {}).get("usd", 0)
    vol     = (g.get("total_volume")     or {}).get("usd", 0)
    cap_chg = g.get("market_cap_change_percentage_24h_usd") or 0.0
    btc     = (g.get("market_cap_percentage") or {}).get("btc", 0.0)
    eth     = (g.get("market_cap_percentage") or {}).get("eth", 0.0)

    arrow = "▲" if cap_chg >= 0 else "▼"
    cs    = "green" if cap_chg >= 0 else "red"
    sign  = "+" if cap_chg >= 0 else ""
    sep   = ("   ·   ", "bright_black")

    tail: list
    if err:
        tail = [sep, ("⚠ ", "yellow"), (err[:50], "yellow")]
    else:
        tail = [sep, ("⟳ ", "dim"), (f"{countdown}s", "cyan"), ("  ctrl+c to exit", "dim")]

    line = Text.assemble(
        ("Cap ", "dim"), (_large(cap), "bold white"), (f" {arrow}{sign}{cap_chg:.1f}%", cs),
        sep,
        ("Vol ", "dim"), (_large(vol), "white"),
        sep,
        ("BTC ", "dim"), (f"{btc:.1f}%", "bold yellow"),
        sep,
        ("ETH ", "dim"), (f"{eth:.1f}%", "bold bright_blue"),
        *tail,
    )
    return Align.center(line)


def _coin_table(coins: list[dict]) -> Table:
    t = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="bright_black",
        row_styles=["", "dim"],
        expand=True,
        show_edge=True,
        padding=(0, 1),
    )
    t.add_column("#",          style="dim",       width=4,    justify="right")
    t.add_column("Coin",                          min_width=20, no_wrap=True)
    t.add_column("Price",                         min_width=14, justify="right")
    t.add_column("24h",                           width=12,    justify="right")
    t.add_column("7d",                            width=12,    justify="right")
    t.add_column("Market Cap",                    min_width=11, justify="right")
    t.add_column("Vol 24h",                       min_width=11, justify="right")
    t.add_column("7d Chart",                      min_width=22)

    for c in coins:
        prices = (c.get("sparkline_in_7d") or {}).get("price") or []
        chg24  = c.get("price_change_percentage_24h_in_currency")
        chg7   = c.get("price_change_percentage_7d_in_currency")
        sc     = "green" if (chg7 or 0) >= 0 else "red"

        coin_label = Text()
        coin_label.append(c["name"],              style="bold white")
        coin_label.append(f"  {c['symbol'].upper()}", style="dim")

        t.add_row(
            str(c.get("market_cap_rank") or "—"),
            coin_label,
            _price(c["current_price"]),
            _pct(chg24),
            _pct(chg7),
            _large(c.get("market_cap")   or 0),
            _large(c.get("total_volume") or 0),
            Text(_spark(prices), style=sc),
        )
    return t


# ── render ────────────────────────────────────────────────────────────────────

def render(coins: list[dict], gdata: dict, countdown: int, err: str | None) -> Panel:
    title = Text.assemble(
        ("◈ ", "bright_cyan"),
        ("CRYPTO", "bold bright_cyan"),
        (" TICKER", "bold white"),
        (f"   {datetime.now().strftime('%H:%M:%S')}", "dim"),
    )

    if not coins:
        body = Align.center(
            Text("\n  Fetching market data…\n", style="dim"),
            vertical="middle",
        )
    else:
        body = Group(
            _stats_bar(gdata, countdown, err),
            Rule(style="bright_black"),
            _coin_table(coins),
        )

    return Panel(
        body,
        title=title,
        subtitle=Text("data: CoinGecko", style="dim"),
        border_style="cyan",
        padding=(0, 1),
    )


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    console = Console()
    coins: list[dict] = []
    gdata: dict = {}
    err: str | None = None
    last_fetch = 0.0

    with Live(console=console, refresh_per_second=2, screen=True) as live:
        while True:
            if time.monotonic() - last_fetch >= REFRESH:
                live.update(render(coins, gdata, 0, err))
                coins, gdata, err = fetch_all()
                last_fetch = time.monotonic()

            countdown = max(0, REFRESH - int(time.monotonic() - last_fetch))
            live.update(render(coins, gdata, countdown, err))
            time.sleep(0.5)


if __name__ == "__main__":
    main()
