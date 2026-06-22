import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy import select, update
from app.models.customer import Customer
from app.models.ticket import Ticket, SlaPolicy
from app.core.scheduler import sweep_sla_breaches
from app.models.kb import KbCategory, KbArticle
from tests._helpers import provision_and_login

@pytest.mark.asyncio
async def test_ticket_lifecycle_and_sla(client: AsyncClient, db_session):
    # 1. Provision an agent and log in.
    agent, headers = await provision_and_login(client, "agent_test", role="agent")
    agent_id = agent["id"]
    
    # 2. Create a customer
    cust = Customer(
        account_number="TC-111111",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone_primary="123456789",
        customer_type="residential",
        status="active",
        segment="standard"
    )
    db_session.add(cust)
    await db_session.commit()
    await db_session.refresh(cust)
    
    # Find or seed a troubleshooting KB category matching ticket category and subject
    cat_res = await db_session.execute(select(KbCategory).where(KbCategory.slug == "troubleshooting"))
    kb_cat = cat_res.scalar_one_or_none()
    if not kb_cat:
        kb_cat = KbCategory(name="Troubleshooting", slug="troubleshooting", description="Troubleshooting guide")
        db_session.add(kb_cat)
        await db_session.commit()
        await db_session.refresh(kb_cat)
    
    art_res = await db_session.execute(select(KbArticle).where(KbArticle.slug == "fixing-server-outages"))
    kb_art = art_res.scalar_one_or_none()
    if not kb_art:
        kb_art = KbArticle(
            title="Fixing Server Outages",
            slug="fixing-server-outages",
            category_id=kb_cat.id,
            body="Here are steps to fix critical server outages.",
            status="published",
            view_count=5
        )
        db_session.add(kb_art)
        await db_session.commit()
    
    # 3. Create a ticket (critical priority)
    ticket_payload = {
        "customer_id": cust.id,
        "subject": "Critical Server Outage",
        "description": "The main server is down.",
        "category": "technical",
        "priority": "critical",
        "channel": "web"
    }
    create_res = await client.post("/api/v1/tickets", json=ticket_payload, headers=headers)
    assert create_res.status_code == 201
    ticket_data = create_res.json()
    assert ticket_data["subject"] == "Critical Server Outage"
    assert ticket_data["priority"] == "critical"
    assert ticket_data["status"] == "open"
    assert ticket_data["sla_policy_id"] is not None
    assert ticket_data["sla_response_due"] is not None
    assert ticket_data["sla_resolution_due"] is not None
    assert ticket_data["sla_breached"] is False
    
    ticket_id = ticket_data["id"]
    
    # 4. Add a public comment and check first_response_at
    comment_payload = {
        "body": "We are investigating the issue immediately.",
        "is_internal": False
    }
    comment_res = await client.post(f"/api/v1/tickets/{ticket_id}/comments", json=comment_payload, headers=headers)
    assert comment_res.status_code == 200
    
    # Check ticket details
    get_res = await client.get(f"/api/v1/tickets/{ticket_id}", headers=headers)
    assert get_res.status_code == 200
    updated_ticket_data = get_res.json()
    assert updated_ticket_data["first_response_at"] is not None
    
    # 5. Claim the ticket atomically (dedicated /claim endpoint).
    claim_res = await client.post(f"/api/v1/tickets/{ticket_id}/claim", headers=headers)
    assert claim_res.status_code == 200
    assert claim_res.json()["assigned_agent_id"] == agent_id
    assert claim_res.json()["status"] == "in_progress"

    # A second claim by the same flow now conflicts (already assigned).
    reclaim_res = await client.post(f"/api/v1/tickets/{ticket_id}/claim", headers=headers)
    assert reclaim_res.status_code == 409
    assert reclaim_res.json()["error"]["code"] == "CRM-TKT-003"
    
    # 6. Escalate the ticket (status = escalated)
    patch_res = await client.patch(f"/api/v1/tickets/{ticket_id}", json={"status": "escalated"}, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "escalated"
    
    # 7. Resolve & Close the ticket
    patch_res = await client.patch(f"/api/v1/tickets/{ticket_id}", json={"status": "closed"}, headers=headers)
    assert patch_res.status_code == 200
    closed_data = patch_res.json()
    assert closed_data["status"] == "closed"
    assert closed_data["resolved_at"] is not None
    assert closed_data["closed_at"] is not None
    
    # 8. Try invalid transition: closed -> in_progress (must fail with CRM-TKT-002)
    invalid_patch_res = await client.patch(f"/api/v1/tickets/{ticket_id}", json={"status": "in_progress"}, headers=headers)
    assert invalid_patch_res.status_code == 409
    assert invalid_patch_res.json()["error"]["code"] == "CRM-TKT-002"
    
    # 9. Test SLA breach sweep
    # Create another ticket
    ticket_payload_2 = {
        "customer_id": cust.id,
        "subject": "Minor network issue",
        "description": "Wi-Fi keeps dropping.",
        "category": "network",
        "priority": "low",
        "channel": "web"
    }
    create_res_2 = await client.post("/api/v1/tickets", json=ticket_payload_2, headers=headers)
    assert create_res_2.status_code == 201
    ticket_id_2 = create_res_2.json()["id"]
    
    # Manually update sla_resolution_due of ticket 2 to the past in DB
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)
    await db_session.execute(
        update(Ticket).where(Ticket.id == ticket_id_2).values(sla_resolution_due=past_time)
    )
    await db_session.commit()
    
    # Verify the ticket SLA resolution due is indeed in the past
    get_res_2_before = await client.get(f"/api/v1/tickets/{ticket_id_2}", headers=headers)
    assert get_res_2_before.json()["sla_breached"] is False
    
    # Run background job sweep
    await sweep_sla_breaches()
    
    # Verify it is now flagged as breached
    get_res_2_after = await client.get(f"/api/v1/tickets/{ticket_id_2}", headers=headers)
    assert get_res_2_after.json()["sla_breached"] is True

    # 10. Test suggested KB articles matching logic
    suggest_res = await client.get(f"/api/v1/tickets/{ticket_id}/suggested-kb", headers=headers)
    assert suggest_res.status_code == 200
    suggested = suggest_res.json()
    assert len(suggested) > 0
    assert any(art["title"] == "Fixing Server Outages" for art in suggested)
