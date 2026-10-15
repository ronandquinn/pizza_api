"""Application factory.

Rails equivalent: config/application.rb + config/initializers/* + config/routes.rb,
all in one function. Nothing is auto-loaded in Flask: if you want a route,
model or extension, you import and register it here.
"""
import os

import redis
from flask import Flask, jsonify
from pydantic import ValidationError

from .config import CONFIGS
from .extensions import db, migrate


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get("APP_ENV", "development")
    config_class = CONFIGS[config_name]
    if hasattr(config_class, "validate"):
        config_class.validate()

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Redis connection used by the job queue (tests replace it with a fake)
    app.extensions["redis"] = redis.from_url(app.config["REDIS_URL"])

    # Make sure models are imported so Alembic/`db.create_all` can see them
    from . import models  # noqa: F401

    # Routes (Rails: config/routes.rb)
    from .routes.health import bp as health_bp
    from .routes.orders import bp as orders_bp
    from .routes.shops import bp as shops_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(shops_bp)
    app.register_blueprint(orders_bp)

    # Error handlers (Rails: rescue_from in ApplicationController)
    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        return jsonify(error="validation_failed", details=err.errors(include_url=False, include_context=False)), 422

    @app.errorhandler(404)
    def handle_not_found(_err):
        return jsonify(error="not_found"), 404

    # `flask shell` pre-imports (Rails console loads everything automatically;
    # Flask only auto-imports `app`, so we add what we want here)
    @app.shell_context_processor
    def make_shell_context():
        from sqlalchemy import func, select

        return {
            "db": db,
            "select": select,
            "func": func,
            "Shop": models.Shop,
            "MenuItem": models.MenuItem,
            "Order": models.Order,
            "OrderItem": models.OrderItem,
        }

    return app
