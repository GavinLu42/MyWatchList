# Watchlist — personal news & price tracker

A tiny, free, self-updating dashboard for a list of stocks/funds you care about.
Shows recent news links and a price chart for each, and refreshes itself automatically.

No servers, no database, no paid API keys.

## How it works

- `tickers.json` — the list of things you're tracking. Edit this to add/remove tickers.
- `scripts/collect.py` — pulls recent news (Google News RSS) and price history (Yahoo
  Finance's public chart endpoint) for each ticker, and writes `data/<SYMBOL>.json`.
- `.github/workflows/update.yml` — a GitHub Action that runs the script every 4 hours
  and commits the updated data automatically.
- `index.html` — the dashboard. Reads `tickers.json` and `data/*.json` and renders
  a ribbon of your holdings (click to switch), a price chart, and a news list.

## One-time setup (~10 minutes)

1. **Create a new GitHub repository** (public or private both work; if private,
   GitHub Pages requires a paid plan — public is simplest and free).

2. **Upload all these files** to the repo, keeping the folder structure:
   ```
   tickers.json
   index.html
   README.md
   scripts/collect.py
   .github/workflows/update.yml
   ```

3. **Enable GitHub Actions** (usually on by default for a new repo):
   Repo → Settings → Actions → General → make sure "Allow all actions" is selected.

4. **Give Actions permission to push commits**:
   Repo → Settings → Actions → General → "Workflow permissions" → select
   **"Read and write permissions"** → Save.
   (This lets the scheduled job commit updated news/price data back to the repo.)

5. **Run the workflow once manually** to populate data immediately instead of waiting
   up to 4 hours:
   Repo → Actions tab → "Update news and prices" → **Run workflow**.
   After it finishes (~1 min), you should see new files appear under `data/`.

6. **Enable GitHub Pages**:
   Repo → Settings → Pages → Source: "Deploy from a branch" → Branch: `main` / `(root)` → Save.
   GitHub will give you a URL like `https://yourusername.github.io/your-repo-name/`.

That's it — visit the URL and you'll see your dashboard. It'll keep itself updated
automatically every 4 hours from then on.

## Adding a new ticker later

Open `tickers.json` and add an entry, e.g.:

```json
{ "symbol": "AAPL", "name": "Apple Inc.", "newsQuery": "Apple Inc stock" }
```

- `symbol` must be a valid Yahoo Finance ticker (works for stocks, ETFs, and mutual funds).
- `newsQuery` is what gets searched on Google News — make it specific enough to avoid
  unrelated results (e.g. "Shell plc stock" rather than just "Shell").

Commit the change (or edit the file directly on github.com), then either wait for the
next scheduled run or trigger it manually from the Actions tab. The new ticker will
appear in the dashboard automatically once its data file is created.

## Adjusting the schedule

Edit the `cron` line in `.github/workflows/update.yml`. It's currently
`0 22 * * *` (once a day, 22:00 UTC / ~5-6pm ET, shortly after the US market
closes). GitHub Actions schedules run in UTC and free-tier public repos don't
pay for this — it's included.

## Notes & limitations

- News is link-only by design (title, source, publish date, and a link) — no article
  text is stored or displayed, keeping things simple and copyright-clean.
- Price history defaults to 6 months (`PRICE_RANGE` in `collect.py`); change it to
  `1y`, `5y`, etc. if you want more history.
- Yahoo's chart endpoint and Google News RSS are both free and unauthenticated, but
  unofficial — if either ever changes shape, `collect.py` is the only file you'd
  need to patch.
- Mutual funds like FXAIX/FSAGX only price once per day (after market close), so
  their charts will look like a stairstep rather than intraday movement — that's expected.
