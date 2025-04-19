#!/usr/bin/env python
"""
Pi-nopoly Test Coverage Runner
This script runs tests with coverage reporting.
"""

import os
import sys
import argparse
import subprocess
import webbrowser
from pathlib import Path

def print_header(text):
    """Print a header with decoration."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def run_coverage(html=True, xml=False, report=True, verbose=False, tests_pattern=None):
    """Run tests with coverage and generate reports."""
    print_header("Pi-nopoly Test Coverage Runner")
    
    # Check if coverage is installed
    try:
        import coverage
    except ImportError:
        print("Error: 'coverage' package is not installed.")
        print("Please install it with 'pip install coverage'")
        return False
    
    coverage_dir = Path(".coverage_reports")
    coverage_dir.mkdir(exist_ok=True)
    
    # Determine test pattern
    tests_pattern = tests_pattern or "test_*.py"
    
    # Build coverage command
    cmd = [sys.executable, "-m", "coverage", "run", "--source=src", "-m", "unittest", "discover", "-p", tests_pattern]
    if verbose:
        print(f"Running command: {' '.join(cmd)}")
    
    # Run coverage
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running tests with coverage: {e}")
        return False
    
    # Generate reports
    success = True
    
    if report:
        print("\nGenerating coverage report...")
        try:
            subprocess.run([sys.executable, "-m", "coverage", "report"], check=True)
        except subprocess.CalledProcessError:
            print("Error generating coverage report")
            success = False
    
    if xml:
        print("\nGenerating XML coverage report...")
        try:
            xml_path = coverage_dir / "coverage.xml"
            subprocess.run([sys.executable, "-m", "coverage", "xml", "-o", str(xml_path)], check=True)
            print(f"XML report saved to {xml_path}")
        except subprocess.CalledProcessError:
            print("Error generating XML coverage report")
            success = False
    
    if html:
        print("\nGenerating HTML coverage report...")
        try:
            html_dir = coverage_dir / "html"
            subprocess.run([sys.executable, "-m", "coverage", "html", "--directory", str(html_dir)], check=True)
            html_index = html_dir / "index.html"
            print(f"HTML report saved to {html_index}")
            
            # Open in browser if requested
            open_browser = input("Open HTML report in browser? (y/n): ").lower() == 'y'
            if open_browser:
                webbrowser.open(f"file://{html_index.absolute()}")
        except subprocess.CalledProcessError:
            print("Error generating HTML coverage report")
            success = False
    
    print_header("Coverage Complete")
    return success

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run Pi-nopoly tests with coverage")
    parser.add_argument("--no-html", action="store_false", dest="html", 
                       help="Don't generate HTML report")
    parser.add_argument("--xml", action="store_true", 
                       help="Generate XML report (for CI/CD)")
    parser.add_argument("--no-report", action="store_false", dest="report", 
                       help="Don't show coverage report in terminal")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Verbose output")
    parser.add_argument("-p", "--pattern", 
                       help="Test pattern to discover (default: test_*.py)")
    
    args = parser.parse_args()
    
    success = run_coverage(
        html=args.html,
        xml=args.xml,
        report=args.report,
        verbose=args.verbose,
        tests_pattern=args.pattern
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 