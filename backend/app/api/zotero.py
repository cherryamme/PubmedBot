"""Zotero multi-account export endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.paper import Paper
from ..models.chat import ChatSession
from ..models.zotero_account import ZoteroAccount
from ..services.zotero_service import export_paper, list_collections, check_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["zotero"])


# ---- Account CRUD ----

class ZoteroAccountIn(BaseModel):
    name: str
    library_id: str
    library_type: str = "user"
    api_key: str


class ZoteroAccountOut(BaseModel):
    id: int
    name: str
    library_id: str
    library_type: str
    api_key_set: bool

    class Config:
        from_attributes = True


@router.get("/zotero/accounts", response_model=list[ZoteroAccountOut])
async def get_accounts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ZoteroAccount).order_by(ZoteroAccount.id))
    return [
        ZoteroAccountOut(id=a.id, name=a.name, library_id=a.library_id,
                         library_type=a.library_type, api_key_set=bool(a.api_key))
        for a in result.scalars()
    ]


@router.post("/zotero/accounts", response_model=ZoteroAccountOut)
async def add_account(body: ZoteroAccountIn, db: AsyncSession = Depends(get_db)):
    acct = ZoteroAccount(name=body.name, library_id=body.library_id,
                         library_type=body.library_type, api_key=body.api_key)
    db.add(acct)
    await db.commit()
    await db.refresh(acct)
    return ZoteroAccountOut(id=acct.id, name=acct.name, library_id=acct.library_id,
                            library_type=acct.library_type, api_key_set=True)


@router.put("/zotero/accounts/{acct_id}", response_model=ZoteroAccountOut)
async def update_account(acct_id: int, body: ZoteroAccountIn, db: AsyncSession = Depends(get_db)):
    acct = (await db.execute(select(ZoteroAccount).where(ZoteroAccount.id == acct_id))).scalar_one_or_none()
    if not acct:
        raise HTTPException(404, "账户不存在")
    acct.name = body.name
    acct.library_id = body.library_id
    acct.library_type = body.library_type
    if body.api_key:
        acct.api_key = body.api_key
    await db.commit()
    return ZoteroAccountOut(id=acct.id, name=acct.name, library_id=acct.library_id,
                            library_type=acct.library_type, api_key_set=bool(acct.api_key))


@router.delete("/zotero/accounts/{acct_id}")
async def delete_account(acct_id: int, db: AsyncSession = Depends(get_db)):
    acct = (await db.execute(select(ZoteroAccount).where(ZoteroAccount.id == acct_id))).scalar_one_or_none()
    if not acct:
        raise HTTPException(404, "账户不存在")
    await db.delete(acct)
    await db.commit()
    return {"ok": True}


@router.get("/zotero/accounts/{acct_id}/check")
async def check_account(acct_id: int, db: AsyncSession = Depends(get_db)):
    acct = (await db.execute(select(ZoteroAccount).where(ZoteroAccount.id == acct_id))).scalar_one_or_none()
    if not acct:
        raise HTTPException(404, "账户不存在")
    return await check_connection(acct.library_id, acct.library_type, acct.api_key)


# ---- Collections ----

@router.get("/zotero/accounts/{acct_id}/collections")
async def get_collections(acct_id: int, db: AsyncSession = Depends(get_db)):
    acct = (await db.execute(select(ZoteroAccount).where(ZoteroAccount.id == acct_id))).scalar_one_or_none()
    if not acct:
        raise HTTPException(404, "账户不存在")
    try:
        return await list_collections(acct.library_id, acct.library_type, acct.api_key)
    except Exception as e:
        raise HTTPException(500, f"获取文件夹失败: {e}")


# ---- Export ----

class ExportRequest(BaseModel):
    account_id: int
    collection_key: str | None = None
    include_chat: bool = True


class ExportResponse(BaseModel):
    success: bool
    item_key: str | None = None
    message: str


@router.post("/papers/{paper_id}/zotero/export", response_model=ExportResponse)
async def export_to_zotero(paper_id: int, req: ExportRequest, db: AsyncSession = Depends(get_db)):
    acct = (await db.execute(select(ZoteroAccount).where(ZoteroAccount.id == req.account_id))).scalar_one_or_none()
    if not acct:
        return ExportResponse(success=False, message="Zotero 账户不存在，请先在设置中添加")

    from ..models.summary import FulltextAnalysis
    paper = (await db.execute(
        select(Paper).options(
            selectinload(Paper.authors),
            selectinload(Paper.summary),
            selectinload(Paper.fulltext_analysis),
        ).where(Paper.id == paper_id)
    )).scalar_one_or_none()
    if not paper:
        raise HTTPException(404, "论文不存在")

    chat_msgs = None
    if req.include_chat:
        sessions = (await db.execute(
            select(ChatSession).options(selectinload(ChatSession.messages))
            .where(ChatSession.paper_id == paper_id).order_by(ChatSession.created_at.desc())
        )).scalars().all()
        if sessions:
            chat_msgs = [{"role": m.role, "content": m.content} for s in sessions for m in s.messages]

    try:
        result = await export_paper(
            library_id=acct.library_id, library_type=acct.library_type, api_key=acct.api_key,
            title=paper.title, doi=paper.doi, journal=paper.journal, year=paper.year,
            issn=paper.issn, authors=[{"name": a.name} for a in paper.authors],
            abstract=paper.abstract,
            summary_cn=paper.summary.summary_cn if paper.summary else None,
            innovation_points=paper.summary.innovation_points if paper.summary else None,
            limitations=paper.summary.limitations if paper.summary else None,
            fulltext_analysis=paper.fulltext_analysis.analysis if paper.fulltext_analysis else None,
            chat_messages=chat_msgs, collection_key=req.collection_key,
        )
        return ExportResponse(success=True, item_key=result["item_key"], message="成功导出到 Zotero")
    except Exception as e:
        logger.error(f"Zotero export failed: {e}")
        return ExportResponse(success=False, message=f"导出失败: {e}")
