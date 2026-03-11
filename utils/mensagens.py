from enum import Enum


class Msg(str, Enum):
    LOGOUT_SUCESSO = "Logout realizado com sucesso!"
    CADASTRO_SUCESSO = "Cadastro realizado com sucesso!"
    PRODUTO_ADICIONADO = "Produto adicionado com sucesso!"
    PRODUTO_ATUALIZADO = "Produto atualizado com sucesso!"
    PRODUTO_DELETADO = "Produto deletado com sucesso!"
    CARRINHO_ADICIONADO = "Produto adicionado ao carrinho!"
    CARRINHO_REMOVIDO = "Produto removido do carrinho."
    CARRINHO_LIMPO = "Carrinho esvaziado."

    ERRO_EMAIL_EXISTE = "Este e-mail já está cadastrado."
    ERRO_CREDENCIAIS = "E-mail ou senha incorretos."
    ERRO_PRODUTO_NAO_ENCONTRADO = "Produto não encontrado."
    ERRO_PERMISSAO = "Você não tem permissão para esta ação."
    ERRO_UPLOAD = "Erro no upload da imagem."
    ERRO_ESTOQUE = "Produto sem estoque disponível."
    SENHAS_NAO_CONFEREM = "As senhas não conferem."
