class AppError(Exception):
    """Base para todas as exceções de domínio."""


class NotFoundError(AppError):
    """Recurso não encontrado."""


class ForbiddenError(AppError):
    """Ação não permitida para este usuário."""


class ConflictError(AppError):
    """Conflito de dados (ex: e-mail duplicado)."""


class ValidationError(AppError):
    """Dado inválido."""


class AuthenticationError(AppError):
    """Credenciais inválidas."""


class UploadError(AppError):
    """Erro no upload de arquivo."""
