import time
import uuid
from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..logging_config import logger

class EnhancedLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request_time = time.time()
        
        # Log request
        logger.info(
            "API Request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client": request.client.host if request.client else None
            }
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - request_time
            
            # Log response
            logger.info(
                "API Response",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time_seconds": round(process_time, 4),
                    "response_headers": dict(response.headers)
                }
            )
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            process_time = time.time() - request_time
            logger.error(
                "API Error",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                    "process_time_seconds": round(process_time, 4)
                },
                exc_info=True
            )
            raise
