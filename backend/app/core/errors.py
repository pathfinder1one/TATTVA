from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        request_id = request.headers.get("x-request-id") or f"req_{uuid4().hex}"
        code = {
            400: "BAD_REQUEST",
            401: "UNAUTHENTICATED",
            403: "CASE_ACCESS_DENIED",
            404: "NOT_FOUND",
            409: "CONFLICT",
            413: "UPLOAD_TOO_LARGE",
            422: "VALIDATION_ERROR",
        }.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else "The request could not be completed."
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content={"error": {"code": code, "message": message, "request_id": request_id, "retryable": False}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        request_id = request.headers.get("x-request-id") or f"req_{uuid4().hex}"
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request did not match the required schema.",
                    "request_id": request_id,
                    "retryable": False,
                }
            },
        )
