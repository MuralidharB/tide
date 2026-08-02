"""Scheduler status endpoint — one row per configured cron job.

Merges the static JOBS metadata (labels, schedule repr) from tide.scheduler with
per-job runtime state (last_run, last_success, last_error, next_run) read from
the scheduler_status table. If the scheduler process has never run, the state
fields are all null.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from tide.db import connect
from tide.scheduler import JOBS

router = APIRouter()


class SchedulerJob(BaseModel):
    id: str
    label: str
    description: str
    schedule_repr: str
    last_run_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None
    last_error_at: datetime | None
    next_run_at: datetime | None


class SchedulerOut(BaseModel):
    jobs: list[SchedulerJob]


@router.get("/scheduler", response_model=SchedulerOut)
def get_scheduler() -> SchedulerOut:
    status: dict[str, tuple] = {}
    with connect(read_only=True) as conn:
        for row in conn.execute(
            """
            SELECT job_id, last_run_at, last_success_at, last_error, last_error_at, next_run_at
            FROM scheduler_status
            """
        ).fetchall():
            status[row[0]] = row[1:]

    out: list[SchedulerJob] = []
    for job in JOBS:
        s = status.get(job["id"], (None, None, None, None, None))
        out.append(SchedulerJob(
            id=job["id"],
            label=job["label"],
            description=job["description"],
            schedule_repr=job["schedule_repr"],
            last_run_at=s[0],
            last_success_at=s[1],
            last_error=s[2],
            last_error_at=s[3],
            next_run_at=s[4],
        ))
    return SchedulerOut(jobs=out)
