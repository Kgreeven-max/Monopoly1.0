#!/usr/bin/env python
"""
Pi-nopoly Test Runner
This script discovers and runs all tests in the Pi-nopoly project.
"""

import unittest
import os
import sys
import argparse
import time
from datetime import datetime

def print_header(text):
    """Print a header with decoration."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def discover_and_run_tests(pattern=None, verbose=False, failfast=False, specific_test=None):
    """Discover and run tests in the project."""
    print_header("Pi-nopoly Test Runner")
    
    # Start timing
    start_time = time.time()
    
    # Create test loader
    loader = unittest.TestLoader()
    
    if specific_test:
        # Run specific test module
        if specific_test.endswith('.py'):
            specific_test = specific_test[:-3]  # Remove .py extension
        
        try:
            suite = loader.loadTestsFromName(specific_test)
            if suite.countTestCases() == 0:
                print(f"No tests found in '{specific_test}'")
                return False
            
            print(f"Running tests from '{specific_test}'")
            
        except (ImportError, AttributeError) as e:
            print(f"Error loading tests from '{specific_test}': {e}")
            return False
    else:
        # Discover all tests matching pattern
        pattern = pattern or "test_*.py"
        print(f"Discovering tests matching pattern: {pattern}")
        
        try:
            suite = loader.discover('.', pattern=pattern)
            if suite.countTestCases() == 0:
                print("No tests discovered")
                return False
            
            print(f"Discovered {suite.countTestCases()} tests")
            
        except Exception as e:
            print(f"Error discovering tests: {e}")
            return False
    
    # Create test runner
    runner = unittest.TextTestRunner(
        verbosity=2 if verbose else 1,
        failfast=failfast
    )
    
    # Run tests
    print(f"\nRunning tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    result = runner.run(suite)
    
    # Calculate timing
    end_time = time.time()
    duration = end_time - start_time
    
    # Print summary
    print_header("Test Results")
    print(f"Ran {result.testsRun} tests in {duration:.2f} seconds")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    # Return True if all tests passed
    return len(result.failures) == 0 and len(result.errors) == 0

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run Pi-nopoly tests")
    parser.add_argument("-p", "--pattern", help="Test pattern to discover (default: test_*.py)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-f", "--failfast", action="store_true", help="Stop on first failure")
    parser.add_argument("-t", "--test", help="Run specific test module")
    
    args = parser.parse_args()
    
    success = discover_and_run_tests(
        pattern=args.pattern,
        verbose=args.verbose,
        failfast=args.failfast,
        specific_test=args.test
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 