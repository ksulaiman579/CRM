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

from app.db.session import _build_connect_args
engine = create_async_engine(settings.DATABASE_URL, echo=False, connect_args=_build_connect_args())
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
fake = Faker()
Faker.seed(42)
random.seed(42)

# --- Realistic telecom content (replaces lorem-ipsum) ---
TICKET_CONTENT = {
    "billing": [
        ("Disputed charge on latest invoice", "Customer says this month's bill is higher than usual and wants the extra charges explained."),
        ("Double charged for monthly plan", "Two identical charges appeared for the monthly subscription; customer requests a refund."),
        ("Refund not yet received", "Approved refund from last month has not appeared on the customer's card."),
        ("Request for itemized bill", "Customer would like a detailed breakdown of calls and data usage for the period."),
    ],
    "network": [
        ("No signal at home address", "Customer reports complete loss of mobile signal at their home since yesterday."),
        ("Frequent call drops", "Calls disconnect after a minute or two; happens across multiple devices."),
        ("Slow data speeds", "Mobile data is far slower than the plan's advertised speed during evenings."),
        ("Intermittent service outage", "Service drops several times a day for a few minutes at a time."),
    ],
    "technical": [
        ("Router keeps restarting", "Home router reboots on its own every few hours, dropping the connection."),
        ("Cannot connect to Wi-Fi", "Devices fail to connect to the home Wi-Fi after a recent power cut."),
        ("Email configuration help", "Customer needs help setting up their email account on a new phone."),
        ("Device not provisioning", "Newly purchased handset is not activating on the network."),
    ],
    "plan_change": [
        ("Upgrade to higher data plan", "Customer wants to move to a larger data allowance starting next cycle."),
        ("Downgrade monthly package", "Customer would like to reduce their plan to lower the monthly cost."),
        ("Add international roaming", "Customer is travelling next week and wants a roaming add-on."),
        ("Switch to fiber broadband", "Customer is interested in switching from DSL to a fiber plan."),
    ],
    "complaint": [
        ("Unresolved issue after multiple calls", "Customer has called several times about the same fault with no resolution."),
        ("Technician did not show up", "Scheduled engineer visit was missed; customer waited all morning."),
        ("Long hold times", "Customer is frustrated with repeated long waits to reach an agent."),
        ("Poor experience at retail store", "Customer reports unhelpful service during a recent store visit."),
    ],
    "provisioning": [
        ("New SIM activation", "Customer needs a replacement SIM activated on their existing number."),
        ("Number port-in request", "Customer wants to bring their existing number from another operator."),
        ("New line setup", "Customer is adding an additional line to their account."),
        ("eSIM activation", "Customer requests activation of an eSIM profile on their new device."),
    ],
    "general": [
        ("Update contact details", "Customer wants to update the phone number and email on their account."),
        ("Change billing date", "Customer asks to move their monthly billing date to align with payday."),
        ("Enable paperless billing", "Customer would like to switch to electronic invoices."),
        ("General account question", "Customer has a general question about the services on their account."),
    ],
}

INTERACTION_POOL = [
    ("Billing query", "Walked the customer through the charges on their latest invoice."),
    ("Plan upgrade enquiry", "Discussed available higher-tier plans and pricing with the customer."),
    ("Network issue reported", "Logged a coverage complaint and ran a line check; advised next steps."),
    ("Payment taken", "Processed a one-off payment for the outstanding balance."),
    ("SIM activation", "Activated a replacement SIM and confirmed service was restored."),
    ("Roaming request", "Added an international roaming bundle ahead of the customer's trip."),
    ("Address update", "Updated the customer's billing and service address on file."),
    ("Contract renewal", "Reviewed renewal options and confirmed the customer's preferred plan."),
    ("Speed complaint", "Investigated slow speeds; scheduled a follow-up diagnostic."),
    ("General enquiry", "Answered a general account question and confirmed account details."),
]

KB_BY_SLUG = {
    "troubleshooting": [
        ("How to restart your router", "Steps to power-cycle your router and restore your connection."),
        ("Fixing slow internet speeds", "Common causes of slow speeds and how to resolve them at home."),
        ("Resolving dropped calls", "Troubleshooting steps for calls that disconnect unexpectedly."),
        ("No signal: troubleshooting steps", "What to check when your device shows no network signal."),
    ],
    "billing-faqs": [
        ("Understanding your monthly bill", "A breakdown of the charges that appear on a typical monthly invoice."),
        ("Setting up auto-pay", "How to enable automatic payments and avoid late fees."),
        ("What is a proration charge?", "Why a partial-month charge appears when you change plans mid-cycle."),
        ("How to dispute a charge", "The process for raising and tracking a billing dispute."),
    ],
    "internal-procedures": [
        ("Outage escalation procedure", "When and how to escalate a confirmed network outage."),
        ("VIP customer handling", "Service standards and routing for VIP-segment customers."),
        ("Refund authorization policy", "Approval thresholds and steps for issuing customer refunds."),
        ("Complaint resolution workflow", "End-to-end steps for handling and closing a complaint."),
    ],
    "product-manuals": [
        ("Fiber 1Gbps plan specifications", "Speeds, equipment and fair-use details for the 1Gbps fiber plan."),
        ("5G mobile plan details", "Coverage, data allowances and device requirements for 5G plans."),
        ("Router model X setup guide", "Step-by-step setup for the standard home router."),
        ("Set-top box quick start", "Getting your TV set-top box connected and registered."),
    ],
}


def _kb_body(title: str, intro: str) -> str:
    return (
        f"## Overview\n\n{intro}\n\n## Steps\n\n"
        "1. Confirm the customer's account and the affected service.\n"
        "2. Follow the checks in order, confirming the result of each.\n"
        "3. If the issue persists, escalate per the relevant procedure.\n\n"
        "## Notes\n\nKeep the customer informed at each step and log the outcome "
        "on the ticket or interaction."
    )

async def seed_data(reset=False):
    async with AsyncSessionLocal() as session:
        if reset:
            print("Resetting seeded data...")
            tables = [
                "calls", "ticket_comments", "tickets", "payments", "line_items", "invoices",
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
        
        # 3. Plans (realistic telecom catalog)
        plan_defs = [
            ("Mobile Lite",        "mobile", None,  19.99, 5),
            ("Mobile Plus",        "mobile", None,  39.99, 50),
            ("Mobile Unlimited",   "mobile", None,  59.99, None),
            ("5G Premium",         "mobile", None,  89.99, None),
            ("Fiber 100",          "fiber",  100,   39.99, None),
            ("Fiber 300",          "fiber",  300,   59.99, None),
            ("Fiber 1Gbps",        "fiber",  1000,  89.99, None),
            ("DSL Basic",          "dsl",    50,    24.99, None),
            ("DSL Home",           "dsl",    100,   34.99, None),
            ("Home Bundle",        "bundle", 300,   99.99, None),
            ("Family Bundle",      "bundle", 500,   120.00, None),
            ("Business Pro",       "bundle", 1000,  149.99, None),
        ]
        plans = []
        for i, (name, ptype, speed, price, cap) in enumerate(plan_defs):
            plans.append(Plan(
                plan_code=f"PLAN-{i+1}", name=name,
                description=f"{name} — {ptype} plan.",
                plan_type=ptype, speed_mbps=speed, monthly_price=price, data_cap_gb=cap,
            ))
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
                subj, note = random.choice(INTERACTION_POOL)
                interaction = Interaction(
                    customer_id=c.id,
                    agent_id=random.choice(users).id,
                    channel=random.choice(["call", "email", "chat"]),
                    subject=subj,
                    notes=note,
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
            subj, desc_text = random.choice(TICKET_CONTENT[cat])
            t = Ticket(
                ticket_number=f"TKT-{fake.unique.random_int(min=10000, max=99999)}",
                customer_id=cust.id,
                subject=subj,
                description=desc_text,
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
                # Most resolved/closed tickets get a CSAT rating (skewed positive).
                if random.random() < 0.8:
                    t.csat_rating = random.choices([1, 2, 3, 4, 5], weights=[5, 8, 17, 30, 40])[0]
                    if random.random() < 0.5:
                        t.csat_feedback = random.choice([
                            "Quick and helpful, thank you!",
                            "Issue resolved on the first call.",
                            "Agent was polite and professional.",
                            "Took a while but got sorted in the end.",
                            "Still not fully happy with the outcome.",
                            "Great service as always.",
                        ])
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
            title, intro = random.choice(KB_BY_SLUG.get(cat.slug, KB_BY_SLUG["troubleshooting"]))
            slug = title.lower().replace(" ", "-").replace("?", "").replace(":", "").replace(".", "") + f"-{i}"
            article = KbArticle(
                title=title,
                slug=slug,
                category_id=cat.id,
                body=_kb_body(title, intro),
                tags=[cat.slug, "telecom", "support"],
                status="published",
                author_id=random.choice(users).id,
                view_count=random.randint(0, 500)
            )
            articles.append(article)
        session.add_all(articles)

        # 7. Call history (completed simulated calls) for contact-center views/analytics.
        from app.models.call import Call
        from app.core.acd import INTENT_TEMPLATES
        import uuid as _uuid
        agents = [u for u in users if u.role == "agent"]
        agents_by_team = {}
        for a in agents:
            agents_by_team.setdefault(a.team_id, []).append(a)
        for _ in range(50):
            intent = random.choice(list(INTENT_TEMPLATES.keys()))
            team_code, lines = INTENT_TEMPLATES[intent]
            team_id = team_by_code.get(team_code)
            team_agents = agents_by_team.get(team_id) or agents
            agent = random.choice(team_agents)
            cust = random.choice(customers)
            queued = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 14), minutes=random.randint(0, 600))
            answered = queued + timedelta(seconds=random.randint(5, 60))
            ended = answered + timedelta(seconds=random.randint(60, 900))
            disposition = random.choices(["completed", "missed", "abandoned"], weights=[85, 8, 7])[0]
            session.add(Call(
                call_number=f"CALL-{_uuid.uuid4().hex[:8].upper()}",
                customer_id=cust.id, team_id=team_id, intent=intent,
                opening_line=random.choice(lines).format(name=cust.first_name),
                status=disposition,
                assigned_agent_id=agent.id if disposition != "missed" else None,
                queued_at=queued,
                answered_at=answered if disposition == "completed" else None,
                ended_at=ended if disposition != "missed" else None,
            ))

        await session.commit()
        print("Seeded successfully: 120 customers (with 360 data), 200 tickets, 50 calls, 5 teams, 5 supervisors + 10 agents, 12 plans, 40 KB articles.")

if __name__ == "__main__":
    reset = "--reset" in sys.argv
    asyncio.run(seed_data(reset=reset))
