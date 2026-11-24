from app.article.service import ArticleService
from app.common.schemas import ArticleSummary


class LatestRecommender:
    def __init__(self, articles: ArticleService):
        self.articles = articles

    def recommend(self, line_user_id: str, limit: int) -> list[ArticleSummary]:
        return self.articles.latest_enriched(limit)  # Phase 2 由 EmbeddingRecommender 取代
