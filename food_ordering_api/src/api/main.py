from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.cart import router as cart_router
from src.api.routers.menu import router as menu_router
from src.api.routers.orders import router as orders_router


# PUBLIC_INTERFACE
def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A configured FastAPI app including CORS and API routers.
    """
    openapi_tags = [
        {"name": "Health", "description": "Service health and diagnostics."},
        {"name": "Menu", "description": "Menu browsing endpoints."},
        {"name": "Cart", "description": "Cart CRUD endpoints."},
        {"name": "Orders", "description": "Checkout and order tracking endpoints."},
    ]

    app = FastAPI(
        title="Food Ordering API",
        description=(
            "Backend APIs for menu browsing, cart management, and ordering.\n\n"
            "Authentication:\n"
            "- Pass a Supabase Auth JWT from the frontend via `Authorization: Bearer <token>`.\n"
            "- The API verifies the token against Supabase and uses the authenticated user's id.\n\n"
            "Database:\n"
            "- Uses Supabase PostgREST via the Python client.\n"
            "- If required tables are not present yet, endpoints return 501 with guidance."
        ),
        version="0.2.0",
        openapi_tags=openapi_tags,
    )

    # CORS: allow the local React dev server explicitly (per requirements)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get(
        "/",
        tags=["Health"],
        summary="Health check",
        description="Simple health check endpoint to verify the API is running.",
        operation_id="health_check",
    )
    # PUBLIC_INTERFACE
    def health_check():
        """Health check endpoint.

        Returns:
            JSON payload indicating service health.
        """
        return {"message": "Healthy"}

    # Register routers
    app.include_router(menu_router)
    app.include_router(cart_router)
    app.include_router(orders_router)

    return app


app = create_app()
