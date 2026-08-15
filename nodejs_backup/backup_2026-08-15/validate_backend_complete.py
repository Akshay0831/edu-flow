#!/usr/bin/env python3
"""
Backend Validation Script for Edu-Flow

This script validates the complete backend system state and provides detailed analysis
of what's working and what needs attention.

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

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackendValidator:
    """Complete backend validator"""
    
    def __init__(self):
        self.validation_results = []
        self.backend_path = os.path.dirname(os.path.abspath(__file__))
        
    def add_result(self, component: str, status: str, message: str, details: Any = None):
        """Add validation result"""
        result = {
            "component": component,
            "status": status,  # "working", "warning", "error", "missing"
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.validation_results.append(result)
        
        status_icon = {
            "working": "✅",
            "warning": "⚠️", 
            "error": "❌",
            "missing": "❓"
        }.get(status, "❓")
        
        logger.info(f"{status_icon} {component}: {message}")
    
    def validate_imports(self):
        """Validate all imports"""
        logger.info("📦 Validating imports...")
        
        imports_to_test = [
            ("FastAPI", "from fastapi import FastAPI"),
            ("asyncio", "import asyncio"),
            ("pydantic", "from pydantic import BaseModel"),
            ("sqlalchemy", "from sqlalchemy import create_engine"),
            ("pymongo", "from pymongo import MongoClient"),
            ("redis", "import redis"),
            ("aiohttp", "import aiohttp"),
            ("uvicorn", "import uvicorn"),
        ]
        
        # Test Rust AI services imports
        rust_ai_imports = [
            "from src.services.rust_ai_services.container import ServiceContainer",
            "from src.services.rust_ai_services.config import ConfigManager",
            "from src.services.rust_ai_services.registry import ServiceRegistry",
        ]
        
        for import_name, import_stmt in imports_to_test:
            try:
                exec(import_stmt)
                self.add_result(f"Import_{import_name}", "working", f"{import_name} imported successfully")
            except ImportError as e:
                self.add_result(f"Import_{import_name}", "missing", f"{import_name} not available: {str(e)}")
            except Exception as e:
                self.add_result(f"Import_{import_name}", "error", f"Error importing {import_name}: {str(e)}")
        
        # Test Rust AI services specifically
        try:
            sys.path.insert(0, os.path.join(self.backend_path, 'src', 'services'))
            from src.services.rust_ai_services import get_container, initialize_container, shutdown_container
            self.add_result("RustAI_Imports", "working", "Rust AI services imported successfully")
        except Exception as e:
            self.add_result("RustAI_Imports", "error", f"Rust AI services import failed: {str(e)}")
    
    def validate_file_structure(self):
        """Validate file structure"""
        logger.info("📁 Validating file structure...")
        
        required_files = [
            "src/main.py",
            "src/__init__.py",
            "src/core/dependencies.py",
            "src/core/security.py", 
            "src/core/exceptions.py",
            "src/auth/service.py",
            "src/auth/__init__.py",
            "src/config/logging_config.py",
            "src/models/__init__.py",
            "src/services/__init__.py",
            "src/services/rust_ai_services/__init__.py",
            "src/services/rust_ai_services/container.py",
            "src/services/rust_ai_services/config/__init__.py",
            "src/services/rust_ai_services/config/settings.py",
            "src/services/rust_ai_services/registry.py",
            "src/services/rust_ai_services/course_recommendation_service.py",
            "src/services/rust_ai_services/knowledge_search_service.py",
            "src/services/rust_ai_services/adaptive_learning_service.py",
            "src/services/rust_ai_services/integration.py",
            "src/services/rust_ai_services/monitoring.py",
            "src/services/rust_ai_services/rust_ai_config.json",
            "requirements.txt",
        ]
        
        for file_path in required_files:
            full_path = os.path.join(self.backend_path, file_path)
            if os.path.exists(full_path):
                self.add_result(f"File_{file_path}", "working", f"File exists: {file_path}")
            else:
                self.add_result(f"File_{file_path}", "missing", f"File missing: {file_path}")
    
    def validate_configuration(self):
        """Validate configuration files"""
        logger.info("⚙️ Validating configuration...")
        
        # Check Rust AI configuration
        config_path = os.path.join(self.backend_path, 'src', 'services', 'rust_ai_services', 'rust_ai_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                services = config.get('services', {})
                models = config.get('models', {})
                
                self.add_result("Config_RustAI_JSON", "working", "Rust AI configuration loaded successfully")
                self.add_result("Config_RustAI_Services", "working", f"Found {len(services)} services: {list(services.keys())}")
                self.add_result("Config_RustAI_Models", "working", f"Found {len(models)} models: {list(models.keys())}")
                
            except Exception as e:
                self.add_result("Config_RustAI_JSON", "error", f"Error loading Rust AI config: {str(e)}")
        else:
            self.add_result("Config_RustAI_JSON", "missing", "Rust AI configuration file not found")
    
    async def validate_rust_ai_services(self):
        """Validate Rust AI Services"""
        logger.info("🔬 Validating Rust AI Services...")
        
        try:
            from src.services.rust_ai_services import get_container, initialize_container, shutdown_container
            
            # Initialize container
            await initialize_container()
            self.add_result("RustAI_Container_Init", "working", "Container initialized successfully")
            
            container = get_container()
            
            # Test service discovery
            available_services = container.get_available_services_sync()
            self.add_result("RustAI_Service_Discovery", "working", 
                          f"Found {len(available_services)} services: {available_services}")
            
            # Test individual services
            for service_name in available_services:
                try:
                    service = await container.get_service(service_name)
                    if service:
                        self.add_result(f"RustAI_Service_{service_name}", "working", 
                                      f"Service {service_name} accessible: {type(service).__name__}")
                        
                        # Test basic service functionality
                        if service_name == 'knowledge_search':
                            result = await service.search({'query': 'test', 'search_type': 'keyword'})
                            self.add_result(f"RustAI_Service_{service_name}_Function", "working", 
                                          f"Service {service_name} search method working")
                        elif service_name == 'adaptive_learning':
                            # Test with minimal valid parameters
                            result = await service.get_adaptive_path('TEST001', 'TEST001', 'math101')
                            self.add_result(f"RustAI_Service_{service_name}_Function", "working", 
                                          f"Service {service_name} get_adaptive_path method working")
                        elif service_name == 'course_recommendation':
                            # Test with minimal valid data structure
                            result = await service.get_recommendations({
                                'student_id': 'TEST001',
                                'current_semester': 3,
                                'gpa': 3.5
                            })
                            self.add_result(f"RustAI_Service_{service_name}_Function", "working", 
                                          f"Service {service_name} get_recommendations method working")
                    else:
                        self.add_result(f"RustAI_Service_{service_name}", "warning", 
                                      f"Service {service_name} not accessible")
                except Exception as e:
                    self.add_result(f"RustAI_Service_{service_name}", "error", 
                                  f"Error testing service {service_name}: {str(e)}")
            
            # Shutdown container
            await shutdown_container()
            self.add_result("RustAI_Container_Shutdown", "working", "Container shutdown successfully")
            
        except Exception as e:
            self.add_result("RustAI_Services_Overall", "error", f"Rust AI services validation failed: {str(e)}")
    
    def validate_dependencies(self):
        """Validate dependencies"""
        logger.info("📋 Validating dependencies...")
        
        if os.path.exists("requirements.txt"):
            try:
                with open("requirements.txt", "r") as f:
                    requirements = f.read()
                
                # Check for key dependencies
                key_deps = [
                    ("fastapi", "FastAPI framework"),
                    ("uvicorn", "ASGI server"),
                    ("sqlalchemy", "SQL ORM"),
                    ("pymongo", "MongoDB driver"),
                    ("redis", "Redis client"),
                    ("pydantic", "Data validation"),
                    ("aiohttp", "Async HTTP client"),
                    ("python-jose[cryptography]", "JWT handling"),
                    ("passlib[bcrypt]", "Password hashing"),
                    ("python-multipart", "Form handling"),
                ]
                
                for dep, description in key_deps:
                    if dep.lower() in requirements.lower():
                        self.add_result(f"Dep_{dep}", "working", f"{description} found in requirements")
                    else:
                        self.add_result(f"Dep_{dep}", "warning", f"{description} missing from requirements")
            except Exception as e:
                self.add_result("Dep_Requirements_File", "error", f"Error reading requirements.txt: {str(e)}")
        else:
            self.add_result("Dep_Requirements_File", "missing", "requirements.txt not found")
    
    def validate_python_syntax(self):
        """Validate Python syntax"""
        logger.info("🐍 Validating Python syntax...")
        
        # Key Python files to check
        python_files = [
            "src/main.py",
            "src/auth/service.py",
            "src/core/security.py",
            "src/core/dependencies.py",
            "src/services/rust_ai_services/container.py",
            "src/services/rust_ai_services/config/settings.py",
            "src/services/rust_ai_services/course_recommendation_service.py",
            "src/services/rust_ai_services/knowledge_search_service.py",
            "src/services/rust_ai_services/adaptive_learning_service.py",
        ]
        
        for file_path in python_files:
            full_path = os.path.join(self.backend_path, file_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    # Try to compile the code
                    compile(content, full_path, 'exec')
                    self.add_result(f"Syntax_{file_path}", "working", f"Syntax valid: {file_path}")
                except SyntaxError as e:
                    self.add_result(f"Syntax_{file_path}", "error", f"Syntax error in {file_path}: {str(e)}")
                except Exception as e:
                    self.add_result(f"Syntax_{file_path}", "error", f"Error validating {file_path}: {str(e)}")
            else:
                self.add_result(f"Syntax_{file_path}", "missing", f"File not found: {file_path}")
    
    async def validate_database_schema(self):
        """Validate database schema existence"""
        logger.info("🗄️ Validating database schema...")
        
        # Check for model files
        model_files = [
            "src/models/student.py",
            "src/models/course.py",
            "src/models/teacher.py",
            "src/models/auth.py",
        ]
        
        for file_path in model_files:
            full_path = os.path.join(self.backend_path, file_path)
            if os.path.exists(full_path):
                self.add_result(f"Schema_{file_path}", "working", f"Model file exists: {file_path}")
            else:
                self.add_result(f"Schema_{file_path}", "missing", f"Model file missing: {file_path}")
    
    def generate_validation_report(self):
        """Generate validation report"""
        logger.info("📊 Generating validation report...")
        
        # Count results by status
        status_counts = {}
        for result in self.validation_results:
            status = result["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        overall_status = "working" if status_counts.get("working", 0) > len(self.validation_results) * 0.8 else "warning"
        if status_counts.get("error", 0) > 0:
            overall_status = "error"
        
        report = {
            "validation_summary": {
                "total_components": len(self.validation_results),
                "working_components": status_counts.get("working", 0),
                "warning_components": status_counts.get("warning", 0),
                "error_components": status_counts.get("error", 0),
                "missing_components": status_counts.get("missing", 0),
                "overall_status": overall_status,
                "health_score": (status_counts.get("working", 0) / len(self.validation_results) * 100) if self.validation_results else 0
            },
            "validation_details": self.validation_results,
            "generated_at": datetime.now().isoformat()
        }
        
        # Save report
        with open("backend_validation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Validation report saved to: backend_validation_report.json")
        return report
    
    async def run_complete_validation(self):
        """Run complete validation"""
        logger.info("🔍 Starting Complete Backend Validation...")
        
        start_time = time.time()
        
        # Run all validations
        self.validate_imports()
        self.validate_file_structure()
        self.validate_configuration()
        self.validate_dependencies()
        self.validate_python_syntax()
        await self.validate_rust_ai_services()
        await self.validate_database_schema()
        
        # Generate report
        report = self.generate_validation_report()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Print summary
        print("\n" + "="*60)
        print("🔍 BACKEND VALIDATION RESULTS")
        print("="*60)
        print(f"Total Components: {report['validation_summary']['total_components']}")
        print(f"✅ Working: {report['validation_summary']['working_components']}")
        print(f"⚠️ Warnings: {report['validation_summary']['warning_components']}")
        print(f"❌ Errors: {report['validation_summary']['error_components']}")
        print(f"❓ Missing: {report['validation_summary']['missing_components']}")
        print(f"📊 Health Score: {report['validation_summary']['health_score']:.1f}%")
        print(f"Overall Status: {report['validation_summary']['overall_status'].upper()}")
        print(f"⏱️ Validation Time: {total_time:.2f} seconds")
        
        print("\n📋 COMPONENT STATUS BREAKDOWN:")
        for result in self.validation_results:
            status_icon = {
                "working": "✅",
                "warning": "⚠️", 
                "error": "❌",
                "missing": "❓"
            }.get(result["status"], "❓")
            
            print(f"  {status_icon} {result['component']}: {result['message']}")
        
        print("\n" + "="*60)
        
        return report['validation_summary']['overall_status'] == 'working'

async def main():
    """Main function"""
    print("🔍 Starting Complete Backend Validation...")
    print("=" * 60)
    
    validator = BackendValidator()
    success = await validator.run_complete_validation()
    
    if success:
        print("\n🎉 BACKEND VALIDATION PASSED! System is ready.")
        sys.exit(0)
    else:
        print("\n⚠️ BACKEND VALIDATION ISSUES DETECTED. Review components above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())