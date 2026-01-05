from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps.auth import AuthContext, require_auth
from src.api.models.cart import (
    AddToCartRequest,
    AddToCartResponse,
    CartItem,
    CartResponse,
    UpdateCartItemRequest,
)
from src.api.services.repository import SupabaseRepository

router = APIRouter(prefix="", tags=["Cart"])


def _compute_subtotal(items: list[CartItem]) -> float:
    subtotal = 0.0
    for it in items:
        if it.price is not None:
            subtotal += float(it.price) * int(it.quantity)
    return round(subtotal, 2)


def _enrich_cart_items(repo: SupabaseRepository, raw_items: list[dict]) -> list[CartItem]:
    """Enrich cart items by attaching menu item fields when possible."""
    result: list[CartItem] = []
    for r in raw_items:
        menu_item_id = str(r.get("menu_item_id") or r.get("menuItemId") or "")
        menu = repo.get_menu_item(menu_item_id) if menu_item_id else None

        result.append(
            CartItem(
                id=str(r.get("id")),
                user_id=str(r.get("user_id")),
                menu_item_id=menu_item_id,
                quantity=int(r.get("quantity") or 1),
                name=(menu.get("name") if menu else None),
                price=(float(menu.get("price")) if menu and menu.get("price") is not None else None),
                image_url=(menu.get("image_url") if menu else None),
            )
        )
    return result


@router.post(
    "/cart",
    response_model=AddToCartResponse,
    summary="Add item to cart",
    description="Add a menu item to the authenticated user's cart (upserts by menu_item_id).",
    operation_id="add_to_cart",
)
# PUBLIC_INTERFACE
def add_to_cart(payload: AddToCartRequest, ctx: AuthContext = Depends(require_auth)) -> AddToCartResponse:
    """Add an item to the user's cart.

    Args:
        payload: menu_item_id and quantity
        ctx: authenticated user context

    Returns:
        AddToCartResponse containing the resulting cart item.
    """
    repo = SupabaseRepository()

    # Ensure menu item exists (gives clearer errors than inserting unknown id).
    menu = repo.get_menu_item(payload.menu_item_id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found.")

    item_raw = repo.upsert_cart_item(ctx.user_id, payload.menu_item_id, payload.quantity)

    item = _enrich_cart_items(repo, [item_raw])[0]
    return AddToCartResponse(item=item)


@router.get(
    "/cart",
    response_model=CartResponse,
    summary="Get cart",
    description="Return the authenticated user's cart items.",
    operation_id="get_cart",
)
# PUBLIC_INTERFACE
def get_cart(ctx: AuthContext = Depends(require_auth)) -> CartResponse:
    """Get the user's cart."""
    repo = SupabaseRepository()
    raw_items = repo.list_cart_items(ctx.user_id)
    items = _enrich_cart_items(repo, raw_items)
    return CartResponse(items=items, subtotal=_compute_subtotal(items))


@router.patch(
    "/cart/{item_id}",
    response_model=CartItem,
    summary="Update cart item quantity",
    description="Update the quantity for an item in the authenticated user's cart.",
    operation_id="update_cart_item",
)
# PUBLIC_INTERFACE
def update_cart_item(
    item_id: str, payload: UpdateCartItemRequest, ctx: AuthContext = Depends(require_auth)
) -> CartItem:
    """Update cart item quantity."""
    repo = SupabaseRepository()
    updated = repo.update_cart_item_quantity(ctx.user_id, item_id, payload.quantity)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")
    return _enrich_cart_items(repo, [updated])[0]


@router.delete(
    "/cart/{item_id}",
    summary="Remove item from cart",
    description="Remove a cart item from the authenticated user's cart.",
    operation_id="delete_cart_item",
    status_code=status.HTTP_204_NO_CONTENT,
)
# PUBLIC_INTERFACE
def delete_cart_item(item_id: str, ctx: AuthContext = Depends(require_auth)) -> None:
    """Delete a cart item."""
    repo = SupabaseRepository()
    deleted = repo.delete_cart_item(ctx.user_id, item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")
    return None
