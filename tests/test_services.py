"""
Testes unitários dos serviços principais.
Execute com: pytest tests/ -v
"""
import pytest
from unittest.mock import MagicMock, patch
from werkzeug.datastructures import FileStorage
import io

from core.exceptions.domain import (
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from core.security.password import BcryptPasswordHasher
from models.entities import Produto, Usuario
from services.usuario_service import UsuarioService
from services.produto_service import ProdutoService
from utils.validators import Validator


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def mock_hasher():
    hasher = MagicMock()
    hasher.hash.return_value = "hashed_pw"
    hasher.verify.return_value = True
    return hasher


@pytest.fixture
def mock_usuario_repo():
    return MagicMock()


@pytest.fixture
def mock_produto_repo():
    return MagicMock()


@pytest.fixture
def mock_uploader():
    uploader = MagicMock()
    uploader.save.return_value = "uuid_image.jpg"
    return uploader


@pytest.fixture
def usuario_service(mock_usuario_repo, mock_hasher):
    return UsuarioService(repo=mock_usuario_repo, hasher=mock_hasher)


@pytest.fixture
def produto_service(mock_produto_repo, mock_uploader):
    return ProdutoService(repo=mock_produto_repo, uploader=mock_uploader)


@pytest.fixture
def usuario_existente():
    return Usuario(id=1, nome="João", email="joao@test.com", senha="hashed_pw")


@pytest.fixture
def produto_existente():
    return Produto(id=1, nome="iPhone", preco=5000.0, estoque=10, usuario_id=1, imagem=None)


# ──────────────────────────────────────────────
# UsuarioService
# ──────────────────────────────────────────────

class TestUsuarioService:

    def test_cadastrar_sucesso(self, usuario_service, mock_usuario_repo, mock_hasher):
        mock_usuario_repo.buscar_por_email.return_value = None
        usuario_service.cadastrar("João", "joao@test.com", "Senha123")
        mock_hasher.hash.assert_called_once_with("Senha123")
        mock_usuario_repo.criar.assert_called_once()

    def test_cadastrar_email_duplicado(self, usuario_service, mock_usuario_repo, usuario_existente):
        mock_usuario_repo.buscar_por_email.return_value = usuario_existente
        with pytest.raises(ConflictError):
            usuario_service.cadastrar("João", "joao@test.com", "Senha123")

    def test_autenticar_sucesso(self, usuario_service, mock_usuario_repo, mock_hasher, usuario_existente):
        mock_usuario_repo.buscar_por_email.return_value = usuario_existente
        mock_hasher.verify.return_value = True
        result = usuario_service.autenticar("joao@test.com", "Senha123")
        assert result.id == 1

    def test_autenticar_senha_errada(self, usuario_service, mock_usuario_repo, mock_hasher, usuario_existente):
        mock_usuario_repo.buscar_por_email.return_value = usuario_existente
        mock_hasher.verify.return_value = False
        with pytest.raises(AuthenticationError):
            usuario_service.autenticar("joao@test.com", "errada")

    def test_autenticar_usuario_inexistente(self, usuario_service, mock_usuario_repo):
        mock_usuario_repo.buscar_por_email.return_value = None
        with pytest.raises(AuthenticationError):
            usuario_service.autenticar("nao@existe.com", "qualquer")


# ──────────────────────────────────────────────
# ProdutoService
# ──────────────────────────────────────────────

class TestProdutoService:

    def test_adicionar_sucesso(self, produto_service, mock_produto_repo):
        produto_service.adicionar("iPhone", 5000.0, 10, usuario_id=1)
        mock_produto_repo.adicionar.assert_called_once_with("iPhone", 5000.0, 10, None, 1)

    def test_adicionar_preco_negativo(self, produto_service):
        with pytest.raises(ValidationError):
            produto_service.adicionar("iPhone", -1, 10, usuario_id=1)

    def test_adicionar_estoque_negativo(self, produto_service):
        with pytest.raises(ValidationError):
            produto_service.adicionar("iPhone", 100, -5, usuario_id=1)

    def test_adicionar_com_imagem(self, produto_service, mock_produto_repo, mock_uploader):
        fake_file = MagicMock(spec=FileStorage)
        fake_file.filename = "foto.jpg"
        produto_service.adicionar("iPhone", 5000.0, 10, usuario_id=1, imagem_file=fake_file)
        mock_uploader.save.assert_called_once_with(fake_file)

    def test_deletar_produto_de_outro_usuario(self, produto_service, mock_produto_repo, produto_existente):
        mock_produto_repo.buscar_por_id.return_value = produto_existente
        with pytest.raises(ForbiddenError):
            produto_service.deletar(produto_id=1, usuario_id=999)  # usuario_id diferente

    def test_deletar_produto_inexistente(self, produto_service, mock_produto_repo):
        mock_produto_repo.buscar_por_id.return_value = None
        with pytest.raises(NotFoundError):
            produto_service.deletar(produto_id=999, usuario_id=1)

    def test_atualizar_deleta_imagem_antiga(self, produto_service, mock_produto_repo, mock_uploader):
        produto = Produto(id=1, nome="iPhone", preco=5000.0, estoque=10, usuario_id=1, imagem="old.jpg")
        mock_produto_repo.buscar_por_id.return_value = produto

        nova_imagem = MagicMock(spec=FileStorage)
        nova_imagem.filename = "nova.jpg"

        produto_service.atualizar(produto_id=1, usuario_id=1, imagem_file=nova_imagem)
        mock_uploader.delete.assert_called_once_with("old.jpg")
        mock_uploader.save.assert_called_once_with(nova_imagem)


# ──────────────────────────────────────────────
# Validators
# ──────────────────────────────────────────────

class TestValidators:

    @pytest.mark.parametrize("email", [
        "joao@gmail.com", "teste+tag@empresa.com.br", "a@b.io"
    ])
    def test_email_valido(self, email):
        assert Validator.email(email).valid

    @pytest.mark.parametrize("email", [
        "invalido", "@semdominio.com", "sem@", "", "a" * 300 + "@x.com"
    ])
    def test_email_invalido(self, email):
        assert not Validator.email(email).valid

    @pytest.mark.parametrize("senha", [
        "Senha123", "abc12345", "ABCD5678"
    ])
    def test_senha_valida(self, senha):
        assert Validator.senha(senha).valid

    @pytest.mark.parametrize("senha", [
        "curta1", "semnumero", "12345678", ""
    ])
    def test_senha_invalida(self, senha):
        assert not Validator.senha(senha).valid

    def test_preco_valido(self):
        assert Validator.preco(100.50).valid
        assert Validator.preco(0).valid
        assert Validator.preco(1_000_000).valid

    def test_preco_invalido(self):
        assert not Validator.preco(-1).valid
        assert not Validator.preco(1_000_001).valid
        assert not Validator.preco("abc").valid

    def test_estoque_invalido(self):
        assert not Validator.estoque(-1).valid
        assert not Validator.estoque("x").valid


# ──────────────────────────────────────────────
# PasswordHasher
# ──────────────────────────────────────────────

class TestPasswordHasher:

    def test_hash_e_verify(self):
        hasher = BcryptPasswordHasher(rounds=4)  # rounds baixo para teste rápido
        hashed = hasher.hash("MinhaSenha1")
        assert hasher.verify("MinhaSenha1", hashed)
        assert not hasher.verify("SenhaErrada", hashed)

    def test_hashes_diferentes_para_mesma_senha(self):
        hasher = BcryptPasswordHasher(rounds=4)
        h1 = hasher.hash("MinhaSenha1")
        h2 = hasher.hash("MinhaSenha1")
        assert h1 != h2  # salt diferente a cada hash


# ──────────────────────────────────────────────
# TwoFactorService
# ──────────────────────────────────────────────

class TestTwoFactorService:

    def _make_service(self):
        from services.two_factor_service import RedisTwoFactorService, IEmailSender
        mock_redis = MagicMock()
        mock_sender = MagicMock(spec=IEmailSender)
        service = RedisTwoFactorService(redis_client=mock_redis, email_sender=mock_sender)
        return service, mock_redis, mock_sender

    def test_gerar_envia_email(self):
        service, mock_redis, mock_sender = self._make_service()
        service.gerar_e_enviar(usuario_id=1, email="joao@test.com")
        mock_sender.enviar.assert_called_once()
        mock_redis.set.assert_called_once()

    def test_verificar_codigo_correto(self):
        service, mock_redis, _ = self._make_service()
        mock_redis.get.return_value = "123456"
        assert service.verificar(usuario_id=1, codigo="123456") is True

    def test_verificar_codigo_errado(self):
        service, mock_redis, _ = self._make_service()
        mock_redis.get.return_value = "123456"
        assert service.verificar(usuario_id=1, codigo="000000") is False

    def test_verificar_codigo_expirado(self):
        service, mock_redis, _ = self._make_service()
        mock_redis.get.return_value = None  # TTL expirou
        assert service.verificar(usuario_id=1, codigo="123456") is False

    def test_invalidar_deleta_chave(self):
        service, mock_redis, _ = self._make_service()
        service.invalidar(usuario_id=1)
        mock_redis.delete.assert_called_once_with("2fa:1")