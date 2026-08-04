"""
Collects recent news links and price history for each ticker in tickers.json,
and writes/updates data/<SYMBOL>.json for the frontend to read.

No API keys required:
- News comes from Google News RSS
- Prices come from Yahoo Finance's public chart endpoint

Run manually with: python scripts/collect.py
In production this is run on a schedule by .github/workflows/update.yml
"""
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKERS_FILE = os.path.join(ROOT, "tickers.json")
DATA_DIR = os.path.join(ROOT, "data")
MAX_NEWS = 40
PRICE_RANGE = "6mo"  # yahoo chart range param, e.g. 1mo/3mo/6mo/1y/5y

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PersonalNewsTracker/1.0)"}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def fetch_news(query):
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    root = ET.fromstring(fetch(url))
    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        source_el = item.find("{https://news.google.com/rss}source")
        source = source_el.text.strip() if source_el is not None and source_el.text else ""
        if title and link:
            items.append({"title": title, "link": link, "pubDate": pub, "source": source})
    return items


def fetch_prices(symbol):
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}"
        f"?range={PRICE_RANGE}&interval=1d"
    )
    obj = json.loads(fetch(url))
    result = obj["chart"]["result"][0]
    timestamps = result.get("timestamp", [])
    closes = result["indicators"]["quote"][0].get("close", [])
    points = []
    for t, c in zip(timestamps, closes):
        if c is None:
            continue
        points.append({
            "date": datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d"),
            "close": round(c, 2),
        })
    meta = result.get("meta", {})
    return points, meta


def load_tickers():
    with open(TICKERS_FILE) as f:
        return json.load(f)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    tickers = load_tickers()

    for t in tickers:
        symbol = t["symbol"]
        query = t.get("newsQuery", symbol)
        path = os.path.join(DATA_DIR, f"{symbol}.json")

        existing = {"news": [], "prices": [], "meta": {}}
        if os.path.exists(path):
            with open(path) as f:
                existing = json.load(f)

        try:
            new_items = fetch_news(query)
        except Exception as e:
            new_items = []
            print(f"[news] failed for {symbol}: {e}")

        seen = {n["link"] for n in existing.get("news", [])}
        merged = list(existing.get("news", []))
        for n in new_items:
            if n["link"] not in seen:
                merged.append(n)
                seen.add(n["link"])
        merged.sort(key=lambda n: n.get("pubDate", ""), reverse=True)
        merged = merged[:MAX_NEWS]

        try:
            prices, meta = fetch_prices(symbol)
        except Exception as e:
            prices = existing.get("prices", [])
            meta = existing.get("meta", {})
            print(f"[prices] failed for {symbol}: {e}")

        out = {
            "symbol": symbol,
            "name": t.get("name", symbol),
            "updated": datetime.now(timezone.utc).isoformat(),
            "news": merged,
            "prices": prices,
            "meta": meta,
        }
        with open(path, "w") as f:
            json.dump(out, f, indent=2)

        print(f"Updated {symbol}: {len(merged)} news items, {len(prices)} price points")
        time.sleep(1)  # be polite to the free endpoints


if __name__ == "__main__":
    main()
