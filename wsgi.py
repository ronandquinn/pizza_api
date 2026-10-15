"""WSGI entry point. Gunicorn imports `app` from here.
Rails equivalent: config.ru."""
from app import create_app

app = create_app()
