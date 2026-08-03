"""Pydantic response schemas — these are the wire contract with the SvelteKit frontend."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class VoteOut(BaseModel):
    direction: str
    reason: str


class ReadingOut(BaseModel):
    metric_id: str
    name: str
    tier: int
    source: str
    unit: str
    value: str
    delta: str
    delta_class: str
    z: float
    z_label: str
    z_class: str
    as_of: date
    sparkline: list[float]
    vote: VoteOut
    include_in_composite: bool = True
    description: str | None = None


class TierOut(BaseModel):
    tier: int
    name: str
    tag: str
    cadence: str
    metrics: list[ReadingOut]
    avg_z: float | None = None


class TallyOut(BaseModel):
    bull: int
    neutral: int
    bear: int


class CompositeOut(BaseModel):
    z: float
    z_label: str
    sign_class: str
    tally: TallyOut
    metrics_total: int


class CompositeHistoryPoint(BaseModel):
    ts: date
    z: float
    spy_close: float | None = None
    # Per-tier averages that produced this composite z. JSON object keys must be
    # strings, so tiers are keyed by "1".."4"; the frontend re-maps to ints.
    tier_zs: dict[str, float] = {}


class TierHistoryPoint(BaseModel):
    ts: date
    z: float


class TierHistoryOut(BaseModel):
    tier: int
    name: str
    tag: str
    points: list[TierHistoryPoint]
    latest_z: float | None


class DashboardOut(BaseModel):
    composite: CompositeOut | None
    tiers: list[TierOut]
    composite_history: list[CompositeHistoryPoint] = []


class HistoryPoint(BaseModel):
    ts: date
    value: float


class HistoryOut(BaseModel):
    metric_id: str
    points: list[HistoryPoint]


class DetailPoint(BaseModel):
    ts: date
    indicator: float
    z: float | None


class MetricDetailOut(BaseModel):
    metric_id: str
    name: str
    tier: int
    source: str
    source_kind: str
    source_series: str | None
    unit: str
    cadence: str
    description: str | None
    direction_kind: str
    indicator_kind: str
    indicator_window: int
    indicator_lag: int
    zscore_years: int
    include_in_composite: bool
    reading: ReadingOut | None
    series: list[DetailPoint]
    obs_count: int
