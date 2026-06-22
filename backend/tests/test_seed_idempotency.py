import pytest
from sqlalchemy import select, func
from app.db.seed import seed_data
from app.models.customer import Customer
from app.models.ticket import Ticket
from app.models.plan import Plan
from app.models.user import User

@pytest.mark.asyncio
async def test_seed_idempotency(db_session):
    # 1. Run seed script for the first time
    await seed_data()
    
    # Get initial seeded counts
    customer_count_1 = await db_session.scalar(select(func.count()).select_from(Customer))
    ticket_count_1 = await db_session.scalar(select(func.count()).select_from(Ticket))
    plan_count_1 = await db_session.scalar(select(func.count()).select_from(Plan))
    user_count_1 = await db_session.scalar(select(func.count()).select_from(User))
    
    assert customer_count_1 == 120
    assert ticket_count_1 == 200
    assert plan_count_1 == 12
    # 9 seeded users + any registered users (from other tests if run sequentially, but this is fine)
    assert user_count_1 >= 9
    
    # 2. Run seed script for the second time
    await seed_data()
    
    # Verify counts did not double or change
    customer_count_2 = await db_session.scalar(select(func.count()).select_from(Customer))
    ticket_count_2 = await db_session.scalar(select(func.count()).select_from(Ticket))
    plan_count_2 = await db_session.scalar(select(func.count()).select_from(Plan))
    user_count_2 = await db_session.scalar(select(func.count()).select_from(User))
    
    assert customer_count_2 == customer_count_1
    assert ticket_count_2 == ticket_count_1
    assert plan_count_2 == plan_count_1
    assert user_count_2 == user_count_1
