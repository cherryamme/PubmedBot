from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), unique=True, nullable=False)
    summary_en: Mapped[str | None] = mapped_column(Text)
    summary_cn: Mapped[str | None] = mapped_column(Text)
    innovation_points: Mapped[str | None] = mapped_column(Text)
    limitations: Mapped[str | None] = mapped_column(Text)
    model_used: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    paper: Mapped["Paper"] = relationship(back_populates="summary")


class FulltextCache(Base):
    __tablename__ = "fulltext_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), unique=True, nullable=False)
    source: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    content_type: Mapped[str | None] = mapped_column(Text)
    oa_url: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    paper: Mapped["Paper"] = relationship(back_populates="fulltext_cache")


class FulltextAnalysis(Base):
    __tablename__ = "fulltext_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), unique=True, nullable=False)
    analysis: Mapped[str | None] = mapped_column(Text)
    model_used: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    paper: Mapped["Paper"] = relationship(back_populates="fulltext_analysis")


from .paper import Paper  # noqa: E402
