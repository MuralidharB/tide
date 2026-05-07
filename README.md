# TIDE — Capital Pressure Observatory

A four-tier composite dashboard tracking macro liquidity, capital flows, market microstructure, and sentiment & positioning across 19 indicators.

The original design lives at [`docs/mockup/tide_dashboard_mockup.html`](docs/mockup/tide_dashboard_mockup.html).

## Architecture

- **Backend** (`backend/`) — FastAPI serves a JSON API; DuckDB stores observations and a metrics registry; a separate `tide-ingest` CLI runs APScheduler-driven jobs to pull from FRED and other free sources.
- **Frontend** (`frontend/`) — SvelteKit, server-side rendered. The page server calls the FastAPI `/api/dashboard` endpoint once per request and hands the full payload to the page.
- **Z-scores** are 3-year rolling, computed in DuckDB SQL.
- **Composite** is the equal-weight average of the four tier averages.
- **Stale data** stays visible. Each metric carries an `as of` date; the dashboard never silently uses stale numbers as fresh.

## v1 scope

Wave 1 ships a single end-to-end metric (M2 from FRED) wired all the way through. Subsequent waves add the remaining 18 indicators per `docs/mockup/`. Theses, annotations, and backtests are aspirational and not yet modeled.

## Quickstart

```bash
cp .env.example .env
# add your FRED_API_KEY to .env

make install        # creates backend/.venv and installs frontend deps
make init-db        # creates DuckDB schema and seeds metrics registry
make ingest-m2      # pulls M2SL from FRED into DuckDB

# in two terminals:
make dev-api        # FastAPI on :8000
make dev-web        # SvelteKit on :5173
```

Open http://localhost:5173.

## Layout

```
backend/tide/
  api/          FastAPI app + routes
  compute/      z-score and composite SQL
  ingest/       CLI + APScheduler + per-source clients
  metrics/      Per-metric definitions, organized by tier
  config.py     Settings
  db.py         DuckDB connection + schema
frontend/src/
  lib/components/   CompositeHero, TierGrid, MetricCard, Sparkline
  routes/           +layout, +page (dashboard), +page.server.ts
  app.css           Ported from the mockup
docs/mockup/    Original HTML mockup
```
