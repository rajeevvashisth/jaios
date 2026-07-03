from contextlib import ExitStack

from langgraph.checkpoint.postgres import PostgresSaver

from app.config import get_settings

_exit_stack = ExitStack()
_checkpointer: PostgresSaver | None = None


def _to_psycopg_dsn(sqlalchemy_url: str) -> str:
    """``langgraph-checkpoint-postgres`` opens its own psycopg connection and
    expects a plain ``postgresql://`` DSN, not SQLAlchemy's
    ``postgresql+psycopg://`` driver-qualified form."""
    return sqlalchemy_url.replace("postgresql+psycopg://", "postgresql://")


def get_checkpointer() -> PostgresSaver:
    """Return the process-wide LangGraph checkpointer, opening it (and
    running its one-time ``setup()``) on first use. Kept open for the
    process lifetime via a module-level ExitStack — closed by
    ``shutdown_checkpointer()`` on app shutdown.
    """
    global _checkpointer
    if _checkpointer is None:
        settings = get_settings()
        dsn = _to_psycopg_dsn(settings.database_url)
        _checkpointer = _exit_stack.enter_context(PostgresSaver.from_conn_string(dsn))
        _checkpointer.setup()
    return _checkpointer


def shutdown_checkpointer() -> None:
    global _checkpointer
    _exit_stack.close()
    _checkpointer = None
