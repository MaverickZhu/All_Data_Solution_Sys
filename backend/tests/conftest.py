import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Any, AsyncGenerator
import os
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.core.database import Base, get_db
from backend.main import app
from backend.core.security import create_access_token
from backend.models.user import User
from backend.models.project import Project


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing test collection and execution.
    This is the earliest point to reliably modify settings for all tests.
    """
    from backend.core.config import settings
    from backend.core.celery_app import celery_app
    
    # Force the app into testing mode
    settings.testing = True
    
    # Force celery to run tasks eagerly and in-memory, bypassing Redis
    settings.celery_task_always_eager = True
    settings.celery_broker_url = 'memory://'
    settings.celery_result_backend = 'memory://'
    
    # Reconfigure the existing celery_app instance with the new settings
    celery_app.conf.update(
        broker_url=settings.celery_broker_url,
        result_backend=settings.celery_result_backend,
        task_always_eager=settings.celery_task_always_eager
    )


# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function")
async def db_engine():
    """Fixture that creates a new in-memory async database engine for every test."""
    engine = create_async_engine(TEST_DATABASE_URL)
    
    # Import all models here to ensure they are registered with Base
    from backend.models import User, Project, DataSource, Task
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, Any]:
    """Fixture that provides a transactional async session for each test."""
    async with db_engine.connect() as connection:
        async with connection.begin() as transaction:
            SessionLocal = async_sessionmaker(
                bind=connection,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            async with SessionLocal() as session:
                yield session
                await transaction.rollback()


# --- Sync fixtures for Celery task testing ---

@pytest.fixture(scope="function")
def sync_db_engine():
    """Fixture that creates a sync in-memory SQLite engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="function")
def sync_db_session(sync_db_engine) -> Generator[Session, Any, None]:
    """Fixture that provides a sync session for task testing."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_db_engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Common fixtures (API and others) ---

@pytest.fixture(scope="function")
async def async_client(db_session) -> AsyncGenerator[httpx.AsyncClient, Any]:
    """Create an async client for testing the API."""
    
    async def override_get_db() -> AsyncGenerator[AsyncSession, Any]:
        """Dependency override to use the test session."""
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(db_session) -> User:
    """Create a test user in the database."""
    user = User(
        email="testuser@example.com", 
        hashed_password="testpassword",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> dict:
    """Return authentication headers for a test user."""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
async def test_project(db_session, test_user: User) -> Project:
    """Create a test project for the test user."""
    project = Project(name="Test Project", user_id=test_user.id)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project