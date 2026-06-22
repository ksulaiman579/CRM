import asyncio
import json
import logging

logger = logging.getLogger(__name__)

# List to keep track of active connection queues
active_connections: list[asyncio.Queue] = []

# In-memory per-ticket presence: {ticket_id: {user_id: full_name}}.
# Best-effort collision awareness for concurrent agents (not durable).
ticket_viewers: dict[int, dict[int, str]] = {}


def set_viewer(ticket_id: int, user_id: int, full_name: str) -> list[dict]:
    viewers = ticket_viewers.setdefault(ticket_id, {})
    viewers[user_id] = full_name
    return [{"id": uid, "full_name": name} for uid, name in viewers.items()]


def clear_viewer(ticket_id: int, user_id: int) -> list[dict]:
    viewers = ticket_viewers.get(ticket_id, {})
    viewers.pop(user_id, None)
    if not viewers:
        ticket_viewers.pop(ticket_id, None)
    return [{"id": uid, "full_name": name} for uid, name in viewers.items()]

async def broadcast_event(event_type: str, data: dict):
    """
    Broadcasts an event payload to all connected clients.
    """
    event_payload = {
        "event": event_type,
        "data": data
    }
    serialized = json.dumps(event_payload)
    
    # Send to all connected queues
    connections_to_remove = []
    for queue in list(active_connections):
        try:
            queue.put_nowait(serialized)
        except Exception as e:
            logger.error(f"Failed to push event to queue: {e}")
            connections_to_remove.append(queue)
            
    # Clean up stale connections
    for conn in connections_to_remove:
        if conn in active_connections:
            active_connections.remove(conn)
            
    if connections_to_remove:
        logger.info(f"Cleaned up {len(connections_to_remove)} stale connections during broadcast.")
