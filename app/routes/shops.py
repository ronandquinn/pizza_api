"""Shop and menu endpoints.

Rails equivalent: ShopsController + MenuItemsController and their routes.
A Blueprint is a group of routes (like a routes.rb `resources` block); the
route function plays the role of a controller action.
"""
from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import MenuItem, Shop
from ..schemas import MenuItemCreate, ShopCreate

bp = Blueprint("shops", __name__, url_prefix="/shops")


@bp.post("")
def create_shop():
    data = ShopCreate.model_validate(request.get_json(silent=True) or {})
    shop = Shop(name=data.name, city=data.city)
    db.session.add(shop)
    db.session.commit()
    return jsonify(shop.to_dict()), 201


@bp.get("")
def list_shops():
    shops = db.session.scalars(db.select(Shop).order_by(Shop.id)).all()
    return jsonify([s.to_dict() for s in shops])


@bp.post("/<int:shop_id>/menu")
def add_menu_item(shop_id: int):
    shop = db.get_or_404(Shop, shop_id)
    data = MenuItemCreate.model_validate(request.get_json(silent=True) or {})
    item = MenuItem(shop_id=shop.id, name=data.name, price_pence=data.price_pence)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.get("/<int:shop_id>/menu")
def list_menu(shop_id: int):
    shop = db.get_or_404(Shop, shop_id)
    return jsonify([i.to_dict() for i in shop.menu_items])
