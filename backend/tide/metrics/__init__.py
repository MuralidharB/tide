"""Metric registry.

Each metric module under tide/metrics/tierN/ calls `register()` at import time.
Adding a new metric: drop a module under the right tier and import it from the tier's __init__.py.
"""
from __future__ import annotations

from tide.metrics.base import MetricDefinition

_REGISTRY: dict[str, MetricDefinition] = {}


def register(metric: MetricDefinition) -> None:
    if metric.id in _REGISTRY:
        raise ValueError(f"Duplicate metric id: {metric.id}")
    _REGISTRY[metric.id] = metric


def get_metric(metric_id: str) -> MetricDefinition:
    return _REGISTRY[metric_id]


def all_metrics() -> list[MetricDefinition]:
    return sorted(_REGISTRY.values(), key=lambda m: (m.tier, m.sort_order, m.id))


def metrics_in_tier(tier: int) -> list[MetricDefinition]:
    return [m for m in all_metrics() if m.tier == tier]


# Import tiers so registrations run on package import.
from tide.metrics import tier1, tier2, tier3, tier4  # noqa: E402, F401
