from typing import Optional

from core.exceptions.domain import AuthenticationError, ConflictError, NotFoundError
from core.security.password import IPasswordHasher, password_hasher
from models.entities import Usuario
from repositories.usuario_repository import IUsuarioRepository, usuario_repository


class UsuarioService:
    """
    Orquestra regras de negócio de usuário.
    Recebe dependências via construtor (Dependency Injection).
    """

    def __init__(
        self,
        repo: IUsuarioRepository,
        hasher: IPasswordHasher,
    ):
        self._repo = repo
        self._hasher = hasher

    def cadastrar(self, nome: str, email: str, senha: str, avatar: Optional[str] = None) -> None:
        if self._repo.buscar_por_email(email):
            raise ConflictError("E-mail já cadastrado.")
        senha_hash = self._hasher.hash(senha)
        self._repo.criar(nome, email, senha_hash, avatar)

    def autenticar(self, email: str, senha: str) -> Usuario:
        usuario = self._repo.buscar_por_email(email)
        if not usuario or not self._hasher.verify(senha, usuario.senha):
            raise AuthenticationError("Credenciais inválidas.")
        return usuario

    def buscar_por_id(self, usuario_id: int) -> Usuario:
        usuario = self._repo.buscar_por_id(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado.")
        return usuario

    def atualizar(
        self,
        usuario_id: int,
        nome: Optional[str] = None,
        email: Optional[str] = None,
        senha: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> None:
        atual = self.buscar_por_id(usuario_id)
        novo_nome = nome or atual.nome
        novo_email = email or atual.email
        nova_senha = self._hasher.hash(senha) if senha else atual.senha
        novo_avatar = avatar if avatar is not None else atual.avatar
        self._repo.atualizar(usuario_id, novo_nome, novo_email, nova_senha, novo_avatar)

    def deletar(self, usuario_id: int) -> None:
        self.buscar_por_id(usuario_id)
        self._repo.deletar(usuario_id)


# Instância padrão com dependências reais
usuario_service = UsuarioService(repo=usuario_repository, hasher=password_hasher)
