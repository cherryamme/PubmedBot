"""Runtime configuration endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from ..config import settings

router = APIRouter(prefix="/api/config", tags=["config"])


class ConfigResponse(BaseModel):
    ncbi_email: str
    ncbi_api_key_set: bool
    easyscholar_key_set: bool
    llm_base_url: str
    llm_model: str
    llm_api_key_set: bool
    unpaywall_email: str


class ConfigUpdate(BaseModel):
    ncbi_email: str | None = None
    ncbi_api_key: str | None = None
    easyscholar_secret_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    unpaywall_email: str | None = None


@router.get("", response_model=ConfigResponse)
async def get_config():
    return ConfigResponse(
        ncbi_email=settings.ncbi_email,
        ncbi_api_key_set=bool(settings.ncbi_api_key),
        easyscholar_key_set=bool(settings.easyscholar_secret_key),
        llm_base_url=settings.llm_base_url,
        llm_model=settings.llm_model,
        llm_api_key_set=bool(settings.llm_api_key),
        unpaywall_email=settings.unpaywall_email,
    )


@router.put("", response_model=ConfigResponse)
async def update_config(update: ConfigUpdate):
    if update.ncbi_email is not None:
        settings.ncbi_email = update.ncbi_email
    if update.ncbi_api_key is not None:
        settings.ncbi_api_key = update.ncbi_api_key
    if update.easyscholar_secret_key is not None:
        settings.easyscholar_secret_key = update.easyscholar_secret_key
    if update.llm_base_url is not None:
        settings.llm_base_url = update.llm_base_url
    if update.llm_model is not None:
        settings.llm_model = update.llm_model
    if update.llm_api_key is not None:
        settings.llm_api_key = update.llm_api_key
    if update.unpaywall_email is not None:
        settings.unpaywall_email = update.unpaywall_email
    return await get_config()
