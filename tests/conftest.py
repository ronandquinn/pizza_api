"""Shared pytest fixtures.  Rails equivalent: spec/rails_helper.rb + FactoryBot setup."""
import fakeredis
import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def app():
    app = create_app("testing")
    app.extensions["redis"] = fakeredis.FakeRedis()  # no real Redis needed in tests
    with app.app_context():
        db.create_all()  # in-memory SQLite; real databases use migrations
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def shop_with_menu(client):
    shop = client.post("/shops", json={"name": "Tony's Slice", "city": "Belfast"}).get_json()
    margherita = client.post(f"/shops/{shop['id']}/menu", json={"name": "Margherita", "price_pence": 1000}).get_json()
    pepperoni = client.post(f"/shops/{shop['id']}/menu", json={"name": "Pepperoni", "price_pence": 1200}).get_json()
    return shop, margherita, pepperoni
