import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from better_profanity import profanity


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    error: Optional[str] = None

    @classmethod
    def ok(cls) -> "ValidationResult":
        return cls(valid=True)

    @classmethod
    def fail(cls, error: str) -> "ValidationResult":
        return cls(valid=False, error=error)


def _sanitize(value: str) -> str:
    """Remove caracteres de controle e normaliza unicode."""
    value = unicodedata.normalize("NFC", value)
    return "".join(c for c in value if unicodedata.category(c) != "Cc")


class Validator:
    """Validadores puros — sem side effects, sem dependência de Redis ou DB."""

    EMAIL_REGEX = re.compile(r"^[\w.\-+]+@[\w\-]+\.\w{2,}$")
    NOME_REGEX = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ ]{2,50}$")
    SENHA_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,255}$")
    REPETICAO_REGEX = re.compile(r"(.)\1{9,}")

    @classmethod
    def email(cls, value: str) -> ValidationResult:
        if not isinstance(value, str) or not cls.EMAIL_REGEX.match(value.strip()):
            return ValidationResult.fail("E-mail inválido.")
        return ValidationResult.ok()

    @classmethod
    def nome(cls, value: str) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult.fail("Nome inválido.")
        value = _sanitize(value).strip()
        if profanity.contains_profanity(value):
            return ValidationResult.fail("Nome contém conteúdo inapropriado.")
        if not cls.NOME_REGEX.match(value):
            return ValidationResult.fail("Nome deve ter entre 2 e 50 letras.")
        return ValidationResult.ok()

    @classmethod
    def senha(cls, value: str) -> ValidationResult:
        if not isinstance(value, str) or not cls.SENHA_REGEX.match(value):
            return ValidationResult.fail("Senha deve ter ao menos 8 caracteres, 1 letra e 1 número.")
        return ValidationResult.ok()

    @classmethod
    def preco(cls, value) -> ValidationResult:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return ValidationResult.fail("Preço inválido.")
        if not (0 <= v <= 1_000_000):
            return ValidationResult.fail("Preço deve estar entre 0 e 1.000.000.")
        return ValidationResult.ok()

    @classmethod
    def estoque(cls, value) -> ValidationResult:
        try:
            v = int(value)
        except (TypeError, ValueError):
            return ValidationResult.fail("Estoque inválido.")
        if not (0 <= v <= 1_000_000):
            return ValidationResult.fail("Estoque deve estar entre 0 e 1.000.000.")
        return ValidationResult.ok()

    @classmethod
    def nome_produto(cls, value: str) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult.fail("Nome do produto inválido.")
        value = _sanitize(value).strip()
        if len(value) < 2 or len(value) > 100:
            return ValidationResult.fail("Nome do produto deve ter entre 2 e 100 caracteres.")
        if cls.REPETICAO_REGEX.search(value):
            return ValidationResult.fail("Nome do produto inválido.")
        if profanity.contains_profanity(value):
            return ValidationResult.fail("Nome do produto contém conteúdo inapropriado.")
        return ValidationResult.ok()

    @classmethod
    def descricao_produto(cls, value: Optional[str]) -> ValidationResult:
        if value is None or value.strip() == "":
            return ValidationResult.ok()
        if not isinstance(value, str):
            return ValidationResult.fail("Descrição inválida.")
        value = _sanitize(value).strip()
        if len(value) > 500:
            return ValidationResult.fail("Descrição deve ter no máximo 500 caracteres.")
        if cls.REPETICAO_REGEX.search(value):
            return ValidationResult.fail("Descrição inválida.")
        if profanity.contains_profanity(value):
            return ValidationResult.fail("Descrição contém conteúdo inapropriado.")
        return ValidationResult.ok()
