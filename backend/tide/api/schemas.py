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
