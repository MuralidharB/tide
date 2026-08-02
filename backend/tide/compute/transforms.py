"""Indicator transforms run at ingest time — they consume raw upstream data and
produce the (date, indicator_value) series stored in observations.
"""
from __future__ import annotations

from datetime import date


def amihud_from_ohlcv(
    bars: list[tuple[date, float, float]],
    smoothing: int = 5,
) -> list[tuple[date, float]]:
    """Compute Amihud illiquidity from daily (date, close, volume) bars.

    Amihud_t = |daily_return_pct_t| / dollar_volume_billions_t

    Higher = less liquid (price moves a lot per dollar of flow); lower = more liquid.
    Output is smoothed with a trailing `smoothing`-day arithmetic mean to dampen the
    day-to-day noise that |return| introduces.
    """
    raw: list[tuple[date, float]] = []
    for i in range(1, len(bars)):
        d, close, vol = bars[i]
        _, prev_close, _ = bars[i - 1]
        if prev_close <= 0 or vol <= 0:
            continue
        ret_pct = abs((close / prev_close - 1) * 100)
        dollar_vol_b = close * vol / 1e9
        if dollar_vol_b <= 0:
            continue
        raw.append((d, ret_pct / dollar_vol_b))

    if smoothing <= 1 or len(raw) < smoothing:
        return raw

    out: list[tuple[date, float]] = []
    for i in range(smoothing - 1, len(raw)):
        window = raw[i - smoothing + 1 : i + 1]
        avg = sum(v for _, v in window) / smoothing
        out.append((raw[i][0], avg))
    return out


def rolling_pearson_corr(
    a_returns: list[tuple[date, float]],
    b_returns: list[tuple[date, float]],
    window: int,
) -> list[tuple[date, float]]:
    """Compute rolling Pearson correlation of two return series, aligned by date.

    Both inputs should be (date, return) lists. Output has one observation per common
    date once the window has filled. Returns are typically simple daily returns
    `close_t / close_{t-1} - 1`.
    """
    a = dict(a_returns)
    b = dict(b_returns)
    common = sorted(set(a) & set(b))
    if len(common) < window:
        return []
    out: list[tuple[date, float]] = []
    for i in range(window - 1, len(common)):
        days = common[i - window + 1 : i + 1]
        xs = [a[d] for d in days]
        ys = [b[d] for d in days]
        n = len(xs)
        mx = sum(xs) / n
        my = sum(ys) / n
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        sx = sum((x - mx) ** 2 for x in xs) ** 0.5
        sy = sum((y - my) ** 2 for y in ys) ** 0.5
        if sx == 0 or sy == 0:
            continue
        out.append((common[i], cov / (sx * sy)))
    return out


def daily_returns(closes: list[tuple[date, float]]) -> list[tuple[date, float]]:
    """Simple daily return series. The first observation is dropped (no prior close)."""
    out: list[tuple[date, float]] = []
    for i in range(1, len(closes)):
        d, c = closes[i]
        _, prev = closes[i - 1]
        if prev <= 0:
            continue
        out.append((d, c / prev - 1))
    return out


def realized_vol(
    closes: list[tuple[date, float]],
    window: int = 20,
    annualization: int = 252,
) -> list[tuple[date, float]]:
    """Rolling annualized realized volatility of simple daily returns.

    Standard deviation is taken over `window` daily returns and scaled by
    sqrt(annualization) to express as annualized vol (0.10 = 10% annual).
    Output has one observation per date once the window has filled.
    """
    rets = daily_returns(closes)
    if len(rets) < window:
        return []
    out: list[tuple[date, float]] = []
    scale = annualization ** 0.5
    for i in range(window - 1, len(rets)):
        days = rets[i - window + 1 : i + 1]
        xs = [r for _, r in days]
        n = len(xs)
        m = sum(xs) / n
        var = sum((x - m) ** 2 for x in xs) / (n - 1)
        sd = var ** 0.5
        out.append((rets[i][0], sd * scale))
    return out
