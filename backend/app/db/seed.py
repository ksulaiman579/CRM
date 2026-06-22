import asyncio
import random
from datetime import datetime, timedelta, timezone, date
from faker import Faker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, func, text
from app.config import settings

from app.models.customer import Customer, Interaction
from app.models.user import Team, User
from app.models.ticket import SlaPolicy, Ticket, TicketComment
from app.models.plan import Plan, Addon, PlanFeature
from app.models.service import Subscription, Device
from app.models.billing import Invoice, Payment, LineItem
from app.models.kb import KbCategory, KbArticle
from app.core.security import hash_password
from app.core.sla import compute_sla_due_dates
import sys

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
fake = Faker()
Faker.seed(42)
random.seed(42)

async def seed_data(reset=False):
    async with AsyncSessionLocal() as session:
        if reset:
            print("Resetting database (dropping tables requires alembic, here we just delete rows).")
            # For SQLite, DELETE FROM table is easier, but be careful with foreign keys. 
            # We'll rely on the user to rebuild the DB or just run the seed once.
            pass

        # Fixed superuser (admin/admin) — DEMO ONLY, not for deployment.
        # Provisions all other accounts. Seeded idempotently, independent of
        # the customer-data seed below.
        existing_admin = await session.scalar(select(User).where(User.username == "admin"))
        if not existing_admin:
            session.add(User(
                username="admin",
                email="admin@telecom-crm.com",
                full_name="System Administrator",
                password_hash=hash_password("admin"),
                role="superuser",
                must_change_password=False,
            ))
            await session.commit()
            print("Seeded superuser: admin / admin")

        cust_count = await session.scalar(select(func.count()).select_from(Customer))
        if cust_count and cust_count > 0:
            print("Database already seeded with customers. Skipping seed to prevent duplicates.")
            return

        print("Seeding database...")
        
        # 1. Teams & SLAs
        team1 = Team(name="Tier 1 Support", description="First line support")
        team2 = Team(name="Tier 2 Technical", description="Advanced technical support")
        team3 = Team(name="Billing Support", description="Billing inquiries")
        session.add_all([team1, team2, team3])
        
        sla_low = SlaPolicy(name="Low Priority", priority="low", first_response_mins=480, resolution_mins=7200)
        sla_med = SlaPolicy(name="Medium Priority", priority="medium", first_response_mins=240, resolution_mins=1440)
        sla_high = SlaPolicy(name="High Priority", priority="high", first_response_mins=60, resolution_mins=480)
        sla_crit = SlaPolicy(name="Critical Priority", priority="critical", first_response_mins=15, resolution_mins=240)
        session.add_all([sla_low, sla_med, sla_high, sla_crit])
        
        await session.flush()
        
        # 2. Users (2 supervisors, 7 agents)
        users = []
        pw_hash = hash_password("password123")
        for i in range(2):
            u = User(username=f"supervisor{i+1}", email=f"supervisor{i+1}@example.com", full_name=fake.name(), password_hash=pw_hash, role="supervisor", team_id=team1.id)
            users.append(u)
        for i in range(7):
            u = User(username=f"agent{i+1}", email=f"agent{i+1}@example.com", full_name=fake.name(), password_hash=pw_hash, role="agent", team_id=random.choice([team1.id, team2.id, team3.id]))
            users.append(u)
        session.add_all(users)
        await session.flush()
        
        # 3. Plans
        plans = []
        for i in range(12):
            p = Plan(
                plan_code=f"PLAN-{i+1}", name=f"Plan {fake.word().capitalize()}", description=fake.sentence(),
                plan_type=random.choice(["mobile", "fiber", "dsl", "bundle"]), speed_mbps=random.choice([100, 300, 1000]),
                monthly_price=random.choice([19.99, 39.99, 59.99, 89.99, 120.00]),
                data_cap_gb=random.choice([None, 50, 100, 500])
            )
            plans.append(p)
        session.add_all(plans)
        await session.flush()
        
        # 4. Customers & 360 Data
        customers = []
        for i in range(110):
            c = Customer(
                account_number=f"TC-{fake.unique.random_int(min=100000, max=999999)}",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                phone_primary=fake.phone_number()[:15],
                customer_type=random.choices(["residential", "business", "enterprise"], weights=[60, 30, 10])[0],
                status=random.choices(["active", "suspended", "terminated", "pending"], weights=[75, 10, 5, 10])[0],
                segment=random.choices(["standard", "premium", "vip"], weights=[70, 20, 10])[0]
            )
            session.add(c)
            await session.flush()
            customers.append(c)
            
            # Subscriptions
            plan = random.choice(plans)
            start_date = fake.date_between(start_date='-2y', end_date='today')
            sub = Subscription(
                customer_id=c.id,
                plan_id=plan.id,
                status="active" if c.status == "active" else "paused",
                start_date=start_date,
                monthly_charge=plan.monthly_price
            )
            session.add(sub)
            await session.flush()
            
            # Invoices
            inv_date = date.today().replace(day=1) - timedelta(days=30)
            inv = Invoice(
                invoice_number=f"INV-{fake.unique.random_int(min=100000, max=999999)}",
                customer_id=c.id,
                billing_period_start=inv_date,
                billing_period_end=inv_date + timedelta(days=30),
                subtotal=sub.monthly_charge,
                total_amount=sub.monthly_charge * 1.1, # +10% tax
                status=random.choices(["paid", "pending", "overdue"], weights=[70, 20, 10])[0],
                due_date=inv_date + timedelta(days=15)
            )
            session.add(inv)
            await session.flush()
            
            if inv.status == "paid":
                payment = Payment(
                    payment_ref=f"PAY-{fake.unique.random_int(min=100000, max=999999)}",
                    invoice_id=inv.id,
                    customer_id=c.id,
                    amount=inv.total_amount,
                    status="completed"
                )
                session.add(payment)
                
            # Interactions
            for _ in range(random.randint(1, 4)):
                interaction = Interaction(
                    customer_id=c.id,
                    agent_id=random.choice(users).id,
                    channel=random.choice(["call", "email", "chat"]),
                    subject=fake.sentence(nb_words=4),
                    notes=fake.paragraph()
                )
                session.add(interaction)
                
        await session.flush()
        
        # 5. Tickets
        slas = [sla_low, sla_med, sla_high, sla_crit]
        for i in range(150):
            cust = random.choice(customers)
            created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            policy = random.choice(slas)
            
            t = Ticket(
                ticket_number=f"TKT-{fake.unique.random_int(min=10000, max=99999)}",
                customer_id=cust.id,
                subject=fake.sentence(),
                description=fake.paragraph(),
                category=random.choice(["billing", "network", "technical", "plan_change", "complaint", "provisioning", "general"]),
                priority=policy.priority,
                status=random.choices(["open", "in_progress", "pending_customer", "escalated", "resolved", "closed"], weights=[20, 30, 10, 5, 20, 15])[0],
                channel=random.choice(["call", "email", "chat", "web"]),
                assigned_agent_id=random.choice(users).id if random.random() > 0.3 else None,
                sla_policy_id=policy.id,
                created_at=created_at,
                created_by=random.choice(users).id
            )
            t.sla_response_due = created_at + timedelta(minutes=policy.first_response_mins)
            t.sla_resolution_due = created_at + timedelta(minutes=policy.resolution_mins)
            if t.status in ["resolved", "closed"]:
                t.resolved_at = created_at + timedelta(hours=random.randint(1, 48))
            elif datetime.now(timezone.utc) > t.sla_resolution_due:
                t.sla_breached = True
            
            session.add(t)
            
        # 6. Knowledge Base
        categories = [
            KbCategory(name="Troubleshooting", slug="troubleshooting", description="Guides to resolve common technical issues."),
            KbCategory(name="Billing FAQs", slug="billing-faqs", description="Answers to customer billing questions."),
            KbCategory(name="Internal Procedures", slug="internal-procedures", description="SOPs and company policies."),
            KbCategory(name="Product Manuals", slug="product-manuals", description="Specifications for devices and plans.")
        ]
        session.add_all(categories)
        await session.flush()
        
        articles = []
        for i in range(40):
            cat = random.choice(categories)
            title = fake.sentence(nb_words=6)
            slug = title.lower().replace(" ", "-").replace(".", "") + f"-{i}"
            article = KbArticle(
                title=title,
                slug=slug,
                category_id=cat.id,
                body=f"## Overview\n\n{fake.paragraph(nb_sentences=5)}\n\n## Steps to Resolve\n\n1. {fake.sentence()}\n2. {fake.sentence()}\n3. {fake.sentence()}\n\n## Conclusion\n\n{fake.paragraph()}",
                tags=[fake.word(), fake.word(), fake.word()],
                status="published",
                author_id=random.choice(users).id,
                view_count=random.randint(0, 500)
            )
            articles.append(article)
        session.add_all(articles)
        
        await session.commit()
        print("Seeded successfully: 110 customers (with 360 data), 150 tickets, 9 agents, 12 plans, 40 KB articles.")

if __name__ == "__main__":
    reset = False
    if "--reset" in sys.argv:
        reset = True
        print("Resetting is not fully implemented in code, please delete sqlite.db and run alembic upgrade head.")
    asyncio.run(seed_data(reset=reset))
