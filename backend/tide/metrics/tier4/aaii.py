"""AAII Bull/Bear Spread — weekly retail sentiment survey.

Indicator: AAII Bullish %% minus Bearish %% (the "spread" column from their xls),
in percentage points. Z-scored over 156 weeks.

Direction: contrarian. Mid-range is neutral; extreme bullish is contrarian-bear,
extreme bearish is contrarian-bull. Same vote pattern as COT S&P.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import duckdb

from tide.compute.zscore import latest_with_z, level_series
from tide.metrics import register
from tide.metrics.base import MetricDefinition, Reading, Vote


def _ingest() -> list[tuple[date, float]]:
    from tide.ingest.sources.aaii import fetch_bull_bear_spread
    return fetch_bull_bear_spread()


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    points = level_series(conn, "aaii", window=156)
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 2)  # 1 week back
    delta = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    if z > 1.5:
        direction = "bear"
        reason = "Retail euphoria — contrarian bearish at extreme bullishness"
        directional = -z
    elif z < -1.5:
        direction = "bull"
        reason = "Retail capitulation — contrarian bullish at extreme bearishness"
        directional = -z
    else:
        direction = "neutral"
        reason = "Sentiment elevated but not at contrarian extreme yet" if z > 0.5 else (
            "Sentiment subdued but not at contrarian extreme" if z < -0.5 else
            "Sentiment near long-run mean"
        )
        directional = -0.3 * z

    z_class = "neg" if direction == "bear" else ("pos" if direction == "bull" else "neu")

    return Reading(
        metric_id="aaii",
        name="AAII Bull/Bear",
        tier=4,
        source="AAII · weekly survey",
        unit="spread (pp)",
        value=f"{latest.indicator:+.0f}",
        delta=f"{delta:+.1f} 1W",
        delta_class="pos" if delta >= 0 else "neg",
        z=z,
        z_label=f"{z:+.1f}σ",
        z_class=z_class,
        directional_z=directional,
        as_of=latest.ts,
        sparkline=sparkline,
        vote=Vote(direction=direction, reason=reason),
    )


register(MetricDefinition(
    id="aaii",
    name="AAII Bull/Bear",
    tier=4,
    source="AAII · weekly survey",
    source_kind="aaii",
    source_series="sentiment.xls",
    unit="spread (pp)",
    cadence="weekly",
    sort_order=20,
    indicator_kind="level",
    indicator_window=156,
    direction_kind="contrarian_long",
    description=(
        "A weekly survey the American Association of Individual Investors sends to its retail "
        "members: \"Bullish, Neutral, or Bearish for the next 6 months?\" Shown as the spread "
        "(bullish % minus bearish %). Read contrarianly: extreme bullishness (everyone's "
        "already long, no one left to buy) is a warning; extreme bearishness (retail "
        "capitulation) often marks bottoms. Mid-range readings carry little signal."
    ),
    ingest_fn=_ingest,
    compute_fn=_compute,
))
