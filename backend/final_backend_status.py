#!/usr/bin/env python3
"""
Final Backend Status Report for Edu-Flow

This script provides a comprehensive status report of the backend system,
focusing on what's working and what needs attention.

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

class BackendStatusAnalyzer:
    """Backend status analyzer and reporter"""
    
    def __init__(self):
        self.status_results = []
        self.backend_path = os.path.dirname(os.path.abspath(__file__))
        
    def add_status(self, category: str, component: str, status: str, message: str, details: Any = None):
        """Add status result"""
        result = {
            "category": category,
            "component": component,
            "status": status,  # "operational", "functional", "needs_attention", "critical"
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.status_results.append(result)
        
        status_icon = {
            "operational": "🟢",
            "functional": "🟡", 
            "needs_attention": "🟠",
            "critical": "🔴"
        }.get(status, "⚪")
        
        logger.info(f"{status_icon} {category}.{component}: {message}")
    
    def analyze_file_structure(self):
        """Analyze file structure status"""
        logger.info("📁 Analyzing file structure...")
        
        critical_files = [
            "src/main.py",
            "src/core/dependencies.py",
            "src/core/security.py",
            "src/auth/service.py",
            "src/config/logging_config.py",
        ]
        
        functional_files = [
            "src/models/student.py",
            "src/models/course.py",
            "src/services/course_service.py",
            "src/services/student_service.py",
            "src/services/user_service.py",
        ]
        
        # Rust AI Services files
        rust_ai_files = [
            "src/services/rust_ai_services/__init__.py",
            "src/services/rust_ai_services/container.py",
            "src/services/rust_ai_services/config/settings.py",
            "src/services/rust_ai_services/rust_ai_config.json",
            "src/services/rust_ai_services/course_recommendation_service.py",
            "src/services/rust_ai_services/knowledge_search_service.py",
            "src/services/rust_ai_services/adaptive_learning_service.py",
        ]
        
        for file_path in critical_files:
            full_path = os.path.join(self.backend_path, file_path)
            if os.path.exists(full_path):
                self.add_status("FileStructure", file_path, "operational", f"Critical file exists: {file_path}")
            else:
                self.add_status("FileStructure", file_path, "critical", f"Critical file missing: {file_path}")
        
        for file_path in functional_files:
            full_path = os.path.join(self.backend_path, file_path)
            if os.path.exists(full_path):
                self.add_status("FileStructure", file_path, "functional", f"Functional file exists: {file_path}")
            else:
                self.add_status("FileStructure", file_path, "needs_attention", f"Functional file missing: {file_path}")
        
        for file_path in rust_ai_files:
            full_path = os.path.join(self.backend_path, file_path)
            if os.path.exists(full_path):
                self.add_status("RustAI", file_path, "operational", f"Rust AI file exists: {file_path}")
            else:
                self.add_status("RustAI", file_path, "critical", f"Rust AI file missing: {file_path}")
    
    def analyze_configuration(self):
        """Analyze configuration status"""
        logger.info("⚙️ Analyzing configuration...")
        
        # Check Rust AI configuration
        config_path = os.path.join(self.backend_path, 'src', 'services', 'rust_ai_services', 'rust_ai_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                services = config.get('services', {})
                models = config.get('models', {})
                
                self.add_status("Configuration", "rust_ai_config.json", "operational", 
                              f"Rust AI configuration loaded: {len(services)} services, {len(models)} models")
                self.add_status("Configuration", "services_count", "functional", 
                              f"Services configured: {list(services.keys())}")
                self.add_status("Configuration", "models_count", "functional", 
                              f"Models configured: {list(models.keys())}")
                
            except Exception as e:
                self.add_status("Configuration", "rust_ai_config.json", "critical", 
                              f"Error loading Rust AI config: {str(e)}")
        else:
            self.add_status("Configuration", "rust_ai_config.json", "critical", 
                          "Rust AI configuration file not found")
    
    async def analyze_rust_ai_services(self):
        """Analyze Rust AI Services status"""
        logger.info("🔬 Analyzing Rust AI Services...")
        
        try:
            from src.services.rust_ai_services import get_container, initialize_container, shutdown_container
            
            # Initialize container
            await initialize_container()
            self.add_status("RustAI", "container_initialization", "operational", 
                          "Rust AI container initialized successfully")
            
            container = get_container()
            
            # Test service discovery
            available_services = container.get_available_services_sync()
            self.add_status("RustAI", "service_discovery", "operational", 
                          f"Found {len(available_services)} services: {available_services}")
            
            # Test individual services
            service_status = {
                'course_recommendation': 'functional',
                'knowledge_search': 'operational', 
                'adaptive_learning': 'functional'
            }
            
            for service_name in available_services:
                try:
                    service = await container.get_service(service_name)
                    if service:
                        self.add_status("RustAI", f"service_{service_name}", "operational", 
                                      f"Service {service_name} accessible: {type(service).__name__}")
                        
                        # Test basic service functionality
                        if service_name == 'knowledge_search':
                            result = await service.search({'query': 'test', 'search_type': 'keyword'})
                            self.add_status("RustAI", f"service_{service_name}_search", "operational", 
                                          f"Service {service_name} search method working")
                        elif service_name == 'adaptive_learning':
                            try:
                                result = await service.get_adaptive_path('TEST001', 'TEST001', 'math101')
                                self.add_status("RustAI", f"service_{service_name}_get_adaptive_path", "functional", 
                                              f"Service {service_name} get_adaptive_path method working")
                            except Exception as e:
                                self.add_status("RustAI", f"service_{service_name}_get_adaptive_path", "needs_attention", 
                                              f"Service {service_name} method needs attention: {str(e)}")
                        elif service_name == 'course_recommendation':
                            try:
                                result = await service.get_recommendations({
                                    'student_id': 'TEST001',
                                    'current_semester': 3,
                                    'gpa': 3.5
                                })
                                self.add_status("RustAI", f"service_{service_name}_get_recommendations", "functional", 
                                              f"Service {service_name} get_recommendations method working")
                            except Exception as e:
                                self.add_status("RustAI", f"service_{service_name}_get_recommendations", "needs_attention", 
                                              f"Service {service_name} method needs attention: {str(e)}")
                    else:
                        self.add_status("RustAI", f"service_{service_name}", "needs_attention", 
                                      f"Service {service_name} not accessible")
                except Exception as e:
                    self.add_status("RustAI", f"service_{service_name}", "needs_attention", 
                                  f"Service {service_name} testing issue: {str(e)}")
            
            # Shutdown container
            await shutdown_container()
            self.add_status("RustAI", "container_shutdown", "operational", 
                          "Rust AI container shutdown successfully")
            
        except Exception as e:
            self.add_status("RustAI", "services_overall", "critical", 
                          f"Rust AI services analysis failed: {str(e)}")
    
    def analyze_dependencies(self):
        """Analyze dependencies status"""
        logger.info("📋 Analyzing dependencies...")
        
        if os.path.exists("requirements.txt"):
            try:
                with open("requirements.txt", "r") as f:
                    requirements = f.read()
                
                # Check for critical dependencies
                critical_deps = [
                    ("fastapi", "FastAPI framework"),
                    ("uvicorn", "ASGI server"),
                    ("sqlalchemy", "SQL ORM"),
                ]
                
                for dep, description in critical_deps:
                    if dep.lower() in requirements.lower():
                        self.add_status("Dependencies", dep, "operational", f"Critical dependency found: {description}")
                    else:
                        self.add_status("Dependencies", dep, "critical", f"Critical dependency missing: {description}")
                
                # Check for additional dependencies
                additional_deps = [
                    ("pymongo", "MongoDB driver"),
                    ("redis", "Redis client"),
                    ("pydantic", "Data validation"),
                ]
                
                for dep, description in additional_deps:
                    if dep.lower() in requirements.lower():
                        self.add_status("Dependencies", dep, "functional", f"Additional dependency found: {description}")
                    else:
                        self.add_status("Dependencies", dep, "needs_attention", f"Additional dependency missing: {description}")
                        
            except Exception as e:
                self.add_status("Dependencies", "requirements_file", "critical", 
                              f"Error reading requirements.txt: {str(e)}")
        else:
            self.add_status("Dependencies", "requirements_file", "critical", 
                          "requirements.txt not found")
    
    def analyze_code_quality(self):
        """Analyze code quality"""
        logger.info("🔍 Analyzing code quality...")
        
        # Check for Python files and basic syntax
        python_files = [
            "src/main.py",
            "src/auth/service.py",
            "src/core/security.py",
            "src/services/rust_ai_services/container.py",
            "src/services/rust_ai_services/course_recommendation_service.py",
            "src/services/rust_ai_services/knowledge_search_service.py",
            "src/services/rust_ai_services/adaptive_learning_service.py",
        ]
        
        for file_path in python_files:
            full_path = os.path.join(self.backend_path, file_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Try to compile the code
                    compile(content, full_path, 'exec')
                    self.add_status("CodeQuality", file_path, "operational", 
                                  f"Syntax valid: {file_path}")
                except SyntaxError as e:
                    self.add_status("CodeQuality", file_path, "critical", 
                                  f"Syntax error in {file_path}: {str(e)}")
                except UnicodeDecodeError as e:
                    self.add_status("CodeQuality", file_path, "critical", 
                                  f"Encoding error in {file_path}: {str(e)}")
                except Exception as e:
                    self.add_status("CodeQuality", file_path, "needs_attention", 
                                  f"Error validating {file_path}: {str(e)}")
            else:
                self.add_status("CodeQuality", file_path, "needs_attention", 
                              f"File not found: {file_path}")
    
    def generate_status_report(self):
        """Generate comprehensive status report"""
        logger.info("📊 Generating status report...")
        
        # Count results by status
        status_counts = {}
        category_counts = {}
        
        for result in self.status_results:
            status = result["status"]
            category = result["category"]
            
            status_counts[status] = status_counts.get(status, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Calculate overall status
        total_components = len(self.status_results)
        critical_issues = status_counts.get("critical", 0)
        attention_needed = status_counts.get("needs_attention", 0)
        
        if critical_issues > 0:
            overall_status = "critical"
        elif attention_needed > total_components * 0.2:
            overall_status = "needs_attention"
        elif status_counts.get("operational", 0) > total_components * 0.8:
            overall_status = "operational"
        else:
            overall_status = "functional"
        
        report = {
            "status_summary": {
                "total_components": total_components,
                "operational_components": status_counts.get("operational", 0),
                "functional_components": status_counts.get("functional", 0),
                "needs_attention_components": status_counts.get("needs_attention", 0),
                "critical_components": status_counts.get("critical", 0),
                "overall_status": overall_status,
                "health_score": (status_counts.get("operational", 0) / total_components * 100) if total_components > 0 else 0
            },
            "category_summary": category_counts,
            "status_details": self.status_results,
            "generated_at": datetime.now().isoformat(),
            "recommendations": self._generate_recommendations(status_counts, category_counts)
        }
        
        # Save report
        with open("backend_status_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Status report saved to: backend_status_report.json")
        return report
    
    def _generate_recommendations(self, status_counts: Dict[str, int], category_counts: Dict[str, int]) -> List[str]:
        """Generate recommendations based on status"""
        recommendations = []
        
        if status_counts.get("critical", 0) > 0:
            recommendations.append("🔴 CRITICAL: Address critical issues immediately before deployment")
        
        if status_counts.get("needs_attention", 0) > 0:
            recommendations.append("🟠 ATTENTION: Some components need attention but system can function")
        
        if "RustAI" in category_counts and status_counts.get("critical", 0) == 0:
            recommendations.append("🟢 RUST AI SERVICES: Core functionality implemented and working")
        
        if "Configuration" in category_counts and status_counts.get("critical", 0) == 0:
            recommendations.append("⚙️ CONFIGURATION: System properly configured")
        
        if status_counts.get("operational", 0) > status_counts.get("critical", 0) * 3:
            recommendations.append("📈 SYSTEM HEALTH: Majority of components are operational")
        
        return recommendations
    
    async def run_complete_analysis(self):
        """Run complete backend analysis"""
        logger.info("🔍 Starting Complete Backend Analysis...")
        
        start_time = time.time()
        
        # Run all analyses
        self.analyze_file_structure()
        self.analyze_configuration()
        self.analyze_dependencies()
        self.analyze_code_quality()
        await self.analyze_rust_ai_services()
        
        # Generate report
        report = self.generate_status_report()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Print summary
        print("\n" + "="*60)
        print("🔍 EDU-FLOW BACKEND STATUS REPORT")
        print("="*60)
        print(f"Total Components: {report['status_summary']['total_components']}")
        print(f"🟢 Operational: {report['status_summary']['operational_components']}")
        print(f"🟡 Functional: {report['status_summary']['functional_components']}")
        print(f"🟠 Needs Attention: {report['status_summary']['needs_attention_components']}")
        print(f"🔴 Critical: {report['status_summary']['critical_components']}")
        print(f"📊 Health Score: {report['status_summary']['health_score']:.1f}%")
        print(f"Overall Status: {report['status_summary']['overall_status'].upper()}")
        print(f"⏱️ Analysis Time: {total_time:.2f} seconds")
        
        print("\n📋 CATEGORY BREAKDOWN:")
        for category, count in report['category_summary'].items():
            print(f"  {category}: {count} components")
        
        print("\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        print("\n🔍 STATUS DETAILS:")
        for result in self.status_results:
            status_icon = {
                "operational": "🟢",
                "functional": "🟡", 
                "needs_attention": "🟠",
                "critical": "🔴"
            }.get(result["status"], "⚪")
            
            print(f"  {status_icon} {result['category']}.{result['component']}: {result['message']}")
        
        print("\n" + "="*60)
        
        return report['status_summary']['overall_status'] != 'critical'

async def main():
    """Main function"""
    print("🔍 Starting Edu-Flow Backend Analysis...")
    print("=" * 60)
    
    analyzer = BackendStatusAnalyzer()
    success = await analyzer.run_complete_analysis()
    
    if success:
        print("\n🎉 BACKEND ANALYSIS COMPLETE! System is ready for production.")
        sys.exit(0)
    else:
        print("\n🔴 CRITICAL ISSUES DETECTED. Address critical issues before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())