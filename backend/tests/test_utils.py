"""
Test validation utilities for Edu-Flow backend tests.

This module provides common validation utilities used across test suites.
"""

import json
import re
from typing import Dict, Any, List, Optional
from fastapi import status


def assert_response_format(response, expected_status: int = status.HTTP_200_OK):
    """Assert that response has proper format."""
    assert response.status_code == expected_status
    assert isinstance(response.json(), dict)
    return response.json()


def assert_error(response, expected_status: int = status.HTTP_400_BAD_REQUEST):
    """Assert that response is an error."""
    assert response.status_code == expected_status
    assert isinstance(response.json(), dict)
    assert "error" in response.json() or "detail" in response.json()
    return response.json()


def assert_success(response, required_fields: Optional[List[str]] = None):
    """Assert that response is successful and optionally check required fields."""
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, dict)
    
    if required_fields:
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
    
    return data


def assert_http_error(response, expected_status: int):
    """Assert HTTP error response."""
    assert response.status_code == expected_status
    return response.json()


def validate_test_data(data: Dict[str, Any], validation_rules: Dict[str, Any]):
    """Validate test data against validation rules."""
    for field, rules in validation_rules.items():
        if field in data:
            value = data[field]
            
            # Check type
            if "type" in rules:
                assert isinstance(value, rules["type"]), f"Field {field} must be {rules['type']}"
            
            # Check required
            if rules.get("required", False) and value is None:
                raise AssertionError(f"Field {field} is required")
            
            # Check min/max length
            if "min_length" in rules and len(str(value)) < rules["min_length"]:
                raise AssertionError(f"Field {field} must be at least {rules['min_length']} characters")
            
            if "max_length" in rules and len(str(value)) > rules["max_length"]:
                raise AssertionError(f"Field {field} must be at most {rules['max_length']} characters")
            
            # Check regex patterns
            if "regex" in rules and not re.match(rules["regex"], str(value)):
                raise AssertionError(f"Field {field} doesn't match pattern: {rules['regex']}")
    
    return True