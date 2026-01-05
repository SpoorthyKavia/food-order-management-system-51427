from __future__ import annotations

from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    """Item line on an order."""

    id: str = Field(..., description="Order item id (UUID).")
    menu_item_id: str = Field(..., description="Menu item id.")
    quantity: int = Field(..., ge=1, description="Quantity ordered.")
    unit_price: float = Field(..., ge=0, description="Unit price captured at checkout.")
    name: str | None = Field(None, description="Denormalized name.")


class Order(BaseModel):
    """Order resource."""

    id: str = Field(..., description="Order id (UUID).")
    user_id: str = Field(..., description="Supabase user id.")
    status: str = Field(..., description="Order status, e.g. created, confirmed, preparing, delivered.")
    created_at: str | None = Field(None, description="ISO timestamp.")
    total: float = Field(0, ge=0, description="Computed total for the order.")
    items: list[OrderItem] = Field(default_factory=list, description="Order items.")


class CheckoutResponse(BaseModel):
    """Response for POST /checkout."""

    order: Order = Field(..., description="Created order with items.")


class ListOrdersResponse(BaseModel):
    """Response for GET /orders."""

    orders: list[Order] = Field(default_factory=list, description="Orders belonging to the authenticated user.")
