from datetime import date

from fastapi import APIRouter, HTTPException

from tide.api.schemas import HistoryOut, HistoryPoint
from tide.db import connect
from tide.metrics import _REGISTRY  # noqa: PLC2701  — internal access for existence check

router = APIRouter()


@router.get("/metrics/{metric_id}/history", response_model=HistoryOut)
def get_history(metric_id: str, since: date | None = None) -> HistoryOut:
    if metric_id not in _REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown metric: {metric_id}")
    sql = "SELECT ts, value FROM observations WHERE metric_id = ?"
    params: list = [metric_id]
    if since is not None:
        sql += " AND ts >= ?"
        params.append(since)
    sql += " ORDER BY ts"
    with connect(read_only=True) as conn:
        rows = conn.execute(sql, params).fetchall()
    return HistoryOut(
        metric_id=metric_id,
        points=[HistoryPoint(ts=ts, value=v) for ts, v in rows],
    )
