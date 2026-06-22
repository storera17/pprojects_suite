from __future__ import annotations

from app.core.config import settings
from app.providers.alpha_vantage import AlphaVantageProvider
from app.providers.crypto_fx import CryptoFxProvider
from app.providers.finnhub import FinnhubProvider
from app.providers.fred import FredProvider
from app.providers.marketaux import MarketauxProvider
from app.providers.nytimes import NYTimesProvider
from app.providers.polygon import PolygonProvider
from app.providers.serpstack import SerpstackProvider
from app.providers.stockdata import StockDataProvider
from app.providers.base import is_configured
from app.repositories.records_repository import db_summary
from app.repositories.watchlist_repository import get_watchlist_tickers


def configured_provider_keys() -> dict[str, bool]:
    return {
        "polygon": is_configured(settings.polygon_api_key),
        "finnhub": is_configured(settings.finnhub_api_key),
        "alpha_vantage": is_configured(settings.alpha_vantage_api_key),
        "fred": is_configured(settings.fred_api_key),
        "marketaux": is_configured(settings.marketaux_api_key),
        "nytimes": is_configured(settings.nytimes_api_key),
        "coinlayer": is_configured(settings.coinlayer_api_key),
        "alchemy": is_configured(settings.alchemy_api_key),
        "currencylayer": is_configured(settings.currencylayer_api_key),
        "fixer": is_configured(settings.fixer_api_key),
        "serpstack": is_configured(settings.serpstack_api_key),
        "stockdata": is_configured(settings.stockdata_api_key),
    }


class RefreshOrchestrator:
    def __init__(self):
        self.polygon = PolygonProvider()
        self.alpha_vantage = AlphaVantageProvider()
        self.finnhub = FinnhubProvider()
        self.stockdata = StockDataProvider()
        self.marketaux = MarketauxProvider()
        self.nytimes = NYTimesProvider()
        self.serpstack = SerpstackProvider()
        self.fred = FredProvider()
        self.crypto_fx = CryptoFxProvider()

    def refresh_ticker(self, ticker: str, days: int = 365, force: bool = False) -> dict:
        ticker = ticker.upper()
        return {
            "ticker": ticker,
            "polygon": self.polygon.history(ticker, days=min(days, 365), force=force),
            "alpha_vantage": self.alpha_vantage.history(ticker, days=min(days, 100), force=force),
            "finnhub": self.finnhub.quote(ticker, force=force),
            "stockdata": self.stockdata.quote_and_news(ticker, force=force),
            "nytimes": self.nytimes.news(ticker, force=force),
            "marketaux": self.marketaux.news(ticker, force=force),
            "serpstack": self.serpstack.search(f"{ticker} stock market news", ticker, force=force),
        }

    def refresh_macro_context(self, force: bool = False) -> dict:
        return {
            "fred_FEDFUNDS": self.fred.series("FEDFUNDS", force=force),
            "fred_DGS10": self.fred.series("DGS10", force=force),
            "fred_CPIAUCSL": self.fred.series("CPIAUCSL", force=force),
            "fred_UNRATE": self.fred.series("UNRATE", force=force),
            "fred_GDP": self.fred.series("GDP", force=force),
            "coinlayer": self.crypto_fx.coinlayer(force=force),
            "alchemy": self.crypto_fx.alchemy(force=force),
            "currencylayer": self.crypto_fx.currencylayer(force=force),
            "fixer": self.crypto_fx.fixer(force=force),
        }

    def refresh_all(self, tickers: list[str] | None = None, force: bool = False) -> dict:
        symbols = [ticker.upper() for ticker in (tickers or get_watchlist_tickers())]
        results = {ticker: self.refresh_ticker(ticker, force=force) for ticker in symbols}
        macro = self.refresh_macro_context(force=force)
        return {"status": "ok", "tickers": results, "macro_crypto_fx": macro, "db_summary": db_summary()}
