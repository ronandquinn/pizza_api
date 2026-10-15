def test_create_order_totals_and_confirms(client, shop_with_menu):
    shop, margherita, pepperoni = shop_with_menu
    response = client.post(
        f"/shops/{shop['id']}/orders",
        json={
            "customer_email": "Sam@Example.com",
            "items": [
                {"menu_item_id": margherita["id"], "quantity": 2},
                {"menu_item_id": pepperoni["id"], "quantity": 1},
            ],
        },
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["total_pence"] == 2 * 1000 + 1200
    assert body["customer_email"] == "sam@example.com"  # normalised by the schema

    # Jobs run inline in tests (QUEUE_ASYNC = False), so the order is already confirmed
    fetched = client.get(f"/orders/{body['id']}").get_json()
    assert fetched["status"] == "confirmed"


def test_order_rejects_item_from_another_shop(client, shop_with_menu):
    shop, margherita, _ = shop_with_menu
    other = client.post("/shops", json={"name": "Other", "city": "Derry"}).get_json()
    response = client.post(
        f"/shops/{other['id']}/orders",
        json={"customer_email": "a@b.co", "items": [{"menu_item_id": margherita["id"], "quantity": 1}]},
    )
    assert response.status_code == 422
    assert response.get_json()["error"] == "invalid_menu_item"


def test_order_validation(client, shop_with_menu):
    shop, *_ = shop_with_menu
    response = client.post(f"/shops/{shop['id']}/orders", json={"customer_email": "nope", "items": []})
    assert response.status_code == 422


def test_confirmation_job_is_idempotent(app, client, shop_with_menu):
    from app.jobs import send_order_confirmation

    shop, margherita, _ = shop_with_menu
    order = client.post(
        f"/shops/{shop['id']}/orders",
        json={"customer_email": "a@b.co", "items": [{"menu_item_id": margherita["id"], "quantity": 1}]},
    ).get_json()
    assert send_order_confirmation(order["id"]) == "already_confirmed"


def test_service_creates_order_without_http(app, shop_with_menu):
    """The service can be tested directly: no client, no JSON, no status codes."""
    import pytest

    from app.extensions import db
    from app.models import Shop
    from app.schemas import OrderCreate
    from app.services import orders as order_service

    shop_json, margherita, _ = shop_with_menu
    shop = db.session.get(Shop, shop_json["id"])
    order = order_service.create_order(
        shop, OrderCreate(customer_email="a@b.co", items=[{"menu_item_id": margherita["id"], "quantity": 3}])
    )
    assert order.total_pence == 3000

    with pytest.raises(order_service.InvalidMenuItem):
        order_service.create_order(
            shop, OrderCreate(customer_email="a@b.co", items=[{"menu_item_id": 9999, "quantity": 1}])
        )
