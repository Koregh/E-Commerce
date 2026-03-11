import secrets
import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import redis

from config.settings import settings


# ──────────────────────────────────────────────
# Interface — fácil de mockar em testes
# ──────────────────────────────────────────────

class ITwoFactorService(ABC):
    @abstractmethod
    def gerar_e_enviar(self, usuario_id: int, email: str) -> None:
        """Gera código, armazena no Redis e envia por e-mail."""

    @abstractmethod
    def verificar(self, usuario_id: int, codigo: str) -> bool:
        """Retorna True se o código for válido e não expirado."""

    @abstractmethod
    def invalidar(self, usuario_id: int) -> None:
        """Remove o código após uso bem-sucedido."""


# ──────────────────────────────────────────────
# Implementação Redis + SMTP
# ──────────────────────────────────────────────

class RedisTwoFactorService(ITwoFactorService):
    """
    Fluxo:
    1. Gera código numérico de 6 dígitos com secrets (criptograficamente seguro)
    2. Armazena no Redis com TTL de 10 minutos: key = "2fa:{usuario_id}"
    3. Envia por e-mail via SMTP
    4. Na verificação, compara com timing-safe compare para evitar timing attacks
    """

    CODE_LENGTH = 6
    TTL_SECONDS = 600  # 10 minutos

    def __init__(self, redis_client: redis.StrictRedis, email_sender: "IEmailSender"):
        self._redis = redis_client
        self._sender = email_sender

    def _redis_key(self, usuario_id: int) -> str:
        return f"2fa:{usuario_id}"

    def gerar_e_enviar(self, usuario_id: int, email: str) -> None:
        codigo = "".join([str(secrets.randbelow(10)) for _ in range(self.CODE_LENGTH)])
        self._redis.set(self._redis_key(usuario_id), codigo, ex=self.TTL_SECONDS)
        self._sender.enviar(
            destinatario=email,
            assunto="Seu código de verificação — Mini Loja",
            corpo_html=_template_email(codigo),
        )

    def verificar(self, usuario_id: int, codigo: str) -> bool:
        salvo = self._redis.get(self._redis_key(usuario_id))
        if not salvo:
            return False
        # secrets.compare_digest evita timing attack
        return secrets.compare_digest(salvo, codigo.strip())

    def invalidar(self, usuario_id: int) -> None:
        self._redis.delete(self._redis_key(usuario_id))


# ──────────────────────────────────────────────
# Interface e implementação do sender de e-mail
# ──────────────────────────────────────────────

class IEmailSender(ABC):
    @abstractmethod
    def enviar(self, destinatario: str, assunto: str, corpo_html: str) -> None: ...


class SMTPEmailSender(IEmailSender):
    """Envia e-mail via SMTP (Gmail, Outlook, etc.)."""

    def __init__(self, host: str, port: int, usuario: str, senha: str, use_tls: bool = True):
        self._host = host
        self._port = port
        self._usuario = usuario
        self._senha = senha
        self._use_tls = use_tls

    def enviar(self, destinatario: str, assunto: str, corpo_html: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = self._usuario
        msg["To"] = destinatario
        msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        with smtplib.SMTP(self._host, self._port) as smtp:
            if self._use_tls:
                smtp.starttls()
            smtp.login(self._usuario, self._senha)
            smtp.sendmail(self._usuario, destinatario, msg.as_string())


# ──────────────────────────────────────────────
# Template do e-mail
# ──────────────────────────────────────────────

def _template_email(codigo: str) -> str:
    return f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;
                border:1px solid #eee;border-radius:8px;">
        <h2 style="color:#333;">Verificação em duas etapas</h2>
        <p style="color:#555;">Use o código abaixo para concluir o login na <strong>Mini Loja</strong>:</p>
        <div style="font-size:36px;font-weight:bold;letter-spacing:10px;
                    text-align:center;padding:20px;background:#f5f5f5;
                    border-radius:6px;margin:24px 0;">
            {codigo}
        </div>
        <p style="color:#999;font-size:13px;">
            Este código expira em <strong>10 minutos</strong>.<br>
            Se você não tentou fazer login, ignore este e-mail.
        </p>
    </div>
    """


# ──────────────────────────────────────────────
# Factory — monta a instância com as configs
# ──────────────────────────────────────────────

def make_two_factor_service(redis_client: redis.StrictRedis) -> ITwoFactorService:
    sender = SMTPEmailSender(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        usuario=settings.SMTP_USER,
        senha=settings.SMTP_PASSWORD,
        use_tls=settings.SMTP_USE_TLS,
    )
    return RedisTwoFactorService(redis_client=redis_client, email_sender=sender)