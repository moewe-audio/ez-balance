"""Portfolio rebalancing utilities for ETF allocations."""

from .allocation import AllocationPlan, AllocationTarget, compute_rebalance_plan
from .io import load_allocations

__all__ = [
    "AllocationPlan",
    "AllocationTarget",
    "compute_rebalance_plan",
    "load_allocations",
    "PriceFetcher",
    "PricingError",
]


def __getattr__(name: str):  # pragma: no cover - simple lazy import
    if name in {"PriceFetcher", "PricingError"}:
        from .pricing import PriceFetcher, PricingError

        return {"PriceFetcher": PriceFetcher, "PricingError": PricingError}[name]
    raise AttributeError(f"module 'ez_balance' has no attribute {name!r}")
