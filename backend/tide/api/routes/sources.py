"""Sources endpoint — every registered metric with last-ingested timestamps.

Used by the Sources sidebar page to surface ingestion health (which metrics are
fresh, which are stale, which are stubbed). Helpful when debugging — e.g. AAII's
bot detection cycling, or noticing FRED released a series rebase mid-month.
"""
from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from tide.db import connect
from tide.metrics import all_metrics

router = APIRouter()


class SourceRow(BaseModel):
    metric_id: str
    name: str
    tier: int
    source: str
    source_kind: str
    cadence: str
    status: str               # "live" | "stub"
    last_observation: date | None
    last_ingested_at: datetime | None
    obs_count: int


class SourcesOut(BaseModel):
    rows: list[SourceRow]


@router.get("/sources", response_model=SourcesOut)
def get_sources() -> SourcesOut:
    rows: list[SourceRow] = []
    with connect(read_only=True) as conn:
        for m in all_metrics():
            stat = conn.execute(
                """
                SELECT MAX(ts), MAX(ingested_at), COUNT(*)
                FROM observations WHERE metric_id = ?
                """,
                [m.id],
            ).fetchone()
            last_ts, last_ing, n = stat or (None, None, 0)
            rows.append(SourceRow(
                metric_id=m.id,
                name=m.name,
                tier=m.tier,
                source=m.source,
                source_kind=m.source_kind,
                cadence=m.cadence,
                status="live" if m.ingest_fn is not None else "stub",
                last_observation=last_ts,
                last_ingested_at=last_ing,
                obs_count=int(n or 0),
            ))
    return SourcesOut(rows=rows)
