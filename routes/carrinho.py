from flask import Blueprint, request, jsonify, render_template

from services.carrinho_service import carrinho_service

bp = Blueprint("carrinho", __name__)


# ─────────────────────────────
# Página do carrinho
# ─────────────────────────────
@bp.get("/carrinho")
def pagina_carrinho():

    carrinho = carrinho_service.obter()

    return render_template(
        "carrinho.html",
        carrinho=carrinho
    )


# ─────────────────────────────
# Adicionar produto
# ─────────────────────────────
@bp.post("/carrinho/adicionar/<int:produto_id>")
def adicionar(produto_id):

    data = request.get_json(silent=True) or {}
    quantidade = int(data.get("quantidade", 1))

    carrinho_service.adicionar(produto_id, quantidade)

    carrinho = carrinho_service.obter()

    return jsonify({
        "ok": True,
        "quantidade_total": carrinho_service.quantidade_total(),
        "total": carrinho.total
    })


# ─────────────────────────────
# Remover produto
# ─────────────────────────────
@bp.post("/carrinho/remover/<int:produto_id>")
def remover(produto_id):

    carrinho_service.remover(produto_id)

    carrinho = carrinho_service.obter()

    return jsonify({
        "ok": True,
        "quantidade_total": carrinho_service.quantidade_total(),
        "total": carrinho.total
    })


# ─────────────────────────────
# Atualizar quantidade
# ─────────────────────────────
@bp.post("/carrinho/quantidade/<int:produto_id>")
def atualizar_quantidade(produto_id):

    data = request.get_json()
    quantidade = int(data.get("quantidade", 1))

    carrinho_service.atualizar_quantidade(produto_id, quantidade)

    carrinho = carrinho_service.obter()

    item = next(
        (i for i in carrinho.itens if i.produto_id == produto_id),
        None
    )

    return jsonify({
        "ok": True,
        "quantidade": item.quantidade if item else 0,
        "subtotal": item.subtotal if item else 0,
        "quantidade_total": carrinho_service.quantidade_total(),
        "total": carrinho.total
    })


# ─────────────────────────────
# Limpar carrinho
# ─────────────────────────────
@bp.post("/carrinho/limpar")
def limpar():

    carrinho_service.limpar()

    return jsonify({
        "ok": True
    })