from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

# Resolve database path: if relative, make it relative to the project root (backend/../)
_db_url = settings.database_url
if ":///" in _db_url and not _db_url.split(":///", 1)[1].startswith("/"):
    # Relative path like sqlite+aiosqlite:///./data/pubmed_bot.db
    _project_root = Path(__file__).resolve().parent.parent.parent  # backend/app -> backend -> project root
    _rel_path = _db_url.split(":///", 1)[1]
    _abs_path = (_project_root / _rel_path).resolve()
    _abs_path.parent.mkdir(parents=True, exist_ok=True)
    _db_url = f"sqlite+aiosqlite:///{_abs_path}"

engine = create_async_engine(_db_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        # create_all only creates tables that don't exist yet — it never drops or recreates
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            __import__("sqlalchemy").text("PRAGMA journal_mode=WAL")
        )


async def get_db():
    async with async_session() as session:
        yield session
