from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

if TYPE_CHECKING:
    from app.article.models import Article


class ArticleSummary(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        json_schema_extra={
            "example": {
                "id": 128,
                "title": "範例新聞標題",
                "summary": "第一句。第二句。第三句。",
                "category": "財經",
                "keywords": ["關鍵字A", "關鍵字B"],
                "source": "cna",
                "url": "https://www.cna.com.tw/news/example.aspx",
                "imageUrl": None,
                "publishedAt": "2026-11-24T09:00:00+08:00",
                "similarity": 0.83,
            }
        },
    )

    id: int
    title: str
    summary: str | None
    category: str | None
    keywords: list[str] | None
    source: str
    url: str
    image_url: str | None
    published_at: datetime
    similarity: float | None = None

    @classmethod
    def from_row(cls, article: "Article", similarity: float | None = None) -> "ArticleSummary":
        return cls(
            id=article.id,
            title=article.title,
            summary=article.summary,
            category=article.category,
            keywords=article.keywords,
            source=article.source,
            url=article.url,
            image_url=article.image_url,
            published_at=article.published_at,
            similarity=similarity,
        )


class CategoryCount(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"category": "科技", "count": 42}})

    category: str
    count: int
