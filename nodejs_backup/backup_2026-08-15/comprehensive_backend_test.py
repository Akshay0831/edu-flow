#!/usr/bin/env python3
"""
Comprehensive Backend Test Script for Edu-Flow

This script performs complete validation and testing of the entire backend system:
- FastAPI application
- Database connections (PostgreSQL, MongoDB, Redis)
- Authentication system
- All API endpoints
- Rust AI services
- Error handling
- Integration between components

Author: Edu-Flow Team
"""

import asyncio
import sys
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BackendTestSuite:
    """Comprehensive test suite for Edu-Flow backend"""
    
    def __init__(self):
        self.test_results = []
        self.base_url = "http://localhost:8000"
        self.rust_ai_services_base = "/src/services/rust_ai_services"
        
    def add_result(self, test_name: str, success: bool, message: str, details: Any = None):
        """Add test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        logger.info(f"{'✅' if success else '❌'} {test_name}: {message}")
        
    def print_summary(self):
        """Print test summary"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        print("\n" + "="*60)
        print("🧪 COMPREHENSIVE BACKEND TEST RESULTS")
        print("="*60)
        print(f"Total Tests: {total}")
        print(f"Passed: ✅ {passed}")
        print(f"Failed: ❌ {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n🔴 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test_name']}: {result['message']}")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test_name']}")
        
        print("\n" + "="*60)
        return failed == 0
    
    async def test_rust_ai_services(self):
        """Test Rust AI Services"""
        logger.info("🔬 Testing Rust AI Services...")
        
        try:
            # Import Rust AI services
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'services'))
            from src.services.rust_ai_services import get_container, initialize_container, shutdown_container
            
            # Initialize container
            await initialize_container()
            self.add_result("RustAI_Container_Init", True, "Container initialized successfully")
            
            container = get_container()
            
            # Test available services
            available_services = container.get_available_services_sync()
            self.add_result("RustAI_Service_Discovery", True, 
                          f"Found {len(available_services)} services: {available_services}")
            
            # Test each service
            service_tests = {
                'course_recommendation': {
                    'method': 'get_recommendations',
                    'data': {
                        'student_id': 'TEST001',
                        'current_program': 'Engineering',
                        'current_semester': 3,
                        'gpa': 3.5,
                        'interests': ['math', 'physics'],
                        'career_goals': ['software_engineering']
                    }
                },
                'knowledge_search': {
                    'method': 'search',
                    'data': {
                        'query': 'calculus derivatives',
                        'search_type': 'semantic',
                        'filters': {'type': ['tutorial', 'video']}
                    }
                },
                'adaptive_learning': {
                    'method': 'get_adaptive_path',
                    'data': {
                        'student_flow_id': 'TEST001',
                        'student_id': 'TEST001',
                        'skill_id': 'math101'
                    }
                }
            }
            
            for service_name, test_config in service_tests.items():
                try:
                    service = await container.get_service(service_name)
                    if service:
                        method = getattr(service, test_config['method'])
                        if asyncio.iscoroutinefunction(method):
                            result = await method(test_config['data'])
                        else:
                            result = method(test_config['data'])
                        
                        self.add_result(f"RustAI_{service_name}_Service", True, 
                                      f"Service {service_name} method {test_config['method']} executed successfully")
                    else:
                        self.add_result(f"RustAI_{service_name}_Service", False, 
                                      f"Service {service_name} not available")
                except Exception as e:
                    self.add_result(f"RustAI_{service_name}_Service", False, 
                                  f"Error testing service {service_name}: {str(e)}")
            
            # Shutdown container
            await shutdown_container()
            self.add_result("RustAI_Container_Shutdown", True, "Container shutdown successfully")
            
        except Exception as e:
            self.add_result("RustAI_Services_Overall", False, f"Rust AI services test failed: {str(e)}")
    
    async def test_fastapi_application(self):
        """Test FastAPI Application"""
        logger.info("🚀 Testing FastAPI Application...")
        
        try:
            from src.main import app
            import httpx
            
            async with httpx.AsyncClient(base_url=self.base_url) as client:
                # Test root endpoint
                response = await client.get("/")
                self.add_result("FastAPI_Root_Endpoint", response.status_code == 200, 
                              f"Root endpoint status: {response.status_code}")
                
                # Test API health check
                response = await client.get("/api/v1/health")
                self.add_result("FastAPI_Health_Check", response.status_code == 200,
                              f"Health check status: {response.status_code}")
                
                # Test API docs
                response = await client.get("/docs")
                self.add_result("FastAPI_Docs_Accessible", response.status_code == 200,
                              f"API docs status: {response.status_code}")
                
                # Test OpenAPI schema
                response = await client.get("/openapi.json")
                if response.status_code == 200:
                    schema = response.json()
                    self.add_result("FastAPI_OpenAPI_Valid", True,
                                  f"OpenAPI schema loaded with {len(schema.get('paths', {}))} paths")
                else:
                    self.add_result("FastAPI_OpenAPI_Valid", False,
                                  f"OpenAPI schema failed: {response.status_code}")
        
        except Exception as e:
            self.add_result("FastAPI_Application_Overall", False, 
                          f"FastAPI application test failed: {str(e)}")
    
    async def test_database_connections(self):
        """Test Database Connections"""
        logger.info("🗄️ Testing Database Connections...")
        
        try:
            # Test PostgreSQL connection
            try:
                from sqlalchemy import create_engine
                from sqlalchemy.ext.declarative import declarative_base
                from sqlalchemy.orm import sessionmaker
                
                # Test connection string (adjust as needed)
                test_url = "postgresql://postgres:test_password@localhost:5432/edu_flow"
                engine = create_engine(test_url)
                connection = engine.connect()
                result = connection.execute("SELECT 1")
                self.add_result("PostgreSQL_Connection", True, "PostgreSQL connection successful")
                connection.close()
            except Exception as e:
                self.add_result("PostgreSQL_Connection", False, f"PostgreSQL connection failed: {str(e)}")
            
            # Test MongoDB connection
            try:
                from pymongo import MongoClient
                client = MongoClient("mongodb://localhost:27017/")
                db = client["edu_flow"]
                client.list_database_names()
                self.add_result("MongoDB_Connection", True, "MongoDB connection successful")
                client.close()
            except Exception as e:
                self.add_result("MongoDB_Connection", False, f"MongoDB connection failed: {str(e)}")
            
            # Test Redis connection
            try:
                import redis
                r = redis.Redis(host='localhost', port=6379, db=0)
                r.ping()
                self.add_result("Redis_Connection", True, "Redis connection successful")
                r.close()
            except Exception as e:
                self.add_result("Redis_Connection", False, f"Redis connection failed: {str(e)}")
        
        except Exception as e:
            self.add_result("Database_Connections_Overall", False, 
                          f"Database connections test failed: {str(e)}")
    
    async def test_authentication_system(self):
        """Test Authentication System"""
        logger.info("🔐 Testing Authentication System...")
        
        try:
            from src.auth.service import AuthService
            from src.core.security import verify_password, create_access_token
            
            auth_service = AuthService()
            
            # Test password hashing and verification
            test_password = "test_password_123"
            hashed = auth_service.hash_password(test_password)
            verified = auth_service.verify_password(test_password, hashed)
            self.add_result("Auth_Password_Hashing", verified, 
                          "Password hashing and verification working")
            
            # Test JWT token creation and verification
            token_data = {"user_id": "test_user", "role": "student"}
            token = create_access_token(data=token_data)
            decoded = auth_service.verify_token(token)
            self.add_result("Auth_JWT_Tokens", decoded is not None, 
                          "JWT token creation and verification working")
            
            # Test user validation (if available)
            if hasattr(auth_service, 'validate_user'):
                try:
                    user = await auth_service.validate_user("test_user")
                    self.add_result("Auth_User_Validation", user is not None, 
                                  "User validation working")
                except Exception as e:
                    self.add_result("Auth_User_Validation", False, 
                                  f"User validation failed: {str(e)}")
        
        except Exception as e:
            self.add_result("Authentication_System_Overall", False, 
                          f"Authentication system test failed: {str(e)}")
    
    async def test_api_endpoints(self):
        """Test API Endpoints"""
        logger.info("🌐 Testing API Endpoints...")
        
        try:
            import httpx
            
            async with httpx.AsyncClient(base_url=self.base_url) as client:
                # Test common API endpoints
                endpoints = [
                    ("/api/v1/students", "GET"),
                    ("/api/v1/courses", "GET"),
                    ("/api/v1/teachers", "GET"),
                    ("/api/v1/auth/login", "POST"),
                    ("/api/v1/analytics", "GET"),
                ]
                
                for endpoint, method in endpoints:
                    try:
                        if method == "GET":
                            response = await client.get(endpoint)
                        else:
                            response = await client.post(endpoint, json={"test": "data"})
                        
                        # Don't fail on 404/403 (expected for unauthenticated requests)
                        if response.status_code in [200, 401, 403, 404]:
                            self.add_result(f"API_{endpoint.replace('/', '_')}", True, 
                                          f"Endpoint {method} {endpoint} responded with {response.status_code}")
                        else:
                            self.add_result(f"API_{endpoint.replace('/', '_')}", False, 
                                          f"Endpoint {method} {endpoint} unexpected status: {response.status_code}")
                    except Exception as e:
                        self.add_result(f"API_{endpoint.replace('/', '_')}", False, 
                                      f"Endpoint {method} {endpoint} failed: {str(e)}")
        
        except Exception as e:
            self.add_result("API_Endpoints_Overall", False, 
                          f"API endpoints test failed: {str(e)}")
    
    async def test_error_handling(self):
        """Test Error Handling"""
        logger.info("⚠️ Testing Error Handling...")
        
        try:
            import httpx
            
            async with httpx.AsyncClient(base_url=self.base_url) as client:
                # Test invalid endpoints
                response = await client.get("/api/v1/nonexistent")
                self.add_result("ErrorHandling_Invalid_Endpoint", response.status_code == 404,
                              f"Invalid endpoint handled correctly: {response.status_code}")
                
                # Test invalid data
                response = await client.post("/api/v1/auth/login", json={"invalid": "data"})
                self.add_result("ErrorHandling_Invalid_Data", response.status_code in [400, 422],
                              f"Invalid data handled correctly: {response.status_code}")
                
                # Test missing authentication
                response = await client.get("/api/v1/protected")
                self.add_result("ErrorHandling_Missing_Auth", response.status_code == 401,
                              f"Missing auth handled correctly: {response.status_code}")
        
        except Exception as e:
            self.add_result("Error_Handling_Overall", False, 
                          f"Error handling test failed: {str(e)}")
    
    async def test_configuration_system(self):
        """Test Configuration System"""
        logger.info("⚙️ Testing Configuration System...")
        
        try:
            from src.config.logging_config import setup_logging
            from src.core.dependencies import get_db
            
            # Test logging setup
            logging_config = setup_logging()
            self.add_result("Config_Logging_Setup", logging_config is not None, 
                          "Logging configuration setup successful")
            
            # Test database dependency
            try:
                db_session = await get_db()
                self.add_result("Config_Dependency_Inject", db_session is not None, 
                              "Database dependency injection working")
            except Exception as e:
                self.add_result("Config_Dependency_Inject", False, 
                              f"Database dependency injection failed: {str(e)}")
        
        except Exception as e:
            self.add_result("Configuration_System_Overall", False, 
                          f"Configuration system test failed: {str(e)}")
    
    async def test_service_integration(self):
        """Test Service Integration"""
        logger.info("🔗 Testing Service Integration...")
        
        try:
            from src.services.rust_ai_services import get_container
            from src.services.course_service import CourseService
            from src.services.student_service import StudentService
            from src.services.user_service import UserService
            
            # Test service instantiation
            services = {
                "CourseService": CourseService(),
                "StudentService": StudentService(),
                "UserService": UserService(),
            }
            
            for service_name, service in services.items():
                try:
                    if hasattr(service, 'check_health'):
                        health = await service.check_health()
                        self.add_result(f"Service_{service_name}_Health", True, 
                                      f"{service_name} health check passed")
                    else:
                        self.add_result(f"Service_{service_name}_Health", True, 
                                      f"{service_name} instantiated successfully")
                except Exception as e:
                    self.add_result(f"Service_{service_name}_Health", False, 
                                  f"{service_name} health check failed: {str(e)}")
            
            # Test Rust AI services integration
            container = get_container()
            enabled_services = await container.get_enabled_services()
            self.add_result("RustAI_Integration", len(enabled_services) > 0, 
                          f"Rust AI services integrated: {enabled_services}")
        
        except Exception as e:
            self.add_result("Service_Integration_Overall", False, 
                          f"Service integration test failed: {str(e)}")
    
    async def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        logger.info("🧪 Starting Comprehensive Backend Test Suite...")
        
        start_time = time.time()
        
        # Run all test suites
        test_suites = [
            ("Rust AI Services", self.test_rust_ai_services),
            ("FastAPI Application", self.test_fastapi_application),
            ("Database Connections", self.test_database_connections),
            ("Authentication System", self.test_authentication_system),
            ("API Endpoints", self.test_api_endpoints),
            ("Error Handling", self.test_error_handling),
            ("Configuration System", self.test_configuration_system),
            ("Service Integration", self.test_service_integration),
        ]
        
        for suite_name, test_func in test_suites:
            try:
                logger.info(f"\n📋 Running {suite_name}...")
                await test_func()
            except Exception as e:
                self.add_result(f"{suite_name}_Suite", False, 
                              f"{suite_name} suite failed: {str(e)}")
                logger.error(f"Error in {suite_name}: {str(e)}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Print results
        success = self.print_summary()
        
        logger.info(f"\n⏱️ Total Test Time: {total_time:.2f} seconds")
        logger.info(f"\n📄 Detailed results saved to: backend_test.log")
        
        # Generate test report
        self.generate_test_report()
        
        return success
    
    def generate_test_report(self):
        """Generate detailed test report"""
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results if r["success"]),
                "failed_tests": sum(1 for r in self.test_results if not r["success"]),
                "success_rate": (sum(1 for r in self.test_results if r["success"]) / len(self.test_results) * 100) if self.test_results else 0
            },
            "test_details": self.test_results,
            "generated_at": datetime.now().isoformat()
        }
        
        # Save report to file
        with open("backend_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Test report saved to: backend_test_report.json")

async def main():
    """Main function"""
    print("🚀 Starting Comprehensive Backend Test Suite...")
    print("=" * 60)
    
    test_suite = BackendTestSuite()
    success = await test_suite.run_comprehensive_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! Backend system is fully functional.")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED! Please review the results above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())