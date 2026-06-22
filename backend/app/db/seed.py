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
            print("Resetting seeded data...")
            tables = [
                "ticket_comments", "tickets", "payments", "line_items", "invoices",
                "devices", "subscriptions", "interactions", "customers",
                "kb_articles", "kb_categories", "plan_features", "addons", "plans",
                "sla_policies", "audit_log", "users", "teams",
            ]
            dialect = session.bind.dialect.name
            if dialect == "postgresql":
                await session.execute(text(
                    "TRUNCATE TABLE " + ", ".join(tables) + " RESTART IDENTITY CASCADE"
                ))
            else:
                await session.execute(text("PRAGMA foreign_keys=OFF"))
                for t in tables:
                    await session.execute(text(f"DELETE FROM {t}"))
            await session.commit()
            print("Reset complete.")

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
        
        # 1. Teams (functional, with stable routing codes) & SLAs
        team_defs = [
            ("Sales", "sales", "Sales, upgrades and plan changes"),
            ("Complaints", "complaints", "Customer complaints and escalations"),
            ("Call Center", "call_center", "Inbound call queries and raised tickets"),
            ("Technical", "technical", "Network and technical support"),
            ("Billing", "billing", "Billing and payment inquiries"),
        ]
        teams = [Team(name=n, code=c, description=d) for n, c, d in team_defs]
        session.add_all(teams)
        
        sla_low = SlaPolicy(name="Low Priority", priority="low", first_response_mins=480, resolution_mins=7200)
        sla_med = SlaPolicy(name="Medium Priority", priority="medium", first_response_mins=240, resolution_mins=1440)
        sla_high = SlaPolicy(name="High Priority", priority="high", first_response_mins=60, resolution_mins=480)
        sla_crit = SlaPolicy(name="Critical Priority", priority="critical", first_response_mins=15, resolution_mins=240)
        session.add_all([sla_low, sla_med, sla_high, sla_crit])
        
        await session.flush()
        
        # 2. Users: one supervisor per team, plus agents distributed across teams.
        users = []
        pw_hash = hash_password("password123")
        for i, team in enumerate(teams):
            users.append(User(
                username=f"supervisor{i+1}", email=f"supervisor{i+1}@example.com",
                full_name=fake.name(), password_hash=pw_hash, role="supervisor", team_id=team.id,
            ))
        # 10 agents, ~2 per team, round-robin across teams.
        for i in range(10):
            team = teams[i % len(teams)]
            users.append(User(
                username=f"agent{i+1}", email=f"agent{i+1}@example.com",
                full_name=fake.name(), password_hash=pw_hash, role="agent", team_id=team.id,
            ))
        session.add_all(users)
        await session.flush()

        # Map team code -> id for routing seeded tickets.
        team_by_code = {t.code: t.id for t in teams}
        
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
        for i in range(120):
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
        for i in range(200):
            cust = random.choice(customers)
            created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            policy = random.choice(slas)
            
            cat = random.choice(["billing", "network", "technical", "plan_change", "complaint", "provisioning", "general"])
            from app.core.routing import CATEGORY_TO_TEAM_CODE, DEFAULT_TEAM_CODE
            t = Ticket(
                ticket_number=f"TKT-{fake.unique.random_int(min=10000, max=99999)}",
                customer_id=cust.id,
                subject=fake.sentence(),
                description=fake.paragraph(),
                category=cat,
                team_id=team_by_code.get(CATEGORY_TO_TEAM_CODE.get(cat, DEFAULT_TEAM_CODE)),
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
        print("Seeded successfully: 120 customers (with 360 data), 200 tickets, 5 teams, 5 supervisors + 10 agents, 12 plans, 40 KB articles.")

if __name__ == "__main__":
    reset = "--reset" in sys.argv
    asyncio.run(seed_data(reset=reset))
