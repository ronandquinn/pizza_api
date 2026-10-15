"""Order business logic.  Rails equivalent: a service object (app/services/create_order.rb).

Routes stay thin: they parse the request and turn exceptions into HTTP responses.
The rules (shop ownership, price snapshot, totals, when to enqueue) live here, so they
can be tested without HTTP and reused from a CLI command or a job.
"""
from sqlalchemy import select

from ..extensions import db
from ..jobs import send_order_confirmation
from ..models import MenuItem, Order, OrderItem, Shop
from ..queue import get_queue
from ..schemas import OrderCreate


class InvalidMenuItem(Exception):
    """A requested menu item doesn't exist or belongs to another shop."""

    def __init__(self, menu_item_id: int):
        super().__init__(f"invalid menu item {menu_item_id}")
        self.menu_item_id = menu_item_id


def create_order(shop: Shop, data: OrderCreate) -> Order:
    # One query for all requested items instead of one per line (avoids N+1)
    ids = {line.menu_item_id for line in data.items}
    menu_items = {
        m.id: m for m in db.session.scalars(select(MenuItem).where(MenuItem.id.in_(ids), MenuItem.shop_id == shop.id))
    }

    order = Order(shop_id=shop.id, customer_email=data.customer_email)
    total = 0
    for line in data.items:
        menu_item = menu_items.get(line.menu_item_id)
        if menu_item is None:
            raise InvalidMenuItem(line.menu_item_id)
        total += menu_item.price_pence * line.quantity
        order.items.append(
            OrderItem(
                menu_item_id=menu_item.id,
                quantity=line.quantity,
                unit_price_pence=menu_item.price_pence,  # snapshot the price at order time
            )
        )
    order.total_pence = total

    db.session.add(order)
    db.session.commit()

    # Enqueue only after the commit, so the worker can always find the row
    get_queue().enqueue(send_order_confirmation, order.id)
    return order
