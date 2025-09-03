"""
FastAPI middleware for request/response logging with structured data.
"""
import json
import time
import uuid
from typing import Callable, Dict, Any, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from cartaos.utils.logging_utils import get_logger

logger = get_logger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses with structured data."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process the request and log details."""
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        # Log request
        request_log = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client": request.client.host if request.client else None,
            "request_id": request_id,
        }
        
        logger.info(
            "Request received",
            extra=request_log
        )
        
        # Process request and time it
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            response_log = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_sec": round(process_time, 4),
                "request_id": request_id,
            }
            
            # Add response size if available
            if hasattr(response, "body"):
                response_log["response_size"] = len(response.body)
            
            logger.info(
                "Response sent",
                extra=response_log
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request processing error",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "process_time_sec": round(process_time, 4),
                    "error": str(e),
                    "request_id": request_id,
                },
                exc_info=True
            )
            raise
