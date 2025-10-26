"""Input helpers."""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
from typing import List

from .allocation import AllocationTarget


def load_allocations(path: str | Path) -> List[AllocationTarget]:
    """Load allocation targets from a CSV file."""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    rows: List[AllocationTarget] = []

    with path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        expected = {"isin", "target_percent"}
        missing = expected - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Allocation file missing required columns: {', '.join(sorted(missing))}"
            )

        for raw in reader:
            isin = raw["isin"].strip()
            if not isin:
                raise ValueError("ISIN cannot be empty")
            try:
                percent = Decimal(raw["target_percent"].strip())
            except Exception as exc:  # pragma: no cover - best effort error message
                raise ValueError(f"Invalid percentage for {isin}: {raw['target_percent']}") from exc

            if percent < 0:
                raise ValueError("Target percentage cannot be negative")

            symbol = raw.get("symbol")
            if symbol:
                symbol = symbol.strip() or None

            name = raw.get("name")
            if name:
                name = name.strip() or None

            rows.append(
                AllocationTarget(
                    isin=isin,
                    target_weight=(percent / Decimal("100")),
                    symbol=symbol,
                    name=name,
                )
            )

    if not rows:
        raise ValueError("No allocations found in file")

    return rows
