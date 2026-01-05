from __future__ import annotations

from pydantic import BaseModel, Field


class MenuItem(BaseModel):
    """Menu item returned by GET /menu."""

    id: str = Field(..., description="Menu item id (UUID or slug).")
    name: str = Field(..., description="Display name.")
    description: str = Field("", description="Item description.")
    price: float = Field(..., ge=0, description="Unit price.")
    image_url: str | None = Field(None, description="Optional image URL.")


class MenuListResponse(BaseModel):
    """Response for GET /menu."""

    items: list[MenuItem] = Field(default_factory=list, description="List of menu items.")
