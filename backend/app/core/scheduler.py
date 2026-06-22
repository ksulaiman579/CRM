import logging
from datetime import datetime, timezone
from sqlalchemy import select, update
from app.db.session import AsyncSessionLocal
from app.models.ticket import Ticket
from app.models.billing import Invoice

logger = logging.getLogger(__name__)

async def sweep_sla_breaches():
    """
    Background job to check all active tickets and flag them if they have breached their SLA resolution time.
    """
    try:
        async with AsyncSessionLocal() as session:
            now = datetime.now(timezone.utc)
            # Find tickets that are open/in_progress/escalated, not yet breached, and past their resolution due date
            stmt = select(Ticket).where(
                Ticket.status.in_(["open", "in_progress", "escalated"]),
                Ticket.sla_breached == False,
                Ticket.sla_resolution_due != None,
                Ticket.sla_resolution_due < now
            )
            result = await session.execute(stmt)
            tickets = result.scalars().all()
            
            if tickets:
                for t in tickets:
                    t.sla_breached = True
                
                await session.commit()
                logger.info(f"SLA Sweep: Flagged {len(tickets)} tickets as breached.")
                
                from app.core.cache import cache
                cache.delete("supervisor_dash_None")
                for t in tickets:
                    if t.team_id:
                        cache.delete(f"supervisor_dash_{t.team_id}")
                
                # Broadcast SLA breach events
                from app.core.events import broadcast_event
                for t in tickets:
                    await broadcast_event("sla_breached", {
                        "id": t.id,
                        "ticket_number": t.ticket_number,
                        "subject": t.subject
                    })
            else:
                logger.debug("SLA Sweep: No new breaches found.")
    except Exception as e:
        logger.error(f"Error in SLA sweep job: {e}")

async def sweep_overdue_invoices():
    """
    Background job to check pending invoices and flag them as overdue if past the due date.
    """
    try:
        async with AsyncSessionLocal() as session:
            now_date = datetime.now(timezone.utc).date()
            stmt = select(Invoice).where(
                Invoice.status == "pending",
                Invoice.due_date != None,
                Invoice.due_date < now_date
            )
            result = await session.execute(stmt)
            invoices = result.scalars().all()
            
            if invoices:
                for inv in invoices:
                    inv.status = "overdue"
                
                await session.commit()
                logger.info(f"Invoice Sweep: Flagged {len(invoices)} invoices as overdue.")
            else:
                logger.debug("Invoice Sweep: No overdue invoices found.")
    except Exception as e:
        logger.error(f"Error in Invoice sweep job: {e}")

def setup_scheduler(scheduler):
    """
    Register all background jobs to the provided scheduler instance.
    """
    # Sweep SLA every minute
    scheduler.add_job(sweep_sla_breaches, "interval", minutes=1, id="sweep_sla", replace_existing=True)
    # Sweep Invoices every 5 minutes (for demo purposes, normally hourly or daily)
    scheduler.add_job(sweep_overdue_invoices, "interval", minutes=5, id="sweep_invoices", replace_existing=True)
    # Refresh dashboard cache every 5 minutes
    scheduler.add_job(refresh_dashboard_cache, "interval", minutes=5, id="refresh_dash_cache", replace_existing=True)
    logger.info("Background jobs registered.")

async def refresh_dashboard_cache():
    """
    Precomputes supervisor dashboard metrics and populates the cache to keep it warm.
    """
    try:
        from app.models.user import Team
        from app.schemas.dashboard import SupervisorDashboard
        from sqlalchemy import func
        from app.core.cache import cache
        
        async with AsyncSessionLocal() as session:
            # Get all teams
            teams = await session.execute(select(Team.id))
            team_ids = [None] + [row[0] for row in teams.all()]
            
            for team_id in team_ids:
                cache_key = f"supervisor_dash_{team_id}"
                
                query_depth = select(func.count()).select_from(Ticket).where(Ticket.status.notin_(["resolved", "closed"]))
                if team_id: query_depth = query_depth.where(Ticket.team_id == team_id)
                depth = await session.scalar(query_depth) or 0
                
                query_unassigned = select(func.count()).select_from(Ticket).where(Ticket.assigned_agent_id == None, Ticket.status.notin_(["resolved", "closed"]))
                if team_id: query_unassigned = query_unassigned.where(Ticket.team_id == team_id)
                unassigned = await session.scalar(query_unassigned) or 0
                
                query_breached = select(func.count()).select_from(Ticket).where(Ticket.sla_breached == True, Ticket.status.notin_(["resolved", "closed"]))
                if team_id: query_breached = query_breached.where(Ticket.team_id == team_id)
                breached = await session.scalar(query_breached) or 0
                
                breach_rate = round((breached / depth * 100) if depth > 0 else 0.0, 1)
                
                query_status = select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
                if team_id: query_status = query_status.where(Ticket.team_id == team_id)
                res_status = await session.execute(query_status)
                tickets_by_status = {row[0]: row[1] for row in res_status.all()}
                
                query_cat = select(Ticket.category, func.count(Ticket.id)).where(Ticket.status.notin_(["resolved", "closed"])).group_by(Ticket.category)
                if team_id: query_cat = query_cat.where(Ticket.team_id == team_id)
                res_cat = await session.execute(query_cat)
                tickets_by_cat = {row[0]: row[1] for row in res_cat.all()}
                
                # CSAT Statistics
                query_csat = select(func.avg(Ticket.csat_rating)).where(Ticket.csat_rating.isnot(None))
                if team_id:
                    query_csat = query_csat.where(Ticket.team_id == team_id)
                avg_csat_val = await session.scalar(query_csat)
                avg_csat = round(float(avg_csat_val), 2) if avg_csat_val is not None else None
                
                query_csat_counts = select(Ticket.csat_rating, func.count(Ticket.id)).where(Ticket.csat_rating.isnot(None)).group_by(Ticket.csat_rating)
                if team_id:
                    query_csat_counts = query_csat_counts.where(Ticket.team_id == team_id)
                res_csat_counts = await session.execute(query_csat_counts)
                csat_rating_counts = {i: 0 for i in range(1, 6)}
                for row in res_csat_counts.all():
                    rating = int(row[0])
                    if 1 <= rating <= 5:
                        csat_rating_counts[rating] = row[1]
                
                dash = SupervisorDashboard(
                    team_queue_depth=depth,
                    unassigned_count=unassigned,
                    sla_breach_rate_pct=breach_rate,
                    tickets_by_status=tickets_by_status,
                    tickets_by_category=tickets_by_cat,
                    average_csat=avg_csat,
                    csat_rating_counts=csat_rating_counts
                )
                cache.set(cache_key, dash, ttl_seconds=300)
                
        logger.info("Dashboard cache refreshed successfully.")
    except Exception as e:
        logger.error(f"Error in dashboard cache refresh job: {e}")
