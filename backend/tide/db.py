"""DuckDB connection + schema management.

The schema is intentionally simple: one wide observations table keyed by metric_id and ts,
plus a metrics registry. Z-scores and composite are computed by SQL views, not stored.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import duckdb

from tide.config import settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS metrics (
    id              VARCHAR PRIMARY KEY,
    name            VARCHAR NOT NULL,
    tier            INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 4),
    source          VARCHAR NOT NULL,        -- 'FRED · M2SL' display string
    source_kind     VARCHAR NOT NULL,        -- 'fred', 'yfinance', 'cboe', etc.
    source_series   VARCHAR,                  -- the upstream series id, e.g. 'M2SL'
    unit            VARCHAR,                  -- 'YoY', 'bps · OAS', etc.
    cadence         VARCHAR,                  -- 'monthly', 'weekly', 'daily'
    zscore_years    INTEGER NOT NULL DEFAULT 3,
    sort_order      INTEGER NOT NULL DEFAULT 0
);

-- observations holds general-purpose (series_id, ts, value) tuples. The series_id is
-- *usually* a metric registered in `metrics`, but it can also be a watchlist ticker
-- (`wl_<ticker>`), a derived series (`_composite_z`), or any other named series.
-- We don't FK to metrics — that table is purely a dashboard-display registry.
CREATE TABLE IF NOT EXISTS observations (
    metric_id       VARCHAR NOT NULL,
    ts              DATE    NOT NULL,
    value           DOUBLE  NOT NULL,
    ingested_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (metric_id, ts)
);

CREATE INDEX IF NOT EXISTS idx_observations_metric_ts ON observations(metric_id, ts DESC);
"""


def ensure_db_path() -> None:
    settings.tide_db_path.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def connect(read_only: bool = False) -> Iterator[duckdb.DuckDBPyConnection]:
    ensure_db_path()
    conn = duckdb.connect(str(settings.tide_db_path), read_only=read_only)
    try:
        yield conn
    finally:
        conn.close()


def init() -> None:
    """Create schema and seed the metrics registry from code."""
    from tide.metrics import all_metrics

    ensure_db_path()
    with connect() as conn:
        conn.execute(SCHEMA_SQL)
        for m in all_metrics():
            conn.execute(
                """
                INSERT INTO metrics
                    (id, name, tier, source, source_kind, source_series, unit, cadence, zscore_years, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    name = excluded.name,
                    tier = excluded.tier,
                    source = excluded.source,
                    source_kind = excluded.source_kind,
                    source_series = excluded.source_series,
                    unit = excluded.unit,
                    cadence = excluded.cadence,
                    zscore_years = excluded.zscore_years,
                    sort_order = excluded.sort_order
                """,
                [
                    m.id, m.name, m.tier, m.source, m.source_kind,
                    m.source_series, m.unit, m.cadence, m.zscore_years, m.sort_order,
                ],
            )
    print(f"DB initialized at {settings.tide_db_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init()
    else:
        print("usage: python -m tide.db init")
