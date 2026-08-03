"""Composite history — historical (date, composite_z) series.

For each registered metric, computes the (date, directional_z) series via
yoy_series / level_series + the metric's direction_kind. Then for each business
day in the requested window, forward-fills the latest available directional_z
per metric, groups by tier, averages per tier, then averages the four tier
averages into the composite z.

Stored in observations under series_id `_composite_z`, with per-tier averages
persisted alongside as `_tier_z_1`, `_tier_z_2`, `_tier_z_3`, `_tier_z_4` so the
tier subpages can chart their own regime history and the hero can display a
per-tier decomposition of the current composite.
"""
from __future__ import annotations

import bisect
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean

import duckdb

from tide.compute.zscore import level_series, yoy_series
from tide.metrics import all_metrics
from tide.metrics.base import MetricDefinition, directional_from_z


@dataclass(frozen=True)
class HistoryPoint:
    """One business day of composite computation: date, composite z, per-tier averages."""
    ts: date
    composite_z: float
    tier_zs: dict[int, float]


def _historical_directional_z(
    conn: duckdb.DuckDBPyConnection,
    m: MetricDefinition,
) -> list[tuple[date, float]]:
    """Return the full (ts, directional_z) history for one metric using its registry config."""
    if m.indicator_kind == "yoy":
        points = yoy_series(conn, m.id, m.indicator_lag, m.indicator_window)
    else:
        points = level_series(conn, m.id, m.indicator_window)
    return [
        (p.ts, directional_from_z(p.z, m.direction_kind))
        for p in points
        if p.z is not None
    ]


def composite_history(
    conn: duckdb.DuckDBPyConnection,
    days_back: int = 252,
) -> list[HistoryPoint]:
    """Compute (date, composite_z, per-tier averages) for each weekday in the last `days_back` days.

    Forward-fills each metric's last known directional_z so missing days (weekends,
    holidays, publication lag) inherit the prior reading. Returns only dates where
    at least one tier has at least one metric reading.
    """
    # Skip loadedness metrics (include_in_composite=False) — they belong on tier cards
    # but not in the directional composite history.
    metrics = [
        m for m in all_metrics()
        if m.compute_fn is not None and m.include_in_composite
    ]

    # Pull each metric's full directional-z history once.
    per_metric: dict[str, list[tuple[date, float]]] = {}
    metric_tier: dict[str, int] = {}
    for m in metrics:
        series = _historical_directional_z(conn, m)
        if series:
            per_metric[m.id] = series
            metric_tier[m.id] = m.tier

    if not per_metric:
        return []

    sorted_dates: dict[str, list[date]] = {
        mid: [s[0] for s in series] for mid, series in per_metric.items()
    }
    latest_date = max(s[-1][0] for s in per_metric.values())
    start_date = latest_date - timedelta(days=int(days_back * 1.5))

    out: list[HistoryPoint] = []
    cursor = start_date
    while cursor <= latest_date:
        if cursor.weekday() >= 5:
            cursor += timedelta(days=1)
            continue

        by_tier: dict[int, list[float]] = {}
        for mid, series in per_metric.items():
            dates = sorted_dates[mid]
            idx = bisect.bisect_right(dates, cursor)
            if idx == 0:
                continue
            _, dz = series[idx - 1]
            by_tier.setdefault(metric_tier[mid], []).append(dz)

        if by_tier:
            tier_zs = {tier: mean(vs) for tier, vs in by_tier.items()}
            composite_z = mean(tier_zs.values())
            out.append(HistoryPoint(ts=cursor, composite_z=composite_z, tier_zs=tier_zs))

        cursor += timedelta(days=1)

    return out


def write_composite_history(conn: duckdb.DuckDBPyConnection, days_back: int = 252) -> int:
    """Compute composite history and persist derived series in observations.

    Persists:
      - `_composite_z`  : the composite z per business day
      - `_tier_z_1..4`  : per-tier averages per business day
      - `_spy_close`    : SPY reference series for chart overlay (best-effort)

    Returns the number of composite points written.
    """
    series = composite_history(conn, days_back=days_back)
    if not series:
        return 0

    # Replace the entire derived-series set each run — these are computed views.
    conn.execute("DELETE FROM observations WHERE metric_id = '_composite_z'")
    conn.executemany(
        "INSERT INTO observations (metric_id, ts, value) VALUES ('_composite_z', ?, ?)",
        [(p.ts, p.composite_z) for p in series],
    )

    for tier in (1, 2, 3, 4):
        conn.execute(f"DELETE FROM observations WHERE metric_id = '_tier_z_{tier}'")
        rows = [(p.ts, p.tier_zs[tier]) for p in series if tier in p.tier_zs]
        if rows:
            conn.executemany(
                f"INSERT INTO observations (metric_id, ts, value) VALUES ('_tier_z_{tier}', ?, ?)",
                rows,
            )

    _refresh_spy_reference(conn)
    return len(series)


def _refresh_spy_reference(conn: duckdb.DuckDBPyConnection) -> int:
    """Store SPY closes as observations under `_spy_close` for the composite chart overlay."""
    from tide.ingest.sources.yahoo import fetch_close_series
    try:
        closes = fetch_close_series("SPY", start="2020-01-01")
    except Exception:  # noqa: BLE001
        # Don't fail the whole backfill for a missing overlay. logging module isn't
        # configured in the CLI path; the API layer will show a chart without SPY.
        return 0
    if not closes:
        return 0
    conn.execute("DELETE FROM observations WHERE metric_id = '_spy_close'")
    conn.executemany(
        "INSERT INTO observations (metric_id, ts, value) VALUES ('_spy_close', ?, ?)",
        closes,
    )
    return len(closes)
