from app.schemas.compliance import ApplicabilityStatus
from app.services.compliance_framework import seed_india_llp_compliance_framework


def test_seed_creates_items_without_fabricating_due_dates(db_session, make_company):
    company = make_company("Framework Seed Co")

    created = seed_india_llp_compliance_framework(db_session, company_id=company.id)

    assert len(created) > 0
    for obligation in created:
        assert obligation.company_id == company.id
        # None of these are confirmed dates — see compliance_framework.py's
        # module docstring for why due_date must stay unset here.
        assert obligation.due_date is None


def test_seed_marks_blanket_llp_filings_as_applicable(db_session, make_company):
    company = make_company("Framework Applicable Co")

    created = seed_india_llp_compliance_framework(db_session, company_id=company.id)
    by_title = {o.title: o for o in created}

    assert by_title["LLP Annual Return (Form 11)"].applicability_status == "applicable"
    assert by_title["Statement of Account & Solvency (Form 8)"].applicability_status == "applicable"
    assert by_title["Income Tax Return (LLP)"].applicability_status == "applicable"


def test_seed_marks_conditional_items_as_review_pending(db_session, make_company):
    company = make_company("Framework Review Pending Co")

    created = seed_india_llp_compliance_framework(db_session, company_id=company.id)
    by_title = {o.title: o for o in created}

    assert by_title["GST registration & filings"].applicability_status == "review_pending"
    assert by_title["Tax audit applicability (Section 44AB)"].applicability_status == (
        ApplicabilityStatus.review_pending
    )
    assert by_title["TDS compliance"].applicability_status == "review_pending"
