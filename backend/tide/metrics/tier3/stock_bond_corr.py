"""Stock-Bond Correlation — 60D rolling Pearson on SPY vs TLT daily returns.

Indicator: rolling 60-day correlation of SPY and TLT daily returns, computed at ingest.
INVERTED: more negative correlation = stocks and bonds diversify each other = healthy
risk-on regime. Positive correlation (regime change) is bearish.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import duckdb

from tide.compute.transforms import daily_returns, rolling_pearson_corr
from tide.compute.zscore import latest_with_z, level_series
from tide.metrics import register
from tide.metrics.base import MetricDefinition, Reading, Vote


def _ingest() -> list[tuple[date, float]]:
    from tide.ingest.sources.yahoo import fetch_close_series
    spy = fetch_close_series("SPY", start="2005-01-01")
    tlt = fetch_close_series("TLT", start="2005-01-01")
    return rolling_pearson_corr(daily_returns(spy), daily_returns(tlt), window=60)


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    points = level_series(conn, "stock_bond_corr", window=756)
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 21)
    delta = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    directional = -z  # INVERTED — more negative corr = better diversification = bull

    if directional > 0.5:
        direction = "bull"
        reason = "Strong negative correlation — bonds hedging equity well"
    elif directional < -0.5:
        direction = "bear"
        reason = "Correlation turning positive — diversification breaking down"
    else:
        direction = "neutral"
        reason = "Diversification working but not strongly"

    z_class = "pos" if directional > 0.3 else ("neg" if directional < -0.3 else "neu")
    descriptor = "diversifying" if latest.indicator < 0 else "co-moving"

    return Reading(
        metric_id="stock_bond_corr",
        name="Stock-Bond Correlation",
        tier=3,
        source="60D rolling · SPY/TLT",
        unit=f"correlation · {descriptor}",
        value=f"{latest.indicator:+.2f}",
        delta=f"{delta:+.2f} 1M",
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
    id="stock_bond_corr",
    name="Stock-Bond Correlation",
    tier=3,
    source="60D rolling · SPY/TLT",
    source_kind="derived",
    source_series="SPY/TLT",
    unit="correlation",
    cadence="daily",
    sort_order=40,
    indicator_kind="level",
    indicator_window=756,
    direction_kind="inverted",
    ingest_fn=_ingest,
    compute_fn=_compute,
))
