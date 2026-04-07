"""Paper detail and fulltext endpoints."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.paper import Paper, JournalMetric
from ..models.summary import FulltextCache
from ..schemas.paper import PaperDetail, AuthorSchema, SummarySchema
from ..services.fulltext import get_fulltext

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.get("/{paper_id}", response_model=PaperDetail)
async def get_paper(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Get full paper details."""
    paper = (await db.execute(
        select(Paper)
        .options(selectinload(Paper.authors))
        .options(selectinload(Paper.summary))
        .options(selectinload(Paper.fulltext_cache))
        .where(Paper.id == paper_id)
    )).scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    metric = None
    if paper.issn:
        metric = (await db.execute(
            select(JournalMetric).where(JournalMetric.issn == paper.issn)
        )).scalar_one_or_none()

    summary_data = SummarySchema.model_validate(paper.summary) if paper.summary else None

    return PaperDetail(
        id=paper.id,
        pmid=paper.pmid,
        pmcid=paper.pmcid,
        doi=paper.doi,
        title=paper.title,
        abstract=paper.abstract,
        journal=paper.journal,
        issn=paper.issn,
        year=paper.year,
        keywords=paper.keywords,
        mesh_terms=paper.mesh_terms,
        created_at=paper.created_at,
        authors=[AuthorSchema.model_validate(a) for a in paper.authors],
        impact_factor=metric.impact_factor if metric else None,
        sci_partition=metric.sci_partition if metric else None,
        summary=summary_data,
        has_fulltext=paper.fulltext_cache is not None,
    )


@router.get("/{paper_id}/fulltext")
async def get_paper_fulltext(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Get or fetch full text for a paper."""
    paper = (await db.execute(
        select(Paper)
        .options(selectinload(Paper.fulltext_cache))
        .where(Paper.id == paper_id)
    )).scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    # Return cached if available
    if paper.fulltext_cache:
        return {
            "available": True,
            "source": paper.fulltext_cache.source,
            "content_type": paper.fulltext_cache.content_type,
            "content": paper.fulltext_cache.content,
            "oa_url": paper.fulltext_cache.oa_url,
        }

    # Fetch from external sources
    result = await get_fulltext(paper.pmid, paper.pmcid, paper.doi)

    if result.available:
        cache = FulltextCache(
            paper_id=paper.id,
            source=result.source,
            content=result.content,
            content_type=result.content_type,
            oa_url=result.oa_url,
        )
        db.add(cache)
        await db.commit()

        return {
            "available": True,
            "source": result.source,
            "content_type": result.content_type,
            "content": result.content,
            "oa_url": result.oa_url,
        }

    return {"available": False, "source": None, "content": None, "oa_url": None}
