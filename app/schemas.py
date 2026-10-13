from pydantic import BaseModel, Field
from typing import Literal

class IngestResponse(BaseModel):
    filename: str
    chunks_indexed: int
    document_id: str

class Evidence(BaseModel):
    source: str
    excerpt: str
    score: float

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=10)

class AskResponse(BaseModel):
    answer: str
    abstained: bool
    evidence: list[Evidence]
    retrieval_count: int
    status: Literal["answered", "insufficient_evidence"]
