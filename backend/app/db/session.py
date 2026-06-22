import ssl
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings


def _build_connect_args() -> dict:
    """asyncpg-specific options for Postgres / Supabase.

    - statement_cache_size=0 keeps us compatible with the Supabase pooler
      (pgbouncer transaction mode), which rejects prepared statements.
    - ssl: Supabase requires TLS. We require encryption but skip full chain
      verification (equivalent to libpq sslmode=require), because the pooler
      presents a cert that isn't in the default CA bundle. For production,
      bundle Supabase's CA and switch to a verifying context.
    SQLite ignores these — they are only applied for the asyncpg driver.
    """
    if not settings.DATABASE_URL.startswith("postgresql+asyncpg"):
        return {}
    args: dict = {}
    if settings.DB_DISABLE_STATEMENT_CACHE:
        args["statement_cache_size"] = 0
    if settings.DB_SSL:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        args["ssl"] = ctx
    return args


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,  # transparently recycle connections the pooler dropped
    connect_args=_build_connect_args(),
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
