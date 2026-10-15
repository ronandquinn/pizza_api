"""Configuration classes, selected by the APP_ENV environment variable.

Rails equivalent: config/environments/{development,test,production}.rb
plus config/database.yml and ENV / credentials. Flask has no built-in
environments, so this is a plain Python class per environment.
"""
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://pizza:pizza@localhost:5432/pizza_dev"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    QUEUE_ASYNC = True  # False = run jobs inline (used in tests)


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    QUEUE_ASYNC = False


class ProductionConfig(Config):
    DEBUG = False

    @classmethod
    def validate(cls):
        # Fail fast on boot if a required secret is missing
        # (Rails: ENV.fetch("SECRET_KEY_BASE") with no default).
        if cls.SECRET_KEY == "dev-only-change-me":
            raise RuntimeError("SECRET_KEY must be set in production")


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
