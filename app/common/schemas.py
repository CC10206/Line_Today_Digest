from datetime import datetime

from pydantic import BaseModel


class ArticleSummary(BaseModel):
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

    # TODO: from_row(article, similarity=None) classmethod
