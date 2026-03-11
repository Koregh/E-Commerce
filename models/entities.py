from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Usuario:
    id: Optional[int]
    nome: str
    email: str
    senha: str
    avatar: Optional[str] = None


@dataclass
class Produto:
    id: Optional[int]
    nome: str
    preco: float
    estoque: int
    usuario_id: int
    imagem: Optional[str] = None
    descricao: Optional[str] = None


@dataclass
class ItemCarrinho:
    produto_id: int
    nome: str
    preco: float
    imagem: Optional[str]
    quantidade: int = 1

    @property
    def subtotal(self) -> float:
        return round(self.preco * self.quantidade, 2)


@dataclass
class Carrinho:
    itens: List[ItemCarrinho] = field(default_factory=list)

    @property
    def total(self) -> float:
        return round(sum(i.subtotal for i in self.itens), 2)

    @property
    def quantidade_total(self) -> int:
        return sum(i.quantidade for i in self.itens)
