from pydantic import BaseModel

class AgentDashboard(BaseModel):
    my_open_tickets: int
    tickets_due_soon: int
    tickets_breached: int
    resolved_today: int
    avg_handle_time_mins: float | None

class SupervisorDashboard(BaseModel):
    team_queue_depth: int
    unassigned_count: int
    sla_breach_rate_pct: float
    tickets_by_status: dict[str, int]
    tickets_by_category: dict[str, int]
    average_csat: float | None = None
    csat_rating_counts: dict[int, int] = {}
