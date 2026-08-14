"""
Service Test Runner

This script runs all service integration tests and provides comprehensive validation
of the service layer implementation. It includes error handling, logging, and detailed reporting.

Author: Edu-Flow Team
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Any
import traceback

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.infrastructure.services.service_container_fixed import ServiceContainer
from tests.unit.test_service_integration import TestServiceIntegration


class TestRunner:
    """Test runner for service integration tests."""
    
    def __init__(self):
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.logger = self._setup_logger()
        self.container = None
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for test runner."""
        logger = logging.getLogger('test_runner')
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        
        return logger
    
    async def setup(self):
        """Set up test environment."""
        try:
            self.logger.info("Setting up test environment...")
            
            # Create service container
            self.container = ServiceContainer()
            
            # Initialize all services
            await self.container.initialize()
            
            self.logger.info("Test environment setup complete")
            
        except Exception as e:
            self.logger.error(f"Failed to setup test environment: {str(e)}")
            raise
    
    async def teardown(self):
        """Clean up test environment."""
        try:
            if self.container:
                await self.container.dispose()
                self.logger.info("Test environment cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    async def run_individual_test(self, test_name: str, test_func):
        """Run an individual test."""
        start_time = datetime.now()
        result = {
            'name': test_name,
            'status': 'running',
            'start_time': start_time,
            'end_time': None,
            'duration': None,
            'error': None,
            'error_trace': None
        }
        
        try:
            await test_func()
            result['status'] = 'passed'
            self.logger.info(f"✓ Test passed: {test_name}")
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            result['error_trace'] = traceback.format_exc()
            self.logger.error(f"✗ Test failed: {test_name}")
            self.logger.error(f"Error: {str(e)}")
        
        end_time = datetime.now()
        result['end_time'] = end_time
        result['duration'] = (end_time - start_time).total_seconds()
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        try:
            await self.setup()
            
            self.logger.info("Starting service integration tests...")
            self.logger.info("=" * 50)
            
            # Get test methods from TestServiceIntegration
            test_instance = TestServiceIntegration()
            test_methods = []
            
            # Get all methods starting with 'test_'
            for attr_name in dir(test_instance):
                if attr_name.startswith('test_') and callable(getattr(test_instance, attr_name)):
                    test_methods.append(attr_name)
            
            self.logger.info(f"Found {len(test_methods)} test methods")
            
            # Run tests
            for test_method in test_methods:
                try:
                    test_func = getattr(test_instance, test_method)
                    result = await self.run_individual_test(test_method, test_func)
                    self.test_results[test_method] = result
                except Exception as e:
                    self.logger.error(f"Error running test {test_method}: {str(e)}")
                    self.test_results[test_method] = {
                        'name': test_method,
                        'status': 'error',
                        'error': str(e),
                        'error_trace': traceback.format_exc()
                    }
            
            # Generate report
            report = self.generate_test_report()
            
            self.logger.info("=" * 50)
            self.logger.info("All tests completed!")
            self.logger.info(f"Total tests: {len(test_methods)}")
            self.logger.info(f"Passed: {report['summary']['passed']}")
            self.logger.info(f"Failed: {report['summary']['failed']}")
            self.logger.info(f"Error: {report['summary']['error']}")
            
            await self.teardown()
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error running tests: {str(e)}")
            await self.teardown()
            raise
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        summary = {
            'total': len(self.test_results),
            'passed': 0,
            'failed': 0,
            'error': 0,
            'total_duration': 0,
            'passed_duration': 0,
            'failed_duration': 0,
            'error_duration': 0
        }
        
        detailed_results = []
        
        for test_name, result in self.test_results.items():
            summary['total_duration'] += result['duration']
            
            if result['status'] == 'passed':
                summary['passed'] += 1
                summary['passed_duration'] += result['duration']
            elif result['status'] == 'failed':
                summary['failed'] += 1
                summary['failed_duration'] += result['duration']
            else:
                summary['error'] += 1
                summary['error_duration'] += result['duration']
            
            detailed_results.append({
                'name': test_name,
                'status': result['status'],
                'duration': round(result['duration'], 2),
                'error': result.get('error'),
                'start_time': result['start_time'].isoformat(),
                'end_time': result['end_time'].isoformat()
            })
        
        # Sort results by status and duration
        detailed_results.sort(key=lambda x: (x['status'] != 'passed', x['duration']), reverse=True)
        
        # Calculate success rate
        if summary['total'] > 0:
            summary['success_rate'] = (summary['passed'] / summary['total']) * 100
        else:
            summary['success_rate'] = 0
        
        # Get top failed tests
        failed_tests = [r for r in detailed_results if r['status'] == 'failed']
        top_failed = failed_tests[:5] if failed_tests else []
        
        # Get slowest tests
        slowest_tests = sorted(detailed_results, key=lambda x: x['duration'], reverse=True)[:5]
        
        report = {
            'summary': summary,
            'detailed_results': detailed_results,
            'top_failed_tests': top_failed,
            'slowest_tests': slowest_tests,
            'test_service_integration_status': {
                'total_tests': len(self.test_results),
                'passed_tests': summary['passed'],
                'failed_tests': summary['failed'],
                'error_tests': summary['error'],
                'success_rate': summary['success_rate'],
                'total_duration': round(summary['total_duration'], 2),
                'average_duration': round(summary['total_duration'] / summary['total'], 2) if summary['total'] > 0 else 0
            }
        }
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """Print formatted test report."""
        print("\n" + "=" * 60)
        print("SERVICE INTEGRATION TEST REPORT")
        print("=" * 60)
        
        # Summary
        print("\n📊 SUMMARY:")
        print(f"   Total Tests: {report['summary']['total']}")
        print(f"   Passed: {report['summary']['passed']}")
        print(f"   Failed: {report['summary']['failed']}")
        print(f"   Errors: {report['summary']['error']}")
        print(f"   Success Rate: {report['summary']['success_rate']:.2f}%")
        print(f"   Total Duration: {report['summary']['total_duration']:.2f}s")
        
        # Top Failed Tests
        if report['top_failed_tests']:
            print("\n❌ TOP FAILED TESTS:")
            for test in report['top_failed_tests']:
                print(f"   {test['name']}: {test['error']}")
        
        # Slowest Tests
        print("\n🐌 SLOWEST TESTS:")
        for test in report['slowest_tests']:
            print(f"   {test['name']}: {test['duration']:.2f}s")
        
        # Service Integration Status
        status = report['test_service_integration_status']
        print("\n🔧 SERVICE INTEGRATION STATUS:")
        print(f"   ✅ Backend Service Layer: {status['passed_tests'] > 0}")
        print(f"   📋 Test Coverage: {status['total_tests']} tests")
        print(f"   ⏱️  Performance: {status['average_duration']:.2f}s avg per test")
        print(f"   🎯 Success Rate: {status['success_rate']:.2f}%")
        
        print("\n" + "=" * 60)
        print("REPORT END")
        print("=" * 60)


async def main():
    """Main test runner function."""
    runner = TestRunner()
    
    try:
        # Run all tests
        report = await runner.run_all_tests()
        
        # Print report
        runner.print_report(report)
        
        # Return appropriate exit code
        if report['summary']['failed'] > 0 or report['summary']['error'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"Test runner failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the test runner
    asyncio.run(main())