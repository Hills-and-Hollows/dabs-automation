#!/usr/bin/env python3
"""
DABS Automation System Test Runner

This script provides a comprehensive test runner for the DABS automation system
with options for different test types, coverage reporting, and performance analysis.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --performance      # Run only performance tests
    python run_tests.py --coverage         # Run with coverage reporting
    python run_tests.py --fast             # Skip slow tests
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path
from datetime import datetime


def setup_environment():
    """Setup test environment"""
    # Add src to Python path
    src_path = Path(__file__).parent / 'src'
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # Set environment variables
    os.environ['PYTHONPATH'] = str(src_path)
    os.environ['TESTING'] = 'true'
    
    # Create test directories if they don't exist
    test_dirs = ['tests/unit', 'tests/integration', 'tests/fixtures', 'logs']
    for test_dir in test_dirs:
        Path(test_dir).mkdir(parents=True, exist_ok=True)


def run_pytest(args):
    """Run pytest with specified arguments"""
    cmd = ['python3', '-m', 'pytest'] + args
    
    print(f"🚀 Running: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(
        description="DABS Automation System Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit             # Run only unit tests
  python run_tests.py --integration      # Run only integration tests
  python run_tests.py --performance      # Run only performance tests
  python run_tests.py --coverage         # Run with coverage reporting
  python run_tests.py --fast             # Skip slow tests
  python run_tests.py --verbose          # Verbose output
  python run_tests.py --audit            # Run only audit-related tests
        """
    )
    
    # Test selection options
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument('--unit', action='store_true',
                           help='Run only unit tests')
    test_group.add_argument('--integration', action='store_true',
                           help='Run only integration tests')
    test_group.add_argument('--performance', action='store_true',
                           help='Run only performance tests')
    test_group.add_argument('--audit', action='store_true',
                           help='Run only audit-related tests')
    test_group.add_argument('--validation', action='store_true',
                           help='Run only validation tests')
    test_group.add_argument('--export', action='store_true',
                           help='Run only export functionality tests')
    
    # Test execution options
    parser.add_argument('--coverage', action='store_true',
                       help='Run with coverage reporting')
    parser.add_argument('--fast', action='store_true',
                       help='Skip slow tests')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--parallel', '-n', type=int, metavar='N',
                       help='Run tests in parallel with N workers')
    parser.add_argument('--failfast', '-x', action='store_true',
                       help='Stop on first failure')
    parser.add_argument('--lf', '--last-failed', action='store_true',
                       help='Run only tests that failed in the last run')
    parser.add_argument('--tb', choices=['short', 'long', 'line', 'native'],
                       default='short', help='Traceback style')
    
    # Output options
    parser.add_argument('--html-report', action='store_true',
                       help='Generate HTML coverage report')
    parser.add_argument('--junit-xml', metavar='FILE',
                       help='Generate JUnit XML report')
    
    # Test filtering
    parser.add_argument('--keyword', '-k', metavar='EXPRESSION',
                       help='Run tests matching keyword expression')
    parser.add_argument('--marker', '-m', metavar='MARKEXPR',
                       help='Run tests matching marker expression')
    
    # Additional pytest arguments
    parser.add_argument('pytest_args', nargs='*',
                       help='Additional arguments to pass to pytest')
    
    args = parser.parse_args()
    
    # Setup environment
    setup_environment()
    
    # Build pytest command
    pytest_args = []
    
    # Test selection
    if args.unit:
        pytest_args.extend(['-m', 'unit'])
    elif args.integration:
        pytest_args.extend(['-m', 'integration'])
    elif args.performance:
        pytest_args.extend(['-m', 'performance'])
    elif args.audit:
        pytest_args.extend(['-m', 'audit'])
    elif args.validation:
        pytest_args.extend(['-m', 'validation'])
    elif args.export:
        pytest_args.extend(['-m', 'export'])
    
    # Skip slow tests if requested
    if args.fast:
        if '-m' in pytest_args:
            # Combine with existing marker expression
            marker_index = pytest_args.index('-m') + 1
            pytest_args[marker_index] += ' and not slow'
        else:
            pytest_args.extend(['-m', 'not slow'])
    
    # Coverage options
    if args.coverage:
        pytest_args.extend([
            '--cov=src',
            '--cov-report=term-missing',
            '--cov-fail-under=90'
        ])
        
        if args.html_report:
            pytest_args.extend(['--cov-report=html:htmlcov'])
    
    # Execution options
    if args.verbose:
        pytest_args.append('-vv')
    
    if args.parallel:
        pytest_args.extend(['-n', str(args.parallel)])
    
    if args.failfast:
        pytest_args.append('-x')
    
    if args.lf:
        pytest_args.append('--lf')
    
    pytest_args.extend(['--tb', args.tb])
    
    # Output options
    if args.junit_xml:
        pytest_args.extend(['--junit-xml', args.junit_xml])
    
    # Filtering options
    if args.keyword:
        pytest_args.extend(['-k', args.keyword])
    
    if args.marker:
        if '-m' in pytest_args:
            # Combine with existing marker expression
            marker_index = pytest_args.index('-m') + 1
            pytest_args[marker_index] = f"({pytest_args[marker_index]}) and ({args.marker})"
        else:
            pytest_args.extend(['-m', args.marker])
    
    # Add any additional pytest arguments
    pytest_args.extend(args.pytest_args)
    
    # Print test configuration
    print("🧪 DABS Automation System Test Suite")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.unit:
        print("🔬 Running: Unit tests only")
    elif args.integration:
        print("🔗 Running: Integration tests only")
    elif args.performance:
        print("⚡ Running: Performance tests only")
    elif args.audit:
        print("📋 Running: Audit-related tests only")
    elif args.validation:
        print("✅ Running: Validation tests only")
    elif args.export:
        print("📤 Running: Export functionality tests only")
    else:
        print("🎯 Running: All tests")
    
    if args.fast:
        print("🏃 Mode: Fast (skipping slow tests)")
    
    if args.coverage:
        print("📊 Coverage: Enabled")
    
    print()
    
    # Run tests
    exit_code = run_pytest(pytest_args)
    
    # Print summary
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    print(f"📅 Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.coverage and args.html_report:
        print("📊 HTML coverage report: htmlcov/index.html")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
