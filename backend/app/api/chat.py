"""Chat (Q&A) endpoints with SSE streaming."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.paper import Paper
from ..models.chat import ChatSession, ChatMessage
from ..models.summary import FulltextCache
from ..schemas.chat import ChatRequest, ChatHistoryResponse, ChatMessageSchema
from ..services.fulltext import get_fulltext
from ..services.llm import stream_chat
from ..utils.text_processor import chunk_fulltext_sections, build_context_from_sections

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/papers", tags=["chat"])


@router.post("/{paper_id}/chat")
async def chat_with_paper(
    paper_id: int,
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Stream a chat response about a paper via SSE."""
    paper = (await db.execute(
        select(Paper)
        .options(selectinload(Paper.summary))
        .options(selectinload(Paper.fulltext_cache))
        .where(Paper.id == paper_id)
    )).scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    # Get or create session
    if req.session_id:
        session = (await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == req.session_id)
        )).scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        session = ChatSession(paper_id=paper_id)
        db.add(session)
        await db.flush()

    # Save user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=req.message)
    db.add(user_msg)
    await db.commit()

    # Load chat history
    msgs = (await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
    )).scalars().all()

    chat_history = [{"role": m.role, "content": m.content} for m in msgs[:-1]]  # Exclude current

    # Prepare fulltext: use cache if available, otherwise fetch on demand
    # (same behavior as /analyze-fulltext) so that Q&A has the full paper as context.
    if not paper.fulltext_cache:
        try:
            result = await get_fulltext(paper.pmid, paper.pmcid, paper.doi)
            if result.available and result.content:
                cache = FulltextCache(
                    paper_id=paper.id,
                    source=result.source,
                    content=result.content,
                    content_type=result.content_type,
                    oa_url=result.oa_url,
                )
                db.add(cache)
                await db.commit()
                await db.refresh(paper, ["fulltext_cache"])
                logger.info(
                    f"Chat: fetched fulltext for paper {paper.id} from {result.source}"
                )
            else:
                logger.info(
                    f"Chat: no fulltext available for paper {paper.id}, falling back to abstract"
                )
        except Exception as e:
            logger.warning(f"Chat: fulltext fetch failed for paper {paper.id}: {e}")

    fulltext = None
    if paper.fulltext_cache and paper.fulltext_cache.content:
        if paper.fulltext_cache.content_type == "json":
            try:
                passages = json.loads(paper.fulltext_cache.content)
                sections = chunk_fulltext_sections(passages)
                fulltext = build_context_from_sections(sections)
            except json.JSONDecodeError:
                fulltext = paper.fulltext_cache.content
        else:
            fulltext = paper.fulltext_cache.content

    logger.info(
        f"Chat: paper {paper.id} context — abstract={'yes' if paper.abstract else 'no'}, "
        f"fulltext={'yes (%d chars)' % len(fulltext) if fulltext else 'no'}, "
        f"summary={'yes' if paper.summary else 'no'}"
    )

    summary_cn = paper.summary.summary_cn if paper.summary else None
    session_id = session.id

    async def event_stream():
        full_response = []
        try:
            async for chunk in stream_chat(
                title=paper.title,
                journal=paper.journal,
                year=paper.year,
                abstract=paper.abstract,
                fulltext=fulltext,
                summary_cn=summary_cn,
                chat_history=chat_history,
                user_message=req.message,
            ):
                full_response.append(chunk)
                data = json.dumps({"content": chunk, "done": False, "session_id": session_id})
                yield f"data: {data}\n\n"

            # Final event
            data = json.dumps({"content": "", "done": True, "session_id": session_id})
            yield f"data: {data}\n\n"

            # Save assistant response
            assistant_content = "".join(full_response)
            async with get_db_session() as save_db:
                save_db.add(ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=assistant_content,
                ))
                await save_db.commit()

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            data = json.dumps({"content": f"\n\n[错误: {str(e)}]", "done": True, "session_id": session_id})
            yield f"data: {data}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{paper_id}/chat/history", response_model=list[ChatHistoryResponse])
async def get_chat_history(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Get all chat sessions for a paper."""
    sessions = (await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.paper_id == paper_id)
        .order_by(ChatSession.created_at.desc())
    )).scalars().all()

    return [
        ChatHistoryResponse(
            session_id=s.id,
            paper_id=paper_id,
            messages=[ChatMessageSchema.model_validate(m) for m in s.messages],
        )
        for s in sessions
    ]


# Helper to get a fresh db session for saving in the streaming context
from contextlib import asynccontextmanager
from ..database import async_session

@asynccontextmanager
async def get_db_session():
    async with async_session() as session:
        yield session
