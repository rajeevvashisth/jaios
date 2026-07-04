"""Seeds the standard compliance checklist for an Indian LLP.

This is deliberately NOT a set of confirmed, dated obligations — it's a
starting checklist of categories that commonly apply to an Indian LLP,
seeded with honest ``applicability_status``:

- Two items (LLP Annual Return / Form 11, and Statement of Account &
  Solvency / Form 8) are blanket statutory requirements for every LLP
  regardless of turnover or activity, so those are seeded
  ``applicable`` — but still with ``due_date=None``, because the exact due
  date depends on the LLP's financial year and incorporation date, which
  this system doesn't know. The well-known statutory windows are noted in
  ``notes`` for reference, not written into ``due_date`` as if confirmed.
- Everything else (GST, tax audit, TDS, trademark, state/local
  registrations) depends on facts this system has no way to know
  (turnover, employee count, physical office, whether a filing already
  exists) — those are seeded ``review_pending`` and must not be treated as
  active obligations until a human (ideally with a CA) confirms them.

Nothing here is a substitute for actual professional advice — it's a
tracking scaffold, not a compliance engine.
"""

from sqlalchemy.orm import Session

from app.models.compliance import ComplianceObligation

_INDIA_LLP_FRAMEWORK: list[dict] = [
    {
        "title": "LLP Annual Return (Form 11)",
        "category": "corporate",
        "jurisdiction_level": "mca_roc",
        "governing_authority": "Ministry of Corporate Affairs (MCA) / Registrar of Companies (ROC)",
        "recurrence": "annual",
        "applicability_status": "applicable",
        "filing_status": "applicability_review_pending",
        "required_documents": [
            {"name": "List of partners and contribution details", "obtained": False}
        ],
        "notes": (
            "Statutory for every LLP regardless of turnover. Typically due within 60 days of "
            "financial year end (commonly by 30 May for a March FY-end) — confirm exact due date "
            "for the current FY with your CA before treating a date as fixed."
        ),
    },
    {
        "title": "Statement of Account & Solvency (Form 8)",
        "category": "corporate",
        "jurisdiction_level": "mca_roc",
        "governing_authority": "Ministry of Corporate Affairs (MCA) / Registrar of Companies (ROC)",
        "recurrence": "annual",
        "applicability_status": "applicable",
        "filing_status": "applicability_review_pending",
        "required_documents": [
            {"name": "Statement of Account and Solvency", "obtained": False},
            {"name": "Financial statements for the FY", "obtained": False},
        ],
        "notes": (
            "Statutory for every LLP regardless of turnover. Typically due within 30 days of "
            "6 months from FY end (commonly by 30 Oct for a March FY-end) — confirm exact due date "
            "for the current FY with your CA before treating a date as fixed."
        ),
    },
    {
        "title": "Income Tax Return (LLP)",
        "category": "tax",
        "jurisdiction_level": "income_tax",
        "governing_authority": "Income Tax Department",
        "recurrence": "annual",
        "applicability_status": "applicable",
        "filing_status": "applicability_review_pending",
        "required_documents": [
            {"name": "Profit & Loss statement", "obtained": False},
            {"name": "Balance sheet", "obtained": False},
            {"name": "Bank statements", "obtained": False},
        ],
        "notes": (
            "Statutory for every LLP regardless of profit/loss. Due date depends on whether a tax "
            "audit applies (31 July if not audit-liable, 31 Oct if audit-liable) — confirm "
            "applicability and exact due date with your CA."
        ),
    },
    {
        "title": "Tax audit applicability (Section 44AB)",
        "category": "tax",
        "jurisdiction_level": "income_tax",
        "governing_authority": "Income Tax Department",
        "recurrence": "annual",
        "applicability_status": "review_pending",
        "filing_status": "applicability_review_pending",
        "notes": (
            "Depends on annual turnover crossing the prescribed threshold — confirm once known."
        ),
    },
    {
        "title": "GST registration & filings",
        "category": "tax",
        "jurisdiction_level": "gst",
        "governing_authority": "GST Department",
        "recurrence": "monthly",
        "applicability_status": "review_pending",
        "filing_status": "applicability_review_pending",
        "notes": (
            "Depends on turnover crossing the registration threshold, or voluntary "
            "registration — confirm current GST registration status and, if registered, "
            "the filing cadence (GSTR-1/3B)."
        ),
    },
    {
        "title": "TDS compliance",
        "category": "tax",
        "jurisdiction_level": "income_tax",
        "governing_authority": "Income Tax Department",
        "recurrence": "quarterly",
        "applicability_status": "review_pending",
        "filing_status": "applicability_review_pending",
        "notes": (
            "Applicable only if there are payments subject to TDS (salaries above threshold, "
            "contractor/professional payments above threshold, rent, etc.) — confirm applicability."
        ),
    },
    {
        "title": "LLP agreement / partner or contribution changes",
        "category": "corporate",
        "jurisdiction_level": "mca_roc",
        "governing_authority": "Ministry of Corporate Affairs (MCA) / Registrar of Companies (ROC)",
        "recurrence": "event_based",
        "applicability_status": "applicable",
        "filing_status": "not_applicable",
        "notes": (
            "Event-triggered, not a standing due date: Form 3/4 must be filed within 30 "
            "days of any change to the LLP agreement, partners, or capital contribution. "
            "Currently no known pending event — revisit if partners, contribution, or the "
            "registered office changes."
        ),
    },
    {
        "title": "Trademark registration — brand/product names",
        "category": "trademark",
        "jurisdiction_level": "other",
        "governing_authority": "Trade Marks Registry (India)",
        "recurrence": "one_time",
        "applicability_status": "review_pending",
        "filing_status": "applicability_review_pending",
        "notes": (
            "Confirm whether a trademark application for the company or product brand "
            "names already exists or is planned."
        ),
    },
    {
        "title": "Delhi / local establishment registrations",
        "category": "legal",
        "jurisdiction_level": "delhi_local",
        "governing_authority": "Delhi state / local authority",
        "recurrence": "one_time",
        "applicability_status": "review_pending",
        "filing_status": "applicability_review_pending",
        "notes": (
            "e.g. Shops & Establishment registration, professional tax — applicability depends on "
            "having a physical office and/or employees in Delhi. Confirm before treating as active."
        ),
    },
]


def seed_india_llp_compliance_framework(
    db: Session, *, company_id: str
) -> list[ComplianceObligation]:
    """Insert the standard India-LLP compliance checklist for a company.
    Safe to call once per company — does not check for existing duplicates,
    so callers should only invoke this on a company that hasn't been seeded
    yet (or accept duplicates as a known tradeoff of re-running it)."""
    created = []
    for item in _INDIA_LLP_FRAMEWORK:
        obligation = ComplianceObligation(company_id=company_id, **item)
        db.add(obligation)
        created.append(obligation)
    db.commit()
    for obligation in created:
        db.refresh(obligation)
    return created
