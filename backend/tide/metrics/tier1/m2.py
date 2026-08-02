"""M2 Money Supply — FRED M2SL (monthly).

Indicator: YoY % change of M2 level. Vote bull when YoY z > +0.3 (reaccelerating),
bear when z < -0.5 (sharp decel). Direction = natural (high z = bull).
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
    return fetch_series("M2SL", start="1995-01-01")


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    points = yoy_series(conn, "m2", lag=12, window=36)
    latest = latest_with_z(points)
    if latest is None:
        return None

    # 13W ≈ 3 monthly observations back
    prior_idx = max(0, len(points) - 4)
    delta_pp = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    if z > 0.3:
        direction = "bull"
        reason = "Reaccelerating from cycle low; expanding base liquidity"
    elif z < -0.5:
        direction = "bear"
        reason = "Decelerating sharply; contracting base liquidity"
    else:
        direction = "neutral"
        reason = "Near long-run trend"

    z_class = "pos" if z > 0.3 else ("neg" if z < -0.3 else "neu")

    return Reading(
        metric_id="m2",
        name="M2 Money Supply",
        tier=1,
        source="FRED · M2SL",
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
    id="m2",
    name="M2 Money Supply",
    tier=1,
    source="FRED · M2SL",
    source_kind="fred",
    source_series="M2SL",
    unit="YoY",
    cadence="monthly",
    sort_order=10,
    indicator_kind="yoy",
    indicator_lag=12,
    indicator_window=36,
    direction_kind="natural",
    description=(
        "The total pool of dollars in checking, savings, and money-market accounts across "
        "the US economy. When M2 grows faster than average, more cash is available to chase "
        "assets — historically supportive of stock and bond prices. Shown as % change vs "
        "the same month last year; positive z-score means growing faster than the 3-year "
        "average, which is bullish for risk assets."
    ),
    ingest_fn=_ingest,
    compute_fn=_compute,
))
