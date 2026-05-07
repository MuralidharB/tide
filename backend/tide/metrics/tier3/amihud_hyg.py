"""HYG Illiquidity (Amihud) — substitute for HYG bid-ask spread.

True bid-ask spreads need intraday data, which isn't available on free tiers. Amihud
illiquidity on HYG end-of-day data captures the same conceptual dimension: when HYG
becomes harder to transact, modest dollar flow moves price more.

Indicator: |daily return %| / HYG dollar volume in $B, 5-day smoothed.
INVERTED: lower Amihud = healthy credit ETF function = bull.
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
    bars = fetch_close_volume("HYG", start="2008-01-01")
    return amihud_from_ohlcv(bars, smoothing=5)


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    points = level_series(conn, "amihud_hyg", window=756)
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 21)
    delta = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    directional = -z  # INVERTED — low = healthy = bull

    if directional > 0.3:
        direction = "bull"
        reason = "Healthy HY ETF function; tight effective spreads"
    elif directional < -0.7:
        direction = "bear"
        reason = "HY ETF illiquidity rising — credit market function deteriorating"
    else:
        direction = "neutral"
        reason = "HY ETF liquidity near long-run mean"

    z_class = "pos" if directional > 0.3 else ("neg" if directional < -0.3 else "neu")

    return Reading(
        metric_id="amihud_hyg",
        name="HYG Illiquidity (Amihud)",
        tier=3,
        source="Yahoo · HYG OHLCV",
        unit="|ret %| / $B · 5D MA",
        value=f"{latest.indicator:.3f}",
        delta=f"{delta:+.3f} 1M",
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
    id="amihud_hyg",
    name="HYG Illiquidity (Amihud)",
    tier=3,
    source="Yahoo · HYG OHLCV",
    source_kind="yahoo",
    source_series="HYG",
    unit="|ret %| / $B",
    cadence="daily",
    sort_order=30,
    indicator_kind="level",
    indicator_window=756,
    direction_kind="inverted",
    ingest_fn=_ingest,
    compute_fn=_compute,
))
