"""COT S&P 500 spec net — CFTC TFF report on E-MINI S&P 500.

Indicator: leveraged-money net long position as %% of open interest. Computed weekly
(report comes out every Friday afternoon for Tuesday's positions).

Direction = INVERTED with a contrarian flip: small net positions are neutral; high
positive (extreme long) is contrarian-bearish; high negative (extreme short) is
contrarian-bullish. The mockup convention: extreme long at +2σ → vote=bear despite
positive z, with reasoning "contrarian bearish at +2σ".

Implementation note: the indicator is z-scored over a 156-week (3y) rolling window.
Vote logic uses absolute z magnitude past ±1.5σ to flip, otherwise mid-range is neutral
with a mild trend bias.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import duckdb

from tide.compute.zscore import latest_with_z, level_series
from tide.metrics import register
from tide.metrics.base import MetricDefinition, Reading, Vote


def _ingest() -> list[tuple[date, float]]:
    from tide.ingest.sources.cftc import (
        EMINI_SP500_RE,
        fetch_tff_history,
        parse_emini_sp500_spec_net_pct,
    )
    rows = fetch_tff_history(EMINI_SP500_RE, start_year=2010)
    return parse_emini_sp500_spec_net_pct(rows)


def _compute(conn: duckdb.DuckDBPyConnection) -> Optional[Reading]:
    points = level_series(conn, "cot_sp", window=156)
    latest = latest_with_z(points)
    if latest is None:
        return None

    prior_idx = max(0, len(points) - 5)  # ~4 weeks back
    delta = latest.indicator - points[prior_idx].indicator
    sparkline = [p.indicator for p in points[-60:]]

    z = float(latest.z)
    # Contrarian: extreme long is bearish, extreme short is bullish.
    if z > 1.5:
        direction = "bear"
        reason = "Spec positioning extreme long — contrarian bearish"
        directional = -z
    elif z < -1.5:
        direction = "bull"
        reason = "Spec positioning extreme short — contrarian bullish"
        directional = -z
    elif z > 0.3:
        direction = "neutral"
        reason = "Spec positioning elevated long but not yet extreme"
        directional = -0.3 * z  # mild contrarian bias
    elif z < -0.5:
        direction = "neutral"
        reason = "Spec positioning short but not yet extreme"
        directional = -0.3 * z
    else:
        direction = "neutral"
        reason = "Spec positioning balanced"
        directional = 0.0

    # z_class follows the *vote* color: bear vote = neg, bull = pos, neutral = neu
    z_class = "neg" if direction == "bear" else ("pos" if direction == "bull" else "neu")

    side = "net long" if latest.indicator > 0 else "net short"

    return Reading(
        metric_id="cot_sp",
        name="COT S&P Spec Net",
        tier=4,
        source="CFTC · E-MINI S&P 500 (TFF)",
        unit=f"%% of OI · {side}",
        value=f"{latest.indicator:+.1f}%",
        delta=f"{delta:+.1f}pp 4W",
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
    id="cot_sp",
    name="COT S&P Spec Net",
    tier=4,
    source="CFTC · E-MINI S&P 500 (TFF)",
    source_kind="cftc",
    source_series="E-MINI S&P 500",
    unit="% of OI",
    cadence="weekly",
    sort_order=40,
    indicator_kind="level",
    indicator_window=156,
    direction_kind="contrarian_long",
    description=(
        "Net position of leveraged-money speculators (hedge funds, CTAs) in S&P 500 e-mini "
        "futures, published weekly by the CFTC. Expressed as % of total open interest. Read "
        "contrarianly: when speculators are extremely net long, the trade is crowded and any "
        "reversal forces them to sell — bearish. Extreme net short = crowded bear positioning, "
        "vulnerable to a short squeeze — bullish."
    ),
    ingest_fn=_ingest,
    compute_fn=_compute,
))
