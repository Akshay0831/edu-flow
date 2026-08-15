#!/usr/bin/env python3
"""
Comprehensive Test Runner for Edu-Flow Backend

This script runs all tests across different categories and provides a summary.
It includes unit tests, integration tests, performance tests, and basic functionality tests.

Author: Edu-Flow Team
"""

import subprocess
import sys
import os
from datetime import datetime

def run_test_suite(description, test_pattern):
    """Run a specific test suite and return the results."""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_pattern, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        return {
            "description": description,
            "exit_code": result.returncode,
            "output": result.stdout,
            "error": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {
            "description": description,
            "exit_code": 1,
            "output": "",
            "error": str(e),
            "success": False
        }

def main():
    """Main test runner function."""
    print("Edu-Flow Backend Comprehensive Test Runner")
    print(f"Test Run Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define test suites to run
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    test_suites = [
        {
            "description": "Unit Tests - Student Service",
            "pattern": os.path.join(base_dir, "tests", "unit", "test_actual_student_service.py")
        },
        {
            "description": "Performance Tests - Basic",
            "pattern": os.path.join(base_dir, "tests", "performance", "test_basic_performance.py")
        },
        {
            "description": "Unit Tests - Simple Student Service",
            "pattern": os.path.join(base_dir, "tests", "unit", "test_simple_student_service.py")
        }
    ]
    
    # Run all test suites
    results = []
    for suite in test_suites:
        result = run_test_suite(suite["description"], suite["pattern"])
        results.append(result)
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    total_suites = len(results)
    passed_suites = sum(1 for r in results if r["success"])
    failed_suites = total_suites - passed_suites
    
    print(f"Total Test Suites: {total_suites}")
    print(f"Passed: {passed_suites}")
    print(f"Failed: {failed_suites}")
    print(f"Success Rate: {(passed_suites/total_suites)*100:.1f}%")
    
    # Print details for failed suites
    if failed_suites > 0:
        print(f"\n{'='*60}")
        print("FAILED TEST SUITES")
        print(f"{'='*60}")
        for result in results:
            if not result["success"]:
                print(f"\n❌ {result['description']}")
                print(f"   Exit Code: {result['exit_code']}")
                if result["error"]:
                    print(f"   Error: {result['error']}")
    
    # Print success message
    if failed_suites == 0:
        print(f"\n🎉 ALL TEST SUITES PASSED! 🎉")
        print(f"Total Tests Run: {total_suites}")
        print(f"Success Rate: 100%")
    else:
        print(f"\n⚠️  {failed_suites} test suite(s) failed")
        print("Please check the output above for details.")
    
    print(f"\nTest Run Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit with appropriate code
    sys.exit(0 if failed_suites == 0 else 1)

if __name__ == "__main__":
    main()