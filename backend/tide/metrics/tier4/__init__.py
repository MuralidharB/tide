"""Tier IV — Sentiment & Positioning. Willingness to transact · days–weeks.

Implemented in Wave 2:
  - vix_term   — Cboe via Yahoo chart API ^VIX/^VIX3M
  - dix        — SqueezeMetrics CSV

Implemented in Wave 4:
  - aaii       — AAII Bull/Bear spread (binary xls + xlrd, browser headers required)
  - cot_sp     — CFTC TFF weekly E-MINI S&P 500 leveraged-money net % of OI

Stubbed (registered with metadata, no ingest_fn yet):
  - put_call   — Cboe CDN endpoints return 403 to anonymous clients; Yahoo's ^CPC
                 returns no data. Would need browser-shaped scraping of the user-facing
                 https://www.cboe.com/us/options/market_statistics/ page.
"""
from tide.metrics.tier4 import aaii, cot_sp, dix, vix_term  # noqa: F401
