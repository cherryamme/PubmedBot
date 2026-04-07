from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="检索关键词")
    min_year: int | None = Field(None, description="最早年份")
    max_year: int | None = Field(None, description="最晚年份")
    min_impact_factor: float | None = Field(None, ge=0, description="最低影响因子")
    max_results: int = Field(50, ge=1, le=200, description="最大结果数")
