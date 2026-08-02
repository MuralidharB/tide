"""Margin Debt — FRED Z.1 quarterly substitute for FINRA monthly.

The mockup uses FINRA's monthly Margin Statistics. FINRA stopped publishing the
free monthly XLS at the documented URL (returns 404 as of 2026-05). The closest
free-tier substitute is the Federal Reserve's Z.1 Financial Accounts series
`BOGZ1FL663067003Q` — Security Brokers and Dealers; Receivables Due from Customers,
quarterly. Same economic concept (broker margin loans outstanding to customers),
slower cadence.

Indicator: YoY %% change. Vote bull when accelerating (real new buying power),
bear when decelerating sharply, with a contrarian-bear tag at extreme highs.
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
    return fetch_series("BOGZ1FL663067003Q", start="1990-01-01")


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    # Quarterly cadence: lag=4 quarters, window=12 quarters (3y).
    points = yoy_series(conn, "margin_debt", lag=4, window=12)
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 2)  # 1 quarter back
    delta_pp = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    if z > 1.5:
        direction = "bear"
        reason = "Margin debt extreme — late-cycle leverage signal"
    elif z > 0.3:
        direction = "bull"
        reason = "Real new buying power; broker margin expanding"
    elif z < -0.5:
        direction = "bear"
        reason = "Margin debt contracting — leverage being unwound"
    else:
        direction = "neutral"
        reason = "Margin debt growth near long-run trend"

    z_class = "pos" if 0.3 < z < 1.5 else ("neg" if (z < -0.3 or z > 1.5) else "neu")

    return Reading(
        metric_id="margin_debt",
        name="Margin Debt (Z.1)",
        tier=2,
        source="FRED · BOGZ1FL663067003Q",
        unit="YoY · quarterly",
        value=f"{latest.indicator:+.1f}%",
        delta=f"{delta_pp:+.1f}pp QoQ",
        delta_class="pos" if delta_pp >= 0 else "neg",
        z=z,
        z_label=f"{z:+.1f}σ",
        z_class=z_class,
        directional_z=z if z <= 1.5 else -z,  # contrarian flip past +1.5σ
        as_of=latest.ts,
        sparkline=sparkline,
        vote=Vote(direction=direction, reason=reason),
    )


register(MetricDefinition(
    id="margin_debt",
    name="Margin Debt (Z.1)",
    tier=2,
    source="FRED · BOGZ1FL663067003Q",
    source_kind="fred",
    source_series="BOGZ1FL663067003Q",
    unit="YoY · quarterly",
    cadence="quarterly",
    sort_order=10,
    indicator_kind="yoy",
    indicator_lag=4,
    indicator_window=12,
    direction_kind="natural",  # contrarian-flip past +1.5σ is handled in compute_fn
    description=(
        "How much money US investors have borrowed against their brokerage accounts to buy "
        "stocks. Growing = investors are bullish and leveraging up (real new buying power). "
        "But at extreme highs (well above trend), it becomes a late-cycle warning: excess "
        "leverage historically precedes market corrections because forced selling accelerates "
        "any downturn. Quarterly data with a ~2-month publication lag."
    ),
    ingest_fn=_ingest,
    compute_fn=_compute,
))
