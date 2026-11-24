from fastapi import Depends
from sqlalchemy.orm import Session

from app.article.service import ArticleService
from app.config import settings
from app.db import get_db
from app.recommendation.base import Recommender
from app.recommendation.latest import LatestRecommender


def get_recommender(db: Session = Depends(get_db)) -> Recommender:
    match settings.recommender:
        case "latest":
            return LatestRecommender(ArticleService(db))
        case other:
            raise ValueError(f"unknown recommender: {other}")  # Phase 2 加 "embedding"
