from typing import List, Optional
from werkzeug.datastructures import FileStorage

from core.exceptions.domain import ForbiddenError, NotFoundError, ValidationError
from core.security.upload import IFileUploader, file_uploader
from models.entities import Produto
from repositories.produto_repository import IProdutoRepository, produto_repository
from utils.validators import Validator


class ProdutoService:

    def __init__(self, repo: IProdutoRepository, uploader: IFileUploader):
        self._repo = repo
        self._uploader = uploader

    def _validar_campos(self, nome: str, preco, estoque, descricao: Optional[str] = None) -> None:
        for result in [
            Validator.nome_produto(nome),
            Validator.preco(preco),
            Validator.estoque(estoque),
            Validator.descricao_produto(descricao),
        ]:
            if not result.valid:
                raise ValidationError(result.error)

    def adicionar(
        self,
        nome: str,
        preco: float,
        estoque: int,
        usuario_id: int,
        imagem_file: Optional[FileStorage] = None,
        descricao: Optional[str] = None,
    ) -> None:
        self._validar_campos(nome, preco, estoque, descricao)

        if not imagem_file or not imagem_file.filename:
            raise ValidationError("Imagem é obrigatória.")

        imagem_filename = self._uploader.save(imagem_file)
        self._repo.adicionar(nome, float(preco), int(estoque), imagem_filename, usuario_id, descricao)

    def listar_todos(self) -> List[Produto]:
        return self._repo.listar_todos()

    def listar_por_usuario(self, usuario_id: int) -> List[Produto]:
        return self._repo.listar_por_usuario(usuario_id)

    def buscar_por_id(self, produto_id: int) -> Produto:
        produto = self._repo.buscar_por_id(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado.")
        return produto

    def buscar_por_id_e_usuario(self, produto_id: int, usuario_id: int) -> Produto:
        produto = self._repo.buscar_por_id(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado.")
        if produto.usuario_id != usuario_id:
            raise ForbiddenError("Você não tem permissão para este produto.")
        return produto

    def atualizar(
        self,
        produto_id: int,
        usuario_id: int,
        nome: Optional[str] = None,
        preco: Optional[float] = None,
        estoque: Optional[int] = None,
        imagem_file: Optional[FileStorage] = None,
        descricao: Optional[str] = None,
    ) -> None:
        produto = self.buscar_por_id_e_usuario(produto_id, usuario_id)

        novo_nome = nome or produto.nome
        novo_preco = preco if preco is not None else produto.preco
        novo_estoque = estoque if estoque is not None else produto.estoque
        nova_descricao = descricao if descricao is not None else produto.descricao

        self._validar_campos(novo_nome, novo_preco, novo_estoque, nova_descricao)

        nova_imagem = produto.imagem
        if imagem_file and imagem_file.filename:
            if produto.imagem:
                self._uploader.delete(produto.imagem)
            nova_imagem = self._uploader.save(imagem_file)

        self._repo.atualizar(produto_id, novo_nome, float(novo_preco), int(novo_estoque), nova_imagem, usuario_id, nova_descricao)

    def deletar(self, produto_id: int, usuario_id: int) -> None:
        produto = self.buscar_por_id_e_usuario(produto_id, usuario_id)
        if produto.imagem:
            self._uploader.delete(produto.imagem)
        self._repo.deletar(produto_id, usuario_id)


produto_service = ProdutoService(repo=produto_repository, uploader=file_uploader)
