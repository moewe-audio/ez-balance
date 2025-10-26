"""Utilities for retrieving ETF prices."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional

import requests


YAHOO_SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"
YAHOO_QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"
FX_URL = "https://api.exchangerate.host/latest"


class PricingError(RuntimeError):
    """Raised when fetching pricing data fails."""


@dataclass(frozen=True)
class PriceQuote:
    isin: str
    symbol: str
    price: Decimal
    currency: str
    price_in_eur: Decimal
    as_of: datetime
    name: str | None = None


class PriceFetcher:
    """Fetch quotes using publicly available Yahoo Finance endpoints."""

    def __init__(self, base_currency: str = "EUR", session: Optional[requests.Session] = None):
        self.base_currency = base_currency
        self.session = session or requests.Session()
        self._symbol_cache: Dict[str, str] = {}
        self._fx_cache: Dict[str, Decimal] = {self.base_currency: Decimal("1")}

    def close(self) -> None:
        self.session.close()

    def lookup_symbol(self, isin: str) -> str:
        if isin in self._symbol_cache:
            return self._symbol_cache[isin]

        response = self.session.get(
            YAHOO_SEARCH_URL,
            params={"q": isin, "quotesCount": 1, "newsCount": 0},
            timeout=10,
        )
        if response.status_code != 200:
            raise PricingError(f"Failed to search symbol for {isin}: {response.status_code}")

        data = response.json()
        for quote in data.get("quotes", []):
            symbol = quote.get("symbol")
            if symbol:
                self._symbol_cache[isin] = symbol
                return symbol

        raise PricingError(f"No matching symbol found for ISIN {isin}")

    def fetch_quote(self, isin: str, symbol: str | None = None) -> PriceQuote:
        symbol = symbol or self.lookup_symbol(isin)

        response = self.session.get(
            YAHOO_QUOTE_URL,
            params={"symbols": symbol},
            timeout=10,
        )
        if response.status_code != 200:
            raise PricingError(
                f"Failed to fetch quote for {symbol}: {response.status_code}"
            )

        payload = response.json()
        results = payload.get("quoteResponse", {}).get("result", [])
        if not results:
            raise PricingError(f"No quote data returned for symbol {symbol}")

        quote = results[0]
        price = quote.get("regularMarketPrice")
        currency = quote.get("currency", self.base_currency)
        name = quote.get("longName") or quote.get("shortName")

        if price is None:
            raise PricingError(f"No market price available for symbol {symbol}")

        price_decimal = Decimal(str(price))
        price_in_eur = price_decimal * self._get_fx_rate(currency)

        return PriceQuote(
            isin=isin,
            symbol=symbol,
            price=price_decimal.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            currency=currency,
            price_in_eur=price_in_eur.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            as_of=datetime.utcnow(),
            name=name,
        )

    def _get_fx_rate(self, currency: str) -> Decimal:
        currency = currency.upper()
        if currency == self.base_currency:
            return Decimal("1")
        if currency in self._fx_cache:
            return self._fx_cache[currency]

        response = self.session.get(
            FX_URL,
            params={"base": currency, "symbols": self.base_currency},
            timeout=10,
        )
        if response.status_code != 200:
            raise PricingError(
                f"Failed to fetch FX rate for {currency}: {response.status_code}"
            )

        data = response.json()
        rates = data.get("rates") or {}
        rate = rates.get(self.base_currency)
        if rate is None:
            raise PricingError(f"No FX rate available for {currency}")

        rate_decimal = Decimal(str(rate))
        self._fx_cache[currency] = rate_decimal
        return rate_decimal


__all__ = ["PriceFetcher", "PricingError", "PriceQuote"]
