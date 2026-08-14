"""
Edu-Flow Backend Test Runner

This script runs all backend tests with comprehensive coverage reporting.
It includes unit tests, integration tests, and performance tests.

Usage:
    python run_tests.py [test_type]

Arguments:
    test_type: Optional - 'unit', 'integration', 'performance', or 'all'

Author: Edu-Flow Team
"""

import asyncio
import pytest
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

class EduFlowTestRunner:
    """Comprehensive test runner for Edu-Flow backend."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.unit_test_dir = self.base_dir / "tests" / "unit"
        self.integration_test_dir = self.base_dir / "tests" / "integration"
        self.performance_test_dir = self.base_dir / "tests" / "performance"
        
        # Create directories if they don't exist
        for dir_path in [self.unit_test_dir, self.integration_test_dir, self.performance_test_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'unit': {'passed': 0, 'failed': 0, 'total': 0},
            'integration': {'passed': 0, 'failed': 0, 'total': 0},
            'performance': {'passed': 0, 'failed': 0, 'total': 0},
            'total': {'passed': 0, 'failed': 0, 'total': 0}
        }
    
    def run_pytest_command(self, test_dir: Path, pattern: str = "*.py", 
                          additional_args: list = None) -> dict:
        """Run pytest command with specified pattern and arguments."""
        if additional_args is None:
            additional_args = []
        
        # Ensure pytest is installed
        try:
            import pytest
        except ImportError:
            print("❌ Error: pytest not installed. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio", "pytest-cov"])
        
        # Find all matching test files
        import glob
        test_files = glob.glob(str(test_dir / pattern))
        
        if not test_files:
            return {
                'success': False,
                'output': '',
                'stderr': f"No test files found matching pattern: {test_dir / pattern}",
                'returncode': -1
            }
        
        # Run pytest on found files
        cmd = [
            sys.executable, "-m", "pytest",
        ] + test_files + [
            "-v",
            "--tb=short",
            "--junit-xml", str(test_dir / "test_results.xml"),
            "--cov=src",
            "--cov-report=html:" + str(test_dir / "coverage"),
            "--cov-report=term-missing",
            "--cov-report=xml:" + str(test_dir / "coverage.xml"),
            "--asyncio-mode=auto"
        ] + additional_args
        
        try:
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True, timeout=300)
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': '', 'stderr': 'Test timeout', 'returncode': -1}
        except Exception as e:
            return {'success': False, 'output': '', 'stderr': str(e), 'returncode': -1}
    
    def parse_test_output(self, output: str) -> dict:
        """Parse test output to extract statistics."""
        stats = {'passed': 0, 'failed': 0, 'total': 0, 'errors': []}
        
        lines = output.split('\n')
        for line in lines:
            if '::' in line and 'passed' in line:
                count = int(line.split()[0])
                stats['passed'] += count
            elif '::' in line and 'failed' in line:
                count = int(line.split()[0])
                stats['failed'] += count
        
        stats['total'] = stats['passed'] + stats['failed']
        return stats
    
    def run_unit_tests(self) -> bool:
        """Run all unit tests."""
        print("🔍 Running Unit Tests...")
        print("-" * 50)
        
        # Test all unit tests
        result = self.run_pytest_command(self.unit_test_dir, "test_*.py")
        
        if result['success']:
            stats = self.parse_test_output(result['output'])
            self.test_results['unit'] = stats
            print(f"✅ Unit Tests Passed: {stats['passed']}")
            print(f"❌ Unit Tests Failed: {stats['failed']}")
            print(f"📊 Total Unit Tests: {stats['total']}")
        else:
            print(f"❌ Unit Tests Failed: {result['stderr']}")
            self.test_results['unit'] = {'passed': 0, 'failed': 1, 'total': 1}
        
        print()
        return result['success']
    
    def run_integration_tests(self) -> bool:
        """Run all integration tests."""
        print("🔗 Running Integration Tests...")
        print("-" * 50)
        
        # Test specific integration files first
        result = self.run_pytest_command(self.integration_test_dir, "test_*.py", ["-x"])
        
        if result['success']:
            stats = self.parse_test_output(result['output'])
            self.test_results['integration'] = stats
            print(f"✅ Integration Tests Passed: {stats['passed']}")
            print(f"❌ Integration Tests Failed: {stats['failed']}")
            print(f"📊 Total Integration Tests: {stats['total']}")
        else:
            print(f"❌ Integration Tests Failed: {result['stderr']}")
            self.test_results['integration'] = {'passed': 0, 'failed': 1, 'total': 1}
        
        print()
        return result['success']
    
    def run_performance_tests(self) -> bool:
        """Run performance tests."""
        print("⚡ Running Performance Tests...")
        print("-" * 50)
        
        # Test performance directory (might not exist yet)
        if not self.performance_test_dir.exists():
            print("ℹ️  Performance tests not yet implemented. Skipping...")
            self.test_results['performance'] = {'passed': 0, 'failed': 0, 'total': 0}
            return True
        
        result = self.run_pytest_command(self.performance_test_dir, "test_*.py", ["-x"])
        
        if result['success']:
            stats = self.parse_test_output(result['output'])
            self.test_results['performance'] = stats
            print(f"✅ Performance Tests Passed: {stats['passed']}")
            print(f"❌ Performance Tests Failed: {stats['failed']}")
            print(f"📊 Total Performance Tests: {stats['total']}")
        else:
            print(f"❌ Performance Tests Failed: {result['stderr']}")
            self.test_results['performance'] = {'passed': 0, 'failed': 1, 'total': 1}
        
        print()
        return result['success']
    
    def validate_test_structure(self) -> bool:
        """Validate that all test files exist and have proper structure."""
        print("📁 Validating Test Structure...")
        print("-" * 50)
        
        required_files = [
            "tests/unit/test_student_service.py",
            "tests/unit/test_class_service_unit.py",
            "tests/unit/test_department_service_unit.py",
            "tests/unit/test_subject_service_unit.py",
            "tests/unit/test_user_service_unit.py",
            "tests/unit/test_mark_service_unit.py",
            "tests/integration/test_service_interactions.py",
            "tests/integration/test_complete_system_integration.py",
            "tests/performance/test_database_performance.py",
            "tests/performance/test_load_performance.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.base_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing {len(missing_files)} test files:")
            for file in missing_files:
                print(f"   - {file}")
            return False
        
        print(f"✅ All {len(required_files)} test files present")
        return True
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("📊 Generating Test Report...")
        print("-" * 50)
        
        total_passed = (self.test_results['unit']['passed'] + 
                       self.test_results['integration']['passed'] + 
                       self.test_results['performance']['passed'])
        
        total_failed = (self.test_results['unit']['failed'] + 
                       self.test_results['integration']['failed'] + 
                       self.test_results['performance']['failed'])
        
        total_tests = total_passed + total_failed
        
        overall_success = total_failed == 0
        
        if overall_success:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"💥 {total_failed} TESTS FAILED!")
        
        print(f"📈 Unit Tests: {self.test_results['unit']['passed']}/{self.test_results['unit']['total']} passed")
        print(f"🔗 Integration Tests: {self.test_results['integration']['passed']}/{self.test_results['integration']['total']} passed")
        print(f"⚡ Performance Tests: {self.test_results['performance']['passed']}/{self.test_results['performance']['total']} passed")
        print(f"🎯 Overall: {total_passed}/{total_tests} passed ({(total_passed/total_tests)*100:.1f}%)")
        
        # Save detailed report
        report_file = self.base_dir / "test_report.json"
        with open(report_file, 'w') as f:
            f.write(str(self.test_results))
        
        print(f"📄 Detailed report saved to: {report_file}")
        
        return overall_success
    
    def run_all_tests(self, test_type: str = "all") -> bool:
        """Run all tests based on specified type."""
        print("🚀 Edu-Flow Backend Test Runner")
        print("=" * 50)
        print(f"Test Type: {test_type}")
        print(f"Base Directory: {self.base_dir}")
        print()
        
        # Validate test structure first
        if not self.validate_test_structure():
            print("❌ Test structure validation failed!")
            return False
        
        success = True
        
        if test_type in ["unit", "all"]:
            success &= self.run_unit_tests()
        
        if test_type in ["integration", "all"]:
            success &= self.run_integration_tests()
        
        if test_type in ["performance", "all"]:
            success &= self.run_performance_tests()
        
        # Generate final report
        self.generate_test_report()
        
        return success

def main():
    """Main function to run tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Edu-Flow Backend Test Runner")
    parser.add_argument("test_type", choices=["unit", "integration", "performance", "all"], 
                       nargs="?", default="all", help="Type of tests to run")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage reports")
    
    args = parser.parse_args()
    
    # Ensure Python 3.13+ is being used
    if sys.version_info < (3, 13):
        print("❌ Error: Python 3.13+ is required!")
        sys.exit(1)
    
    # Set up environment
    os.environ["PYTHONPATH"] = str(Path(__file__).parent / "src")
    
    # Run tests
    runner = EduFlowTestRunner()
    success = runner.run_all_tests(args.test_type)
    
    if args.coverage:
        print("\n📈 Coverage Analysis:")
        print("-" * 20)
        coverage_dirs = [
            runner.unit_test_dir / "coverage",
            runner.integration_test_dir / "coverage", 
            runner.performance_test_dir / "coverage"
        ]
        
        for cov_dir in coverage_dirs:
            if cov_dir.exists():
                index_file = cov_dir / "index.html"
                if index_file.exists():
                    print(f"📊 Coverage report: {index_file}")
            else:
                print(f"ℹ️  No coverage directory: {cov_dir}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()