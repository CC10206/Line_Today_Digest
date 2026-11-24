from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ClickEvent(Base):
    __tablename__ = "click_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    line_user_id: Mapped[str]
    article_id: Mapped[int] = mapped_column(ForeignKey("article.id"))
    action: Mapped[str]  # RELATED | OPEN
    created_at: Mapped[datetime]
