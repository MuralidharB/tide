"""Dashboard endpoint — single chunky read for the SvelteKit page server.

The page server calls this once per request and hands the full payload to the page.
"""
from __future__ import annotations

from statistics import mean

from fastapi import APIRouter

from tide.api.schemas import (
    CompositeHistoryPoint,
    CompositeOut,
    DashboardOut,
    ReadingOut,
    TallyOut,
    TierOut,
    VoteOut,
)
from tide.compute.composite import composite_from_readings
from tide.db import connect
from tide.metrics import all_metrics, get_metric, metrics_in_tier
from tide.metrics.base import Reading

router = APIRouter()

TIER_META = {
    1: ("Macro Liquidity", "The base · multi-year", "5 series · monthly–weekly cadence"),
    2: ("Capital Flows", "Capital direction · months", "4 series · weekly–monthly cadence"),
    3: ("Market Microstructure", "Capacity to transact · daily", "5 series · realtime–daily cadence"),
    4: ("Sentiment & Positioning", "Willingness to transact · days–weeks", "5 series · daily cadence"),
}


def _reading_to_out(r: Reading) -> ReadingOut:
    return ReadingOut(
        metric_id=r.metric_id,
        name=r.name,
        tier=r.tier,
        source=r.source,
        unit=r.unit,
        value=r.value,
        delta=r.delta,
        delta_class=r.delta_class,
        z=r.z,
        z_label=r.z_label,
        z_class=r.z_class,
        as_of=r.as_of,
        sparkline=r.sparkline,
        vote=VoteOut(direction=r.vote.direction, reason=r.vote.reason),
        include_in_composite=get_metric(r.metric_id).include_in_composite,
    )


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard() -> DashboardOut:
    readings: list[Reading] = []
    composite_readings: list[Reading] = []
    with connect(read_only=True) as conn:
        for m in all_metrics():
            if m.compute_fn is None:
                continue
            r = m.compute_fn(conn)
            if r is not None:
                readings.append(r)
                if m.include_in_composite:
                    composite_readings.append(r)

    # Loadedness/fragility gauges (include_in_composite=False) render as tier cards
    # but do NOT enter the directional composite average or tally.
    composite = composite_from_readings(composite_readings)
    composite_out: CompositeOut | None = None
    if composite is not None:
        composite_out = CompositeOut(
            z=composite.z,
            z_label=composite.z_label,
            sign_class=composite.sign_class,
            tally=TallyOut(
                bull=composite.tally.bull,
                neutral=composite.tally.neutral,
                bear=composite.tally.bear,
            ),
            metrics_total=composite.metrics_total,
        )

    tiers: list[TierOut] = []
    for tier_num in (1, 2, 3, 4):
        name, tag, cadence = TIER_META[tier_num]
        tier_readings = [r for r in readings if r.tier == tier_num]
        avg_z = mean([r.z for r in tier_readings]) if tier_readings else None
        tiers.append(TierOut(
            tier=tier_num,
            name=name,
            tag=tag,
            cadence=cadence,
            metrics=[_reading_to_out(r) for r in tier_readings],
            avg_z=avg_z,
        ))

    # Composite history is precomputed by `tide-ingest backfill-composite` and stored
    # under series id `_composite_z`. SPY closes on the same dates come from `_spy_close`
    # (refreshed by the same backfill) so the frontend can overlay the S&P 500.
    history_rows: list[CompositeHistoryPoint] = []
    with connect(read_only=True) as conn:
        for ts, z, spy in conn.execute(
            """
            SELECT c.ts, c.value AS z, s.value AS spy_close
            FROM observations c
            LEFT JOIN observations s
              ON s.metric_id = '_spy_close' AND s.ts = c.ts
            WHERE c.metric_id = '_composite_z'
            ORDER BY c.ts
            """
        ).fetchall():
            history_rows.append(CompositeHistoryPoint(ts=ts, z=z, spy_close=spy))

    return DashboardOut(composite=composite_out, tiers=tiers, composite_history=history_rows)
