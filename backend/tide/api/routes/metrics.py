from datetime import date

from fastapi import APIRouter, HTTPException

from tide.api.routes.dashboard import _reading_to_out
from tide.api.schemas import DetailPoint, HistoryOut, HistoryPoint, MetricDetailOut
from tide.compute.zscore import level_series, yoy_series
from tide.db import connect
from tide.metrics import _REGISTRY, get_metric  # noqa: PLC2701

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


@router.get("/metrics/{metric_id}/detail", response_model=MetricDetailOut)
def get_detail(metric_id: str) -> MetricDetailOut:
    """Full detail for one metric — registry metadata + latest reading + indicator+z series.

    The series is the *computed indicator* (yoy% or raw level) alongside its rolling
    z-score, matching what compute_fn uses to build the card reading. This lets the
    detail page draw the historical curve of what the user sees on the card, with
    ±1σ / ±2σ context bands derivable client-side from the z column.
    """
    if metric_id not in _REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown metric: {metric_id}")
    m = get_metric(metric_id)

    with connect(read_only=True) as conn:
        if m.indicator_kind == "yoy":
            points = yoy_series(conn, m.id, m.indicator_lag, m.indicator_window)
        else:
            points = level_series(conn, m.id, m.indicator_window)
        series = [DetailPoint(ts=p.ts, indicator=p.indicator, z=p.z) for p in points]

        obs_count = int(
            conn.execute(
                "SELECT COUNT(*) FROM observations WHERE metric_id = ?",
                [metric_id],
            ).fetchone()[0]
        )

        reading_out = None
        if m.compute_fn is not None:
            r = m.compute_fn(conn)
            if r is not None:
                reading_out = _reading_to_out(r)

    return MetricDetailOut(
        metric_id=m.id,
        name=m.name,
        tier=m.tier,
        source=m.source,
        source_kind=m.source_kind,
        source_series=m.source_series,
        unit=m.unit,
        cadence=m.cadence,
        description=m.description,
        direction_kind=m.direction_kind,
        indicator_kind=m.indicator_kind,
        indicator_window=m.indicator_window,
        indicator_lag=m.indicator_lag,
        zscore_years=m.zscore_years,
        include_in_composite=m.include_in_composite,
        reading=reading_out,
        series=series,
        obs_count=obs_count,
    )
