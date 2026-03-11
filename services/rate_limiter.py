from abc import ABC, abstractmethod

import redis

from config.settings import settings


class IRateLimiter(ABC):
    @abstractmethod
    def get_delay(self, key: str) -> float: ...

    @abstractmethod
    def register_fail(self, key: str) -> None: ...

    @abstractmethod
    def reset(self, key: str) -> None: ...


class RedisRateLimiter(IRateLimiter):
    """
    Backoff exponencial por chave (ex: email, IP).
    Delay é retornado para a camada de aplicação decidir como tratar —
    não faz sleep() aqui para não bloquear o thread do servidor.
    """

    MAX_DELAY = settings.RATE_LIMIT_MAX_DELAY
    INITIAL_DELAY = settings.RATE_LIMIT_INITIAL_DELAY
    TTL = settings.RATE_LIMIT_TTL

    def __init__(self, client: redis.StrictRedis):
        self._redis = client

    def _get_attempts(self, key: str) -> int:
        return int(self._redis.get(key) or 0)

    def _calculate_delay(self, attempts: int) -> float:
        if attempts == 0:
            return 0.0
        delay = self.INITIAL_DELAY * (2 ** (attempts - 1))
        return min(delay, self.MAX_DELAY)

    def get_delay(self, key: str) -> float:
        return self._calculate_delay(self._get_attempts(key))

    def register_fail(self, key: str) -> None:
        attempts = self._get_attempts(key) + 1
        self._redis.set(key, attempts, ex=self.TTL)

    def reset(self, key: str) -> None:
        self._redis.delete(key)
