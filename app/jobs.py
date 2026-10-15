"""Background jobs.  Rails equivalent: app/jobs/*.rb (or Sidekiq workers).

Key Flask-vs-Rails difference: a Rails worker boots the whole app, so models
just work. In Flask the worker process has no app context until you create one,
so jobs open one explicitly.
"""
import logging

from flask import has_app_context

from .extensions import db
from .models import Order

log = logging.getLogger(__name__)
_worker_app = None


def _app_for_worker():
    global _worker_app
    if _worker_app is None:
        from . import create_app

        _worker_app = create_app()
    return _worker_app


def send_order_confirmation(order_id: int) -> str:
    """Pretend to email the customer, then mark the order confirmed."""
    if has_app_context():
        return _send(order_id)
    with _app_for_worker().app_context():
        return _send(order_id)


def _send(order_id: int) -> str:
    order = db.session.get(Order, order_id)
    if order is None:
        return "order_missing"
    # Idempotent: running the job twice must not change the outcome
    # (same principle as your Stripe webhook handling).
    if order.status == "confirmed":
        return "already_confirmed"
    log.info("Sending confirmation for order %s to %s", order.id, order.customer_email)
    order.status = "confirmed"
    db.session.commit()
    return "confirmed"
