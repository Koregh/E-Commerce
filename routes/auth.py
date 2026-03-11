from flask import Blueprint, current_app, flash, redirect, render_template, request, session

from core.exceptions.domain import AuthenticationError, ConflictError
from services.usuario_service import usuario_service
from utils.auth_helpers import apply_rate_limit_delay
from utils.mensagens import Msg
from utils.validators import Validator

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash(Msg.LOGOUT_SUCESSO)
    return redirect("/login")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        rl = current_app.rate_limiter
        rl_key = f"login_fail:{email}"

        apply_rate_limit_delay(rl.get_delay(rl_key))

        email_result = Validator.email(email)
        if not email_result.valid:
            flash(email_result.error)
            rl.register_fail(rl_key)
            return redirect("/login")

        try:
            usuario = usuario_service.autenticar(email, senha)

            # Credenciais OK — armazena ID temporário na sessão e envia código 2FA
            session["2fa_usuario_id"] = usuario.id
            session["2fa_usuario_nome"] = usuario.nome
            session["2fa_email"] = usuario.email

            current_app.two_factor.gerar_e_enviar(usuario.id, usuario.email)
            rl.reset(rl_key)
            return redirect("/login/verificar")

        except AuthenticationError:
            flash(Msg.ERRO_CREDENCIAIS)
            rl.register_fail(rl_key)
            return redirect("/login")

    return render_template("login.html")


@auth_bp.route("/login/verificar", methods=["GET", "POST"])
def verificar_2fa():
    # Garante que veio do fluxo de login
    if "2fa_usuario_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip()
        usuario_id = session["2fa_usuario_id"]
        rl = current_app.rate_limiter
        rl_key = f"2fa_fail:{usuario_id}"

        apply_rate_limit_delay(rl.get_delay(rl_key))

        if current_app.two_factor.verificar(usuario_id, codigo):
            # Código válido — promove sessão para autenticada
            current_app.two_factor.invalidar(usuario_id)
            rl.reset(rl_key)

            session["usuario_id"] = session.pop("2fa_usuario_id")
            session["usuario_nome"] = session.pop("2fa_usuario_nome")
            session.pop("2fa_email", None)

            return redirect("/dashboard")
        else:
            flash("Código inválido ou expirado. Tente novamente.")
            rl.register_fail(rl_key)
            return redirect("/login/verificar")

    email = session.get("2fa_email", "")
    # Mostra só o domínio para não expor o e-mail completo na tela
    email_mascarado = _mascarar_email(email)
    return render_template("verificar_2fa.html", email=email_mascarado)


@auth_bp.route("/login/reenviar", methods=["POST"])
def reenviar_codigo():
    if "2fa_usuario_id" not in session:
        return redirect("/login")

    usuario_id = session["2fa_usuario_id"]
    email = session["2fa_email"]
    current_app.two_factor.gerar_e_enviar(usuario_id, email)
    flash("Novo código enviado para o seu e-mail.")
    return redirect("/login/verificar")


@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        confirmar = request.form.get("confirmar", "")
        rl = current_app.rate_limiter
        rl_key = f"cadastro_fail:{email}"

        apply_rate_limit_delay(rl.get_delay(rl_key))

        for result in [
            Validator.nome(nome),
            Validator.email(email),
            Validator.senha(senha),
        ]:
            if not result.valid:
                flash(result.error)
                rl.register_fail(rl_key)
                return redirect("/cadastro")

        if senha != confirmar:
            flash(Msg.SENHAS_NAO_CONFEREM)
            return redirect("/cadastro")

        try:
            usuario_service.cadastrar(nome, email, senha)
            rl.reset(rl_key)
            flash(Msg.CADASTRO_SUCESSO)
            return redirect("/login")
        except ConflictError as e:
            flash(str(e))
            rl.register_fail(rl_key)
            return redirect("/cadastro")

    return render_template("cadastro.html")


def _mascarar_email(email: str) -> str:
    """joao@gmail.com → j***@gmail.com"""
    if "@" not in email:
        return "***"
    local, dominio = email.split("@", 1)
    return f"{local[0]}***@{dominio}"