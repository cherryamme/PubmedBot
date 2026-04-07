from pydantic import BaseModel


class ZoteroExportRequest(BaseModel):
    collection_key: str | None = None
    include_chat: bool = True


class ZoteroExportResponse(BaseModel):
    success: bool
    item_key: str | None = None
    message: str
