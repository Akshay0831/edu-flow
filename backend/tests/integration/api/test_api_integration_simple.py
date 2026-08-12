"""
Simple API Integration Tests using TestClient

This test suite uses TestClient for direct FastAPI app testing.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

class TestAPIIntegration:
    """Comprehensive test suite for API Integration"""
    
    @pytest.fixture
    def client(self):
        """Setup TestClient for testing"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "uptime" in data
        assert data["status"] == "healthy"
    
    def test_api_info_endpoint(self, client):
        """Test API info endpoint"""
        response = client.get("/api/v1/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "endpoints" in data
        
        assert data["name"] == "Edu-Flow Backend API"
        assert data["version"] == "1.0.0"
        assert "auth" in data["endpoints"]
        assert "users" in data["endpoints"]
        assert "students" in data["endpoints"]
        assert "courses" in data["endpoints"]
    
    def test_database_health_endpoint(self, client):
        """Test database health endpoint"""
        response = client.get("/api/v1/database/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "database" in data
        assert "mongodb_connected" in data["database"]
        assert "ping" in data["database"]
        assert "collections" in data["database"]
        assert data["status"] == "healthy"
        assert data["database"]["mongodb_connected"] == True
    
    def test_get_departments(self, client):
        """Test get all departments endpoint"""
        response = client.get("/api/v1/database/departments")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "departments" in data
        assert isinstance(data["departments"], list)
        assert len(data["departments"]) > 0
        
        # Check department structure
        department = data["departments"][0]
        assert "department_id" in department
        assert "name" in department
        assert "code" in department
        assert "description" in department
    
    def test_get_departments_with_filter(self, client):
        """Test get departments with filter"""
        response = client.get("/api/v1/database/departments?department_id=DEPT_CS")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "departments" in data
        assert isinstance(data["departments"], list)
        
        # Check if filtered results match the filter
        if data["departments"]:
            dept = data["departments"][0]
            assert dept["department_id"] == "DEPT_CS"
    
    def test_get_single_department(self, client):
        """Test get single department endpoint"""
        response = client.get("/api/v1/database/departments/DEPT_CS")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "department" in data
        assert data["department"]["department_id"] == "DEPT_CS"
        assert "name" in data["department"]
        assert "code" in data["department"]
        assert "description" in data["department"]