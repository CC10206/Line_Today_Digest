from sqlalchemy.orm import Session

from app.article.models import Category
from app.article.repository import ArticleRepository
from app.common.errors import ArticleNotFound
from app.common.schemas import ArticleSummary, CategoryCount

# claim_pending(limit) 會在階段 3（enrichment）加進來。


class ArticleService:
    def __init__(self, db: Session):
        self.repo = ArticleRepository(db)

    def list_articles(self, category: str | None, page: int, size: int) -> list[ArticleSummary]:
        articles = self.repo.list_enriched(category, page, size)
        return [ArticleSummary.from_row(a) for a in articles]

    def get(self, article_id: int) -> ArticleSummary:
        article = self.repo.get(article_id)
        if article is None or article.status != "ENRICHED":
            raise ArticleNotFound(article_id)
        return ArticleSummary.from_row(article)

    def latest_enriched(self, limit: int) -> list[ArticleSummary]:
        articles = self.repo.list_enriched(None, 0, limit)
        return [ArticleSummary.from_row(a) for a in articles]

    def categories(self) -> list[CategoryCount]:
        counts = self.repo.category_counts()
        return [CategoryCount(category=c.value, count=counts.get(c.value, 0)) for c in Category]
