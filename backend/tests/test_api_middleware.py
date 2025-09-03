"""
Tests for API middleware functionality.
"""
import json
from unittest.mock import ANY, MagicMock, patch

import pytest
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.testclient import TestClient

from cartaos.api.middleware.logging_middleware import RequestLoggingMiddleware

@pytest.fixture
def test_app():
    """Create a test FastAPI app with the logging middleware."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test response"}
    
    return app

def test_request_logging_middleware_logs_request_and_response(test_app):
    """Test that the middleware logs request and response details."""
    # Setup test client with middleware
    test_app.add_middleware(RequestLoggingMiddleware)
    client = TestClient(test_app)
    
    with patch("cartaos.api.middleware.logging_middleware.logger") as mock_logger:
        # Make test request
        response = client.get("/test")
        
        # Verify response
        assert response.status_code == 200
        assert response.json() == {"message": "test response"}
        
        # Verify request logging
        mock_logger.info.assert_any_call(
            "Request received",
            extra={
                "method": "GET",
                "path": "/test",
                "query_params": {},
                "client": ANY,  # Can be None or actual client IP
                "request_id": ANY,
            },
        )
        
        # Verify response logging
        response_log_call = None
        for call in mock_logger.info.call_args_list:
            if call[0][0] == "Response sent":
                response_log_call = call
                break
                
        assert response_log_call is not None
        assert response_log_call[0][0] == "Response sent"
        assert response_log_call[1]["extra"]["method"] == "GET"
        assert response_log_call[1]["extra"]["path"] == "/test"
        assert response_log_call[1]["extra"]["status_code"] == 200
        assert "process_time_sec" in response_log_call[1]["extra"]
        assert isinstance(response_log_call[1]["extra"]["process_time_sec"], float)

def test_request_logging_with_query_params(test_app):
    """Test logging with query parameters."""
    test_app.add_middleware(RequestLoggingMiddleware)
    client = TestClient(test_app)
    
    with patch("cartaos.api.middleware.logging_middleware.logger") as mock_logger:
        response = client.get("/test?param1=value1&param2=value2")
        
        assert response.status_code == 200
        # Verify query params in request logging
        request_log_call = None
        for call in mock_logger.info.call_args_list:
            if call[0][0] == "Request received" and call[1]["extra"].get("path") == "/test":
                request_log_call = call
                break
                
        assert request_log_call is not None
        assert request_log_call[0][0] == "Request received"
        assert request_log_call[1]["extra"]["method"] == "GET"
        assert request_log_call[1]["extra"]["path"] == "/test"
        assert request_log_call[1]["extra"]["query_params"] == {"param1": "value1", "param2": "value2"}
        assert "request_id" in request_log_call[1]["extra"]

def test_request_logging_error_response(test_app):
    """Test logging of error responses."""
    @test_app.get("/error")
    async def error_endpoint():
        raise HTTPException(status_code=400, detail="Test error")
    
    test_app.add_middleware(RequestLoggingMiddleware)
    client = TestClient(test_app)
    
    with patch("cartaos.api.middleware.logging_middleware.logger") as mock_logger:
        response = client.get("/error")
        
        assert response.status_code == 400
        # Verify error response logging
        response_log_call = None
        for call in mock_logger.info.call_args_list:
            if call[0][0] == "Response sent" and call[1]["extra"].get("path") == "/error":
                response_log_call = call
                break
                
        assert response_log_call is not None
        assert response_log_call[0][0] == "Response sent"
        assert response_log_call[1]["extra"]["method"] == "GET"
        assert response_log_call[1]["extra"]["path"] == "/error"
        assert response_log_call[1]["extra"]["status_code"] == 400
        assert "process_time_sec" in response_log_call[1]["extra"]
        assert isinstance(response_log_call[1]["extra"]["process_time_sec"], float)
