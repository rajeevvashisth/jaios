from datetime import date

from app.models.company import Company
from app.models.finance import FinanceEntry
from app.models.product import Product
from app.services.finance_service import summarize_finances


def _make_company_and_product(db_session, name: str):
    company = Company(name=name)
    db_session.add(company)
    db_session.commit()
    product = Product(company_id=company.id, name=f"{name} Product")
    db_session.add(product)
    db_session.commit()
    return company, product


def test_summarize_finances_computes_revenue_expense_and_margin(db_session):
    company, product = _make_company_and_product(db_session, "Finance Co")

    db_session.add_all(
        [
            FinanceEntry(
                company_id=company.id,
                product_id=product.id,
                entry_type="revenue",
                category="subscriptions",
                amount_cents=500_00,
                occurred_on=date(2026, 1, 15),
            ),
            FinanceEntry(
                company_id=company.id,
                product_id=product.id,
                entry_type="revenue",
                category="one_time",
                amount_cents=100_00,
                occurred_on=date(2026, 1, 20),
            ),
            FinanceEntry(
                company_id=company.id,
                product_id=product.id,
                entry_type="expense",
                category="infra",
                amount_cents=150_00,
                occurred_on=date(2026, 1, 10),
            ),
        ]
    )
    db_session.commit()

    summary = summarize_finances(db_session, company_id=company.id)
    assert summary.revenue_cents == 600_00
    assert summary.expense_cents == 150_00
    assert summary.margin_cents == 450_00
    assert {c.category: c.amount_cents for c in summary.revenue_by_category} == {
        "subscriptions": 500_00,
        "one_time": 100_00,
    }


def test_summarize_finances_scopes_by_product(db_session):
    company, product_a = _make_company_and_product(db_session, "Scoped Co A")
    product_b = Product(company_id=company.id, name="Scoped Co B Product")
    db_session.add(product_b)
    db_session.commit()

    db_session.add_all(
        [
            FinanceEntry(
                company_id=company.id,
                product_id=product_a.id,
                entry_type="revenue",
                category="subscriptions",
                amount_cents=100_00,
                occurred_on=date(2026, 1, 1),
            ),
            FinanceEntry(
                company_id=company.id,
                product_id=product_b.id,
                entry_type="revenue",
                category="subscriptions",
                amount_cents=999_00,
                occurred_on=date(2026, 1, 1),
            ),
        ]
    )
    db_session.commit()

    summary = summarize_finances(db_session, company_id=company.id, product_id=product_a.id)
    assert summary.revenue_cents == 100_00


def test_summarize_finances_scopes_by_date_range(db_session):
    company, product = _make_company_and_product(db_session, "Date Range Co")

    db_session.add_all(
        [
            FinanceEntry(
                company_id=company.id,
                product_id=product.id,
                entry_type="revenue",
                category="subscriptions",
                amount_cents=100_00,
                occurred_on=date(2026, 1, 1),
            ),
            FinanceEntry(
                company_id=company.id,
                product_id=product.id,
                entry_type="revenue",
                category="subscriptions",
                amount_cents=200_00,
                occurred_on=date(2026, 6, 1),
            ),
        ]
    )
    db_session.commit()

    summary = summarize_finances(
        db_session, company_id=company.id, since=date(2026, 5, 1), until=date(2026, 12, 31)
    )
    assert summary.revenue_cents == 200_00


def test_summarize_finances_with_no_entries_returns_zeroed_summary(db_session):
    company = Company(name="Empty Finance Co")
    db_session.add(company)
    db_session.commit()

    summary = summarize_finances(db_session, company_id=company.id)
    assert summary.revenue_cents == 0
    assert summary.expense_cents == 0
    assert summary.margin_cents == 0
    assert summary.revenue_by_category == []
