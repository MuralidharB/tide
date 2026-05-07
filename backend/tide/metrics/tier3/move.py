"""MOVE Index — ICE BofA / Cboe Treasury vol (daily).

Indicator: raw MOVE level. INVERTED — low MOVE = calm Treasury vol = stable funding =
bull regime; high MOVE = bond stress = bear.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import duckdb

from tide.compute.zscore import latest_with_z, level_series
from tide.metrics import register
from tide.metrics.base import MetricDefinition, Reading, Vote


def _ingest() -> list[tuple[date, float]]:
    from tide.ingest.sources.yahoo import fetch_close_series
    return fetch_close_series("^MOVE", start="2008-01-01")


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    points = level_series(conn, "move", window=756)
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 14)  # ~13 trading days back
    delta = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    directional = -z  # INVERTED — low MOVE = calm = bull

    if directional > 0.3:
        direction = "bull"
        reason = "Calm Treasury vol — stable funding markets, no bond stress"
    elif directional < -0.5:
        direction = "bear"
        reason = "Treasury vol elevated — bond stress, funding pressure"
    else:
        direction = "neutral"
        reason = "Treasury vol near long-run mean"

    z_class = "pos" if directional > 0.3 else ("neg" if directional < -0.3 else "neu")
    descriptor = "calm" if z < -0.3 else ("stress" if z > 0.5 else "normal")

    return Reading(
        metric_id="move",
        name="MOVE Index",
        tier=3,
        source="Cboe · Treasury vol",
        unit=f"index · {descriptor}",
        value=f"{latest.indicator:.1f}",
        delta=f"{delta:+.1f} 13D",
        delta_class="pos" if delta <= 0 else "neg",
        z=z,
        z_label=f"{z:+.1f}σ",
        z_class=z_class,
        directional_z=directional,
        as_of=latest.ts,
        sparkline=sparkline,
        vote=Vote(direction=direction, reason=reason),
    )


register(MetricDefinition(
    id="move",
    name="MOVE Index",
    tier=3,
    source="Cboe · Treasury vol",
    source_kind="yahoo",
    source_series="^MOVE",
    unit="index",
    cadence="daily",
    sort_order=10,
    indicator_kind="level",
    indicator_window=756,
    direction_kind="inverted",
    ingest_fn=_ingest,
    compute_fn=_compute,
))
