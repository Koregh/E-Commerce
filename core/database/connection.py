import sqlite3
from contextlib import contextmanager
from typing import Generator

from config.settings import settings


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DATABASE_URL)
    conn.row_factory = sqlite3.Row  # acesso por nome da coluna
    conn.execute("PRAGMA journal_mode=WAL")   # melhor concorrência
    conn.execute("PRAGMA foreign_keys=ON")    # enforce FK constraints
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager para conexão com SQLite.
    Garante commit em sucesso e rollback em exceção.
    """
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
