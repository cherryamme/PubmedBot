"""Search API endpoints."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db, async_session
from ..models.paper import Paper, Author, JournalMetric
from ..models.search import SearchHistory, search_papers
from ..models.summary import Summary
from ..schemas.paper import SearchResponse, PaperListItem, AuthorSchema, SummarySchema, SearchHistoryItem
from ..schemas.search import SearchRequest
from ..services import pubmed
from ..services.journal_metrics import get_impact_factor
from ..services.llm import summarize_abstract

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/stream")
async def do_search_stream(
    req: SearchRequest,
    auto_summarize: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Execute PubMed search and stream results paper-by-paper via SSE.

    Events:
      - {"type":"status","message":"..."} — progress updates
      - {"type":"paper","data":{...}} — a single paper result
      - {"type":"summary","paper_id":N,"data":{...}} — summary for a paper (auto_summarize)
      - {"type":"done","search_id":N,"total":N} — search complete
      - {"type":"error","message":"..."} — error
    """

    # Phase 1: search PMIDs
    # Phase 2: fetch papers in batch
    # Phase 3: stream papers one by one (with IF resolution)
    # Phase 4: optionally auto-summarize each

    async def event_stream():
        try:
            yield _sse({"type": "status", "message": "正在检索 PubMed..."})

            raw_papers = await pubmed.search_and_fetch(
                query=req.query,
                min_year=req.min_year,
                max_year=req.max_year,
                retmax=req.max_results,
            )

            yield _sse({"type": "status", "message": f"PubMed 返回 {len(raw_papers)} 篇，正在筛选影响因子..."})

            # Use a fresh session for the streaming context
            async with async_session() as sdb:
                paper_ids_for_search = []
                if_cache: dict[str, tuple] = {}  # journal_name -> (if, partition)

                for i, raw in enumerate(raw_papers):
                    # Dedup / save paper
                    existing = (await sdb.execute(
                        select(Paper).options(
                            selectinload(Paper.authors),
                            selectinload(Paper.summary),
                            selectinload(Paper.fulltext_cache),
                        ).where(Paper.pmid == raw["pmid"])
                    )).scalar_one_or_none()

                    if existing:
                        paper_obj = existing
                    else:
                        paper_obj = Paper(
                            pmid=raw["pmid"],
                            pmcid=raw.get("pmcid"),
                            doi=raw.get("doi"),
                            title=raw["title"],
                            abstract=raw.get("abstract"),
                            journal=raw.get("journal"),
                            issn=raw.get("issn"),
                            year=raw.get("year"),
                            keywords=raw.get("keywords"),
                            mesh_terms=raw.get("mesh_terms"),
                        )
                        sdb.add(paper_obj)
                        await sdb.flush()
                        for auth_data in raw.get("authors", []):
                            sdb.add(Author(
                                paper_id=paper_obj.id,
                                name=auth_data["name"],
                                affiliation=auth_data.get("affiliation"),
                                position=auth_data.get("position", 0),
                            ))
                        await sdb.commit()
                        await sdb.refresh(paper_obj, ["authors", "summary", "fulltext_cache"])

                    # Resolve IF (with cache to avoid duplicate lookups)
                    journal_key = paper_obj.journal or ""
                    if journal_key and journal_key not in if_cache:
                        metric = await get_impact_factor(sdb, paper_obj.issn or "", journal_key)
                        if_cache[journal_key] = (metric.impact_factor, metric.sci_partition)
                    paper_if, paper_part = if_cache.get(journal_key, (None, None))

                    # IF filter
                    if req.min_impact_factor and (paper_if is None or paper_if < req.min_impact_factor):
                        continue

                    paper_ids_for_search.append(paper_obj.id)

                    # Build paper data
                    summary_data = None
                    if paper_obj.summary:
                        summary_data = {
                            "summary_en": paper_obj.summary.summary_en,
                            "summary_cn": paper_obj.summary.summary_cn,
                            "innovation_points": paper_obj.summary.innovation_points,
                            "limitations": paper_obj.summary.limitations,
                            "model_used": paper_obj.summary.model_used,
                        }

                    paper_dict = {
                        "id": paper_obj.id,
                        "pmid": paper_obj.pmid,
                        "doi": paper_obj.doi,
                        "title": paper_obj.title,
                        "abstract": paper_obj.abstract,
                        "journal": paper_obj.journal,
                        "issn": paper_obj.issn,
                        "year": paper_obj.year,
                        "authors": [{"name": a.name, "affiliation": a.affiliation, "position": a.position} for a in paper_obj.authors],
                        "impact_factor": paper_if,
                        "sci_partition": paper_part,
                        "summary": summary_data,
                        "has_fulltext": paper_obj.fulltext_cache is not None,
                    }

                    yield _sse({"type": "paper", "data": paper_dict})

                    # Auto-summarize if enabled and no existing summary
                    if auto_summarize and not paper_obj.summary and paper_obj.abstract:
                        try:
                            result = await summarize_abstract(paper_obj.title, paper_obj.abstract)
                            summary = Summary(
                                paper_id=paper_obj.id,
                                summary_en=result["summary_en"],
                                summary_cn=result["summary_cn"],
                                innovation_points=result["innovation_points"],
                                limitations=result["limitations"],
                                model_used=result["model_used"],
                            )
                            sdb.add(summary)
                            await sdb.commit()
                            yield _sse({
                                "type": "summary",
                                "paper_id": paper_obj.id,
                                "data": result,
                            })
                        except Exception as e:
                            logger.error(f"Auto-summarize failed for paper {paper_obj.id}: {e}")
                            yield _sse({
                                "type": "summary_error",
                                "paper_id": paper_obj.id,
                                "message": str(e),
                            })

                # Save search history
                search_record = SearchHistory(
                    query=req.query,
                    min_year=req.min_year,
                    max_year=req.max_year,
                    min_impact_factor=req.min_impact_factor,
                    result_count=len(paper_ids_for_search),
                )
                sdb.add(search_record)
                await sdb.flush()
                for pid in paper_ids_for_search:
                    await sdb.execute(
                        search_papers.insert().values(search_id=search_record.id, paper_id=pid)
                    )
                await sdb.commit()

                yield _sse({"type": "done", "search_id": search_record.id, "total": len(paper_ids_for_search)})

        except Exception as e:
            logger.error(f"Search stream error: {e}")
            yield _sse({"type": "error", "message": str(e)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# Keep the non-streaming endpoint for history lookups
@router.post("", response_model=SearchResponse)
async def do_search(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    """Non-streaming search (used for loading past results)."""
    raw_papers = await pubmed.search_and_fetch(
        query=req.query, min_year=req.min_year, max_year=req.max_year, retmax=req.max_results,
    )
    paper_objects = []
    for raw in raw_papers:
        existing = (await db.execute(select(Paper).where(Paper.pmid == raw["pmid"]))).scalar_one_or_none()
        if existing:
            paper_objects.append(existing)
            continue
        paper = Paper(pmid=raw["pmid"], pmcid=raw.get("pmcid"), doi=raw.get("doi"),
                      title=raw["title"], abstract=raw.get("abstract"), journal=raw.get("journal"),
                      issn=raw.get("issn"), year=raw.get("year"), keywords=raw.get("keywords"),
                      mesh_terms=raw.get("mesh_terms"))
        db.add(paper)
        await db.flush()
        for a in raw.get("authors", []):
            db.add(Author(paper_id=paper.id, name=a["name"], affiliation=a.get("affiliation"), position=a.get("position", 0)))
        paper_objects.append(paper)
    await db.commit()
    for p in paper_objects:
        await db.refresh(p, ["authors", "summary", "fulltext_cache"])
    if_map = {}
    for p in paper_objects:
        j = p.journal or ""
        if j and j not in if_map:
            m = await get_impact_factor(db, p.issn or "", j)
            if_map[j] = m
    result_papers = []
    for p in paper_objects:
        m = if_map.get(p.journal or "")
        pif = m.impact_factor if m else None
        pp = m.sci_partition if m else None
        if req.min_impact_factor and (pif is None or pif < req.min_impact_factor):
            continue
        sd = SummarySchema.model_validate(p.summary) if p.summary else None
        result_papers.append(PaperListItem(
            id=p.id, pmid=p.pmid, doi=p.doi, title=p.title, abstract=p.abstract,
            journal=p.journal, issn=p.issn, year=p.year,
            authors=[AuthorSchema.model_validate(a) for a in p.authors],
            impact_factor=pif, sci_partition=pp, summary=sd, has_fulltext=p.fulltext_cache is not None))
    sr = SearchHistory(query=req.query, min_year=req.min_year, max_year=req.max_year,
                       min_impact_factor=req.min_impact_factor, result_count=len(result_papers))
    db.add(sr)
    await db.flush()
    for p in paper_objects:
        if any(rp.id == p.id for rp in result_papers):
            await db.execute(search_papers.insert().values(search_id=sr.id, paper_id=p.id))
    await db.commit()
    return SearchResponse(search_id=sr.id, query=req.query, total=len(result_papers), papers=result_papers)


@router.get("/history", response_model=list[SearchHistoryItem])
async def get_search_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SearchHistory).order_by(SearchHistory.created_at.desc()).limit(20))
    return [SearchHistoryItem.model_validate(s) for s in result.scalars()]


@router.delete("/history/{search_id}")
async def delete_search_history(search_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a search history entry."""
    search = (await db.execute(select(SearchHistory).where(SearchHistory.id == search_id))).scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="搜索记录不存在")
    await db.execute(search_papers.delete().where(search_papers.c.search_id == search_id))
    await db.delete(search)
    await db.commit()
    return {"ok": True}


@router.get("/{search_id}", response_model=SearchResponse)
async def get_search_results(search_id: int, db: AsyncSession = Depends(get_db)):
    search = (await db.execute(
        select(SearchHistory)
        .options(selectinload(SearchHistory.papers).selectinload(Paper.authors))
        .options(selectinload(SearchHistory.papers).selectinload(Paper.summary))
        .options(selectinload(SearchHistory.papers).selectinload(Paper.fulltext_cache))
        .where(SearchHistory.id == search_id)
    )).scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="搜索记录不存在")
    papers = []
    for p in search.papers:
        metric = None
        if p.issn:
            metric = (await db.execute(select(JournalMetric).where(JournalMetric.issn == p.issn))).scalar_one_or_none()
        if not metric and p.journal:
            metric = (await db.execute(select(JournalMetric).where(JournalMetric.journal_name == p.journal))).scalar_one_or_none()
        sd = SummarySchema.model_validate(p.summary) if p.summary else None
        papers.append(PaperListItem(
            id=p.id, pmid=p.pmid, doi=p.doi, title=p.title, abstract=p.abstract,
            journal=p.journal, issn=p.issn, year=p.year,
            authors=[AuthorSchema.model_validate(a) for a in p.authors],
            impact_factor=metric.impact_factor if metric else None,
            sci_partition=metric.sci_partition if metric else None,
            summary=sd, has_fulltext=p.fulltext_cache is not None))
    return SearchResponse(search_id=search.id, query=search.query, total=len(papers), papers=papers)
