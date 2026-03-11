"""
CarrinhoService — carrinho server-side via sessão Flask.

Decisão de design: carrinho na sessão (não no Redis diretamente)
porque já temos sessão Redis. Simples, sem estado extra,
e correto para portfólio sem checkout real.
"""

from typing import Dict
from flask import session

from core.exceptions.domain import NotFoundError, ValidationError
from models.entities import Carrinho, ItemCarrinho
from repositories.produto_repository import IProdutoRepository, produto_repository

_SESSION_KEY = "carrinho"


class CarrinhoService:

    def __init__(self, repo: IProdutoRepository):
        self._repo = repo

    # ── helpers internos ──────────────────────────────────────────

    def _load(self) -> Dict[str, dict]:
        """Retorna o dict bruto do carrinho da sessão."""
        carrinho = session.get(_SESSION_KEY)

        if not isinstance(carrinho, dict):
            carrinho = {}

        return carrinho

    def _save(self, data: Dict[str, dict]) -> None:
        """Salva o carrinho na sessão."""
        session[_SESSION_KEY] = data
        session.modified = True

    # ── API pública ───────────────────────────────────────────────

    def adicionar(self, produto_id: int, quantidade: int = 1) -> None:

        quantidade = int(quantidade)

        if quantidade < 1:
            raise ValidationError("Quantidade deve ser ao menos 1.")

        produto = self._repo.buscar_por_id(produto_id)

        if not produto:
            raise NotFoundError("Produto não encontrado.")

        if produto.estoque < 1:
            raise ValidationError("Produto sem estoque disponível.")

        carrinho = self._load()
        chave = str(produto_id)

        qtd_atual = carrinho.get(chave, {}).get("quantidade", 0)
        nova_qtd = qtd_atual + quantidade

        # limita ao estoque
        nova_qtd = min(nova_qtd, produto.estoque)

        carrinho[chave] = {
            "produto_id": produto_id,
            "nome": produto.nome,
            "preco": produto.preco,
            "imagem": produto.imagem,
            "quantidade": nova_qtd,
        }

        self._save(carrinho)

    def remover(self, produto_id: int) -> None:

        carrinho = self._load()
        chave = str(produto_id)

        if chave in carrinho:
            del carrinho[chave]

        self._save(carrinho)

    def atualizar_quantidade(self, produto_id: int, quantidade: int) -> None:

        quantidade = int(quantidade)

        if quantidade < 1:
            self.remover(produto_id)
            return

        produto = self._repo.buscar_por_id(produto_id)

        if not produto:
            raise NotFoundError("Produto não encontrado.")

        carrinho = self._load()
        chave = str(produto_id)

        if chave not in carrinho:
            raise NotFoundError("Item não está no carrinho.")

        carrinho[chave]["quantidade"] = min(quantidade, produto.estoque)

        self._save(carrinho)

    def limpar(self) -> None:
        session.pop(_SESSION_KEY, None)
        session.modified = True

    def obter(self) -> Carrinho:

     raw = self._load()

     itens = []
     carrinho_limpo = {}
 
     for k, v in raw.items():
        try:
            produto = produto_repository.buscar_por_id(v["produto_id"])

            item = ItemCarrinho(
                produto_id=v["produto_id"],
                nome=v["nome"],
                preco=v["preco"],
                imagem=v.get("imagem"),
                quantidade=v["quantidade"],
            )

            itens.append(item)
            carrinho_limpo[k] = v

        except NotFoundError:
            # produto foi deletado → ignora
            pass

     # atualiza sessão sem os produtos inválidos
     session["carrinho"] = carrinho_limpo

     return Carrinho(itens=itens)

    def quantidade_total(self) -> int:

        raw = self._load()

        return sum(
            int(v.get("quantidade", 0))
            for v in raw.values()
        )


carrinho_service = CarrinhoService(repo=produto_repository)