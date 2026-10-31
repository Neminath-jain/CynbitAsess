"""Main application entrypoint re-exporting app from app.web.main."""
from app.web.main import app, create_app

__all__ = ["app", "create_app"]
