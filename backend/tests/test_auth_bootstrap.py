import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.user import User
from tests._helpers import admin_headers, login, provision


@pytest.mark.asyncio
async def test_superuser_provisions_accounts(client: AsyncClient, db_session):
    headers = await admin_headers(client)

    # Superuser creates an agent and a supervisor.
    agent = await provision(client, "prov_agent", role="agent")
    assert agent["role"] == "agent"
    assert agent["must_change_password"] is True  # set own password on first login

    sup = await provision(client, "prov_supervisor", role="supervisor")
    assert sup["role"] == "supervisor"

    # Verify persisted.
    user = (await db_session.execute(select(User).where(User.username == "prov_agent"))).scalar_one()
    assert user.role == "agent"

    # Public self-registration is gone.
    res = await client.post("/api/v1/auth/register", json={
        "username": "x", "email": "x@example.com", "password": "Password123!", "full_name": "X",
    })
    assert res.status_code in (404, 405)

    # Non-superusers cannot provision.
    agent_login = await login(client, "prov_agent", "Password123!")
    agent_headers = {"Authorization": f"Bearer {agent_login['access_token']}"}
    forbidden = await client.post("/api/v1/users", json={
        "username": "nope", "email": "nope@example.com", "full_name": "Nope",
        "password": "Password123!", "role": "agent",
    }, headers=agent_headers)
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_password_rotation_and_admin_reset(client: AsyncClient, db_session):
    headers = await admin_headers(client)
    await provision(client, "rot_agent", role="agent")

    agent_login = await login(client, "rot_agent", "Password123!")
    agent_headers = {"Authorization": f"Bearer {agent_login['access_token']}"}

    # Wrong current password rejected.
    fail = await client.post("/api/v1/auth/change-password", json={
        "current_password": "wrong", "new_password": "NewPassword123!",
    }, headers=agent_headers)
    assert fail.status_code == 400
    assert fail.json()["error"]["code"] == "CRM-AUTH-008"

    # Correct change works and clears must_change_password.
    ok = await client.post("/api/v1/auth/change-password", json={
        "current_password": "Password123!", "new_password": "NewPassword123!",
    }, headers=agent_headers)
    assert ok.status_code == 200

    relogin = await login(client, "rot_agent", "NewPassword123!")
    assert relogin["user"]["must_change_password"] is False

    # Superuser reset forces change on next login.
    user = (await db_session.execute(select(User).where(User.username == "rot_agent"))).scalar_one()
    reset = await client.post(f"/api/v1/users/{user.id}/reset-password", json={
        "new_password": "TempPassword123!",
    }, headers=headers)
    assert reset.status_code == 200

    after = await login(client, "rot_agent", "TempPassword123!")
    assert after["user"]["must_change_password"] is True


@pytest.mark.asyncio
async def test_cannot_demote_last_superuser(client: AsyncClient, db_session):
    headers = await admin_headers(client)
    me = (await db_session.execute(select(User).where(User.username == "admin"))).scalar_one()

    res = await client.patch(f"/api/v1/users/{me.id}", json={"is_active": False}, headers=headers)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "CRM-USER-003"
