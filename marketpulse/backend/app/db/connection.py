from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

MARKETPULSE_WATCHLIST_SEED = (
    "SPY",
    "AAPL",
    "MSFT",
    "NVDA",
    "TSLA",
    "AMZN",
    "META",
    "GOOGL",
    "AMD",
    "QQQ",
    "KR",
)


class Settings(BaseSettings):
    app_env: str = "local"
    frontend_origin: str = "http://localhost:5173"
    sqlite_path: str = "./data/marketpulse.sqlite3"

    refresh_hour: int = 3
    refresh_minute: int = 15
    default_tickers: str = "SPY,AAPL,MSFT,NVDA,TSLA,AMZN,META,GOOGL,AMD,QQQ,KR"

    polygon_api_key: str | None = None
    finnhub_api_key: str | None = None
    alpha_vantage_api_key: str | None = None
    fred_api_key: str | None = None
    marketaux_api_key: str | None = None
    nytimes_api_key: str | None = None

    coinlayer_api_key: str | None = None
    alchemy_api_key: str | None = None
    currencylayer_api_key: str | None = None
    fixer_api_key: str | None = None
    serpstack_api_key: str | None = None
    stockdata_api_key: str | None = None

    llm_mode: str = "local_analyst"
    provider_cache_ttl_seconds: int = 86400

    auto_refresh_enabled: bool = True
    auto_refresh_interval_minutes: int = 1440
    auto_refresh_minimum_interval_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def tickers(self) -> list[str]:
        return [ticker.strip().upper() for ticker in self.default_tickers.split(",") if ticker.strip()]

    @property
    def watchlist_seed_tickers(self) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for ticker in [*self.tickers, *MARKETPULSE_WATCHLIST_SEED]:
            clean = str(ticker or "").strip().upper()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            ordered.append(clean)
        return ordered


settings = Settings()
