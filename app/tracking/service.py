from sqlalchemy.orm import Session

from app.tracking.models import ClickEvent


class TrackingService:
    def __init__(self, db: Session):
        self.db = db

    def record(self, line_user_id: str, article_id: int, action: str) -> None:
        self.db.add(ClickEvent(line_user_id=line_user_id, article_id=article_id, action=action))
        self.db.commit()
