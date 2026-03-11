from abc import ABC, abstractmethod
from typing import Optional

from core.database.connection import get_db
from models.entities import Usuario


class IUsuarioRepository(ABC):
    @abstractmethod
    def criar(self, nome: str, email: str, senha_hash: str, avatar: Optional[str] = None) -> None: ...

    @abstractmethod
    def buscar_por_email(self, email: str) -> Optional[Usuario]: ...

    @abstractmethod
    def buscar_por_id(self, usuario_id: int) -> Optional[Usuario]: ...

    @abstractmethod
    def atualizar(self, usuario_id: int, nome: str, email: str, senha: str, avatar: Optional[str]) -> None: ...

    @abstractmethod
    def deletar(self, usuario_id: int) -> None: ...


class SQLiteUsuarioRepository(IUsuarioRepository):

    def criar(self, nome: str, email: str, senha_hash: str, avatar: Optional[str] = None) -> None:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO usuarios (nome, email, senha, avatar) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, avatar),
            )

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT id, nome, email, senha, avatar FROM usuarios WHERE email = ?",
                (email,),
            ).fetchone()
        return Usuario(**dict(row)) if row else None

    def buscar_por_id(self, usuario_id: int) -> Optional[Usuario]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT id, nome, email, senha, avatar FROM usuarios WHERE id = ?",
                (usuario_id,),
            ).fetchone()
        return Usuario(**dict(row)) if row else None

    def atualizar(self, usuario_id: int, nome: str, email: str, senha: str, avatar: Optional[str]) -> None:
        with get_db() as conn:
            conn.execute(
                "UPDATE usuarios SET nome=?, email=?, senha=?, avatar=? WHERE id=?",
                (nome, email, senha, avatar, usuario_id),
            )

    def deletar(self, usuario_id: int) -> None:
        with get_db() as conn:
            conn.execute("DELETE FROM usuarios WHERE id=?", (usuario_id,))


# Instância padrão
usuario_repository: IUsuarioRepository = SQLiteUsuarioRepository()
