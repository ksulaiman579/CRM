import pytest
import asyncio
import json
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy import select
from app.models.customer import Customer
from app.models.ticket import Ticket
from app.core.events import active_connections
from app.core.scheduler import sweep_sla_breaches
from tests._helpers import provision_and_login

@pytest.mark.asyncio
async def test_realtime_events_unauthorized(client: AsyncClient):
    # Test that connecting to the stream with no token or invalid token returns 422 or 401
    resp = await client.get("/api/v1/events/stream")
    assert resp.status_code == 422  # missing token query param in FastAPI yields validation error
    
    resp_invalid = await client.get("/api/v1/events/stream?token=invalid_token_123")
    assert resp_invalid.status_code == 401

@pytest.mark.asyncio
async def test_realtime_events_broadcasting(client: AsyncClient, db_session):
    # 1. Provision an agent and log in.
    agent, headers = await provision_and_login(client, "events_test_user", role="agent")
    user_id = agent["id"]
    
    # 2. Create a customer
    cust = Customer(
        account_number="TC-222222",
        first_name="Jane",
        last_name="Smith",
        email="jane@example.com",
        phone_primary="987654321",
        customer_type="residential",
        status="active",
        segment="standard"
    )
    db_session.add(cust)
    await db_session.commit()
    await db_session.refresh(cust)

    # Register a local test queue to receive events directly from broadcaster
    test_queue = asyncio.Queue()
    active_connections.append(test_queue)
    
    try:
        # 3. Create a ticket (which broadcasts ticket_created event)
        ticket_payload = {
            "customer_id": cust.id,
            "subject": "Events Outage Check",
            "description": "SSE verification ticket",
            "category": "technical",
            "priority": "low",
            "channel": "web"
        }
        create_res = await client.post("/api/v1/tickets", json=ticket_payload, headers=headers)
        assert create_res.status_code == 201
        ticket_data = create_res.json()
        ticket_id = ticket_data["id"]
        
        # Verify ticket_created event was received in queue
        event_str = await asyncio.wait_for(test_queue.get(), timeout=1.0)
        event = json.loads(event_str)
        assert event["event"] == "ticket_created"
        assert event["data"]["id"] == ticket_id
        assert event["data"]["subject"] == "Events Outage Check"
        
        # 4. Claim ticket (broadcasts ticket_assigned event)
        update_res = await client.post(f"/api/v1/tickets/{ticket_id}/claim", headers=headers)
        assert update_res.status_code == 200
        
        # Verify ticket_assigned event was received in queue
        event_str = await asyncio.wait_for(test_queue.get(), timeout=1.0)
        event = json.loads(event_str)
        assert event["event"] == "ticket_assigned"
        assert event["data"]["id"] == ticket_id
        assert event["data"]["assigned_agent_id"] == user_id
        assert event["data"]["status"] == "in_progress"
        
        # 5. Set ticket's SLA resolution date to past and run SLA sweep (which broadcasts sla_breached event)
        # Fetch the ticket first to ensure we have the latest version in db_session
        result = await db_session.execute(select(Ticket).where(Ticket.id == ticket_id))
        t = result.scalar_one()
        t.sla_resolution_due = datetime.now(timezone.utc) - timedelta(hours=1)
        t.sla_breached = False
        await db_session.commit()
        
        # Run the SLA sweep job
        await sweep_sla_breaches()
        
        # Verify sla_breached event was received in queue
        event_str = await asyncio.wait_for(test_queue.get(), timeout=1.0)
        event = json.loads(event_str)
        assert event["event"] == "sla_breached"
        assert event["data"]["id"] == ticket_id
        assert event["data"]["subject"] == "Events Outage Check"
        
    finally:
        # Clean up queue subscription
        if test_queue in active_connections:
            active_connections.remove(test_queue)
            
        # Clean up database records to avoid polluting other tests
        from sqlalchemy import delete
        try:
            if 'ticket_id' in locals():
                await db_session.execute(delete(Ticket).where(Ticket.id == ticket_id))
            if 'cust' in locals() and cust.id:
                await db_session.execute(delete(Customer).where(Customer.id == cust.id))
            await db_session.commit()
        except Exception:
            pass

