from datetime import date, timedelta

from app.models.compliance import ComplianceObligation
from app.schemas.compliance import ComplianceObligationUpdate, ComplianceUrgency, FilingStatus
from app.services.compliance_service import (
    compute_urgency,
    list_obligations,
    mark_completed,
    update_obligation,
)

TODAY = date(2026, 7, 3)


def _obligation(**overrides) -> ComplianceObligation:
    defaults = dict(
        company_id="c1",
        title="File GST return",
        category="tax",
        due_date=TODAY + timedelta(days=30),
        completed=False,
    )
    defaults.update(overrides)
    return ComplianceObligation(**defaults)


def test_compute_urgency_overdue():
    obligation = _obligation(due_date=TODAY - timedelta(days=1))
    assert compute_urgency(obligation, today=TODAY) == ComplianceUrgency.overdue


def test_compute_urgency_due_soon():
    obligation = _obligation(due_date=TODAY + timedelta(days=7))
    assert compute_urgency(obligation, today=TODAY) == ComplianceUrgency.due_soon


def test_compute_urgency_upcoming():
    obligation = _obligation(due_date=TODAY + timedelta(days=90))
    assert compute_urgency(obligation, today=TODAY) == ComplianceUrgency.upcoming


def test_compute_urgency_completed_overrides_due_date():
    obligation = _obligation(due_date=TODAY - timedelta(days=30), completed=True)
    assert compute_urgency(obligation, today=TODAY) == ComplianceUrgency.completed


def test_compute_urgency_due_date_exactly_at_window_boundary_is_due_soon():
    from app.services.compliance_service import DUE_SOON_WINDOW_DAYS

    obligation = _obligation(due_date=TODAY + timedelta(days=DUE_SOON_WINDOW_DAYS))
    assert compute_urgency(obligation, today=TODAY) == ComplianceUrgency.due_soon


def test_compute_urgency_no_due_date_is_review_pending():
    obligation = _obligation(due_date=None)
    assert compute_urgency(obligation, today=TODAY) == ComplianceUrgency.review_pending


def test_compute_urgency_not_applicable_reads_as_completed():
    obligation = _obligation(due_date=None, applicability_status="not_applicable")
    assert compute_urgency(obligation, today=TODAY) == ComplianceUrgency.completed


def test_list_obligations_excludes_completed_by_default(db_session, make_company):
    company = make_company("Compliance Co")

    db_session.add_all(
        [
            ComplianceObligation(
                company_id=company.id, title="Open one", category="tax", due_date=date(2026, 8, 1)
            ),
            ComplianceObligation(
                company_id=company.id,
                title="Done one",
                category="tax",
                due_date=date(2026, 1, 1),
                completed=True,
            ),
        ]
    )
    db_session.commit()

    results = list_obligations(db_session, company_id=company.id)
    assert [r.title for r in results] == ["Open one"]

    all_results = list_obligations(db_session, company_id=company.id, include_completed=True)
    assert {r.title for r in all_results} == {"Open one", "Done one"}


def test_mark_completed_sets_completed_and_timestamp(db_session, make_company):
    company = make_company("Complete Co")

    obligation = ComplianceObligation(
        company_id=company.id,
        title="Renew trademark",
        category="trademark",
        due_date=date(2026, 9, 1),
    )
    db_session.add(obligation)
    db_session.commit()

    result = mark_completed(db_session, obligation_id=obligation.id)
    assert result.completed is True
    assert result.completed_at is not None
    assert result.urgency == ComplianceUrgency.completed


def test_create_obligation_defaults_to_review_pending_when_persisted(db_session, make_company):
    """Unlike the in-memory ``_obligation()`` helper above, a row that's
    actually inserted picks up the model's column defaults."""
    company = make_company("Default Status Co")

    obligation = ComplianceObligation(
        company_id=company.id, title="GST filing", category="tax", due_date=None
    )
    db_session.add(obligation)
    db_session.commit()
    db_session.refresh(obligation)

    assert obligation.applicability_status == "review_pending"
    assert obligation.filing_status == "draft"


def test_update_obligation_applies_partial_changes(db_session, make_company):
    company = make_company("Update Obligation Co")

    obligation = ComplianceObligation(
        company_id=company.id, title="GST filing", category="tax", due_date=None
    )
    db_session.add(obligation)
    db_session.commit()

    result = update_obligation(
        db_session,
        obligation_id=obligation.id,
        updates=ComplianceObligationUpdate(
            applicability_status="applicable",
            filing_status=FilingStatus.awaiting_ca_vendor,
            external_owner="ABC & Co, Chartered Accountants",
            required_documents=[{"name": "Sales register", "obtained": True}],
        ),
    )

    assert result.applicability_status == "applicable"
    assert result.filing_status == FilingStatus.awaiting_ca_vendor
    assert result.external_owner == "ABC & Co, Chartered Accountants"
    assert result.required_documents[0].name == "Sales register"
    assert result.required_documents[0].obtained is True
    # not yet in a terminal filing status -> completed must stay false
    assert result.completed is False


def test_update_obligation_to_filed_marks_completed(db_session, make_company):
    company = make_company("Filed Obligation Co")

    obligation = ComplianceObligation(
        company_id=company.id, title="Form 11", category="corporate", due_date=None
    )
    db_session.add(obligation)
    db_session.commit()

    result = update_obligation(
        db_session,
        obligation_id=obligation.id,
        updates=ComplianceObligationUpdate(
            filing_status=FilingStatus.filed,
            proof_reference={"srn": "ABC1234567"},
        ),
    )

    assert result.filing_status == FilingStatus.filed
    assert result.completed is True
    assert result.completed_at is not None
    assert result.proof_reference == {"srn": "ABC1234567"}
