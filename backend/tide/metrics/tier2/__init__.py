"""Tier II — Capital Flows. Capital direction · months.

Implemented in Wave 4:
  - margin_debt              — FRED Z.1 BOGZ1FL663067003Q (quarterly substitute for
                               FINRA monthly, which 404'd at the documented URL)
  - foreign_equity_holdings  — Treasury TIC SLT global aggregate, monthly YoY
                               (substitute for TIC monthly net flows, which require
                               scraping Excel attachments)

Stubbed (registered with metadata, no ingest_fn yet):
  - ici_etf_flows  — ICI publishes weekly ETF flow data in PDFs that change format
                     and require manual parsing each release. Workaround proxy is to
                     compute net flows from major-ETF (SPY/QQQ/VTI/IVV) shares-outstanding
                     deltas — but Yahoo's chart API doesn't expose shares outstanding
                     historically. SEC EDGAR N-CSR filings have the right data but
                     parsing varies per fund family. Wave 5+ work.
  - buyback_yield  — S&P DJI publishes the S&P 500 Buyback Index but the actual
                     yield value (TTM buyback dollars / market cap) requires aggregating
                     constituent-level cash flow statements. yfinance Ticker.cashflow
                     would let us do this for each S&P 500 member but the daily-job
                     cost of pulling 500 tickers is meaningful. Defer.
"""
from tide.metrics.tier2 import foreign_equity_holdings, margin_debt  # noqa: F401
