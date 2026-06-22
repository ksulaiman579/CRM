from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Telecom CRM"
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 480

    # --- Database driver options (Postgres / Supabase) ---
    # Supabase requires TLS — set DB_SSL=true when pointing at *.supabase.com.
    DB_SSL: bool = False
    # The Supabase connection pooler (port 6543, transaction mode / pgbouncer)
    # does not support prepared statements. Disabling asyncpg's statement cache
    # makes the app pooler-safe. Harmless on direct connections.
    DB_DISABLE_STATEMENT_CACHE: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
