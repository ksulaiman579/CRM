from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
import asyncio
import logging
from app.core.security import decode_token
from app.core.events import active_connections
from app.core.errors import AppError

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stream")
async def sse_stream(token: str = Query(...)):
    """
    Server-Sent Events streaming endpoint.
    Clients connect passing their JWT token in the query parameter.
    """
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise AppError("CRM-AUTH-005", "Token invalid / malformed", status.HTTP_401_UNAUTHORIZED)
    except Exception:
        raise AppError("CRM-AUTH-005", "Token invalid / malformed", status.HTTP_401_UNAUTHORIZED)
        
    async def event_generator():
        queue = asyncio.Queue()
        active_connections.append(queue)
        logger.info(f"Client connected to SSE stream. Total active connections: {len(active_connections)}")
        
        try:
            # Send initial ping to verify connection establishment
            yield "data: {\"event\": \"ping\", \"data\": {}}\n\n"
            
            while True:
                # Retrieve broadcasted events
                event = await queue.get()
                yield f"data: {event}\n\n"
        except asyncio.CancelledError:
            # Connection closed by client
            pass
        finally:
            if queue in active_connections:
                active_connections.remove(queue)
            logger.info(f"Client disconnected from SSE stream. Total active connections: {len(active_connections)}")
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
