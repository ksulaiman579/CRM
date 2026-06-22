import os
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from dotenv import load_dotenv

# Load env file from backend/ directory relative to tests/
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

# Ensure required fields have values in environment
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///sqlite_test.db"
if "SECRET_KEY" not in os.environ:
    os.environ["SECRET_KEY"] = "super_secret_key_change_in_production"

# Overwrite settings database URL before importing anything else
from app.config import settings
settings.DATABASE_URL = "sqlite+aiosqlite:///sqlite_test.db"


from app.main import app
from app.db.base import Base
from app.db.session import engine, get_db
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.ticket import SlaPolicy
from app.models.user import Team, User
from app.core.security import hash_password

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    # Recreate tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    # Seed teams and SLA policies required for ticket tests
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        # Seed SLA Policies
        sla_low = SlaPolicy(name="Low Priority", priority="low", first_response_mins=480, resolution_mins=7200)
        sla_med = SlaPolicy(name="Medium Priority", priority="medium", first_response_mins=240, resolution_mins=1440)
        sla_high = SlaPolicy(name="High Priority", priority="high", first_response_mins=60, resolution_mins=480)
        sla_crit = SlaPolicy(name="Critical Priority", priority="critical", first_response_mins=15, resolution_mins=240)
        session.add_all([sla_low, sla_med, sla_high, sla_crit])
        
        # Seed Teams
        team1 = Team(name="Tier 1 Support", description="First line support")
        team2 = Team(name="Tier 2 Technical", description="Advanced technical support")
        team3 = Team(name="Billing Support", description="Billing inquiries")
        session.add_all([team1, team2, team3])

        # Fixed superuser used by tests to provision other accounts.
        session.add(User(
            username="admin", email="admin@telecom-crm.com", full_name="System Administrator",
            password_hash=hash_password("admin"), role="superuser", must_change_password=False,
        ))

        await session.commit()
        
    yield
    
    # Cleanup database file after session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Remove test file if it exists
    if os.path.exists("sqlite_test.db"):
        try:
            os.remove("sqlite_test.db")
        except Exception:
            pass

@pytest_asyncio.fixture
async def db_session():
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client():
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
