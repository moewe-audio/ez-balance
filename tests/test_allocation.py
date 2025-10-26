from decimal import Decimal

from ez_balance.allocation import AllocationTarget, compute_rebalance_plan


def test_compute_rebalance_plan_only_purchases():
    targets = [
        AllocationTarget(isin="A", target_weight=Decimal("0.6")),
        AllocationTarget(isin="B", target_weight=Decimal("0.4")),
    ]
    current = {
        "A": Decimal("600"),
        "B": Decimal("200"),
    }
    prices = {
        "A": Decimal("10"),
        "B": Decimal("25"),
    }

    plan = compute_rebalance_plan(targets, current, prices)

    assert plan.final_portfolio_value == Decimal("1000.00")
    assert plan.additional_cash_needed == Decimal("200.00")
    assert plan.purchases["A"] == Decimal("0.00")
    assert plan.purchases["B"] == Decimal("200.00")
    assert plan.units_to_buy["B"] == Decimal("8.0000")
