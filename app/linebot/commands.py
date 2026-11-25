from fastapi import Depends
from sqlalchemy.orm import Session

from app.article.models import Category
from app.article.service import ArticleService
from app.cache.base import Cache
from app.cache.factory import get_cache
from app.common.errors import ArticleNotFound
from app.common.schemas import ArticleSummary
from app.db import get_db
from app.linebot.flex import article_carousel, text_message
from app.recommendation.base import Recommender
from app.recommendation.factory import get_recommender
from app.search.service import SearchService
from app.tracking.service import TrackingService

LIST_LIMIT = 5
RELATED_LIMIT = 3


class CommandRouter:
    def __init__(
        self,
        articles: ArticleService,
        search: SearchService,
        recommender: Recommender,
        tracking: TrackingService,
    ):
        self.articles = articles
        self.search = search
        self.recommender = recommender
        self.tracking = tracking

    def on_text(self, user_id: str, text: str) -> list:
        if text == "今日新聞":
            return self._carousel_or_empty(self.articles.list_articles(None, 0, LIST_LIMIT))
        if text in set(Category):
            return self._carousel_or_empty(self.articles.list_articles(text, 0, LIST_LIMIT))
        if text == "推薦":
            return self._carousel_or_empty(self.recommender.recommend(user_id, LIST_LIMIT))
        return [self._help_message()]

    def on_postback(self, user_id: str, data: str) -> list:
        params = dict(pair.split("=", 1) for pair in data.split("&") if "=" in pair)
        if params.get("action") == "related":
            article_id = int(params["id"])
            try:
                related = self.search.related(article_id, RELATED_LIMIT)
            except ArticleNotFound:
                return [text_message("目前沒有新聞，稍後再試")]
            self.tracking.record(user_id, article_id, "RELATED")
            return self._carousel_or_empty(related)
        return [self._help_message()]

    def _carousel_or_empty(self, articles: list[ArticleSummary]) -> list:
        if not articles:
            return [text_message("目前沒有新聞，稍後再試")]
        return [article_carousel(articles)]

    def _help_message(self):
        return text_message(
            "輸入「今日新聞」看最新新聞，輸入分類名稱（如「科技」）看該分類，或輸入「推薦」看個人化推薦。",
            with_quick_reply=True,
        )


def get_command_router(
    db: Session = Depends(get_db),
    cache: Cache = Depends(get_cache),
    recommender: Recommender = Depends(get_recommender),
) -> CommandRouter:
    return CommandRouter(
        articles=ArticleService(db),
        search=SearchService(db, cache),
        recommender=recommender,
        tracking=TrackingService(db),
    )
