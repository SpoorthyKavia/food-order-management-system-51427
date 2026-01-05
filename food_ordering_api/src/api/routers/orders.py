from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps.auth import AuthContext, require_auth
from src.api.models.orders import CheckoutResponse, ListOrdersResponse, Order, OrderItem
from src.api.services.repository import SupabaseRepository

router = APIRouter(prefix="", tags=["Orders"])


def _build_order(repo: SupabaseRepository, order_row: dict, items_rows: list[dict]) -> Order:
    items: list[OrderItem] = []
    total = 0.0
    for r in items_rows:
        unit_price = float(r.get("unit_price") or 0)
        qty = int(r.get("quantity") or 1)
        total += unit_price * qty

        items.append(
            OrderItem(
                id=str(r.get("id")),
                menu_item_id=str(r.get("menu_item_id")),
                quantity=qty,
                unit_price=unit_price,
                name=r.get("name"),
            )
        )

    return Order(
        id=str(order_row.get("id")),
        user_id=str(order_row.get("user_id")),
        status=str(order_row.get("status") or "created"),
        created_at=order_row.get("created_at"),
        total=round(total, 2),
        items=items,
    )


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Checkout",
    description="Create an order from the authenticated user's current cart and clear the cart.",
    operation_id="checkout",
)
# PUBLIC_INTERFACE
def checkout(ctx: AuthContext = Depends(require_auth)) -> CheckoutResponse:
    """Checkout current cart and create an order."""
    repo = SupabaseRepository()

    cart_items = repo.list_cart_items(ctx.user_id)
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty.")

    order_row = repo.create_order(ctx.user_id, status="created")

    order_items_rows: list[dict] = []
    for c in cart_items:
        menu_item_id = str(c.get("menu_item_id"))
        qty = int(c.get("quantity") or 1)

        menu = repo.get_menu_item(menu_item_id)
        if not menu:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Menu item no longer exists: {menu_item_id}",
            )

        unit_price = float(menu.get("price") or 0)
        name = menu.get("name")

        order_items_rows.append(
            repo.insert_order_item(
                order_id=str(order_row["id"]),
                menu_item_id=menu_item_id,
                quantity=qty,
                unit_price=unit_price,
                name=name,
            )
        )

    # Clear cart after successful creation.
    repo.clear_cart(ctx.user_id)

    order = _build_order(repo, order_row, order_items_rows)
    return CheckoutResponse(order=order)


@router.get(
    "/orders",
    response_model=ListOrdersResponse,
    summary="List orders",
    description="List orders for the authenticated user.",
    operation_id="list_orders",
)
# PUBLIC_INTERFACE
def list_orders(ctx: AuthContext = Depends(require_auth)) -> ListOrdersResponse:
    """List orders for the current user."""
    repo = SupabaseRepository()
    orders_rows = repo.list_orders(ctx.user_id)

    orders: list[Order] = []
    for row in orders_rows:
        items = repo.list_order_items(str(row.get("id")))
        orders.append(_build_order(repo, row, items))

    return ListOrdersResponse(orders=orders)


@router.get(
    "/orders/{order_id}",
    response_model=Order,
    summary="Get order details",
    description="Get a single order and its items for the authenticated user.",
    operation_id="get_order",
)
# PUBLIC_INTERFACE
def get_order(order_id: str, ctx: AuthContext = Depends(require_auth)) -> Order:
    """Get a single order for the current user."""
    repo = SupabaseRepository()
    order_row = repo.get_order(ctx.user_id, order_id)
    if not order_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    items = repo.list_order_items(order_id)
    return _build_order(repo, order_row, items)
