from sqlalchemy.orm import Session

from app.memory.embeddings import embed_text
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Fixed-size character chunking with overlap.

    Good enough for Phase 1's markdown/text/SOP documents; swap for a
    structure-aware splitter later if PDF/DOCX layouts need it — the
    ingestion call site (``ingest_document``) doesn't change either way.
    """
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def ingest_document(
    db: Session,
    *,
    company_id: str,
    title: str,
    source_type: str,
    content: str,
    source_uri: str | None = None,
) -> KnowledgeDocument:
    document = KnowledgeDocument(
        company_id=company_id, title=title, source_type=source_type, source_uri=source_uri
    )
    db.add(document)
    db.flush()  # assign document.id before creating chunks

    for index, chunk in enumerate(chunk_text(content)):
        db.add(
            KnowledgeChunk(
                document_id=document.id,
                chunk_index=index,
                content=chunk,
                embedding=embed_text(chunk),
            )
        )

    db.commit()
    db.refresh(document)
    return document
