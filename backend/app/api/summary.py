"""LLM summarization endpoints."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.paper import Paper
from ..models.summary import Summary, FulltextAnalysis
from ..schemas.summary import SummarizeResponse
from ..services.llm import summarize_abstract, analyze_fulltext
from ..utils.text_processor import chunk_fulltext_sections, build_context_from_sections

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/papers", tags=["summary"])


@router.post("/{paper_id}/summarize", response_model=SummarizeResponse)
async def summarize_paper(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Generate LLM summary for a paper."""
    paper = (await db.execute(
        select(Paper)
        .options(selectinload(Paper.summary))
        .where(Paper.id == paper_id)
    )).scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    # Return existing summary
    if paper.summary:
        return SummarizeResponse(
            paper_id=paper.id,
            summary_en=paper.summary.summary_en or "",
            summary_cn=paper.summary.summary_cn or "",
            innovation_points=paper.summary.innovation_points or "",
            limitations=paper.summary.limitations or "",
            model_used=paper.summary.model_used or "",
        )

    if not paper.abstract:
        raise HTTPException(status_code=400, detail="该论文无摘要，无法生成总结")

    result = await summarize_abstract(paper.title, paper.abstract)

    summary = Summary(
        paper_id=paper.id,
        summary_en=result["summary_en"],
        summary_cn=result["summary_cn"],
        innovation_points=result["innovation_points"],
        limitations=result["limitations"],
        model_used=result["model_used"],
    )
    db.add(summary)
    await db.commit()

    return SummarizeResponse(
        paper_id=paper.id,
        summary_en=result["summary_en"],
        summary_cn=result["summary_cn"],
        innovation_points=result["innovation_points"],
        limitations=result["limitations"],
        model_used=result["model_used"],
    )


@router.post("/{paper_id}/analyze-fulltext")
async def analyze_paper_fulltext(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Analyze full text of a paper with LLM. Fetches full text first if needed."""
    paper = (await db.execute(
        select(Paper)
        .options(selectinload(Paper.fulltext_cache))
        .options(selectinload(Paper.fulltext_analysis))
        .where(Paper.id == paper_id)
    )).scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    if paper.fulltext_analysis:
        return {"analysis": paper.fulltext_analysis.analysis, "model_used": paper.fulltext_analysis.model_used}

    # Try to fetch fulltext if not cached
    if not paper.fulltext_cache:
        from ..services.fulltext import get_fulltext
        from ..models.summary import FulltextCache
        result = await get_fulltext(paper.pmid, paper.pmcid, paper.doi)
        if result.available:
            cache = FulltextCache(
                paper_id=paper.id, source=result.source, content=result.content,
                content_type=result.content_type, oa_url=result.oa_url,
            )
            db.add(cache)
            await db.commit()
            await db.refresh(paper, ["fulltext_cache"])

    if not paper.fulltext_cache or not paper.fulltext_cache.content:
        # Fallback: use abstract for analysis if no full text
        if paper.abstract:
            fulltext_content = f"[仅摘要] {paper.abstract}"
        else:
            raise HTTPException(status_code=400, detail="该论文无全文内容且无摘要，无法进行分析")
    else:
        fulltext_content = paper.fulltext_cache.content
        if paper.fulltext_cache.content_type == "json":
            try:
                passages = json.loads(fulltext_content)
                sections = chunk_fulltext_sections(passages)
                fulltext_content = build_context_from_sections(sections)
            except json.JSONDecodeError:
                pass

    from ..config import settings as app_settings
    analysis_text = await analyze_fulltext(paper.title, fulltext_content)

    analysis = FulltextAnalysis(
        paper_id=paper.id,
        analysis=analysis_text,
        model_used=app_settings.llm_model,
    )
    db.add(analysis)
    await db.commit()

    return {"analysis": analysis_text, "model_used": analysis.model_used}


@router.post("/search/{search_id}/summarize-all")
async def summarize_all_papers(search_id: int, db: AsyncSession = Depends(get_db)):
    """Batch summarize all papers in a search."""
    from ..models.search import SearchHistory

    search = (await db.execute(
        select(SearchHistory)
        .options(
            selectinload(SearchHistory.papers)
            .selectinload(Paper.summary)
        )
        .where(SearchHistory.id == search_id)
    )).scalar_one_or_none()

    if not search:
        raise HTTPException(status_code=404, detail="搜索记录不存在")

    results = []
    for paper in search.papers:
        if paper.summary:
            results.append({"paper_id": paper.id, "status": "exists"})
            continue
        if not paper.abstract:
            results.append({"paper_id": paper.id, "status": "no_abstract"})
            continue
        try:
            result = await summarize_abstract(paper.title, paper.abstract)
            summary = Summary(
                paper_id=paper.id,
                summary_en=result["summary_en"],
                summary_cn=result["summary_cn"],
                innovation_points=result["innovation_points"],
                limitations=result["limitations"],
                model_used=result["model_used"],
            )
            db.add(summary)
            await db.commit()
            results.append({"paper_id": paper.id, "status": "success"})
        except Exception as e:
            logger.error(f"Summary failed for paper {paper.id}: {e}")
            results.append({"paper_id": paper.id, "status": "error", "error": str(e)})

    return {"search_id": search_id, "results": results}
