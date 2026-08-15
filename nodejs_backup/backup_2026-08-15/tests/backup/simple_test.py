
"""
Simple test to verify pytest is working
"""

import pytest

def test_simple_addition():
    """Simple test to verify pytest is working"""
    result = 2 + 2
    assert result == 4

def test_database_import():
    """Test database import works"""
    from src.services.database_service import database_service
    assert database_service is not None

def test_main_app_import():
    """Test main app import works"""
    from src.main import app
    assert app is not None