from datetime import datetime, timezone

from sqlalchemy import Float, ForeignKey, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pmid: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    pmcid: Mapped[str | None] = mapped_column(Text)
    doi: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text)
    journal: Mapped[str | None] = mapped_column(Text)
    issn: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    keywords: Mapped[str | None] = mapped_column(Text)  # JSON list
    mesh_terms: Mapped[str | None] = mapped_column(Text)  # JSON list
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    authors: Mapped[list["Author"]] = relationship(
        back_populates="paper", cascade="all, delete-orphan", order_by="Author.position"
    )
    summary: Mapped["Summary | None"] = relationship(back_populates="paper", uselist=False)
    fulltext_cache: Mapped["FulltextCache | None"] = relationship(back_populates="paper", uselist=False)
    fulltext_analysis: Mapped["FulltextAnalysis | None"] = relationship(back_populates="paper", uselist=False)
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="paper")


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    affiliation: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0)

    paper: Mapped["Paper"] = relationship(back_populates="authors")


class JournalMetric(Base):
    __tablename__ = "journal_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issn: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    journal_name: Mapped[str | None] = mapped_column(Text)
    impact_factor: Mapped[float | None] = mapped_column(Float)
    sci_partition: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


# forward refs for relationships
from .summary import Summary, FulltextCache, FulltextAnalysis  # noqa: E402
from .chat import ChatSession  # noqa: E402
