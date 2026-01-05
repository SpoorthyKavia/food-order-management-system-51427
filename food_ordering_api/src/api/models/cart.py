from __future__ import annotations

from pydantic import BaseModel, Field


class CartItem(BaseModel):
    """A cart item stored for a given user."""

    id: str = Field(..., description="Cart item id (UUID).")
    user_id: str = Field(..., description="Supabase user id.")
    menu_item_id: str = Field(..., description="Menu item id.")
    quantity: int = Field(..., ge=1, description="Quantity for this item.")
    name: str | None = Field(None, description="Denormalized name for convenience (optional).")
    price: float | None = Field(None, ge=0, description="Denormalized price for convenience (optional).")
    image_url: str | None = Field(None, description="Denormalized image URL for convenience (optional).")


class CartResponse(BaseModel):
    """Response for GET /cart."""

    items: list[CartItem] = Field(default_factory=list, description="Cart items.")
    subtotal: float = Field(0, ge=0, description="Computed subtotal (sum of price*quantity where available).")


class AddToCartRequest(BaseModel):
    """Request payload for POST /cart."""

    menu_item_id: str = Field(..., description="Menu item id to add.")
    quantity: int = Field(1, ge=1, description="Quantity to add (default 1).")


class UpdateCartItemRequest(BaseModel):
    """Request payload for PATCH /cart/{item_id}."""

    quantity: int = Field(..., ge=1, description="New quantity.")


class AddToCartResponse(BaseModel):
    """Response payload for POST /cart."""

    item: CartItem = Field(..., description="The resulting cart item.")
