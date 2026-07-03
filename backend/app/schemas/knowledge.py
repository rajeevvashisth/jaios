from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KnowledgeDocumentCreate(BaseModel):
    company_id: str
    title: str
    source_type: str  # markdown|text|pdf|docx
    content: str  # raw text content to chunk + embed
    source_uri: str | None = None


class KnowledgeDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    title: str
    source_type: str
    source_uri: str | None
    ingested_at: datetime


class KnowledgeSearchRequest(BaseModel):
    company_id: str
    query: str
    top_k: int = 5


class KnowledgeSearchResult(BaseModel):
    document_id: str
    document_title: str
    chunk_index: int
    content: str
    score: float
