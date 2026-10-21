"""Authenticated, case-bound WebSocket entry to the Gemini Live voice gateway."""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import HTTPException

from app.api.v1.auth import resolve_actor
from app.config import get_settings
from app.core.security import require_safe_identifier
from app.repositories.audit_repo import AuditRepository
from app.services.case_access import require_case_access
from app.voice.gemini_live_adapter import serve_live_session

router = APIRouter(tags=["voice"])


@router.websocket("/cases/{case_id}/voice")
async def voice_session(websocket: WebSocket, case_id: str):
    settings = get_settings()
    try:
        case_id = require_safe_identifier(case_id, "case ID")
        origin = websocket.headers.get("origin")
        if not origin or origin not in settings.origins:
            await websocket.close(code=1008, reason="Origin is not allowed.")
            return
        actor = resolve_actor(
            settings,
            authorization=websocket.headers.get("authorization"),
            x_user_id=websocket.headers.get("x-user-id"),
            x_tenant_id=websocket.headers.get("x-tenant-id"),
        )
        database = websocket.app.state.database
        await require_case_access(database, actor, case_id)
    except HTTPException as exc:
        close_code = 4401 if exc.status_code == 401 else 1013 if exc.status_code == 503 else 4404
        await websocket.close(code=close_code)
        return
    if not settings.gemini_live_configured:
        await websocket.close(code=1013, reason="Voice service is not configured.")
        return
    semaphore = websocket.app.state.voice_semaphore
    try:
        await asyncio.wait_for(semaphore.acquire(), timeout=0.05)
    except TimeoutError:
        await websocket.close(code=1013, reason="Voice service is at session capacity.")
        return

    await websocket.accept()
    try:
        await AuditRepository(database).append({
            "event_id": f"audit_{uuid4().hex}", "case_id": case_id,
            "tenant_id": actor.tenant_id, "actor_id": actor.user_id,
            "action": "voice.session_started", "target_type": "case",
            "target_id": case_id, "timestamp": datetime.now(timezone.utc),
            "result": "success",
        })
        await serve_live_session(websocket, settings, database, actor, case_id)
    except WebSocketDisconnect:
        return
    finally:
        semaphore.release()
