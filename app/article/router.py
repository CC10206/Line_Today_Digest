from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.article.service import ArticleService
from app.cache.base import Cache
from app.cache.factory import get_cache
from app.common.schemas import ArticleSummary, CategoryCount
from app.db import get_db
from app.search.service import SearchService

router = APIRouter(prefix="/api", tags=["article"])


def get_article_service(db: Session = Depends(get_db)) -> ArticleService:
    return ArticleService(db)


def get_search_service(
    db: Session = Depends(get_db), cache: Cache = Depends(get_cache)
) -> SearchService:
    return SearchService(db, cache)


@router.get(
    "/articles",
    response_model=list[ArticleSummary],
    summary="新聞列表（依發布時間新到舊分頁）",
)
def list_articles(
    category: str | None = Query(None, description="分類名稱，例如「科技」；留空回所有分類"),
    page: int = Query(0, ge=0, description="頁碼，從 0 開始"),
    size: int = Query(20, ge=1, le=100, description="每頁筆數"),
    svc: ArticleService = Depends(get_article_service),
) -> list[ArticleSummary]:
    return svc.list_articles(category, page, size)


@router.get(
    "/articles/{article_id}",
    response_model=ArticleSummary,
    summary="單篇新聞詳情",
    responses={404: {"description": "文章不存在或尚未處理完成"}},
)
def get_article(
    article_id: int, svc: ArticleService = Depends(get_article_service)
) -> ArticleSummary:
    return svc.get(article_id)


@router.get(
    "/articles/{article_id}/related",
    response_model=list[ArticleSummary],
    summary="語意相關新聞",
)
def related_articles(
    article_id: int,
    limit: int = Query(3, le=10, description="回傳筆數"),
    svc: SearchService = Depends(get_search_service),
) -> list[ArticleSummary]:
    return svc.related(article_id, limit)


@router.get(
    "/categories",
    response_model=list[CategoryCount],
    summary="分類清單與各分類文章數",
)
def list_categories(svc: ArticleService = Depends(get_article_service)) -> list[CategoryCount]:
    return svc.categories()
