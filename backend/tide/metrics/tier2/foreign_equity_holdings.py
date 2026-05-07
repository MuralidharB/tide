"""Foreign Equity Holdings — Treasury TIC SLT global aggregate.

The mockup calls for "Foreign Equity Inflow" from Treasury TIC monthly net purchases.
Treasury publishes flows as Excel attachments tied to its monthly press release —
those are gnarly to scrape reliably. The TIC SLT (Securities Long-Term, holdings)
table at ticdata.treasury.gov publishes a clean monthly CSV with per-country
holdings. We sum across countries and z-score the YoY growth.

This captures the same economic dynamic as flows: when foreigners are net
accumulating US stocks, holdings grow faster than the equity market itself; when
they're net selling, holdings grow slower or shrink. Different definition than the
mockup but same conceptual purpose.

Indicator: YoY %% change in total foreign-held US corporate stocks (in millions
USD). Direction = natural (faster growth = bull = capital inflow into US equities).
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import duckdb

from tide.compute.zscore import latest_with_z, yoy_series
from tide.metrics import register
from tide.metrics.base import MetricDefinition, Reading, Vote


def _ingest() -> list[tuple[date, float]]:
    from tide.ingest.sources.treasury_tic import fetch_global_corporate_stock_holdings
    return fetch_global_corporate_stock_holdings()


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    # Monthly: lag=12 months, window=36 (3y).
    points = yoy_series(conn, "foreign_equity_holdings", lag=12, window=36)
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 4)  # ~3 months back
    delta_pp = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    if z > 0.3:
        direction = "bull"
        reason = "Foreign accumulation accelerating; net inflow into US equities"
    elif z < -0.5:
        direction = "bear"
        reason = "Foreign holdings shrinking — capital outflow signal"
    else:
        direction = "neutral"
        reason = "Foreign holdings growing near market pace"

    z_class = "pos" if z > 0.3 else ("neg" if z < -0.3 else "neu")

    return Reading(
        metric_id="foreign_equity_holdings",
        name="Foreign Equity Holdings",
        tier=2,
        source="Treasury TIC · SLT",
        unit="YoY · monthly",
        value=f"{latest.indicator:+.1f}%",
        delta=f"{delta_pp:+.1f}pp 3M",
        delta_class="pos" if delta_pp >= 0 else "neg",
        z=z,
        z_label=f"{z:+.1f}σ",
        z_class=z_class,
        directional_z=z,
        as_of=latest.ts,
        sparkline=sparkline,
        vote=Vote(direction=direction, reason=reason),
    )


register(MetricDefinition(
    id="foreign_equity_holdings",
    name="Foreign Equity Holdings",
    tier=2,
    source="Treasury TIC · SLT",
    source_kind="treasury_tic",
    source_series="slt1d_globl",
    unit="YoY · monthly",
    cadence="monthly",
    sort_order=20,
    indicator_kind="yoy",
    indicator_lag=12,
    indicator_window=36,
    direction_kind="natural",
    ingest_fn=_ingest,
    compute_fn=_compute,
))
