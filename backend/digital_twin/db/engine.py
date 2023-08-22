from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import Session

from digital_twin.config.app_config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)

SYNC_DB_API = "psycopg2"
ASYNC_DB_API = "asyncpg"

# global so we don't create more than one engine per process
# outside of being best practice, this is needed so we can properly pool
# connections and not create a new pool on every request
_SYNC_ENGINE: Engine | None = None
_ASYNC_ENGINE: AsyncEngine | None = None


def get_db_current_time(db_session: Session) -> datetime:
    result = db_session.execute(text("SELECT NOW()")).scalar()
    if result is None:
        raise ValueError("Database did not return a time")
    return result


def translate_db_time_to_server_time(db_time: datetime, db_session: Session) -> datetime:
    server_now = datetime.now()
    db_now = get_db_current_time(db_session)
    time_diff = server_now - db_now.astimezone(timezone.utc).replace(tzinfo=None)
    return db_time + time_diff


def build_connection_string(
    *,
    db_api: str = ASYNC_DB_API,
    user: str = POSTGRES_USER,
    password: str = POSTGRES_PASSWORD,
    host: str = POSTGRES_HOST,
    port: str = POSTGRES_PORT,
    db: str = POSTGRES_DB,
) -> str:
    return f"postgresql+{db_api}://{user}:{password}@{host}:{port}/{db}"


def get_sqlalchemy_engine(pool_pre_ping: bool = False) -> Engine:
    global _SYNC_ENGINE
    if _SYNC_ENGINE is None:
        connection_string = build_connection_string(db_api=SYNC_DB_API)
        _SYNC_ENGINE = create_engine(connection_string)
    return _SYNC_ENGINE


def get_sqlalchemy_async_engine(pool_pre_ping: bool = False) -> AsyncEngine:
    global _ASYNC_ENGINE
    if _ASYNC_ENGINE is None:
        connection_string = build_connection_string()
        # NOTE: pool_pre_ping as per https://stackoverflow.com/questions/70468354/fastapi-sqlalchemy-connection-was-closed-in-the-middle-of-operation
        _ASYNC_ENGINE = create_async_engine(connection_string, pool_pre_ping=pool_pre_ping)
    return _ASYNC_ENGINE


def get_session_generator() -> Generator[Session, None, None]:
    with Session(get_sqlalchemy_engine(), expire_on_commit=False) as session:
        yield session


async def get_async_session_generator() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(get_sqlalchemy_async_engine(), expire_on_commit=False) as async_session:
        yield async_session


def get_async_session(pool_pre_ping: bool = False) -> AsyncSession:
    return AsyncSession(get_sqlalchemy_async_engine(pool_pre_ping), expire_on_commit=False)


def get_session(pool_pre_ping: bool = False) -> Session:
    return Session(get_sqlalchemy_engine(pool_pre_ping), expire_on_commit=False)
