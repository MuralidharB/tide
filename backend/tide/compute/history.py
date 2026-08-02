"""Composite history — historical (date, composite_z) series.

For each registered metric, computes the (date, directional_z) series via
yoy_series / level_series + the metric's direction_kind. Then for each business
day in the requested window, forward-fills the latest available directional_z
per metric, groups by tier, averages per tier, then averages the four tier
averages into the composite z.

Stored in observations under series_id `_composite_z`.
"""
from __future__ import annotations

import bisect
from datetime import date, timedelta
from statistics import mean

import duckdb

from tide.compute.zscore import level_series, yoy_series
from tide.metrics import all_metrics
from tide.metrics.base import MetricDefinition, directional_from_z


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
) -> list[tuple[date, float]]:
    """Compute (date, composite_z) for each weekday in the last `days_back` days.

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

    # For binary search, we need each metric's date list.
    sorted_dates: dict[str, list[date]] = {
        mid: [s[0] for s in series] for mid, series in per_metric.items()
    }

    # Determine the date range. End at the latest reading we have; start days_back
    # business days before that (approximated by 1.5 * days_back calendar days).
    latest_date = max(s[-1][0] for s in per_metric.values())
    start_date = latest_date - timedelta(days=int(days_back * 1.5))

    out: list[tuple[date, float]] = []
    cursor = start_date
    while cursor <= latest_date:
        if cursor.weekday() >= 5:
            cursor += timedelta(days=1)
            continue

        by_tier: dict[int, list[float]] = {}
        for mid, series in per_metric.items():
            dates = sorted_dates[mid]
            # bisect_right gives the insertion index — the last value with ts <= cursor
            # is at index (idx - 1).
            idx = bisect.bisect_right(dates, cursor)
            if idx == 0:
                continue  # no reading yet for this metric at cursor
            _, dz = series[idx - 1]
            by_tier.setdefault(metric_tier[mid], []).append(dz)

        if by_tier:
            tier_avgs = [mean(vs) for vs in by_tier.values()]
            out.append((cursor, mean(tier_avgs)))

        cursor += timedelta(days=1)

    return out


def write_composite_history(conn: duckdb.DuckDBPyConnection, days_back: int = 252) -> int:
    """Compute composite history and persist under observation series '_composite_z'."""
    series = composite_history(conn, days_back=days_back)
    if not series:
        return 0
    # Replace the entire stored series each run — it's a derived view, not raw data.
    conn.execute("DELETE FROM observations WHERE metric_id = '_composite_z'")
    conn.executemany(
        "INSERT INTO observations (metric_id, ts, value) VALUES ('_composite_z', ?, ?)",
        series,
    )
    return len(series)
