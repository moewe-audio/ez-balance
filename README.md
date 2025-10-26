# ez-balance

`ez-balance` is a minimal Python command line tool that helps you rebalance an ETF portfolio
without selling existing holdings. It reads desired asset allocations from a CSV file, asks for
current holding values interactively, fetches latest market prices from Yahoo Finance, and
calculates how many euros (and units) of each ETF you need to buy to reach the desired mix.

## Features

- Load allocation targets from a CSV file containing ISINs, target percentages, and optional
  ticker symbols and names.
- Automatically resolve ISINs to tradeable symbols using Yahoo Finance search when symbols are not
  provided.
- Retrieve latest market prices and convert them to euro amounts using free public endpoints.
- Compute the minimum top-up that reaches the target allocation using purchases only (no selling).
- Display a concise summary of the purchases required to meet your target allocation.

## Installation

Create a virtual environment and install the project in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

Prepare a CSV file with at least two columns: `isin` and `target_percent`. Optional `symbol` and
`name` columns help speed up lookups and make the summary easier to read. See
[`examples/sample_allocations.csv`](examples/sample_allocations.csv) for a template.

Run the tool with the CSV file as its only argument:

```bash
python -m ez_balance examples/sample_allocations.csv
```

You will be prompted for the current euro value of each holding. Enter `0` for holdings that you do
not currently own. The tool will print a summary table showing the current value, target value,
required purchase (in EUR), the price used (converted to EUR), and the resulting units to buy.

> **Note:** The tool relies on public web APIs and therefore requires network access. Pricing data
> is provided on a best-effort basis and may not exactly match broker prices.

## Development

Install development dependencies and run the unit tests:

```bash
pip install -e .[dev]
pytest
```

The project contains a single unit test covering the purchase calculation logic. More tests and
improvements to the CLI UX, price caching, and output formatting can be added in future iterations.
