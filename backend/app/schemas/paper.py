from datetime import datetime

from pydantic import BaseModel


class AuthorSchema(BaseModel):
    name: str
    affiliation: str | None = None
    position: int = 0

    class Config:
        from_attributes = True


class SummarySchema(BaseModel):
    summary_en: str | None = None
    summary_cn: str | None = None
    innovation_points: str | None = None
    limitations: str | None = None
    model_used: str | None = None

    class Config:
        from_attributes = True


class PaperListItem(BaseModel):
    id: int
    pmid: str
    doi: str | None = None
    title: str
    abstract: str | None = None
    journal: str | None = None
    issn: str | None = None
    year: int | None = None
    authors: list[AuthorSchema] = []
    impact_factor: float | None = None
    sci_partition: str | None = None
    summary: SummarySchema | None = None
    has_fulltext: bool = False

    class Config:
        from_attributes = True


class PaperDetail(PaperListItem):
    pmcid: str | None = None
    keywords: str | None = None
    mesh_terms: str | None = None
    created_at: datetime | None = None


class SearchResponse(BaseModel):
    search_id: int
    query: str
    total: int
    papers: list[PaperListItem]


class SearchHistoryItem(BaseModel):
    id: int
    query: str
    min_year: int | None = None
    max_year: int | None = None
    min_impact_factor: float | None = None
    result_count: int
    created_at: datetime

    class Config:
        from_attributes = True
