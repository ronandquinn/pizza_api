"""Health check for load balancers / ECS. Rails equivalent: `get "up"` in routes.rb."""
from flask import Blueprint, jsonify
from sqlalchemy import text

from ..extensions import db

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    db.session.execute(text("SELECT 1"))
    return jsonify(status="ok")
