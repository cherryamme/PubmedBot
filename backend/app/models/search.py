from datetime import datetime, timezone

from sqlalchemy import Column, ForeignKey, Integer, Float, Table, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

search_papers = Table(
    "search_papers",
    Base.metadata,
    Column("search_id", Integer, ForeignKey("search_history.id"), primary_key=True),
    Column("paper_id", Integer, ForeignKey("papers.id"), primary_key=True),
)


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    min_year: Mapped[int | None] = mapped_column(Integer)
    max_year: Mapped[int | None] = mapped_column(Integer)
    min_impact_factor: Mapped[float | None] = mapped_column(Float)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    papers: Mapped[list["Paper"]] = relationship(
        secondary=search_papers, lazy="selectin"
    )


from .paper import Paper  # noqa: E402
