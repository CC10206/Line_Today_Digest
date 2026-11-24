from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.article.models import Article

# claim_pending(limit) 給階段 3（enrichment）用、upsert_on_conflict(url) 給階段 2（ingestion）用，
# 到那兩個階段再加進來。


class ArticleRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_enriched(self, category: str | None, page: int, size: int) -> list[Article]:
        stmt = select(Article).where(Article.status == "ENRICHED")
        if category is not None:
            stmt = stmt.where(Article.category == category)
        stmt = stmt.order_by(Article.published_at.desc()).offset(page * size).limit(size)
        return list(self.db.scalars(stmt))

    def get(self, article_id: int) -> Article | None:
        return self.db.get(Article, article_id)

    def category_counts(self) -> dict[str, int]:
        stmt = (
            select(Article.category, func.count())
            .where(Article.status == "ENRICHED")
            .group_by(Article.category)
        )
        return dict(self.db.execute(stmt).all())
