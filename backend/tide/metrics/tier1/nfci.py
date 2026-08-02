"""Chicago Fed NFCI — FRED NFCI (weekly).

Indicator: raw level. Negative = looser-than-average financial conditions. INVERTED:
loose conditions (low z) are bullish for risk assets; tightening (high z) is bearish.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import duckdb

from tide.compute.zscore import latest_with_z, level_series
from tide.metrics import register
from tide.metrics.base import MetricDefinition, Reading, Vote


def _ingest() -> list[tuple[date, float]]:
    from tide.ingest.sources.fred import fetch_series
    return fetch_series("NFCI", start="2000-01-01")


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    points = level_series(conn, "nfci", window=156)
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 14)  # 13 weeks back
    delta = latest.indicator - points[prior_idx].indicator
    delta_class = "pos" if delta <= 0 else "neg"  # loosening = pos
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    directional = -z  # INVERTED — loose = bull

    if directional > 0.3:
        direction = "bull"
        reason = "Financial conditions loose and easing further"
    elif directional < -0.5:
        direction = "bear"
        reason = "Financial conditions tightening — risk-off pressure"
    else:
        direction = "neutral"
        reason = "Financial conditions near long-run normal"

    z_class = "pos" if directional > 0.3 else ("neg" if directional < -0.3 else "neu")
    label_unit = "loose" if latest.indicator < 0 else "tight"

    return Reading(
        metric_id="nfci",
        name="Chicago Fed NFCI",
        tier=1,
        source="FRED · NFCI",
        unit=f"index · {label_unit}",
        value=f"{latest.indicator:+.2f}",
        delta=f"{delta:+.2f} 13W",
        delta_class=delta_class,
        z=z,
        z_label=f"{z:+.1f}σ",
        z_class=z_class,
        directional_z=directional,
        as_of=latest.ts,
        sparkline=sparkline,
        vote=Vote(direction=direction, reason=reason),
    )


register(MetricDefinition(
    id="nfci",
    name="Chicago Fed NFCI",
    tier=1,
    source="FRED · NFCI",
    source_kind="fred",
    source_series="NFCI",
    unit="index · loose",
    cadence="weekly",
    sort_order=40,
    indicator_kind="level",
    indicator_window=156,
    direction_kind="inverted",
    description=(
        "A single number the Chicago Fed publishes weekly summarizing whether US financial "
        "conditions overall — interest rates, credit availability, market volatility — are "
        "loose or tight. Negative values mean loose (easy to borrow, calm markets); positive "
        "means tight (funding stress). Loose financial conditions are bullish for risk assets."
    ),
    ingest_fn=_ingest,
    compute_fn=_compute,
))
