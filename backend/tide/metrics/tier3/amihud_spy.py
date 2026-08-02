"""Amihud Illiquidity (SPY) — substitute for ES top-of-book depth.

The mockup's Tier III calls for ES e-mini top-of-book depth, which isn't available
on free tiers. Amihud illiquidity is the established academic substitute for the same
conceptual dimension (capacity to absorb flow without moving price).

Indicator: |daily return %| / SPY dollar volume in $B, 5-day smoothed.
INVERTED: lower Amihud = more liquid market = bull (size can transact without impact).
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import duckdb

from tide.compute.transforms import amihud_from_ohlcv
from tide.compute.zscore import latest_with_z, level_series
from tide.metrics import register
from tide.metrics.base import MetricDefinition, Reading, Vote


def _ingest() -> list[tuple[date, float]]:
    from tide.ingest.sources.yahoo import fetch_close_volume
    bars = fetch_close_volume("SPY", start="2005-01-01")
    return amihud_from_ohlcv(bars, smoothing=5)


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    points = level_series(conn, "amihud_spy", window=756)
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 21)  # ~1 month back
    delta = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    directional = -z  # INVERTED — low Amihud = liquid = bull

    if directional > 0.3:
        direction = "bull"
        reason = "Tape absorbing flow easily; size transacts without impact"
    elif directional < -0.7:
        direction = "bear"
        reason = "Liquidity stress — price moves sharply on small flow"
    else:
        direction = "neutral"
        reason = "Liquidity near long-run mean"

    z_class = "pos" if directional > 0.3 else ("neg" if directional < -0.3 else "neu")

    return Reading(
        metric_id="amihud_spy",
        name="SPY Illiquidity (Amihud)",
        tier=3,
        source="Yahoo · SPY OHLCV",
        unit="|ret %| / $B · 5D MA",
        value=f"{latest.indicator:.4f}",
        delta=f"{delta:+.4f} 1M",
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
    id="amihud_spy",
    name="SPY Illiquidity (Amihud)",
    tier=3,
    source="Yahoo · SPY OHLCV",
    source_kind="yahoo",
    source_series="SPY",
    unit="|ret %| / $B",
    cadence="daily",
    sort_order=20,
    indicator_kind="level",
    indicator_window=756,
    direction_kind="inverted",
    description=(
        "A proxy for how easy it is to move size in the S&P 500 ETF (SPY) without moving "
        "the price. Computed from daily price move ÷ dollar volume traded. Low = deep, "
        "healthy liquidity (big trades absorbed without impact). High = fragile market where "
        "small trades move prices a lot. Substitutes for the ES futures top-of-book depth "
        "shown in the mockup (real depth data isn't free)."
    ),
    ingest_fn=_ingest,
    compute_fn=_compute,
))
