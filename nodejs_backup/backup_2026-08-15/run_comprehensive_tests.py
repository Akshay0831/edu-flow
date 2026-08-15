"""
Comprehensive Test Runner for Edu-Flow Backend

This script runs all tests for the Edu-Flow backend system:
- Unit tests for all modules
- Integration tests for API endpoints
- Performance tests
- Security tests
- Database tests

Author: Edu-Flow Team
"""

import subprocess
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TestRunner:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None,
            'duration': None,
            'test_files': [],
            'failed_tests': [],
            'error_details': {}
        }
    
    def run_all_tests(self):
        """Run all tests and generate comprehensive report"""
        logger.info("Starting comprehensive test suite execution")
        self.test_results['start_time'] = datetime.now()
        
        try:
            # Run pytest with different configurations
            self.run_unit_tests()
            self.run_integration_tests()
            self.run_performance_tests()
            self.run_security_tests()
            self.run_database_tests()
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            self.test_results['errors'] += 1
            self.test_results['error_details']['test_execution'] = str(e)
        
        self.test_results['end_time'] = datetime.now()
        self.test_results['duration'] = (
            self.test_results['end_time'] - self.test_results['start_time']
        ).total_seconds()
        
        # Generate test report
        self.generate_test_report()
        
        return self.test_results
    
    def run_unit_tests(self):
        """Run unit tests for all modules"""
        logger.info("Running unit tests")
        
        # Run pytest for unit tests
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/unit/',
            '-v',
            '--tb=short',
            '--cov=src',
            '--cov-report=html:coverage/unit',
            '--cov-report=term-missing',
            '--junitxml=test_results/unit_results.xml'
        ]
        
        result = subprocess.run(
            cmd,
            cwd=self.root_dir,
            capture_output=True,
            text=True
        )
        
        self._process_test_result(result, 'unit')
    
    def run_integration_tests(self):
        """Run integration tests for API endpoints"""
        logger.info("Running integration tests")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/integration/',
            '-v',
            '--tb=short',
            '--cov=src.api',
            '--cov-report=html:coverage/integration',
            '--cov-report=term-missing',
            '--junitxml=test_results/integration_results.xml'
        ]
        
        result = subprocess.run(
            cmd,
            cwd=self.root_dir,
            capture_output=True,
            text=True
        )
        
        self._process_test_result(result, 'integration')
    
    def run_performance_tests(self):
        """Run performance tests"""
        logger.info("Running performance tests")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/performance/',
            '-v',
            '--tb=short',
            '--cov=src.database.performance_optimization',
            '--cov-report=html:coverage/performance',
            '--cov-report=term-missing',
            '--junitxml=test_results/performance_results.xml'
        ]
        
        result = subprocess.run(
            cmd,
            cwd=self.root_dir,
            capture_output=True,
            text=True
        )
        
        self._process_test_result(result, 'performance')
    
    def run_security_tests(self):
        """Run security tests"""
        logger.info("Running security tests")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/security/',
            '-v',
            '--tb=short',
            '--cov=src.core.security_enhancement',
            '--cov-report=html:coverage/security',
            '--cov-report=term-missing',
            '--junitxml=test_results/security_results.xml'
        ]
        
        result = subprocess.run(
            cmd,
            cwd=self.root_dir,
            capture_output=True,
            text=True
        )
        
        self._process_test_result(result, 'security')
    
    def run_database_tests(self):
        """Run database tests"""
        logger.info("Running database tests")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/database/',
            '-v',
            '--tb=short',
            '--cov=src.database',
            '--cov-report=html:coverage/database',
            '--cov-report=term-missing',
            '--junitxml=test_results/database_results.xml'
        ]
        
        result = subprocess.run(
            cmd,
            cwd=self.root_dir,
            capture_output=True,
            text=True
        )
        
        self._process_test_result(result, 'database')
    
    def _process_test_result(self, result, test_type):
        """Process test results and update statistics"""
        try:
            # Parse output to get test counts
            output = result.stdout + result.stderr
            self.test_results['test_files'].append(f'{test_type}_tests')
            
            # Look for pytest output patterns
            import re
            
            # Extract test counts
            collected_pattern = r'collected (\d+) items'
            collected_matches = re.findall(collected_pattern, output)
            
            if collected_matches:
                collected = int(collected_matches[0])
                self.test_results['total_tests'] += collected
            
            # Extract passed/failed counts
            passed_pattern = r'passed (\d+)'
            passed_matches = re.findall(passed_pattern, output)
            
            if passed_matches:
                passed = int(passed_matches[0])
                self.test_results['passed'] += passed
            
            failed_pattern = r'failed (\d+)'
            failed_matches = re.findall(failed_pattern, output)
            
            if failed_matches:
                failed = int(failed_matches[0])
                self.test_results['failed'] += failed
            
            # Parse error details
            error_pattern = r'E\s+(.+)'
            error_matches = re.findall(error_pattern, output)
            
            if error_matches:
                for error in error_matches:
                    error_key = f'{test_type}_error'
                    if error_key not in self.test_results['error_details']:
                        self.test_results['error_details'][error_key] = []
                    self.test_results['error_details'][error_key].append(error.strip())
            
            # Log result
            if result.returncode == 0:
                logger.info(f"✅ {test_type.capitalize()} tests passed")
            else:
                logger.error(f"❌ {test_type.capitalize()} tests failed")
                logger.error(f"Output: {output}")
            
        except Exception as e:
            logger.error(f"Error processing {test_type} test results: {e}")
            self.test_results['errors'] += 1
            self.test_results['error_details'][f'{test_type}_parsing'] = str(e)
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("Generating comprehensive test report")
        
        # Calculate pass rate
        if self.test_results['total_tests'] > 0:
            pass_rate = (self.test_results['passed'] / self.test_results['total_tests']) * 100
        else:
            pass_rate = 0
        
        # Create test report
        report = f"""
# Edu-Flow Backend Test Report

**Generated**: {self.test_results['end_time'].strftime('%Y-%m-%d %H:%M:%S')}

## Test Summary
- **Total Tests**: {self.test_results['total_tests']}
- **Passed**: {self.test_results['passed']} ({pass_rate:.1f}%)
- **Failed**: {self.test_results['failed']}
- **Errors**: {self.test_results['errors']}
- **Duration**: {self.test_results['duration']:.2f} seconds

## Test Files Executed
{chr(10).join(f'- {test_file}' for test_file in self.test_results['test_files'])}

## Failed Tests
"""
        
        if self.test_results['failed_tests']:
            for test in self.test_results['failed_tests']:
                report += f"- {test}\n"
        else:
            report += "No failed tests detected.\n"
        
        report += "\n## Error Details\n"
        
        if self.test_results['error_details']:
            for error_type, errors in self.test_results['error_details'].items():
                report += f"### {error_type.replace('_', ' ').title()}\n"
                for error in errors[:5]:  # Show first 5 errors per type
                    report += f"- {error}\n"
                if len(errors) > 5:
                    report += f"... and {len(errors) - 5} more errors\n"
        else:
            report += "No errors detected.\n"
        
        # Add recommendations
        report += "\n## Recommendations\n"
        
        if pass_rate < 90:
            report += "- Focus on improving test coverage for critical components\n"
        
        if self.test_results['failed'] > 0:
            report += "- Review and fix failing tests before production deployment\n"
        
        if self.test_results['errors'] > 0:
            report += "- Investigate test execution errors and fix infrastructure issues\n"
        
        if pass_rate >= 95:
            report += "- Test suite is in good condition for production deployment\n"
        
        # Write report to file
        report_path = self.root_dir / 'test_report.md'
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Test report generated: {report_path}")
        
        # Print summary
        print("\n" + "="*50)
        print("TEST EXECUTION SUMMARY")
        print("="*50)
        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed']}")
        print(f"Failed: {self.test_results['failed']}")
        print(f"Errors: {self.test_results['errors']}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print(f"Duration: {self.test_results['duration']:.2f} seconds")
        print("="*50)
        
        # Return exit code based on results
        if self.test_results['failed'] > 0 or self.test_results['errors'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

def main():
    """Main entry point"""
    runner = TestRunner()
    results = runner.run_all_tests()
    
    # Exit with appropriate code
    if results['failed'] > 0 or results['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()