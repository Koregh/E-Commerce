import os
import warnings
from dataclasses import dataclass, field
from dotenv import load_dotenv
load_dotenv()


@dataclass(frozen=True)
class Settings:
    # App
    SECRET_KEY: str = field(default_factory=lambda: os.environ.get("SECRET_KEY", ""))
    DEBUG: bool = field(default_factory=lambda: os.environ.get("DEBUG", "false").lower() == "true")
    ENV: str = field(default_factory=lambda: os.environ.get("ENV", "development"))

    # Database
    DATABASE_URL: str = field(default_factory=lambda: os.environ.get("DATABASE_URL", "database.db"))

    # Redis
    REDIS_HOST: str = field(default_factory=lambda: os.environ.get("REDIS_HOST", "localhost"))
    REDIS_PORT: int = field(default_factory=lambda: int(os.environ.get("REDIS_PORT", 6379)))
    REDIS_DB: int = field(default_factory=lambda: int(os.environ.get("REDIS_DB", 0)))

    # Upload
    UPLOAD_FOLDER: str = field(default_factory=lambda: os.environ.get("UPLOAD_FOLDER", "static/images"))
    MAX_UPLOAD_MB: int = field(default_factory=lambda: int(os.environ.get("MAX_UPLOAD_MB", 5)))
    ALLOWED_EXTENSIONS: frozenset = frozenset({"png", "jpg", "jpeg", "webp"})

    # Rate Limiting
    RATE_LIMIT_MAX_DELAY: int = 60
    RATE_LIMIT_INITIAL_DELAY: float = 0.1
    RATE_LIMIT_TTL: int = 3600

    # Session
    SESSION_TYPE: str = "redis"

    # SMTP — 2FA por e-mail
    SMTP_HOST: str = field(default_factory=lambda: os.environ.get("SMTP_HOST", "smtp.gmail.com"))
    SMTP_PORT: int = field(default_factory=lambda: int(os.environ.get("SMTP_PORT", 587)))
    SMTP_USER: str = field(default_factory=lambda: os.environ.get("SMTP_USER", ""))
    SMTP_PASSWORD: str = field(default_factory=lambda: os.environ.get("SMTP_PASSWORD", ""))
    SMTP_USE_TLS: bool = field(default_factory=lambda: os.environ.get("SMTP_USE_TLS", "true").lower() == "true")

    def __post_init__(self):
        if self.ENV == "production" and not self.SECRET_KEY:
            raise ValueError(
                "SECRET_KEY must be set in production.\n"
                "Set the SECRET_KEY environment variable or create a .env file."
            )
        if self.ENV == "development" and not self.SECRET_KEY:
            warnings.warn(
                "SECRET_KEY not set — using insecure default for development only.",
                stacklevel=2,
            )

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


settings = Settings()