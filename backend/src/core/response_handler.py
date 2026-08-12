"""
Standardized Response Handler for Edu-Flow Backend

This module provides a centralized system for handling API responses consistently
across all endpoints, ensuring uniform response formats and proper status codes.

Author: Edu-Flow Team
"""

from typing import Any, Dict, Optional, List, Union
from fastapi import Response
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import uuid


class ResponseFormatter:
    """Centralized response formatting system"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = 200,
        meta: Optional[Dict] = None
    ) -> JSONResponse:
        """Create a standardized success response"""
        response_data = {
            "success": True,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if data is not None:
            response_data["data"] = data
        
        if meta:
            response_data["meta"] = meta
            
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @staticmethod
    def error(
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict] = None,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Create a standardized error response"""
        response_data = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        if details:
            response_data["error"]["details"] = details
            
        if request_id:
            response_data["error"]["request_id"] = request_id
            
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @staticmethod
    def paginated(
        data: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: str = "Data retrieved successfully"
    ) -> JSONResponse:
        """Create a standardized paginated response"""
        return ResponseFormatter.success(
            data=data,
            message=message,
            meta={
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        )
    
    @staticmethod
    def created(data: Any = None, message: str = "Resource created successfully") -> JSONResponse:
        """Create a standardized 201 Created response"""
        return ResponseFormatter.success(data, message, 201)
    
    @staticmethod
    def updated(data: Any = None, message: str = "Resource updated successfully") -> JSONResponse:
        """Create a standardized 200 OK response for updates"""
        return ResponseFormatter.success(data, message, 200)
    
    @staticmethod
    def deleted(message: str = "Resource deleted successfully") -> JSONResponse:
        """Create a standardized 200 OK response for deletions"""
        return ResponseFormatter.success(None, message, 200)
    
    @staticmethod
    def bad_request(message: str = "Bad request", details: Optional[Dict] = None) -> JSONResponse:
        """Create a standardized 400 Bad Request response"""
        return ResponseFormatter.error(message, "VALIDATION_ERROR", 400, details)
    
    @staticmethod
    def unauthorized(message: str = "Unauthorized", details: Optional[Dict] = None) -> JSONResponse:
        """Create a standardized 401 Unauthorized response"""
        return ResponseFormatter.error(message, "UNAUTHORIZED", 401, details)
    
    @staticmethod
    def forbidden(message: str = "Forbidden", details: Optional[Dict] = None) -> JSONResponse:
        """Create a standardized 403 Forbidden response"""
        return ResponseFormatter.error(message, "FORBIDDEN", 403, details)
    
    @staticmethod
    def not_found(message: str = "Resource not found", details: Optional[Dict] = None) -> JSONResponse:
        """Create a standardized 404 Not Found response"""
        return ResponseFormatter.error(message, "NOT_FOUND", 404, details)
    
    @staticmethod
    def conflict(message: str = "Conflict", details: Optional[Dict] = None) -> JSONResponse:
        """Create a standardized 409 Conflict response"""
        return ResponseFormatter.error(message, "CONFLICT", 409, details)
    
    @staticmethod
    def unprocessable_entity(message: str = "Unprocessable entity", details: Optional[Dict] = None) -> JSONResponse:
        """Create a standardized 422 Unprocessable Entity response"""
        return ResponseFormatter.error(message, "VALIDATION_ERROR", 422, details)


class ResponseMiddleware:
    """Middleware to standardize responses and add request ID tracking"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Generate request ID for tracking
            request_id = str(uuid.uuid4())
            
            # Create sender wrapper to add request ID to responses
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    # Add request ID to headers if not already present
                    headers = dict(message.get("headers", []))
                    if b"x-request-id" not in headers:
                        headers[b"x-request-id"] = request_id.encode()
                    message["headers"] = list(headers.items())
                await send(message)
            
            # Add request_id to scope for access in exception handlers
            scope["request_id"] = request_id
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


# Decorator for standardizing endpoint responses
def standardize_response(func):
    """Decorator to automatically standardize endpoint responses"""
    import asyncio
    
    async def wrapper(*args, **kwargs):
        try:
            # Get request from FastAPI context
            request = kwargs.get('request')
            request_id = getattr(request.state, 'request_id', None) if request else None
            
            # Call the original function
            result = await func(*args, **kwargs)
            
            # If result is already a JSONResponse, return it as-is
            if isinstance(result, JSONResponse):
                return result
            
            # If result is a tuple (data, status_code), format it
            if isinstance(result, tuple) and len(result) == 2:
                data, status_code = result
                return ResponseFormatter.success(data, "Success", status_code)
            
            # Otherwise, treat as success response
            return ResponseFormatter.success(result)
            
        except Exception as e:
            # Handle different types of exceptions
            from src.core.exceptions import BaseError
            
            if isinstance(e, BaseError):
                return ResponseFormatter.error(
                    message=e.message,
                    error_code=e.error_code,
                    status_code=getattr(e, 'status_code', 500),
                    details=e.details,
                    request_id=request_id
                )
            else:
                # Generic error handling
                return ResponseFormatter.error(
                    message=str(e),
                    error_code="INTERNAL_ERROR",
                    status_code=500,
                    request_id=request_id
                )
    
    return wrapper