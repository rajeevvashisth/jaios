from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from app.api.routers import (
    agents,
    ai_providers,
    audit,
    auth,
    companies,
    compliance,
    finance,
    knowledge,
    memory,
    products,
    projects,
    reports,
    tasks,
    workflows,
    workspaces,
)
from app.core.logging import configure_logging, get_logger
from app.core.middleware import ObservabilityMiddleware
from app.db.session import SessionLocal
from app.orchestration.checkpoints import get_checkpointer, shutdown_checkpointer
from app.services.agent_service import sync_agent_definitions

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    db = SessionLocal()
    try:
        sync_agent_definitions(db)
        logger.info("agent_registry_synced")
    finally:
        db.close()

    # Must happen at startup, not lazily on first request: the checkpointer's
    # one-time setup() runs `CREATE INDEX CONCURRENTLY`, which blocks until
    # every other open transaction finishes. Triggering it lazily inside a
    # request whose own DB session is sitting idle-in-transaction (e.g.
    # start_workflow, after `db.refresh(run)`) self-deadlocks — the request
    # waits on setup(), setup() waits on the request's own idle transaction.
    # Discovered by actually running this against a real Postgres in Docker;
    # no test had exercised a real graph compilation before.
    get_checkpointer()
    logger.info("checkpointer_ready")

    yield
    shutdown_checkpointer()


def create_app() -> FastAPI:
    app = FastAPI(title="JAIOS API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ObservabilityMiddleware)

    for router in (
        workspaces,
        companies,
        products,
        projects,
        tasks,
        agents,
        workflows,
        memory,
        knowledge,
        audit,
        finance,
        compliance,
        reports,
        auth,
        ai_providers,
    ):
        app.include_router(router.router, prefix="/api")

    @app.get("/health")
    def health() -> dict:
        db_status = "ok"
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001 — any DB failure just marks the check degraded
            db_status = f"error: {exc}"
        finally:
            db.close()

        return {
            "status": "ok" if db_status == "ok" else "degraded",
            "checks": {"database": db_status},
        }

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
