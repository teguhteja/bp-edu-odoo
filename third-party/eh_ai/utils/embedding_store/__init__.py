# Part of the EH AI Suite by ERP Heritage.
from .base import EmbeddingStore
from .indb import InDbCosineStore
from .pgvector_store import PgVectorStore


def get_embedding_store(env):
    """Resolve the embedding store backend for this database.

    Controlled by the ``eh_ai.embedding_store`` system parameter:
    ``auto`` (default) uses pgvector when available and the in-DB cosine store
    otherwise; ``pgvector`` or ``indb`` force a specific backend.
    """
    mode = env["ir.config_parameter"].sudo().get_param("eh_ai.embedding_store", "auto")
    if mode == "indb":
        return InDbCosineStore(env)
    if mode == "pgvector":
        return PgVectorStore(env)
    pg = PgVectorStore(env)
    return pg if pg.available else InDbCosineStore(env)
