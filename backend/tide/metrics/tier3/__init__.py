"""Tier III — Market Microstructure. Capacity to transact · daily.

Implemented in Wave 3:
  - move             — Yahoo ^MOVE (Treasury vol)
  - amihud_spy       — Amihud illiquidity on SPY (substitute for ES top-of-book depth)
  - amihud_hyg       — Amihud illiquidity on HYG (substitute for HYG bid-ask spread)
  - stock_bond_corr  — 60D rolling Pearson on SPY/TLT daily returns

Stubbed (registered with metadata, no ingest_fn yet):
  - uvol_dvol        — NYSE up-volume / down-volume ratio. Yahoo doesn't carry the
                       direct tickers (^UVOL/^DVOL/^NYAD/^ADVL all return 'no result'),
                       and Cboe's market-statistics page is gated like its put/call
                       endpoints. Two viable paths for Wave 4: scrape Cboe's HTML
                       market_statistics page, or compute from S&P 500 constituents
                       (pull every member's daily volume + classify advancing/declining
                       — heavy but fully under our control).
"""
from tide.metrics.tier3 import amihud_hyg, amihud_spy, move, stock_bond_corr  # noqa: F401

