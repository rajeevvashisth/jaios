from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.knowledge.ingest import ingest_document
from app.knowledge.retrieval import search_knowledge
from app.schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentRead,
    KnowledgeSearchRequest,
    KnowledgeSearchResult,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/documents", response_model=KnowledgeDocumentRead)
def create_document(payload: KnowledgeDocumentCreate, db: Session = Depends(get_db)):
    return ingest_document(
        db,
        company_id=payload.company_id,
        title=payload.title,
        source_type=payload.source_type,
        content=payload.content,
        source_uri=payload.source_uri,
    )


@router.post("/search", response_model=list[KnowledgeSearchResult])
def search(payload: KnowledgeSearchRequest, db: Session = Depends(get_db)):
    return search_knowledge(
        db, company_id=payload.company_id, query=payload.query, top_k=payload.top_k
    )
