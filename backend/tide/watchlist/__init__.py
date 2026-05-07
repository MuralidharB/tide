"""Watchlist — equities being tracked alongside the macro composite.

Static metadata (target price, fwd P/E, qualitative status) is hardcoded here. Daily
prices for each ticker + the benchmark (XLV) are stored in observations under
`wl_<ticker>` series ids and refreshed via the `tide-ingest watchlist` CLI subcommand.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WatchlistStatus = Literal["watching", "starter", "building"]


@dataclass(frozen=True)
class WatchlistTicker:
    ticker: str
    name: str
    sub: str                  # short sector descriptor
    target_price: float       # analyst-agnostic personal target
    fwd_pe: str               # display string with × suffix; refresh manually each Q
    status: WatchlistStatus


# Healthcare de-rated quality basket — same 8 names from the mockup.
TICKERS: tuple[WatchlistTicker, ...] = (
    WatchlistTicker("MRK",  "Merck & Co.",     "Pharma",          128.0, "12.4×", "starter"),
    WatchlistTicker("UNH",  "UnitedHealth",    "Managed Care",    420.0, "11.8×", "building"),
    WatchlistTicker("TMO",  "Thermo Fisher",   "Life Sci Tools",  630.0, "21.6×", "watching"),
    WatchlistTicker("DHR",  "Danaher",         "Life Sci Tools",  275.0, "24.2×", "watching"),
    WatchlistTicker("ABBV", "AbbVie",          "Pharma",          215.0, "14.3×", "watching"),
    WatchlistTicker("GILD", "Gilead Sciences", "Pharma",          110.0, "10.7×", "starter"),
    WatchlistTicker("NVO",  "Novo Nordisk",    "Pharma · ADR",     78.0, "17.2×", "watching"),
    WatchlistTicker("MDT",  "Medtronic",       "Med Devices",     105.0, "15.1×", "watching"),
)

BENCHMARK = "XLV"


def all_symbols_to_ingest() -> list[str]:
    return [t.ticker for t in TICKERS] + [BENCHMARK]
