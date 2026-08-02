"""Total Bank Credit — FRED TOTLL (weekly).

Indicator: YoY % change. Bull when accelerating (net credit creation), bear when contracting.
Direction = natural.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import duckdb

from tide.compute.zscore import latest_with_z, yoy_series
from tide.metrics import register
from tide.metrics.base import MetricDefinition, Reading, Vote


def _ingest() -> list[tuple[date, float]]:
    from tide.ingest.sources.fred import fetch_series
    return fetch_series("TOTLL", start="2000-01-01")


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    points = yoy_series(conn, "totll", lag=52, window=156)
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 14)
    delta_pp = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    if z > 0.3:
        direction = "bull"
        reason = "Net credit creation positive and accelerating"
    elif z < -0.5:
        direction = "bear"
        reason = "Bank credit growth decelerating sharply"
    else:
        direction = "neutral"
        reason = "Credit growth near long-run trend"

    z_class = "pos" if z > 0.3 else ("neg" if z < -0.3 else "neu")

    return Reading(
        metric_id="totll",
        name="Bank Credit Total",
        tier=1,
        source="FRED · TOTLL",
        unit="YoY",
        value=f"{latest.indicator:+.1f}%",
        delta=f"{delta_pp:+.1f}pp 13W",
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
    id="totll",
    name="Bank Credit Total",
    tier=1,
    source="FRED · TOTLL",
    source_kind="fred",
    source_series="TOTLL",
    unit="YoY",
    cadence="weekly",
    sort_order=50,
    indicator_kind="yoy",
    indicator_lag=52,
    indicator_window=156,
    direction_kind="natural",
    description=(
        "The total dollar amount of loans on the books of US commercial banks. Rising = "
        "banks are actually lending (real credit creation, driving economic activity). "
        "Falling or stagnant = banks pulling back, credit contracting. Shown as year-over-"
        "year growth; positive z-score = credit expanding faster than trend, bullish."
    ),
    ingest_fn=_ingest,
    compute_fn=_compute,
))
