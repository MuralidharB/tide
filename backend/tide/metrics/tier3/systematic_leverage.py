"""Systematic Leverage Proxy — vol-target implied leverage on ^IXIC 20D realized vol.

This is a LOADEDNESS gauge, not a direction signal, and is deliberately excluded
from the composite (`include_in_composite=False`).

Rationale: vol-target and risk-parity strategies mechanically size positions inversely
to trailing realized vol. When RV falls, the same target vol implies more leverage —
funds must add exposure. When a shock hits and RV spikes, those strategies must sell
to bring exposure back in line, and their forced selling amplifies the move. So "low,
falling RV" simultaneously looks calm on every direction gauge and represents a
loaded spring underneath.

Indicator: target_vol / realized_vol_20D, with target_vol = 10% annualized (typical
vol-target parameter). Clamped to 5.0 to keep the spring finite when RV → 0.

Direction: INVERTED — a high leverage proxy (low RV) is FRAGILE, so tilts bear.
But because encoding loadedness on the bull/bear axis is a category error, this
metric renders as a tier card while being held out of the composite average.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import duckdb

from tide.compute.transforms import realized_vol
from tide.compute.zscore import latest_with_z, level_series
from tide.metrics import register
from tide.metrics.base import MetricDefinition, Reading, Vote

TARGET_VOL = 0.10        # annualized
LEVERAGE_CLAMP = 5.0     # cap on proxy when RV gets tiny


def _ingest() -> list[tuple[date, float]]:
    from tide.ingest.sources.yahoo import fetch_close_series
    closes = fetch_close_series("^IXIC", start="2005-01-01")
    rv = realized_vol(closes, window=20)
    out: list[tuple[date, float]] = []
    for ts, sd in rv:
        if sd <= 0:
            continue
        proxy = min(TARGET_VOL / sd, LEVERAGE_CLAMP)
        out.append((ts, proxy))
    return out


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    points = level_series(conn, "systematic_leverage", window=756)
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 21)  # ~1 month back
    delta = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    directional = -z  # INVERTED — high proxy = fragile = bear tilt

    if z > 1.5:
        direction = "bear"
        reason = "Systematic leverage extreme — fragile to a vol shock"
    elif z < -1.0:
        direction = "bull"
        reason = "Leverage low — limited forced-selling overhang"
    else:
        direction = "neutral"
        reason = "Systematic leverage near long-run mean"

    z_class = "neg" if z > 0.3 else ("pos" if z < -0.3 else "neu")

    return Reading(
        metric_id="systematic_leverage",
        name="Systematic Leverage",
        tier=3,
        source="Derived · ^IXIC 20D RV",
        unit="vol-target leverage proxy",
        value=f"{latest.indicator:.2f}×",
        delta=f"{delta:+.2f} 1M",
        delta_class="neg" if delta >= 0 else "pos",  # rising leverage = more fragile
        z=z,
        z_label=f"{z:+.1f}σ",
        z_class=z_class,
        directional_z=directional,
        as_of=latest.ts,
        sparkline=sparkline,
        vote=Vote(direction=direction, reason=reason),
    )


register(MetricDefinition(
    id="systematic_leverage",
    name="Systematic Leverage",
    tier=3,
    source="Derived · ^IXIC 20D RV",
    source_kind="derived",
    source_series="^IXIC",
    unit="vol-target leverage proxy",
    cadence="daily",
    sort_order=50,
    indicator_kind="level",
    indicator_window=756,
    direction_kind="inverted",
    include_in_composite=False,
    description=(
        "Estimated leverage of vol-targeting and risk-parity funds, implied by trailing "
        "realized volatility. These funds mechanically SIZE UP when vol is low and SIZE DOWN "
        "when vol spikes — so calm markets quietly load a spring. High values = fragility: "
        "if vol shocks, forced selling accelerates any move. Held out of the composite "
        "because it's a LOADEDNESS gauge, not a direction signal."
    ),
    ingest_fn=_ingest,
    compute_fn=_compute,
))
