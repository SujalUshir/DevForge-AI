"""
HTTP request/response middleware.

RequestLoggingMiddleware: Logs every request with method, path, status code,
and response time. Catches unhandled exceptions and returns a structured
500 response instead of crashing the server.
"""

import time

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log every HTTP request with timing.

    On unhandled exceptions, returns a structured JSON 500 response
    rather than leaking a Python traceback to the client.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "http_request_unhandled_error",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                error=str(exc),
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An internal server error occurred.",
                    "path": request.url.path,
                },
            )
