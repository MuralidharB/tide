"""Watchlist — equities being tracked alongside the macro composite.

Configuration lives at `<project_root>/watchlist.toml` so quarterly target/P/E
updates don't require code changes. Live fields (price, returns) are pulled
from Yahoo by `tide-ingest watchlist`. Manual fields (target_price, fwd_pe,
status, name, sector) come from the TOML.

`fwd_pe` stays manual because forward analyst-consensus P/E isn't reachable
on free tiers — Yahoo's quoteSummary endpoint sits behind the crumb-auth
wall that breaks yfinance, and free fundamentals APIs typically don't carry
forward estimates. Refresh quarterly with earnings.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from typing import Literal

from tide.config import PROJECT_ROOT

WatchlistStatus = Literal["watching", "starter", "building"]

CONFIG_PATH = PROJECT_ROOT / "watchlist.toml"


@dataclass(frozen=True)
class WatchlistTicker:
    ticker: str
    name: str
    sub: str                  # short sector descriptor
    target_price: float       # personal target, not analyst consensus
    fwd_pe: str               # display string with × suffix
    status: WatchlistStatus


def _load() -> tuple[tuple[WatchlistTicker, ...], str]:
    with open(CONFIG_PATH, "rb") as f:
        data = tomllib.load(f)
    tickers = tuple(
        WatchlistTicker(
            ticker=t["ticker"],
            name=t["name"],
            sub=t["sector"],
            target_price=float(t["target_price"]),
            fwd_pe=str(t["fwd_pe"]),
            status=t["status"],
        )
        for t in data.get("tickers", [])
    )
    benchmark = str(data.get("benchmark", "XLV"))
    return tickers, benchmark


TICKERS, BENCHMARK = _load()


def all_symbols_to_ingest() -> list[str]:
    return [t.ticker for t in TICKERS] + [BENCHMARK]
