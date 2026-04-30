from app.api.routes.documents import router as documents_router
from app.api.routes.query import router as query_router
from app.api.routes.google_drive import router as google_drive_router
from app.api.routes.auth import router as auth_router

__all__ = ["documents_router", "query_router", "google_drive_router", "auth_router"]
