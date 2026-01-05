from __future__ import annotations

from fastapi import HTTPException, status


# PUBLIC_INTERFACE
def raise_schema_not_ready(detail: str) -> None:
    """Raise a standardized error when DB schema is not ready.

    Args:
        detail: Human-readable detail about the missing table/schema.

    Raises:
        HTTPException(501)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            f"{detail} "
            "Database schema may not be provisioned yet. "
            "Please create required tables in Supabase: menu_items, cart_items, orders, order_items."
        ),
    )
