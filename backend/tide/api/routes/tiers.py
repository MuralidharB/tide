"""Per-tier history endpoint — used by the tier focus pages to render a regime chart.

Data comes from the derived series `_tier_z_1..4` populated by
`tide-ingest backfill-composite`. This endpoint is a thin SELECT + join with the
static tier metadata that already lives in dashboard.py's TIER_META.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from tide.api.routes.dashboard import TIER_META
from tide.api.schemas import TierHistoryOut, TierHistoryPoint
from tide.db import connect

router = APIRouter()


@router.get("/tier/{tier}/history", response_model=TierHistoryOut)
def get_tier_history(tier: int) -> TierHistoryOut:
    if tier not in (1, 2, 3, 4):
        raise HTTPException(status_code=404, detail=f"Unknown tier: {tier}")
    name, tag, _cadence = TIER_META[tier]
    series_id = f"_tier_z_{tier}"

    with connect(read_only=True) as conn:
        rows = conn.execute(
            "SELECT ts, value FROM observations WHERE metric_id = ? ORDER BY ts",
            [series_id],
        ).fetchall()

    points = [TierHistoryPoint(ts=ts, z=z) for ts, z in rows]
    latest_z = points[-1].z if points else None

    return TierHistoryOut(tier=tier, name=name, tag=tag, points=points, latest_z=latest_z)
