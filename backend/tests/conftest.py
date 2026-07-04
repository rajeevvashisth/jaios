import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.db.base import Base
from app.models import *  # noqa: F401,F403 — populate metadata
from app.models.company import Company
from app.models.workspace import Workspace
from app.services.agent_service import sync_agent_definitions


@pytest.fixture(scope="session")
def _engine():
    """A real Postgres+pgvector connection is required for model/DB tests
    (SQLite can't represent the ``Vector`` column type). Skip this whole
    class of test when no local Postgres is reachable, e.g. before
    ``docker compose up -d postgres`` has been run."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Postgres not reachable for DB-backed tests: {exc}")

    Base.metadata.create_all(engine)

    # tasks.assignee_agent_key / memory_records.agent_key FK into
    # agent_definitions — seed it here the same way app startup does, so
    # tests that assign an agent to a task don't hit a FK violation.
    seed_session = sessionmaker(bind=engine)()
    try:
        sync_agent_definitions(seed_session)
    finally:
        seed_session.close()

    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session(_engine):
    session = sessionmaker(bind=_engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def make_company(db_session):
    """Every company now requires a workspace_id (the multi-tenant top
    level — see models/workspace.py). Most tests don't care about the
    workspace itself, just that a valid company exists, so this creates
    a throwaway workspace named after the company and returns the
    persisted ``Company`` — a one-line replacement for the old
    ``Company(name=...); db_session.add(...); db_session.commit()``."""

    def _make(name: str, **kwargs) -> Company:
        workspace = Workspace(name=f"{name} Workspace")
        db_session.add(workspace)
        db_session.commit()
        company = Company(name=name, workspace_id=workspace.id, **kwargs)
        db_session.add(company)
        db_session.commit()
        return company

    return _make


@pytest.fixture()
def client(_engine):
    """A FastAPI TestClient with the app's real lifespan (agent registry
    sync, etc.) run against the same Postgres as ``db_session`` — depends
    on ``_engine`` so it inherits the same skip-when-unreachable behavior."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
