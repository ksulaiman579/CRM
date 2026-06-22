from app.db.base import Base
from app.models.user import User, Team, AuditLog
from app.models.customer import Customer, Interaction
from app.models.service import Subscription, Device
from app.models.billing import Invoice, Payment, LineItem
from app.models.plan import Plan, PlanFeature, Addon
from app.models.ticket import Ticket, TicketComment, SlaPolicy
from app.models.kb import KbArticle, KbCategory

# This __init__.py ensures all models are imported before Alembic runs
# so that they get registered on the Base.metadata
