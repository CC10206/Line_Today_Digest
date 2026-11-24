from datetime import datetime
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Category(StrEnum):
    POLITICS = "政治"
    INTERNATIONAL = "國際"
    FINANCE = "財經"
    TECH = "科技"
    SOCIETY = "社會"
    LIFE = "生活"
    ENTERTAINMENT = "娛樂"
    SPORTS = "運動"
    HEALTH = "健康"
    OTHER = "其他"


class Article(Base):
    __tablename__ = "article"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(unique=True)
    source: Mapped[str]
    title: Mapped[str]
    content: Mapped[str | None]
    image_url: Mapped[str | None]
    published_at: Mapped[datetime]
    summary: Mapped[str | None]
    category: Mapped[str | None]
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    status: Mapped[str] = mapped_column(default="PENDING")
    retry_count: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    enriched_at: Mapped[datetime | None]
