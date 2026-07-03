from app.knowledge.ingest import chunk_text, ingest_document
from app.knowledge.retrieval import search_knowledge
from app.models.company import Company


def test_chunk_text_produces_overlapping_chunks():
    text = "a" * 2000
    chunks = chunk_text(text, chunk_size=800, overlap=100)
    assert len(chunks) == 3
    assert chunks[0][-100:] == chunks[1][:100]


def test_ingest_and_search_round_trip(db_session):
    company = Company(name="Knowledge Co")
    db_session.add(company)
    db_session.commit()

    ingest_document(
        db_session,
        company_id=company.id,
        title="Onboarding SOP",
        source_type="markdown",
        content="New engineers should set up their local dev environment first, "
        "then read the architecture doc, then pick up a starter task.",
    )

    results = search_knowledge(db_session, company_id=company.id, query="dev environment setup")
    assert len(results) >= 1
    assert results[0].document_title == "Onboarding SOP"


def test_search_is_scoped_to_company(db_session):
    company_a = Company(name="Company A")
    company_b = Company(name="Company B")
    db_session.add_all([company_a, company_b])
    db_session.commit()

    ingest_document(
        db_session,
        company_id=company_a.id,
        title="Company A doc",
        source_type="text",
        content="This document only belongs to company A.",
    )

    results = search_knowledge(db_session, company_id=company_b.id, query="company A doc")
    assert all(r.document_title != "Company A doc" for r in results)
