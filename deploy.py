#!/usr/bin/env python
"""
Pi-nopoly Deployment Script

A flexible deployment script for Pi-nopoly that handles both backend and frontend deployment.
Provides options for development or production builds of the frontend.
"""

import argparse
import os
import sys
import subprocess
import platform
from pathlib import Path

# Import main deployment functionality
import local_deploy

def build_frontend_production():
    """Build the frontend for production"""
    client_dir = Path("client")
    if not client_dir.exists():
        print("Client directory not found")
        sys.exit(1)
    
    print("Building frontend for production...")
    result = subprocess.run(
        "npm run build", 
        cwd=client_dir, 
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.returncode == 0:
        print("Frontend built successfully!")
        print(f"Production files are in {client_dir}/dist/")
    else:
        print("Frontend build failed:")
        print(result.stderr)
        sys.exit(1)

def npm_install_package(package_name, dev=False):
    """Install a specific npm package"""
    client_dir = Path("client")
    if not client_dir.exists():
        print("Client directory not found")
        sys.exit(1)
    
    dev_flag = "--save-dev" if dev else "--save"
    print(f"Installing npm package: {package_name} ({dev_flag})...")
    
    result = subprocess.run(
        f"npm install {package_name} {dev_flag}", 
        cwd=client_dir, 
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.returncode == 0:
        print(f"Package {package_name} installed successfully!")
    else:
        print(f"Failed to install {package_name}:")
        print(result.stderr)
        sys.exit(1)

def npm_audit():
    """Run npm audit to check for vulnerabilities"""
    client_dir = Path("client")
    if not client_dir.exists():
        print("Client directory not found")
        sys.exit(1)
    
    print("Running npm audit...")
    result = subprocess.run(
        "npm audit", 
        cwd=client_dir, 
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print(result.stdout)
    if result.returncode > 0:
        print("Vulnerabilities found. Consider running 'npm audit fix'")

def show_help():
    """Show help information"""
    print("Pi-nopoly Deployment Script")
    print("===========================")
    print("Available commands:")
    print("  python deploy.py                 - Start development servers (backend + frontend)")
    print("  python deploy.py --build         - Build frontend for production")
    print("  python deploy.py --install PKG   - Install npm package")
    print("  python deploy.py --install-dev PKG - Install npm dev package")
    print("  python deploy.py --audit         - Run npm audit")
    print("  python deploy.py --help          - Show this help message")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pi-nopoly Deployment Script")
    parser.add_argument("--build", action="store_true", help="Build frontend for production")
    parser.add_argument("--install", metavar="PACKAGE", help="Install npm package")
    parser.add_argument("--install-dev", metavar="PACKAGE", help="Install npm dev package")
    parser.add_argument("--audit", action="store_true", help="Run npm audit")
    args = parser.parse_args()
    
    if args.build:
        build_frontend_production()
    elif args.install:
        npm_install_package(args.install, dev=False)
    elif args.install_dev:
        npm_install_package(args.install_dev, dev=True)
    elif args.audit:
        npm_audit()
    elif len(sys.argv) > 1 and sys.argv[1] == "--help":
        show_help()
    else:
        # Default: run the full deployment
        local_deploy.main() 