from sqlalchemy import select
from sqlalchemy.orm import Session

from app.memory.embeddings import embed_text
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.schemas.knowledge import KnowledgeSearchResult


def search_knowledge(
    db: Session, *, company_id: str, query: str, top_k: int = 5
) -> list[KnowledgeSearchResult]:
    """Semantic search over a company's ingested knowledge via pgvector
    cosine distance, permission-scoped to ``company_id`` at the query level
    so an agent can never retrieve another company's documents."""
    query_embedding = embed_text(query)

    stmt = (
        select(
            KnowledgeChunk,
            KnowledgeDocument.title,
            KnowledgeChunk.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .where(KnowledgeDocument.company_id == company_id)
        .order_by("distance")
        .limit(top_k)
    )

    results = []
    for chunk, document_title, distance in db.execute(stmt).all():
        results.append(
            KnowledgeSearchResult(
                document_id=chunk.document_id,
                document_title=document_title,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=1.0 - float(distance),
            )
        )
    return results
