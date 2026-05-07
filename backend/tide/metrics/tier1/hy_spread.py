"""HY Credit Spread — FRED BAMLH0A0HYM2 (daily, OAS in bps).

Indicator: raw spread level. INVERTED: tight spreads (low z) = bull. The displayed `z`
keeps its natural sign (so the dashboard reads "−1.4σ" when spreads are tight); `z_class`
and `directional_z` are flipped so the chip is green and the composite reads bullish.
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
    # OAS series goes back to 1996. Daily data — 3y window = ~756 trading days.
    return fetch_series("BAMLH0A0HYM2", start="2000-01-01")


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    # FRED truncated this series to a rolling 3y window in April 2026 (per the FRED
    # series notes). With only ~785 daily obs available, a 756-day z-window leaves
    # essentially zero valid history for the sparkline, so we fall back to a 1y window.
    points = level_series(conn, "hy_spread", window=252)
    latest = latest_with_z(points)
    if latest is None:
        return None

    # FRED's BAMLH0A0HYM2 is published in percent (e.g. 2.87 = 287 bps). Display in bps.
    value_bps = latest.indicator * 100
    prior_idx = max(0, len(points) - 66)  # ~13 weeks of trading days
    delta_bps = (latest.indicator - points[prior_idx].indicator) * 100
    delta_class = "pos" if delta_bps <= 0 else "neg"  # tightening = pos
    sparkline = [p.indicator * 100 for p in points[-60:]]

    z = float(latest.z)
    # INVERTED: tight (low z) = bull. directional_z flips the sign.
    directional = -z

    if directional > 0.3:
        direction = "bull"
        reason = "Tight spreads — abundant credit, healthy risk appetite"
    elif directional < -0.5:
        direction = "bear"
        reason = "Widening spreads — credit stress building"
    else:
        direction = "neutral"
        reason = "Spreads near long-run mean"

    z_class = "pos" if directional > 0.3 else ("neg" if directional < -0.3 else "neu")

    return Reading(
        metric_id="hy_spread",
        name="HY Credit Spread",
        tier=1,
        source="FRED · BAMLH0A0HYM2",
        unit="bps · OAS",
        value=f"{value_bps:.0f}",
        delta=f"{delta_bps:+.0f}bps 13W",
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
    id="hy_spread",
    name="HY Credit Spread",
    tier=1,
    source="FRED · BAMLH0A0HYM2",
    source_kind="fred",
    source_series="BAMLH0A0HYM2",
    unit="bps · OAS",
    cadence="daily",
    zscore_years=1,  # constrained by FRED's 3y series truncation — see _compute
    sort_order=30,
    indicator_kind="level",
    indicator_window=252,
    direction_kind="inverted",
    ingest_fn=_ingest,
    compute_fn=_compute,
))
