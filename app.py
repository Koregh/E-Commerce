import redis
from flask import Flask
from flask_session import Session

from config.settings import settings
from services.rate_limiter import RedisRateLimiter
from services.two_factor_service import make_two_factor_service
from routes.carrinho import bp as carrinho_bp



def create_app() -> Flask:
    app = Flask(__name__)

    # ----------------------------------------------------------------
    # Configurações
    # ----------------------------------------------------------------
    app.secret_key = settings.SECRET_KEY or "dev-only-insecure-key"
    app.config["MAX_CONTENT_LENGTH"] = settings.max_upload_bytes
    app.config["SESSION_TYPE"] = settings.SESSION_TYPE
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = not settings.DEBUG

    # ----------------------------------------------------------------
    # Redis — dois clientes separados (session=binário, cache=string)
    # ----------------------------------------------------------------
    _redis_kwargs = dict(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
    )
    session_redis = redis.StrictRedis(**_redis_kwargs, decode_responses=False)
    cache_redis = redis.StrictRedis(**_redis_kwargs, decode_responses=True)

    app.config["SESSION_REDIS"] = session_redis
    Session(app)

    app.rate_limiter = RedisRateLimiter(client=cache_redis)          # type: ignore[attr-defined]
    app.two_factor = make_two_factor_service(redis_client=cache_redis)  # type: ignore[attr-defined]

    # ----------------------------------------------------------------
    # Blueprints
    # ----------------------------------------------------------------
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(carrinho_bp)

    # ----------------------------------------------------------------
    # Error handlers globais
    # ----------------------------------------------------------------
    @app.errorhandler(413)
    def too_large(e):
        from flask import flash, redirect
        flash(f"Arquivo muito grande. Máximo: {settings.MAX_UPLOAD_MB}MB")
        return redirect("/"), 413

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=settings.DEBUG)