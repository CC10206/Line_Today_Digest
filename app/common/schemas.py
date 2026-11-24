from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

if TYPE_CHECKING:
    from app.article.models import Article


class ArticleSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

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
    category: str
    count: int
