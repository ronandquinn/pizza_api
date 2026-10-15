"""Order endpoints.  Rails equivalent: OrdersController#create / #show."""
from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Order, Shop
from ..schemas import OrderCreate
from ..services import orders as order_service

bp = Blueprint("orders", __name__)


@bp.post("/shops/<int:shop_id>/orders")
def create_order(shop_id: int):
    shop = db.get_or_404(Shop, shop_id)
    data = OrderCreate.model_validate(request.get_json(silent=True) or {})
    try:
        order = order_service.create_order(shop, data)
    except order_service.InvalidMenuItem as err:
        return jsonify(error="invalid_menu_item", menu_item_id=err.menu_item_id), 422
    return jsonify(order.to_dict()), 201


@bp.get("/orders/<int:order_id>")
def show_order(order_id: int):
    order = db.get_or_404(Order, order_id)
    return jsonify(order.to_dict())
