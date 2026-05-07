"""Reusable z-score helpers — every metric's compute_fn pulls a series via one of these.

Two shapes cover most metrics:
  - level_series:  raw observation z-scored over a rolling window (HY spread, NFCI, VIX)
  - yoy_series:    YoY % change z-scored over a rolling window (M2, WALCL, TOTLL)

`window` is the rolling window length in *observation periods* — match it to the metric's
publication cadence (monthly metric: 36 ≈ 3 years; weekly: 156; daily: 756).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import duckdb


@dataclass(frozen=True)
class ZPoint:
    ts: date
    indicator: float        # the displayed series value (raw or YoY%)
    z: float | None         # rolling z-score; None where window is incomplete


def level_series(
    conn: duckdb.DuckDBPyConnection,
    metric_id: str,
    window: int,
) -> list[ZPoint]:
    """Z-score the raw observation values over a rolling window."""
    sql = f"""
    WITH obs AS (
        SELECT ts, value FROM observations WHERE metric_id = ? ORDER BY ts
    ),
    z AS (
        SELECT
            ts,
            value,
            AVG(value)    OVER w AS m,
            STDDEV(value) OVER w AS s
        FROM obs
        WINDOW w AS (ORDER BY ts ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW)
    )
    SELECT ts, value,
           CASE WHEN s IS NULL OR s = 0 THEN NULL ELSE (value - m) / s END AS z
    FROM z
    ORDER BY ts
    """
    rows = conn.execute(sql, [metric_id]).fetchall()
    return [ZPoint(ts=r[0], indicator=r[1], z=r[2]) for r in rows]


def yoy_series(
    conn: duckdb.DuckDBPyConnection,
    metric_id: str,
    lag: int,
    window: int,
) -> list[ZPoint]:
    """Compute YoY %% change (current / lag periods ago - 1) and z-score that series."""
    sql = f"""
    WITH obs AS (
        SELECT ts, value FROM observations WHERE metric_id = ? ORDER BY ts
    ),
    yoy AS (
        SELECT
            ts,
            value,
            LAG(value, {lag}) OVER (ORDER BY ts) AS prior,
            (value / NULLIF(LAG(value, {lag}) OVER (ORDER BY ts), 0) - 1) * 100 AS yoy_pct
        FROM obs
    ),
    z AS (
        SELECT
            ts,
            yoy_pct,
            AVG(yoy_pct)    OVER w AS m,
            STDDEV(yoy_pct) OVER w AS s
        FROM yoy
        WHERE prior IS NOT NULL
        WINDOW w AS (ORDER BY ts ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW)
    )
    SELECT ts, yoy_pct,
           CASE WHEN s IS NULL OR s = 0 THEN NULL ELSE (yoy_pct - m) / s END AS z
    FROM z
    ORDER BY ts
    """
    rows = conn.execute(sql, [metric_id]).fetchall()
    return [ZPoint(ts=r[0], indicator=r[1], z=r[2]) for r in rows if r[1] is not None]


def latest_with_z(points: list[ZPoint]) -> ZPoint | None:
    """Return the most recent point that has a defined z-score."""
    for p in reversed(points):
        if p.z is not None:
            return p
    return None
