from pydantic import BaseModel


class SummarizeRequest(BaseModel):
    pass  # paper_id comes from URL path


class SummarizeResponse(BaseModel):
    paper_id: int
    summary_en: str
    summary_cn: str
    innovation_points: str
    limitations: str
    model_used: str
