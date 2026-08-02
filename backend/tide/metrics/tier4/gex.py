"""Dealer Gamma Exposure (GEX) — SqueezeMetrics aggregate gamma in $ per 1% move.

Indicator: raw GEX level. Direction = natural (positive/high GEX → dealers long
gamma → they sell rallies and buy dips → vol dampened, bull regime; negative or
low GEX → dealers short gamma → they accelerate moves → vol amplified, bear).
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import duckdb

from tide.compute.zscore import latest_with_z, level_series
from tide.metrics import register
from tide.metrics.base import MetricDefinition, Reading, Vote


def _ingest() -> list[tuple[date, float]]:
    from tide.ingest.sources.squeezemetrics import fetch_gex
    return fetch_gex(start="2012-01-01")


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    points = level_series(conn, "gex", window=756)
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 6)  # 5 trading days back
    delta_5d = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    if z > 0.3:
        direction = "bull"
        reason = "Dealers long gamma — vol dampened, dips bought"
    elif z < -0.5:
        direction = "bear"
        reason = "Dealers short gamma — vol amplified, selloffs accelerate"
    else:
        direction = "neutral"
        reason = "Dealer gamma near long-run mean"

    z_class = "pos" if z > 0.3 else ("neg" if z < -0.3 else "neu")

    return Reading(
        metric_id="gex",
        name="Dealer Gamma (GEX)",
        tier=4,
        source="SqueezeMetrics",
        unit="$ gamma / 1% move",
        value=f"{latest.indicator:+.2e}",
        delta=f"{delta_5d:+.2e} 5D",
        delta_class="pos" if delta_5d >= 0 else "neg",
        z=z,
        z_label=f"{z:+.1f}σ",
        z_class=z_class,
        directional_z=z,
        as_of=latest.ts,
        sparkline=sparkline,
        vote=Vote(direction=direction, reason=reason),
    )


register(MetricDefinition(
    id="gex",
    name="Dealer Gamma (GEX)",
    tier=4,
    source="SqueezeMetrics",
    source_kind="squeezemetrics",
    source_series="GEX",
    unit="$ gamma / 1% move",
    cadence="daily",
    sort_order=35,
    indicator_kind="level",
    indicator_window=756,
    direction_kind="natural",
    ingest_fn=_ingest,
    compute_fn=_compute,
))
