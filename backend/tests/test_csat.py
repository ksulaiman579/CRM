import pytest
from httpx import AsyncClient
from sqlalchemy import select, update, delete
from app.models.customer import Customer
from app.models.ticket import Ticket
from app.models.user import User
from tests._helpers import provision_and_login

@pytest.mark.asyncio
async def test_csat_workflow(client: AsyncClient, db_session):
    # 1. Provision a supervisor and an agent.
    _, headers_super = await provision_and_login(client, "super_csat_test", role="supervisor")
    _, headers_agent = await provision_and_login(client, "agent_csat_test", role="agent")
    
    # 2. Create customer
    cust = Customer(
        account_number="TC-333333",
        first_name="Alice",
        last_name="Green",
        email="alice@example.com",
        phone_primary="555555555",
        customer_type="residential",
        status="active",
        segment="standard"
    )
    db_session.add(cust)
    await db_session.commit()
    await db_session.refresh(cust)
    
    ticket_id = None
    try:
        # 3. Create ticket
        ticket_payload = {
            "customer_id": cust.id,
            "subject": "CSAT Test Ticket",
            "description": "Validating satisfaction scores",
            "category": "technical",
            "priority": "medium",
            "channel": "web"
        }
        create_res = await client.post("/api/v1/tickets", json=ticket_payload, headers=headers_agent)
        assert create_res.status_code == 201
        ticket_id = create_res.json()["id"]

        # Agent must own the ticket to edit it — claim first.
        claim_res = await client.post(f"/api/v1/tickets/{ticket_id}/claim", headers=headers_agent)
        assert claim_res.status_code == 200

        # 4. Try updating ticket status to in_progress but submitting CSAT (should fail with 400 because not resolved/closed)
        fail_update = await client.patch(f"/api/v1/tickets/{ticket_id}", json={
            "status": "in_progress",
            "csat_rating": 5
        }, headers=headers_agent)
        assert fail_update.status_code == 400
        assert fail_update.json()["error"]["code"] == "CRM-TKT-003"
        
        # 5. Try updating ticket CSAT rating with out-of-range rating (should fail with 422 because of ge=1, le=5 constraint)
        fail_rating = await client.patch(f"/api/v1/tickets/{ticket_id}", json={
            "status": "resolved",
            "csat_rating": 6
        }, headers=headers_agent)
        assert fail_rating.status_code == 422
        
        # 6. Resolve ticket with valid CSAT rating and comments (should succeed)
        success_resolve = await client.patch(f"/api/v1/tickets/{ticket_id}", json={
            "status": "resolved",
            "csat_rating": 5,
            "csat_feedback": "Fast resolution, perfect!"
        }, headers=headers_agent)
        assert success_resolve.status_code == 200
        assert success_resolve.json()["csat_rating"] == 5
        assert success_resolve.json()["csat_feedback"] == "Fast resolution, perfect!"
        
        # 7. Check that the CSAT ratings propagate to the supervisor dashboard
        dash_res = await client.get("/api/v1/dashboard/supervisor", headers=headers_super)
        assert dash_res.status_code == 200
        dash_data = dash_res.json()
        assert dash_data["average_csat"] == 5.0
        assert dash_data["csat_rating_counts"]["5"] == 1
        assert dash_data["csat_rating_counts"]["4"] == 0
        
    finally:
        # Clean up DB records
        try:
            if ticket_id is not None:
                await db_session.execute(delete(Ticket).where(Ticket.id == ticket_id))
            await db_session.execute(delete(Customer).where(Customer.id == cust.id))
            await db_session.commit()
        except Exception:
            pass
