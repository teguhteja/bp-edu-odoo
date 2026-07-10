# Part of the EH AI Suite by ERP Heritage.
"""Detect the PostgreSQL pgvector extension without ever failing an install.

Unlike the Enterprise engine, which hard-fails its install when pgvector is
absent, this engine treats pgvector as an optional accelerator. If it is not
present, the in-database cosine store is used instead.
"""
import logging

_logger = logging.getLogger(__name__)


def is_pgvector_available(env):
    """Return True if the ``vector`` extension exists or can be created."""
    cr = env.cr
    cr.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
    if cr.fetchone():
        return True
    # Try to create it inside a savepoint so a failure (no superuser, binaries
    # missing) leaves the transaction usable.
    try:
        with cr.savepoint():
            cr.execute("CREATE EXTENSION IF NOT EXISTS vector")
        return True
    except Exception as error:  # noqa: BLE001 - absence is an expected outcome
        _logger.info("EH AI: pgvector not available, using in-DB cosine store (%s)", error)
        return False
