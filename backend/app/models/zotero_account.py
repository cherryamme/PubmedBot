from datetime import datetime, timezone

from sqlalchemy import Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ZoteroAccount(Base):
    __tablename__ = "zotero_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)  # display name
    library_id: Mapped[str] = mapped_column(Text, nullable=False)
    library_type: Mapped[str] = mapped_column(Text, default="user")  # "user" or "group"
    api_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
