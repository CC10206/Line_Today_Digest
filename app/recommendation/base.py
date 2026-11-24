from typing import Protocol

from app.common.schemas import ArticleSummary


class Recommender(Protocol):
    def recommend(self, line_user_id: str, limit: int) -> list[ArticleSummary]: ...
