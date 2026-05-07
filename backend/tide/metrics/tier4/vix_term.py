"""VIX Term Structure — Cboe via yfinance ^VIX / ^VIX3M (daily ratio).

Indicator: VIX / VIX3M ratio. <1 = contango (front-month cheaper than 3M, calm regime);
>1 = backwardation (front-month richer, fear regime). INVERTED: low ratio = bull.

Implementation note: this metric reads from TWO upstream series (^VIX and ^VIX3M). We
ingest each into its own metric_id (`_vix` and `_vix3m` — leading underscore so they
don't show on the dashboard), then compose the ratio at compute time. This keeps raw
observations stored verbatim and the indicator logic in code.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import duckdb

from tide.metrics import register
from tide.metrics.base import MetricDefinition, Reading, Vote


def _ingest() -> list[tuple[date, float]]:
    """Fetch both legs and merge by date. Returns the ratio series for storage."""
    from tide.ingest.sources.yahoo import fetch_close_series
    vix = dict(fetch_close_series("^VIX", start="2008-01-01"))
    vix3m = dict(fetch_close_series("^VIX3M", start="2008-01-01"))
    common = sorted(set(vix) & set(vix3m))
    return [(d, vix[d] / vix3m[d]) for d in common if vix3m[d] > 0]


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    from tide.compute.zscore import latest_with_z, level_series
    points = level_series(conn, "vix_term", window=756)  # ~3 trading years
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 6)  # 5 trading days back
    delta_5d = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    directional = -z  # INVERTED — contango (low ratio) = bull

    if directional > 0.5:
        direction = "bull"
        reason = "Steep contango — low fear, calm regime"
    elif directional < -0.7:
        direction = "bear"
        reason = "Backwardation — front-end fear elevated"
    else:
        direction = "neutral"
        reason = "Term structure near long-run mean"

    z_class = "pos" if directional > 0.3 else ("neg" if directional < -0.3 else "neu")
    structure = "contango" if latest.indicator < 1 else "backwardation"

    return Reading(
        metric_id="vix_term",
        name="VIX Term Structure",
        tier=4,
        source="Cboe · VIX/VIX3M",
        unit=f"ratio · {structure}",
        value=f"{latest.indicator:.2f}",
        delta=f"{delta_5d:+.2f} 5D",
        delta_class="pos" if delta_5d <= 0 else "neg",
        z=z,
        z_label=f"{z:+.1f}σ",
        z_class=z_class,
        directional_z=directional,
        as_of=latest.ts,
        sparkline=sparkline,
        vote=Vote(direction=direction, reason=reason),
    )


register(MetricDefinition(
    id="vix_term",
    name="VIX Term Structure",
    tier=4,
    source="Cboe · VIX/VIX3M",
    source_kind="yfinance",
    source_series="^VIX/^VIX3M",
    unit="ratio · contango",
    cadence="daily",
    sort_order=10,
    indicator_kind="level",
    indicator_window=756,
    direction_kind="inverted",
    ingest_fn=_ingest,
    compute_fn=_compute,
))
