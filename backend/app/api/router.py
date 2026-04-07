"""Master API router."""

from fastapi import APIRouter

from . import search, papers, summary, chat, zotero, config_routes

api_router = APIRouter()
api_router.include_router(search.router)
api_router.include_router(papers.router)
api_router.include_router(summary.router)
api_router.include_router(chat.router)
api_router.include_router(zotero.router)
api_router.include_router(config_routes.router)
