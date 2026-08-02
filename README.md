# TIDE — Capital Pressure Observatory

A four-tier composite dashboard tracking macro liquidity, capital flows, market microstructure, and sentiment & positioning across 19 indicators. **15 of 19 metrics live**, free-tier data only.

The original design lives at [`docs/mockup/tide_dashboard_mockup.html`](docs/mockup/tide_dashboard_mockup.html).

## What's on the dashboard

- **Composite reading** with 252-business-day SVG history chart in the hero panel
- **Tier I — Macro Liquidity:** M2, Fed Balance Sheet, HY Credit Spread, NFCI, Bank Credit Total
- **Tier II — Capital Flows:** Margin Debt (Z.1), Foreign Equity Holdings (TIC SLT)
- **Tier III — Market Microstructure:** MOVE, SPY illiquidity (Amihud), HYG illiquidity (Amihud), Stock-Bond 60D correlation
- **Tier IV — Sentiment & Positioning:** VIX term structure, AAII Bull/Bear, Dealer Gamma (DIX), COT S&P spec net
- **Watchlist** (8 healthcare tickers benchmarked vs XLV with 30-day relative returns and sparklines)

Four metrics from the original 19 are stubbed (registered with metadata, no `ingest_fn`) because their free sources are gated or require disproportionate engineering: `ici_etf_flows`, `buyback_yield`, `put_call`, `uvol_dvol`. Per-tier `__init__.py` docstrings document the unblock paths.

## Architecture

- **Backend** (`backend/`) — FastAPI serves a JSON API; DuckDB stores observations and a metrics registry; a separate `tide-ingest` CLI pulls from upstream sources. The dashboard endpoint and the ingest process share only the database, so a wedged scrape never takes the dashboard down.
- **Frontend** (`frontend/`) — SvelteKit, SSR-first. The page server calls the FastAPI `/api/dashboard` endpoint once per request and hands the full payload to the page.
- **Z-scores** are 3-year rolling by default, configurable per-metric via `MetricDefinition.zscore_years`.
- **Composite** is the equal-weight average of the four tier averages, using each metric's `directional_z` so inverted-convention metrics (HY tight = bull, VIX low = bull, etc.) contribute correctly.
- **Stale data** is shown, not hidden. Every metric card displays its `as of` date and the composite uses last known values for series that publish on a lag.

## Data sources (all free-tier)

| Source | Used by | Notes |
|---|---|---|
| FRED (`fredapi`) | M2, WALCL, HY spread, NFCI, TOTLL, Margin Debt | Requires `FRED_API_KEY` |
| Yahoo Finance chart API (direct HTTP) | MOVE, VIX, VIX3M, SPY, TLT, HYG, all watchlist tickers | No `yfinance` dep — direct HTTP to `query1.finance.yahoo.com/v8/finance/chart/` |
| SqueezeMetrics CSV | Dealer Gamma (DIX) | Public CSV at `squeezemetrics.com/monitor/static/DIX.csv` |
| AAII (binary `.xls`) | AAII Bull/Bear spread | Needs `xlrd`, browser-shaped headers, retry-on-403 (bot detection cycles) |
| CFTC TFF year archives | COT S&P spec net | TLS verification disabled *only for cftc.gov*; contract regex matches both legacy and current names |
| Treasury TIC SLT (`slt1d_globl.csv`) | Foreign Equity Holdings | File caps at 2023-01 — newer data lives at different URLs per press release |

## Quickstart

```bash
cp .env.example .env
# Add your FRED_API_KEY to .env (free at fred.stlouisfed.org/docs/api/api_key.html)

make install                # backend deps into $VENV (default: ~/sandbox/envs/tideenv); frontend npm
make init-db                # creates DuckDB schema and seeds metrics registry
make ingest-all             # pulls every metric with an ingest_fn (~30s)
make ingest-watchlist       # pulls 8 healthcare tickers + XLV benchmark
make backfill-composite     # computes the 252-day historical composite series

# In two terminals:
make dev-api                # FastAPI on :8765
make dev-web                # SvelteKit on :5173 (binds 0.0.0.0)
```

Open <http://localhost:5173> (or your LAN IP).

The Makefile honors `VENV` and `PORT` env vars — e.g. `make dev-api PORT=9000` or `make install VENV=./backend/.venv`.

## Refresh cycle

Once initialized, the daily refresh is three commands:

```bash
make ingest-all         # idempotent — re-pulls each source's full series
make ingest-watchlist
make backfill-composite # recomputes the historical composite from current data
```

### Automated: `make scheduler`

For an always-fresh dashboard without manual runs, start the scheduler service:

```bash
make scheduler           # blocks; runs cron jobs until Ctrl-C
# or, to test the job bodies once and exit:
make scheduler-once
```

The scheduler runs two cron-triggered jobs (America/New_York timezone):

- **`daily_ingest`** — Mon–Fri 17:00 (after US market close). Pulls every metric with `cadence="daily"`, refreshes the watchlist, and runs `backfill-composite`.
- **`release_ingest`** — Fri 18:00. Pulls every non-daily metric (weekly / monthly / quarterly) — polling weekly on Fridays is cheap and catches new FRED / FINRA / Treasury / CFTC releases within a week — then runs `backfill-composite`.

Per-job status (next run, last success, last error) persists to the `scheduler_status` DuckDB table and is surfaced on the **Sources page** (`/sources`).

To keep the scheduler running across reboots, drop it under systemd. Minimal unit:

```ini
# /etc/systemd/system/tide-scheduler.service
[Unit]
Description=TIDE ingestion scheduler
After=network.target

[Service]
Type=simple
User=murali
WorkingDirectory=/home/murali/sandbox/tide
ExecStart=/home/murali/sandbox/envs/tideenv/bin/python -m tide.ingest.cli scheduler
Restart=on-failure
RestartSec=30s
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

Then `sudo systemctl enable --now tide-scheduler`. `journalctl -u tide-scheduler -f` tails the logs.

## Layout

```
backend/tide/
  api/                FastAPI app + routes (dashboard, watchlist, metrics, health)
  compute/
    composite.py      tier-average → composite z + tally
    history.py        252-day historical composite via per-metric forward-fill
    transforms.py     Amihud, daily returns, rolling Pearson — runs at ingest
    zscore.py         level_series + yoy_series rolling-z helpers (DuckDB SQL)
  ingest/
    cli.py            tide-ingest entry point: init-db, run, watchlist, backfill-composite
    sources/          per-source clients: fred, yahoo, cftc, aaii, squeezemetrics, treasury_tic
  metrics/
    base.py           Metric, Vote, Reading, MetricDefinition, directional_from_z
    tier1/ … tier4/   per-metric modules; each registers a MetricDefinition
  watchlist/          hardcoded ticker list + compute helpers
  config.py           pydantic-settings; resolves DB path against project root
  db.py               DuckDB connection + schema (observations, metrics tables)
frontend/src/
  lib/components/     CompositeHero, CompositeChart, TierGrid, MetricCard,
                      Sparkline, Tally, Watchlist
  routes/
    +layout.svelte    sidebar + brand
    +page.svelte      composite hero, tier grids, watchlist
    +page.server.ts   parallel fetch of /api/dashboard + /api/watchlist
  app.css             ported design tokens + component styles from the mockup
docs/mockup/          original HTML mockup for design reference
```

## Adding a new metric

1. Drop a module under `backend/tide/metrics/tierN/<id>.py` following the pattern of e.g. `tier1/m2.py`:
   - `_ingest()` returns `[(date, float)]` from the upstream source
   - `_compute(conn)` reads from `observations`, computes the latest reading via `level_series`/`yoy_series`, applies the metric's vote logic, returns a `Reading`
   - `register(MetricDefinition(...))` at module bottom — must include `indicator_kind`, `indicator_lag` (for `yoy`), `indicator_window`, `direction_kind` so the historical composite can pick it up
2. Add the import to that tier's `__init__.py`
3. `make init-db` to seed the registry, then `tide-ingest run --metric <id>` to pull data, then `make backfill-composite`

## Known gotchas

Documented inline in source comments; the highlights:

- **`yfinance` is unreliable** — auth/crumb breakage every few weeks. We hit Yahoo's chart API directly and it's been stable.
- **FRED truncated `BAMLH0A0HYM2` to a 3y window** (April 2026 license change). HY spread's `zscore_years` is dropped to 1y to match.
- **CFTC contract names migrated** from "E-MINI S&P 500 STOCK INDEX -" to "E-MINI S&P 500 -" at some point; the parser uses a regex matching both.
- **Cboe Put/Call** is locked behind the CDN; Yahoo's `^CPC` returns empty. Stubbed.
- **AAII bot detection** cycles — same headers return 200 / 403 minutes apart. Helper retries 4× with backoff and validates the OLE2 magic bytes.
