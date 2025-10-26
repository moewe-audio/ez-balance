"""Core portfolio allocation calculations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, List, Mapping


@dataclass(frozen=True)
class AllocationTarget:
    """Desired allocation for a single instrument."""

    isin: str
    target_weight: Decimal
    symbol: str | None = None
    name: str | None = None


@dataclass
class AllocationPlan:
    """Result of a rebalance calculation."""

    totals: Mapping[str, Decimal]
    purchases: Mapping[str, Decimal]
    units_to_buy: Mapping[str, Decimal]
    additional_cash_needed: Decimal
    final_portfolio_value: Decimal


def normalise_weights(targets: Iterable[AllocationTarget]) -> List[AllocationTarget]:
    """Normalise the target weights so they sum to one."""

    targets = list(targets)
    total = sum((t.target_weight for t in targets), Decimal("0"))
    if total <= Decimal("0"):
        raise ValueError("Total target weight must be greater than zero")

    return [
        AllocationTarget(
            isin=t.isin,
            target_weight=(t.target_weight / total),
            symbol=t.symbol,
            name=t.name,
        )
        for t in targets
    ]


def compute_rebalance_plan(
    targets: Iterable[AllocationTarget],
    current_values: Mapping[str, Decimal],
    prices: Mapping[str, Decimal],
) -> AllocationPlan:
    """Compute the purchases required to reach the allocation without selling."""

    targets = normalise_weights(targets)
    current_values = {k: Decimal(v) for k, v in current_values.items()}
    prices = {k: Decimal(v) for k, v in prices.items()}

    missing = {t.isin for t in targets} - current_values.keys()
    if missing:
        raise KeyError(f"Missing current value for: {', '.join(sorted(missing))}")

    price_missing = {t.isin for t in targets} - prices.keys()
    if price_missing:
        raise KeyError(f"Missing price data for: {', '.join(sorted(price_missing))}")

    total_current = sum(current_values.values(), Decimal("0"))

    required_total = total_current
    for target in targets:
        if target.target_weight == 0:
            if current_values[target.isin] > 0:
                raise ValueError(
                    "Cannot reach a zero allocation target without selling holdings"
                )
            else:
                continue
        required_total = max(
            required_total,
            (current_values[target.isin] / target.target_weight).quantize(
                Decimal("0.0000000001"), rounding=ROUND_HALF_UP
            ),
        )

    additional_cash = required_total - total_current

    purchases: Dict[str, Decimal] = {}
    units: Dict[str, Decimal] = {}
    totals: Dict[str, Decimal] = {}

    for target in targets:
        target_value = (target.target_weight * required_total).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        current_value = current_values[target.isin]
        to_buy = max(target_value - current_value, Decimal("0"))
        price = prices[target.isin]
        units_to_buy = (to_buy / price) if price > 0 else Decimal("0")
        purchases[target.isin] = to_buy
        units[target.isin] = units_to_buy.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        totals[target.isin] = current_value + to_buy

    return AllocationPlan(
        totals=totals,
        purchases=purchases,
        units_to_buy=units,
        additional_cash_needed=additional_cash.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ),
        final_portfolio_value=required_total.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ),
    )
