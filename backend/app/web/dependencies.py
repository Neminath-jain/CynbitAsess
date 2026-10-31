"""FastAPI route dependencies for database sessions and domain services."""
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.db.session import DatabaseManager, get_db_manager
from app.adapters.llm_client import BaseLLMClient, get_llm_client
from app.config import Settings, get_settings
from app.services.ingestion import IngestionService
from app.services.review_service import ReviewService
from app.services.sanitizer import InputSanitizerService


def get_db(settings: Annotated[Settings, Depends(get_settings)]) -> Generator[Session, None, None]:
    """Provide a transactional synchronous database session for request lifetime."""
    manager: DatabaseManager = get_db_manager(settings)
    session: Session = manager.session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_review_service(settings: Annotated[Settings, Depends(get_settings)]) -> ReviewService:
    """Dependency provider for ReviewService."""
    llm_client: BaseLLMClient = get_llm_client(settings)
    ingestion_service = IngestionService()
    sanitizer_service = InputSanitizerService()
    return ReviewService(
        settings=settings,
        ingestion_service=ingestion_service,
        sanitizer_service=sanitizer_service,
        llm_client=llm_client,
    )
