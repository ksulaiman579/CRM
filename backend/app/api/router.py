from fastapi import APIRouter

from app.api.v1 import auth, tickets, customers, interactions, billing, plans, kb, dashboard, users, events

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(interactions.router, prefix="/interactions", tags=["interactions"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(kb.router, prefix="/kb", tags=["kb"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
