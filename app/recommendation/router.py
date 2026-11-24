from fastapi import APIRouter, Depends, Query

from app.common.schemas import ArticleSummary
from app.recommendation.base import Recommender
from app.recommendation.factory import get_recommender

router = APIRouter(prefix="/api", tags=["recommendation"])


@router.get(
    "/recommend",
    response_model=list[ArticleSummary],
    summary="個人化推薦（MVP 等同最新新聞）",
)
def recommend(
    line_user_id: str = Query(..., alias="lineUserId", description="LINE 使用者 ID"),
    limit: int = Query(5, ge=1, le=20),
    recommender: Recommender = Depends(get_recommender),
) -> list[ArticleSummary]:
    return recommender.recommend(line_user_id, limit)
