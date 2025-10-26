"""Command line interface for ez-balance."""

from __future__ import annotations

import argparse
from contextlib import closing
from decimal import Decimal, InvalidOperation
from typing import Dict

from .allocation import compute_rebalance_plan
from .io import load_allocations
from .pricing import PriceFetcher, PricingError


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate the purchases required to rebalance an ETF portfolio.",
    )
    parser.add_argument(
        "allocations_file",
        help="Path to a CSV file containing at least 'isin' and 'target_percent' columns.",
    )
    return parser.parse_args(argv)


def prompt_decimal(prompt: str) -> Decimal:
    while True:
        raw = input(prompt).strip()
        try:
            value = Decimal(raw)
        except (InvalidOperation, ValueError):
            print("Please enter a valid number (e.g. 1234.56).")
            continue
        if value < 0:
            print("Value cannot be negative when only purchases are allowed.")
            continue
        return value


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    targets = load_allocations(args.allocations_file)

    quotes: Dict[str, Decimal] = {}
    symbols: Dict[str, str] = {}
    names: Dict[str, str | None] = {}

    with closing(PriceFetcher()) as fetcher:
        for target in targets:
            try:
                quote = fetcher.fetch_quote(target.isin, symbol=target.symbol)
            except PricingError as exc:
                print(f"Failed to fetch data for {target.isin}: {exc}")
                return 1
            quotes[target.isin] = quote.price_in_eur
            symbols[target.isin] = quote.symbol
            names[target.isin] = quote.name

    current_values: Dict[str, Decimal] = {}
    print("Enter the current euro value for each holding. If you do not hold the instrument, enter 0.")
    for target in targets:
        label = symbols.get(target.isin) or target.isin
        if names.get(target.isin):
            label = f"{label} ({names[target.isin]})"
        current_values[target.isin] = prompt_decimal(f"Current value for {label}: ")

    plan = compute_rebalance_plan(targets, current_values, quotes)

    print("\nRebalance summary (values in EUR):")
    header = f"{'ISIN':<15} {'Symbol':<15} {'Current':>12} {'Target':>12} {'Buy':>12} {'Price EUR':>12} {'Units':>10}"
    print(header)
    print("-" * len(header))

    for target in targets:
        isin = target.isin
        symbol = symbols.get(isin, "-")
        current_value = current_values[isin]
        target_value = plan.totals[isin]
        to_buy = plan.purchases[isin]
        price = quotes[isin]
        units = plan.units_to_buy[isin]
        print(
            f"{isin:<15} {symbol:<15} "
            f"{current_value:>12.2f} {target_value:>12.2f} {to_buy:>12.2f} {price:>12.4f} {units:>10.4f}"
        )

    print("-" * len(header))
    print(f"Additional cash required: EUR {plan.additional_cash_needed:.2f}")
    print(f"Final portfolio value:   EUR {plan.final_portfolio_value:.2f}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
