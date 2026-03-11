import sqlite3
import sys

from config.settings import settings


MIGRATIONS = [
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        nome    TEXT    NOT NULL,
        email   TEXT    UNIQUE NOT NULL,
        senha   TEXT    NOT NULL,
        avatar  TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        nome        TEXT    NOT NULL,
        preco       REAL    NOT NULL CHECK(preco >= 0),
        estoque     INTEGER NOT NULL CHECK(estoque >= 0),
        imagem      TEXT    NOT NULL,
        descricao   TEXT,
        usuario_id  INTEGER NOT NULL,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_produtos_usuario ON produtos(usuario_id)
    """,
]

# Adiciona coluna descricao se não existir (migration para bancos já criados)
SAFE_MIGRATIONS = [
    "ALTER TABLE produtos ADD COLUMN descricao TEXT",
    "ALTER TABLE produtos ADD COLUMN imagem TEXT NOT NULL DEFAULT ''",
]


def init_db() -> None:
    conn = sqlite3.connect(settings.DATABASE_URL)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        for sql in MIGRATIONS:
            conn.execute(sql)
        # Migrations seguras — ignoram erro se coluna já existe
        for sql in SAFE_MIGRATIONS:
            try:
                conn.execute(sql)
            except Exception:
                pass
        conn.commit()
        print(f"✅ Banco '{settings.DATABASE_URL}' inicializado com sucesso.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao inicializar banco: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()