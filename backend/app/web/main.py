from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.db.session import get_db_manager
from app.config import Settings, get_settings
from app.web.errors import register_exception_handlers
from app.web.middleware import RequestIDMiddleware
from app.web.routes.reviews import router as reviews_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager to initialize resources."""
    settings = getattr(app.state, "settings", get_settings())
    # Ensure database tables exist
    db_manager = get_db_manager(settings)
    db_manager.create_tables()
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure a production-ready FastAPI application."""
    active_settings = settings or get_settings()

    app = FastAPI(
        title="BitElevate PR Review Copilot",
        description="AI first-pass pull request review and human mentor triage engine.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = active_settings

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID tracking
    app.add_middleware(RequestIDMiddleware)

    # Centralized exception handlers
    register_exception_handlers(app)

    # Attach routers
    app.include_router(reviews_router)

    @app.get("/health", tags=["System"], operation_id="health_check")
    async def health_check() -> dict[str, str]:
        """Health check endpoint verifying application operational status."""
        return {"status": "ok", "app_env": active_settings.APP_ENV}

    return app


app = create_app()
