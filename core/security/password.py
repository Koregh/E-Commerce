from abc import ABC, abstractmethod

import bcrypt


class IPasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verify(self, password: str, hashed: str) -> bool: ...


class BcryptPasswordHasher(IPasswordHasher):
    """
    Implementação usando bcrypt com custo configurável.
    Depende apenas da interface — fácil de trocar em testes.
    """

    def __init__(self, rounds: int = 12):
        self._rounds = rounds

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(self._rounds)).decode()

    def verify(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())


# Instância padrão — injetável nos serviços
password_hasher: IPasswordHasher = BcryptPasswordHasher()
