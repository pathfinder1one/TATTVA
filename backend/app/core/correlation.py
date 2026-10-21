from contextvars import ContextVar
import re
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,80}$")


class RequestCorrelationMiddleware:
    """Assign a bounded request ID and echo it for API and WebSocket traffic."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        requested = headers.get(b"x-request-id", b"").decode("ascii", errors="ignore")
        request_id = requested if _REQUEST_ID.fullmatch(requested) else uuid4().hex
        token = request_id_context.set(request_id)

        async def send_with_id(message: Message) -> None:
            if scope["type"] == "http" and message["type"] == "http.response.start":
                message = dict(message)
                message["headers"] = list(message.get("headers", []))
                message["headers"].append((b"x-request-id", request_id.encode("ascii")))
            elif scope["type"] == "websocket" and message["type"] == "websocket.accept":
                message = dict(message)
                message["headers"] = list(message.get("headers", []))
                message["headers"].append((b"x-request-id", request_id.encode("ascii")))
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            request_id_context.reset(token)
