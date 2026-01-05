from __future__ import annotations

from typing import Any

from src.api.core.errors import raise_schema_not_ready
from src.api.core.supabase_client import get_supabase_admin_client


def _maybe_schema_error(exc: Exception) -> bool:
    """Heuristic to detect missing table/schema errors from Supabase/PostgREST."""
    msg = str(exc).lower()
    return any(
        token in msg
        for token in [
            "could not find",
            "does not exist",
            "relation",
            "schema cache",
            "not found",
            "postgrest",
        ]
    )


class SupabaseRepository:
    """Repository wrapping Supabase PostgREST calls.

    Tables expected (recommended):
    - menu_items: id, name, description, price, image_url
    - cart_items: id, user_id, menu_item_id, quantity
    - orders: id, user_id, status, created_at
    - order_items: id, order_id, menu_item_id, quantity, unit_price, name
    """

    def __init__(self) -> None:
        self.sb = get_supabase_admin_client()

    # PUBLIC_INTERFACE
    def list_menu_items(self) -> list[dict[str, Any]]:
        """List menu items."""
        try:
            res = self.sb.table("menu_items").select("*").order("name").execute()
            return res.data or []
        except Exception as e:
            if _maybe_schema_error(e):
                raise_schema_not_ready("Menu is unavailable: table `menu_items` not found.")
            raise

    # PUBLIC_INTERFACE
    def get_menu_item(self, menu_item_id: str) -> dict[str, Any] | None:
        """Fetch a single menu item by id."""
        try:
            res = (
                self.sb.table("menu_items")
                .select("*")
                .eq("id", menu_item_id)
                .maybe_single()
                .execute()
            )
            return res.data
        except Exception as e:
            if _maybe_schema_error(e):
                raise_schema_not_ready("Menu is unavailable: table `menu_items` not found.")
            raise

    # PUBLIC_INTERFACE
    def list_cart_items(self, user_id: str) -> list[dict[str, Any]]:
        """List cart items for a user."""
        try:
            res = self.sb.table("cart_items").select("*").eq("user_id", user_id).execute()
            return res.data or []
        except Exception as e:
            if _maybe_schema_error(e):
                raise_schema_not_ready("Cart is unavailable: table `cart_items` not found.")
            raise

    # PUBLIC_INTERFACE
    def upsert_cart_item(self, user_id: str, menu_item_id: str, quantity: int) -> dict[str, Any]:
        """Insert or update a cart item for (user_id, menu_item_id)."""
        try:
            # First try to find existing item.
            existing = (
                self.sb.table("cart_items")
                .select("*")
                .eq("user_id", user_id)
                .eq("menu_item_id", menu_item_id)
                .maybe_single()
                .execute()
            )
            if existing.data:
                updated = (
                    self.sb.table("cart_items")
                    .update({"quantity": quantity})
                    .eq("id", existing.data["id"])
                    .select("*")
                    .single()
                    .execute()
                )
                return updated.data

            inserted = (
                self.sb.table("cart_items")
                .insert({"user_id": user_id, "menu_item_id": menu_item_id, "quantity": quantity})
                .select("*")
                .single()
                .execute()
            )
            return inserted.data
        except Exception as e:
            if _maybe_schema_error(e):
                raise_schema_not_ready("Cart is unavailable: table `cart_items` not found.")
            raise

    # PUBLIC_INTERFACE
    def update_cart_item_quantity(self, user_id: str, item_id: str, quantity: int) -> dict[str, Any] | None:
        """Update quantity for a cart item (must belong to user)."""
        try:
            # Ensure user ownership.
            existing = (
                self.sb.table("cart_items")
                .select("*")
                .eq("id", item_id)
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            if not existing.data:
                return None

            updated = (
                self.sb.table("cart_items")
                .update({"quantity": quantity})
                .eq("id", item_id)
                .select("*")
                .single()
                .execute()
            )
            return updated.data
        except Exception as e:
            if _maybe_schema_error(e):
                raise_schema_not_ready("Cart is unavailable: table `cart_items` not found.")
            raise

    # PUBLIC_INTERFACE
    def delete_cart_item(self, user_id: str, item_id: str) -> bool:
        """Delete a cart item (must belong to user)."""
        try:
            res = self.sb.table("cart_items").delete().eq("id", item_id).eq("user_id", user_id).execute()
            return bool(res.data)
        except Exception as e:
            if _maybe_schema_error(e):
                raise_schema_not_ready("Cart is unavailable: table `cart_items` not found.")
            raise

    # PUBLIC_INTERFACE
    def clear_cart(self, user_id: str) -> None:
        """Remove all cart items for a user."""
        try:
            self.sb.table("cart_items").delete().eq("user_id", user_id).execute()
        except Exception as e:
            if _maybe_schema_error(e):
                raise_schema_not_ready("Cart is unavailable: table `cart_items` not found.")
            raise

    # PUBLIC_INTERFACE
    def create_order(self, user_id: str, status: str = "created") -> dict[str, Any]:
        """Create an order header record."""
        try:
            res = (
                self.sb.table("orders")
                .insert({"user_id": user_id, "status": status})
                .select("*")
                .single()
                .execute()
            )
            return res.data
        except Exception as e:
            if _maybe_schema_error(e):
                raise_schema_not_ready("Checkout is unavailable: table `orders` not found.")
            raise

    # PUBLIC_INTERFACE
    def insert_order_item(
        self,
        order_id: str,
        menu_item_id: str,
        quantity: int,
        unit_price: float,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Insert a line item for an order."""
        try:
            payload: dict[str, Any] = {
                "order_id": order_id,
                "menu_item_id": menu_item_id,
                "quantity": quantity,
                "unit_price": unit_price,
            }
            if name is not None:
                payload["name"] = name

            res = self.sb.table("order_items").insert(payload).select("*").single().execute()
            return res.data
        except Exception as e:
            if _maybe_schema_error(e):
                raise_schema_not_ready("Checkout is unavailable: table `order_items` not found.")
            raise

    # PUBLIC_INTERFACE
    def list_orders(self, user_id: str) -> list[dict[str, Any]]:
        """List orders for a user."""
        try:
            res = self.sb.table("orders").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            if _maybe_schema_error(e):
                raise_schema_not_ready("Orders are unavailable: table `orders` not found.")
            raise

    # PUBLIC_INTERFACE
    def get_order(self, user_id: str, order_id: str) -> dict[str, Any] | None:
        """Get an order header by id, limited to a user."""
        try:
            res = (
                self.sb.table("orders")
                .select("*")
                .eq("id", order_id)
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            return res.data
        except Exception as e:
            if _maybe_schema_error(e):
                raise_schema_not_ready("Orders are unavailable: table `orders` not found.")
            raise

    # PUBLIC_INTERFACE
    def list_order_items(self, order_id: str) -> list[dict[str, Any]]:
        """List items for an order."""
        try:
            res = self.sb.table("order_items").select("*").eq("order_id", order_id).execute()
            return res.data or []
        except Exception as e:
            if _maybe_schema_error(e):
                raise_schema_not_ready("Orders are unavailable: table `order_items` not found.")
            raise
