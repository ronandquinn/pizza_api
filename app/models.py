"""SQLAlchemy models.  Rails equivalent: app/models/*.rb (ActiveRecord).

Differences worth knowing:
  * Columns are declared on the class (there is no schema-reading magic like
    ActiveRecord's); the migration is a separate, generated file.
  * Money is stored as integer pence to avoid float rounding.
  * Validations live in the pydantic schemas (app/schemas.py), not on the model.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Shop(db.Model):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)

    menu_items: Mapped[list["MenuItem"]] = relationship(back_populates="shop", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="shop")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "city": self.city}


class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    price_pence: Mapped[int] = mapped_column(Integer, nullable=False)

    shop: Mapped["Shop"] = relationship(back_populates="menu_items")

    def to_dict(self) -> dict:
        return {"id": self.id, "shop_id": self.shop_id, "name": self.name, "price_pence": self.price_pence}


class Order(db.Model):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)
    customer_email: Mapped[str] = mapped_column(String(254), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    total_pence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    shop: Mapped["Shop"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "shop_id": self.shop_id,
            "customer_email": self.customer_email,
            "status": self.status,
            "total_pence": self.total_pence,
            "items": [i.to_dict() for i in self.items],
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_pence: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")

    def to_dict(self) -> dict:
        return {
            "menu_item_id": self.menu_item_id,
            "quantity": self.quantity,
            "unit_price_pence": self.unit_price_pence,
        }
