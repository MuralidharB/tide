"""Composite scoring.

Equal-weight average of *tier* averages: each tier's metric z-scores average together first,
then the four tier averages average into the composite. This way the four tiers count equally
regardless of how many metrics each has.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from tide.metrics.base import Reading


@dataclass(frozen=True)
class TierTally:
    bull: int
    neutral: int
    bear: int


@dataclass(frozen=True)
class Composite:
    z: float
    z_label: str            # "+0.74σ"
    sign_class: str         # "pos" / "neg" / "neu"
    tier_zs: dict[int, float]
    tally: TierTally
    metrics_total: int


def composite_from_readings(readings: list[Reading]) -> Composite | None:
    if not readings:
        return None

    # Use directional_z so inverted-convention metrics (HY spread, VIX, COT)
    # contribute with the correct sign.
    by_tier: dict[int, list[float]] = {}
    for r in readings:
        by_tier.setdefault(r.tier, []).append(r.directional_z)

    tier_zs = {tier: mean(zs) for tier, zs in by_tier.items()}
    z = mean(tier_zs.values())

    bull = sum(1 for r in readings if r.vote.direction == "bull")
    bear = sum(1 for r in readings if r.vote.direction == "bear")
    neutral = sum(1 for r in readings if r.vote.direction == "neutral")

    sign_class = "pos" if z > 0.3 else ("neg" if z < -0.3 else "neu")

    return Composite(
        z=z,
        z_label=f"{z:+.2f}σ",
        sign_class=sign_class,
        tier_zs=tier_zs,
        tally=TierTally(bull=bull, neutral=neutral, bear=bear),
        metrics_total=len(readings),
    )
