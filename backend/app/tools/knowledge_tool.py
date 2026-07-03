from typing import Any

from sqlalchemy.orm import Session

from app.tools.base import Tool, ToolResult


class KnowledgeSearchTool(Tool):
    """Semantic search over the company knowledge base (pgvector).

    Imports ``app.knowledge.retrieval`` lazily inside ``run`` to avoid a
    import cycle (knowledge -> db/models, tools -> agents -> ... -> tools).
    """

    key = "knowledge_search"
    description = "Search company knowledge (docs, SOPs, contracts) for relevant passages."

    def run(self, action: str, **kwargs: Any) -> ToolResult:
        if action != "search":
            return ToolResult(success=False, output=f"Unknown knowledge action: {action}")

        from app.knowledge.retrieval import search_knowledge

        db: Session = kwargs["db"]
        company_id: str = kwargs["company_id"]
        query: str = kwargs["query"]
        top_k: int = kwargs.get("top_k", 5)

        results = search_knowledge(db, company_id=company_id, query=query, top_k=top_k)
        summary = "\n\n".join(f"[{r.document_title} #{r.chunk_index}] {r.content}" for r in results)
        return ToolResult(
            success=True,
            output=summary or "No matching knowledge found.",
            data={"results": [r.model_dump() for r in results]},
        )
