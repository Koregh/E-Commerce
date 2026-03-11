from flask import Blueprint, flash, jsonify, redirect, render_template, request, session

from core.exceptions.domain import AppError, ForbiddenError, NotFoundError, UploadError
from services.carrinho_service import carrinho_service
from services.produto_service import produto_service
from utils.auth_helpers import login_required
from utils.mensagens import Msg

dashboard_bp = Blueprint("dashboard", __name__)


# ── Loja pública ──────────────────────────────────────────────────

@dashboard_bp.route("/")
def home():
    produtos = produto_service.listar_todos()
    qtd_carrinho = carrinho_service.quantidade_total()
    return render_template(
        "index.html",
        produtos=produtos,
        usuario_nome=session.get("usuario_nome"),
        usuario=session.get("usuario_id"),
        qtd_carrinho=qtd_carrinho,
    )


# ── Carrinho ──────────────────────────────────────────────────────
    
@dashboard_bp.route("/produto/<int:produto_id>")
def ver_produto(produto_id):

    try:
        produto = produto_service.buscar_por_id(produto_id)

    except NotFoundError:
        flash("Produto não encontrado")
        return redirect("/")

    return render_template(
        "produto_detalhe.html",
        produto=produto,
        usuario_nome=session.get("usuario_nome"),
        usuario=session.get("usuario_id"),
        qtd_carrinho=carrinho_service.quantidade_total(),
    )

    produto = produto_service.buscar_por_id(produto_id)

    if not produto:
        flash("Produto não encontrado")
        return redirect("/")

    return render_template(
        "produto_detalhe.html",
        produto=produto,
        usuario_nome=session.get("usuario_nome"),
        usuario=session.get("usuario_id"),
        qtd_carrinho=carrinho_service.quantidade_total(),
    )

@dashboard_bp.route("/carrinho/adicionar/<int:produto_id>", methods=["POST"])
def adicionar_carrinho(produto_id: int):
    try:
        carrinho_service.adicionar(produto_id)
        qtd = carrinho_service.quantidade_total()
        # Suporta chamada AJAX e redirect normal
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
           return jsonify({"ok": True, "quantidade_total": qtd})
        flash(Msg.CARRINHO_ADICIONADO)
    except AppError as e:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "erro": str(e)}), 400
        flash(str(e))
    return redirect(request.referrer or "/")


@dashboard_bp.route("/carrinho/remover/<int:produto_id>", methods=["POST"])
def remover_carrinho(produto_id: int):
    carrinho_service.remover(produto_id)
    flash(Msg.CARRINHO_REMOVIDO)
    return redirect("/carrinho")


@dashboard_bp.route("/carrinho/atualizar/<int:produto_id>", methods=["POST"])
def atualizar_carrinho(produto_id: int):
    try:
        qtd = int(request.form.get("quantidade", 1))
        carrinho_service.atualizar_quantidade(produto_id, qtd)
    except (AppError, ValueError) as e:
        flash(str(e))
    return redirect("/carrinho")


@dashboard_bp.route("/carrinho/limpar", methods=["POST"])
def limpar_carrinho():
    carrinho_service.limpar()
    flash(Msg.CARRINHO_LIMPO)
    return redirect("/carrinho")


# ── Dashboard do vendedor ─────────────────────────────────────────

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    produtos = produto_service.listar_por_usuario(session["usuario_id"])
    return render_template("dashboard.html", produtos=produtos, usuario_nome=session["usuario_nome"])


@dashboard_bp.route("/produto/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_produto():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        preco = request.form.get("preco")
        estoque = request.form.get("estoque")
        descricao = request.form.get("descricao", "").strip() or None
        imagem_file = request.files.get("imagem")
        try:
            produto_service.adicionar(
                nome=nome, preco=preco, estoque=estoque,
                usuario_id=session["usuario_id"],
                imagem_file=imagem_file, descricao=descricao,
            )
            flash(Msg.PRODUTO_ADICIONADO)
            return redirect("/dashboard")
        except (AppError, UploadError) as e:
            flash(str(e))
            return redirect("/produto/adicionar")
    return render_template("produto_form.html")


@dashboard_bp.route("/produto/editar/<int:produto_id>", methods=["GET", "POST"])
@login_required
def editar_produto(produto_id: int):
    usuario_id = session["usuario_id"]
    try:
        produto = produto_service.buscar_por_id_e_usuario(produto_id, usuario_id)
    except (NotFoundError, ForbiddenError) as e:
        flash(str(e))
        return redirect("/dashboard")

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        preco = request.form.get("preco")
        estoque = request.form.get("estoque")
        descricao = request.form.get("descricao", "").strip() or None
        imagem_file = request.files.get("imagem")
        try:
            produto_service.atualizar(
                produto_id=produto_id, usuario_id=usuario_id,
                nome=nome,
                preco=float(preco) if preco else None,
                estoque=int(estoque) if estoque else None,
                imagem_file=imagem_file, descricao=descricao,
            )
            flash(Msg.PRODUTO_ATUALIZADO)
            return redirect("/dashboard")
        except (AppError, UploadError) as e:
            flash(str(e))
    return render_template("produto_form.html", produto=produto)


@dashboard_bp.route("/produto/deletar/<int:produto_id>")
@login_required
def deletar_produto(produto_id: int):
    try:
        produto_service.deletar(produto_id, session["usuario_id"])
        flash(Msg.PRODUTO_DELETADO)
    except (NotFoundError, ForbiddenError) as e:
        flash(str(e))
    return redirect("/dashboard")
