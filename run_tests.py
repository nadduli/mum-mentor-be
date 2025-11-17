"""
Test Runner Script
Runs all tests and generates a detailed report
"""

import subprocess
import sys

def run_tests():
    """Run pytest with coverage and detailed output"""
    
    print("=" * 70)
    print("Running User Settings API Tests")
    print("=" * 70)
    print("\nTest Categories:")
    print("  ✓ 200 Success Cases - Valid requests that should succeed")
    print("  ✓ 400 Invalid Input - Validation errors and bad requests")
    print("  ✓ 500 Server Errors - Database and server failures")
    print("=" * 70)
    print()
    
    # Run pytest with coverage
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_user_settings.py",
        "-v",
        "--tb=short",
        "--cov=api/v1",
        "--cov-report=term-missing",
        "--cov-report=html"
    ])
    
    print("\n" + "=" * 70)
    if result.returncode == 0:
        print("✓ All tests passed!")
        print("\nCoverage report generated in htmlcov/index.html")
    else:
        print("✗ Some tests failed. Check output above.")
    print("=" * 70)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
