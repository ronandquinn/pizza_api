def test_create_and_list_shops(client):
    created = client.post("/shops", json={"name": "Tony's Slice", "city": "Belfast"})
    assert created.status_code == 201
    listing = client.get("/shops").get_json()
    assert [s["name"] for s in listing] == ["Tony's Slice"]


def test_create_shop_validation(client):
    response = client.post("/shops", json={"name": ""})
    assert response.status_code == 422
    assert response.get_json()["error"] == "validation_failed"


def test_menu_for_unknown_shop_is_404(client):
    assert client.get("/shops/999/menu").status_code == 404


def test_menu_item_requires_positive_price(client, shop_with_menu):
    shop, *_ = shop_with_menu
    response = client.post(f"/shops/{shop['id']}/menu", json={"name": "Free pizza", "price_pence": 0})
    assert response.status_code == 422
