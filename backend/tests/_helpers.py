"""Shared test helpers for the provisioned-account model (V2).

Public self-registration was removed: the seeded superuser (admin/admin, see
conftest) provisions every account via POST /api/v1/users.
"""
from httpx import AsyncClient


async def login(client: AsyncClient, username: str, password: str) -> dict:
    res = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
    res.raise_for_status()
    return res.json()


async def admin_headers(client: AsyncClient) -> dict:
    data = await login(client, "admin", "admin")
    return {"Authorization": f"Bearer {data['access_token']}"}


async def provision(client: AsyncClient, username: str, role: str = "agent", team_id: int | None = None,
                    password: str = "Password123!") -> dict:
    """Create a user as the superuser. Returns the created user dict."""
    headers = await admin_headers(client)
    res = await client.post("/api/v1/users", json={
        "username": username,
        "email": f"{username}@example.com",
        "full_name": username.replace("_", " ").title(),
        "password": password,
        "role": role,
        "team_id": team_id,
    }, headers=headers)
    res.raise_for_status()
    return res.json()


async def provision_and_login(client: AsyncClient, username: str, role: str = "agent",
                              team_id: int | None = None, password: str = "Password123!") -> tuple[dict, dict]:
    """Provision a user and log in as them. Returns (user, auth_headers).

    Provisioned users have must_change_password=True, but login still issues a
    usable token, so tests can act as the user immediately.
    """
    user = await provision(client, username, role, team_id, password)
    data = await login(client, username, password)
    return user, {"Authorization": f"Bearer {data['access_token']}"}
