"""Fed Balance Sheet — FRED WALCL (weekly).

Indicator: YoY % change. Vote bull when expanding, bear when shrinking.
Direction = natural (high z = bull).
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
    return fetch_series("WALCL", start="2003-01-01")


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    points = yoy_series(conn, "walcl", lag=52, window=156)
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 14)  # ~13 weeks back
    delta_pp = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    if z > 0.3:
        direction = "bull"
        reason = "Reserve creation accelerating; expanding base liquidity"
    elif z < -0.5:
        direction = "bear"
        reason = "Aggressive QT pace; balance sheet shrinking"
    else:
        direction = "neutral"
        reason = "Pace of change near long-run mean"

    z_class = "pos" if z > 0.3 else ("neg" if z < -0.3 else "neu")

    return Reading(
        metric_id="walcl",
        name="Fed Balance Sheet",
        tier=1,
        source="FRED · WALCL",
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
    id="walcl",
    name="Fed Balance Sheet",
    tier=1,
    source="FRED · WALCL",
    source_kind="fred",
    source_series="WALCL",
    unit="YoY",
    cadence="weekly",
    sort_order=20,
    indicator_kind="yoy",
    indicator_lag=52,
    indicator_window=156,
    direction_kind="natural",
    ingest_fn=_ingest,
    compute_fn=_compute,
))
