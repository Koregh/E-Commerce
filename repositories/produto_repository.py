from abc import ABC, abstractmethod
from typing import List, Optional

from core.database.connection import get_db
from models.entities import Produto


class IProdutoRepository(ABC):
    @abstractmethod
    def adicionar(self, nome: str, preco: float, estoque: int, imagem: str, usuario_id: int, descricao: Optional[str] = None) -> None: ...

    @abstractmethod
    def listar_todos(self) -> List[Produto]: ...

    @abstractmethod
    def listar_por_usuario(self, usuario_id: int) -> List[Produto]: ...

    @abstractmethod
    def buscar_por_id(self, produto_id: int) -> Optional[Produto]: ...

    @abstractmethod
    def atualizar(self, produto_id: int, nome: str, preco: float, estoque: int, imagem: str, usuario_id: int, descricao: Optional[str] = None) -> None: ...

    @abstractmethod
    def deletar(self, produto_id: int, usuario_id: int) -> None: ...


class SQLiteProdutoRepository(IProdutoRepository):

    def _row_to_produto(self, row) -> Produto:
        d = dict(row)
        return Produto(
            id=d["id"],
            nome=d["nome"],
            preco=d["preco"],
            estoque=d["estoque"],
            imagem=d.get("imagem"),
            descricao=d.get("descricao"),
            usuario_id=d["usuario_id"],
        )

    def adicionar(self, nome: str, preco: float, estoque: int, imagem: str, usuario_id: int, descricao: Optional[str] = None) -> None:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO produtos (nome, preco, estoque, imagem, descricao, usuario_id) VALUES (?,?,?,?,?,?)",
                (nome, preco, estoque, imagem, descricao, usuario_id),
            )

    def listar_todos(self) -> List[Produto]:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT id, nome, preco, estoque, imagem, descricao, usuario_id FROM produtos"
            ).fetchall()
        return [self._row_to_produto(r) for r in rows]

    def listar_por_usuario(self, usuario_id: int) -> List[Produto]:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT id, nome, preco, estoque, imagem, descricao, usuario_id FROM produtos WHERE usuario_id = ?",
                (usuario_id,),
            ).fetchall()
        return [self._row_to_produto(r) for r in rows]

    def buscar_por_id(self, produto_id: int) -> Optional[Produto]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT id, nome, preco, estoque, imagem, descricao, usuario_id FROM produtos WHERE id = ?",
                (produto_id,),
            ).fetchone()
        return self._row_to_produto(row) if row else None

    def atualizar(self, produto_id: int, nome: str, preco: float, estoque: int, imagem: str, usuario_id: int, descricao: Optional[str] = None) -> None:
        with get_db() as conn:
            conn.execute(
                "UPDATE produtos SET nome=?, preco=?, estoque=?, imagem=?, descricao=? WHERE id=? AND usuario_id=?",
                (nome, preco, estoque, imagem, descricao, produto_id, usuario_id),
            )

    def deletar(self, produto_id: int, usuario_id: int) -> None:
        with get_db() as conn:
            conn.execute(
                "DELETE FROM produtos WHERE id=? AND usuario_id=?",
                (produto_id, usuario_id),
            )


produto_repository: IProdutoRepository = SQLiteProdutoRepository()