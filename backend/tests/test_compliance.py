from datetime import date, timedelta

from app.models.company import Company
from app.models.compliance import ComplianceObligation
from app.schemas.compliance import ComplianceUrgency
from app.services.compliance_service import compute_urgency, list_obligations, mark_completed

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


def test_list_obligations_excludes_completed_by_default(db_session):
    company = Company(name="Compliance Co")
    db_session.add(company)
    db_session.commit()

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


def test_mark_completed_sets_completed_and_timestamp(db_session):
    company = Company(name="Complete Co")
    db_session.add(company)
    db_session.commit()

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
