"""Request validation with pydantic.

Rails equivalent: strong parameters (params.require(...).permit(...)) plus
model validations, combined. Parse the incoming JSON through one of these
classes; invalid input raises ValidationError, which create_app() turns into a 422.
"""
import re

from pydantic import BaseModel, Field, field_validator

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ShopCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    city: str = Field(min_length=1, max_length=80)


class MenuItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price_pence: int = Field(gt=0)


class OrderItemIn(BaseModel):
    menu_item_id: int
    quantity: int = Field(ge=1, le=50)


class OrderCreate(BaseModel):
    customer_email: str
    items: list[OrderItemIn] = Field(min_length=1)

    @field_validator("customer_email")
    @classmethod
    def _check_email(cls, value: str) -> str:
        if not _EMAIL.match(value):
            raise ValueError("invalid email address")
        return value.lower()
