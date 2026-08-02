from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Literal, Optional

import duckdb

VoteDirection = Literal["bull", "bear", "neutral"]
SignClass = Literal["pos", "neg", "neu"]
IndicatorKind = Literal["level", "yoy"]
DirectionKind = Literal["natural", "inverted", "contrarian_long"]


@dataclass(frozen=True)
class Vote:
    direction: VoteDirection
    reason: str


@dataclass(frozen=True)
class Reading:
    """Computed reading for a single metric — exactly what the dashboard renders.

    `z` is the raw z-score for display (its sign reflects the metric's natural direction).
    `directional_z` is bull-positive: negative when the metric is signalling bear regardless
    of the metric's own sign convention. The composite averages directional_z, not z, so
    inverted-convention metrics (HY spread tight = bull, VIX low = bull, COT extreme = bear)
    contribute correctly.
    """
    metric_id: str
    name: str
    tier: int
    source: str
    unit: str
    value: str               # formatted display value, e.g. "+4.2%"
    delta: str               # e.g. "+0.8pp 13W"
    delta_class: SignClass
    z: float                 # raw, signed by the metric's natural direction
    z_label: str             # "+0.6σ"
    z_class: SignClass       # color class — metric-aware (pos = bullish for THIS metric)
    directional_z: float     # bull-positive — used by composite
    as_of: date
    sparkline: list[float]
    vote: Vote


IngestFn = Callable[[], list[tuple[date, float]]]
ComputeFn = Callable[[duckdb.DuckDBPyConnection], Optional[Reading]]


@dataclass
class MetricDefinition:
    id: str
    name: str
    tier: int
    source: str                   # display string e.g. "FRED · M2SL"
    source_kind: str              # 'fred', 'yahoo', 'cftc', 'aaii', 'treasury_tic', 'squeezemetrics', 'derived'
    source_series: Optional[str]  # upstream series identifier
    unit: str
    cadence: str                  # 'monthly', 'weekly', 'daily'
    zscore_years: int = 3
    sort_order: int = 0
    ingest_fn: Optional[IngestFn] = None
    compute_fn: Optional[ComputeFn] = None

    # Metadata used by composite_history to compute directional z per date without
    # re-running compute_fn for every historical date. compute_fn is unchanged.
    indicator_kind: IndicatorKind = "level"
    indicator_lag: int = 12          # only consulted for indicator_kind == "yoy"
    indicator_window: int = 36
    direction_kind: DirectionKind = "natural"

    # Whether this metric contributes to the directional composite. Loadedness /
    # fragility gauges (systematic_leverage etc.) render as tier cards but must NOT
    # pollute the bull/bear composite — encoding "loaded spring" on a directional
    # axis would be a category error. Tier cards and tally still show these readings.
    include_in_composite: bool = True


def directional_from_z(z: float, kind: DirectionKind) -> float:
    """Map a raw z-score to a bull-positive directional z, per metric convention."""
    if kind == "natural":
        return z
    if kind == "inverted":
        return -z
    if kind == "contrarian_long":
        # Extreme long (z > +1.5) is contrarian bear; extreme short is contrarian bull.
        # Mid-range gets a mild contrarian bias.
        if abs(z) > 1.5:
            return -z
        return -0.3 * z
    return z
