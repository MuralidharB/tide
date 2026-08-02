"""tide-ingest CLI — runs metric ingest jobs out-of-process from the API."""
from __future__ import annotations

import logging
import signal
import sys
import time

import click

from tide.db import connect, init as db_init
from tide.metrics import all_metrics, get_metric


@click.group()
def main() -> None:
    """TIDE ingestion CLI."""


@main.command("init-db")
def init_db_cmd() -> None:
    """Create the schema and seed the metrics registry."""
    db_init()


@main.command("list")
def list_cmd() -> None:
    """List registered metrics."""
    for m in all_metrics():
        impl = "✓" if m.ingest_fn else "—"
        click.echo(f"  [{impl}] tier {m.tier}  {m.id:24s}  {m.source}")


@main.command("backfill-composite")
@click.option("--days", default=252, help="Trading-day lookback for the composite history.")
def backfill_composite_cmd(days: int) -> None:
    """Recompute the composite history series and store it under '_composite_z'."""
    from tide.compute.history import write_composite_history

    with connect() as conn:
        n = write_composite_history(conn, days_back=days)
    click.echo(f"  [ok] composite history: {n} business-day points written")


@main.command("watchlist")
def watchlist_cmd() -> None:
    """Pull daily closes for every watchlist ticker + the benchmark (XLV)."""
    from tide.ingest.sources.yahoo import fetch_close_series
    from tide.watchlist import all_symbols_to_ingest

    with connect() as conn:
        for symbol in all_symbols_to_ingest():
            click.echo(f"  [pull] wl_{symbol} ← Yahoo · {symbol}")
            try:
                rows = fetch_close_series(symbol, start="2023-01-01")
            except Exception as exc:  # noqa: BLE001
                click.echo(f"  [fail] wl_{symbol}: {exc}", err=True)
                continue
            if not rows:
                click.echo(f"  [warn] wl_{symbol}: no rows returned")
                continue
            conn.executemany(
                "INSERT OR REPLACE INTO observations (metric_id, ts, value) VALUES (?, ?, ?)",
                [(f"wl_{symbol}", ts, val) for ts, val in rows],
            )
            click.echo(f"  [ok]   wl_{symbol}: {len(rows)} obs ({rows[0][0]} → {rows[-1][0]})")


@main.command("run")
@click.option("--metric", "metric_ids", multiple=True, help="Metric id(s) to ingest. Repeatable.")
@click.option("--all", "run_all", is_flag=True, help="Ingest every metric with an ingest_fn.")
def run_cmd(metric_ids: tuple[str, ...], run_all: bool) -> None:
    """Pull observations from upstream sources into DuckDB."""
    if run_all:
        targets = [m for m in all_metrics() if m.ingest_fn is not None]
    else:
        if not metric_ids:
            click.echo("Provide --metric ID or --all", err=True)
            sys.exit(2)
        targets = [get_metric(mid) for mid in metric_ids]

    with connect() as conn:
        for m in targets:
            if m.ingest_fn is None:
                click.echo(f"  [skip] {m.id} — no ingest_fn registered")
                continue
            click.echo(f"  [pull] {m.id} ← {m.source}")
            try:
                rows = m.ingest_fn()
            except Exception as exc:  # noqa: BLE001
                click.echo(f"  [fail] {m.id}: {exc}", err=True)
                continue
            if not rows:
                click.echo(f"  [warn] {m.id}: ingest_fn returned no rows")
                continue
            conn.executemany(
                "INSERT OR REPLACE INTO observations (metric_id, ts, value) VALUES (?, ?, ?)",
                [(m.id, ts, val) for ts, val in rows],
            )
            click.echo(f"  [ok]   {m.id}: {len(rows)} obs ({rows[0][0]} → {rows[-1][0]})")


@main.command("scheduler")
@click.option(
    "--fire-once",
    is_flag=True,
    help="Run each scheduled job body once, sequentially, then exit. For smoke tests.",
)
def scheduler_cmd(fire_once: bool) -> None:
    """Start the long-running APScheduler service (cadence-grouped cron jobs).

    Runs until SIGINT / SIGTERM. Job status persists to the scheduler_status table
    so the Sources page can display next-run / last-success / last-error without
    an IPC channel to this process.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
    )
    from tide.scheduler import JOBS, fire_once as _fire_once, start_scheduler

    if fire_once:
        click.echo("  [scheduler] --fire-once: running each job body sequentially")
        _fire_once()
        click.echo("  [scheduler] --fire-once: done")
        return

    sched = start_scheduler()
    sched.start()
    click.echo("  [scheduler] started")
    for job in JOBS:
        click.echo(f"  [scheduler] {job['id']:20s} {job['schedule_repr']}")

    stop = {"flag": False}

    def _handle_signal(signum, frame):  # noqa: ANN001
        click.echo(f"\n  [scheduler] received signal {signum}, shutting down…")
        stop["flag"] = True

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    while not stop["flag"]:
        time.sleep(1)

    sched.shutdown(wait=True)
    click.echo("  [scheduler] stopped")


if __name__ == "__main__":
    main()
