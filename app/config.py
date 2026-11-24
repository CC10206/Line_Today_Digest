from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Feed(BaseModel):
    name: str
    url: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openai_api_key: str
    line_channel_secret: str
    line_channel_access_token: str
    admin_token: str
    database_url: str

    chat_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    enrich_batch_size: int = 20
    enrich_max_retry: int = 3
    ingest_interval_minutes: int = 30
    related_window_days: int = 7
    cache_backend: Literal["memory", "redis"] = "memory"
    recommender: Literal["latest"] = "latest"  # Phase 2 加 "embedding"
    enable_scheduler: bool = True
    feeds: list[Feed] = [
        Feed(name="cna", url="https://feedx.net/rss/cna.xml"),
        Feed(name="ltn", url="https://news.ltn.com.tw/rss/all.xml"),
    ]


settings = Settings()
