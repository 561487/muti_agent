"""
Checkpoint manager — provides the appropriate LangGraph checkpointer
based on environment configuration.

Supports: memory (default), sqlite, and postgres backends.
"""

from langgraph.checkpoint.memory import InMemorySaver

from contelix.config import CHECKPOINT_BACKEND, CHECKPOINT_DB_PATH


def get_checkpointer():
    """
    Return a checkpointer instance based on CONTELIX_CHECKPOINT_BACKEND.

    - ``memory``: In-memory saver (default, no persistence across restarts).
    - ``sqlite``: SQLite-backed saver for local persistence (requires
      ``langgraph-checkpoint-sqlite`` package).
    - ``postgres``: PostgreSQL-backed saver for production (requires
      ``langgraph-checkpoint-postgres`` package).

    Returns:
        A LangGraph checkpointer instance.
    """
    if CHECKPOINT_BACKEND == "sqlite":
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
        except ImportError:
            raise ImportError(
                "langgraph-checkpoint-sqlite is required for SQLite checkpointing. "
                "Install it with: pip install langgraph-checkpoint-sqlite"
            )
        db_path = CHECKPOINT_DB_PATH or "contelix_checkpoints.db"
        return SqliteSaver.from_conn_string(db_path)

    elif CHECKPOINT_BACKEND == "postgres":
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
        except ImportError:
            raise ImportError(
                "langgraph-checkpoint-postgres is required for PostgreSQL "
                "checkpointing. Install it with: pip install langgraph-checkpoint-postgres"
            )
        db_uri = CHECKPOINT_DB_PATH
        if not db_uri:
            raise ValueError(
                "CONTELIX_CHECKPOINT_DB_PATH must be set to a PostgreSQL "
                "connection string when using postgres backend."
            )
        return PostgresSaver.from_conn_string(db_uri)

    else:
        # Default: in-memory (no persistence across restarts)
        return InMemorySaver()
