"""Automated refresh scheduler for TIDE.

Runs as a long-running process (`tide-ingest scheduler`) separate from the FastAPI
server — the two-process architecture keeps a wedged scrape from taking the
dashboard down. Jobs are grouped by metric cadence:

    daily_ingest    17:00 America/New_York Mon–Fri
        - every metric with cadence="daily"
        - watchlist tickers + XLV benchmark
        - backfill-composite at the end

    release_ingest  18:00 America/New_York Fri
        - every metric with cadence != "daily"
          (weekly / monthly / quarterly all polled weekly — cheap, catches new
          FRED / FINRA / Treasury / CFTC releases within a week)
        - backfill-composite at the end

Job status is persisted to the scheduler_status table so the Sources page can
show next-run / last-success / last-error without an IPC channel to this process.
"""
from __future__ import annotations

import logging
import traceback
from datetime import datetime
from typing import Optional

import duckdb
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from tide.db import connect
from tide.metrics import all_metrics

log = logging.getLogger(__name__)

TZ = "America/New_York"

# One entry per scheduled APScheduler job. Trigger + target function are wired in
# start_scheduler(); this list is separate so the Sources page can enumerate the
# static schedule metadata (labels, descriptions) without importing APScheduler.
JOBS = [
    {
        "id": "daily_ingest",
        "label": "Daily ingest",
        "description": "Pull every daily-cadence metric + watchlist, then backfill composite.",
        "trigger": CronTrigger(day_of_week="mon-fri", hour=17, minute=0, timezone=TZ),
        "schedule_repr": "Mon–Fri 17:00 America/New_York",
    },
    {
        "id": "release_ingest",
        "label": "Release ingest",
        "description": "Pull weekly / monthly / quarterly metrics, then backfill composite.",
        "trigger": CronTrigger(day_of_week="fri", hour=18, minute=0, timezone=TZ),
        "schedule_repr": "Fri 18:00 America/New_York",
    },
]


def _record(
    conn: duckdb.DuckDBPyConnection,
    job_id: str,
    *,
    started_at: datetime,
    success: bool,
    err: Optional[str] = None,
    next_run_at: Optional[datetime] = None,
) -> None:
    """Upsert scheduler_status for a job."""
    # DuckDB doesn't have UPSERT-with-partial-update semantics for optional columns,
    # so we hand-roll it: read current row, merge new fields, write back.
    row = conn.execute(
        "SELECT last_success_at, last_error, last_error_at FROM scheduler_status WHERE job_id = ?",
        [job_id],
    ).fetchone()
    prev_success, prev_err, prev_err_at = row if row else (None, None, None)

    last_success_at = started_at if success else prev_success
    last_error = None if success else (err or "")
    last_error_at = None if success else started_at
    # Keep the previous error visible if the last run also failed (informational)
    if not success:
        pass  # last_error / last_error_at already updated

    conn.execute(
        """
        INSERT INTO scheduler_status
            (job_id, last_run_at, last_success_at, last_error, last_error_at, next_run_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (job_id) DO UPDATE SET
            last_run_at = excluded.last_run_at,
            last_success_at = excluded.last_success_at,
            last_error = excluded.last_error,
            last_error_at = excluded.last_error_at,
            next_run_at = excluded.next_run_at
        """,
        [job_id, started_at, last_success_at, last_error, last_error_at, next_run_at],
    )


def _run_metric_ingest(conn: duckdb.DuckDBPyConnection, cadence_filter: set[str]) -> tuple[int, int]:
    """Pull every registered metric whose cadence is in `cadence_filter`.

    Returns (n_success, n_failure). Failures are logged but don't stop the batch —
    one broken upstream shouldn't hold up the rest.
    """
    n_ok = 0
    n_fail = 0
    for m in all_metrics():
        if m.ingest_fn is None or m.cadence not in cadence_filter:
            continue
        try:
            rows = m.ingest_fn()
            if not rows:
                log.warning("[scheduler] %s ingest returned no rows", m.id)
                n_fail += 1
                continue
            conn.executemany(
                "INSERT OR REPLACE INTO observations (metric_id, ts, value) VALUES (?, ?, ?)",
                [(m.id, ts, val) for ts, val in rows],
            )
            log.info("[scheduler] %s: %d obs (%s → %s)", m.id, len(rows), rows[0][0], rows[-1][0])
            n_ok += 1
        except Exception as exc:  # noqa: BLE001
            log.exception("[scheduler] %s ingest failed: %s", m.id, exc)
            n_fail += 1
    return n_ok, n_fail


def _run_watchlist(conn: duckdb.DuckDBPyConnection) -> tuple[int, int]:
    from tide.ingest.sources.yahoo import fetch_close_series
    from tide.watchlist import all_symbols_to_ingest

    n_ok = 0
    n_fail = 0
    for symbol in all_symbols_to_ingest():
        try:
            rows = fetch_close_series(symbol, start="2023-01-01")
            if not rows:
                log.warning("[scheduler] wl_%s returned no rows", symbol)
                n_fail += 1
                continue
            conn.executemany(
                "INSERT OR REPLACE INTO observations (metric_id, ts, value) VALUES (?, ?, ?)",
                [(f"wl_{symbol}", ts, val) for ts, val in rows],
            )
            log.info("[scheduler] wl_%s: %d obs", symbol, len(rows))
            n_ok += 1
        except Exception as exc:  # noqa: BLE001
            log.exception("[scheduler] wl_%s failed: %s", symbol, exc)
            n_fail += 1
    return n_ok, n_fail


def _do_backfill(conn: duckdb.DuckDBPyConnection) -> int:
    from tide.compute.history import write_composite_history
    return write_composite_history(conn)


def _next_run_for(job_id: str, scheduler: Optional[BackgroundScheduler]) -> Optional[datetime]:
    if scheduler is None:
        return None
    job = scheduler.get_job(job_id)
    return job.next_run_time if job else None


def daily_ingest(scheduler: Optional[BackgroundScheduler] = None) -> None:
    """Pull daily metrics + watchlist, then backfill composite."""
    started = datetime.utcnow()
    try:
        with connect() as conn:
            m_ok, m_fail = _run_metric_ingest(conn, {"daily"})
            w_ok, w_fail = _run_watchlist(conn)
            n_composite = _do_backfill(conn)
            _record(
                conn, "daily_ingest",
                started_at=started, success=True,
                next_run_at=_next_run_for("daily_ingest", scheduler),
            )
        log.info(
            "[scheduler] daily_ingest done — metrics %d ok / %d fail, watchlist %d ok / %d fail, composite %d pts",
            m_ok, m_fail, w_ok, w_fail, n_composite,
        )
    except Exception as exc:  # noqa: BLE001
        log.exception("[scheduler] daily_ingest failed")
        with connect() as conn:
            _record(
                conn, "daily_ingest",
                started_at=started, success=False,
                err=f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[:1000]}",
                next_run_at=_next_run_for("daily_ingest", scheduler),
            )


def release_ingest(scheduler: Optional[BackgroundScheduler] = None) -> None:
    """Pull weekly + monthly + quarterly metrics, then backfill composite."""
    started = datetime.utcnow()
    try:
        with connect() as conn:
            m_ok, m_fail = _run_metric_ingest(conn, {"weekly", "monthly", "quarterly"})
            n_composite = _do_backfill(conn)
            _record(
                conn, "release_ingest",
                started_at=started, success=True,
                next_run_at=_next_run_for("release_ingest", scheduler),
            )
        log.info(
            "[scheduler] release_ingest done — metrics %d ok / %d fail, composite %d pts",
            m_ok, m_fail, n_composite,
        )
    except Exception as exc:  # noqa: BLE001
        log.exception("[scheduler] release_ingest failed")
        with connect() as conn:
            _record(
                conn, "release_ingest",
                started_at=started, success=False,
                err=f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[:1000]}",
                next_run_at=_next_run_for("release_ingest", scheduler),
            )


JOB_FUNCS = {
    "daily_ingest": daily_ingest,
    "release_ingest": release_ingest,
}


def start_scheduler() -> BackgroundScheduler:
    """Configure APScheduler with the tide jobs. Caller is responsible for start()."""
    sched = BackgroundScheduler(timezone=TZ)
    for job in JOBS:
        fn = JOB_FUNCS[job["id"]]
        sched.add_job(
            fn,
            trigger=job["trigger"],
            id=job["id"],
            name=job["label"],
            kwargs={"scheduler": sched},
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )
    return sched


def fire_once() -> None:
    """Run every job body exactly once, sequentially. Used for smoke tests."""
    for job in JOBS:
        JOB_FUNCS[job["id"]](scheduler=None)
