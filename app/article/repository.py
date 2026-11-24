from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.article.models import Article


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

    def claim_pending(self, limit: int) -> list[Article]:
        stmt = select(Article).where(Article.status == "PENDING").order_by(Article.created_at).limit(limit)
        return list(self.db.scalars(stmt))

    def upsert_on_conflict(self, rows: list[dict]) -> int:
        if not rows:
            return 0
        stmt = (
            pg_insert(Article)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["url"])
            .returning(Article.id)
        )
        inserted = self.db.execute(stmt).fetchall()
        self.db.commit()
        return len(inserted)
