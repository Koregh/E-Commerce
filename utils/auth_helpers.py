import time
from functools import wraps
from typing import Callable

from flask import redirect, session


def login_required(f: Callable) -> Callable:
    """Redireciona para /login se não houver sessão ativa."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated


def apply_rate_limit_delay(delay: float, max_delay: float = 5.0) -> None:
    """
    Aplica delay de rate limiting de forma segura.
    Limita o delay máximo no thread para evitar travar o servidor
    em desenvolvimento. Em produção, prefira rejeitar com 429.
    """
    if delay > 0:
        time.sleep(min(delay, max_delay))
