from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.api.models.menu import MenuItem, MenuListResponse
from src.api.services.repository import SupabaseRepository

router = APIRouter(prefix="", tags=["Menu"])


@router.get(
    "/menu",
    response_model=MenuListResponse,
    summary="Get menu items",
    description="Return the list of available menu items.",
    operation_id="get_menu",
)
# PUBLIC_INTERFACE
def get_menu() -> MenuListResponse:
    """Get menu items.

    Returns:
        MenuListResponse: Menu items list.
    """
    repo = SupabaseRepository()
    items_raw = repo.list_menu_items()

    items: list[MenuItem] = []
    for r in items_raw:
        try:
            items.append(
                MenuItem(
                    id=str(r.get("id")),
                    name=r.get("name") or "",
                    description=r.get("description") or "",
                    price=float(r.get("price") or 0),
                    image_url=r.get("image_url") or r.get("imageUrl"),
                )
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid menu item row: {type(e).__name__}",
            ) from e

    return MenuListResponse(items=items)
