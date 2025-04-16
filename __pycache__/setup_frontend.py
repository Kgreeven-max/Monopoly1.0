#!/usr/bin/env python
"""
Pi-nopoly Frontend Setup Script
This script helps set up the Node.js environment for Pi-nopoly's frontend.
"""

import os
import sys
import subprocess
import platform
import shutil
import json
from pathlib import Path

def print_header(text):
    """Print a header with decoration."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_step(text):
    """Print a step."""
    print(f"\n>> {text}")

def run_command(command, cwd=None, exit_on_error=True):
    """Run a shell command and return result."""
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, cwd=cwd)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}")
        print(f"Error details: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        if exit_on_error:
            sys.exit(1)
        return False

def check_node():
    """Check if Node.js is installed."""
    print_step("Checking Node.js installation")
    
    node_installed = shutil.which("node") is not None
    npm_installed = shutil.which("npm") is not None
    
    if not node_installed:
        print("Error: Node.js is not installed")
        print("Please install Node.js from https://nodejs.org/")
        print("Recommended version: 14.x or later")
        sys.exit(1)
    
    if not npm_installed:
        print("Error: npm is not installed")
        print("Please install npm (usually comes with Node.js)")
        sys.exit(1)
    
    # Check Node.js version
    try:
        result = subprocess.run(["node", "--version"], check=True, capture_output=True, text=True)
        node_version = result.stdout.strip()
        print(f"Node.js version: {node_version}")
        
        # Extract version numbers
        version_parts = node_version.lstrip('v').split('.')
        if int(version_parts[0]) < 14:
            print("Warning: Recommended Node.js version is 14.x or later")
            print(f"Current version: {node_version}")
    except subprocess.CalledProcessError as e:
        print(f"Error checking Node.js version: {e}")
    
    # Check npm version
    try:
        result = subprocess.run(["npm", "--version"], check=True, capture_output=True, text=True)
        npm_version = result.stdout.strip()
        print(f"npm version: {npm_version}")
    except subprocess.CalledProcessError as e:
        print(f"Error checking npm version: {e}")
    
    return node_installed and npm_installed

def create_env_file(client_dir):
    """Create .env file in the client directory."""
    print_step("Creating frontend .env file")
    
    env_path = os.path.join(client_dir, ".env")
    if not os.path.exists(env_path):
        print("Creating .env file in client directory")
        with open(env_path, "w") as env_file:
            env_file.write("""# Pi-nopoly Frontend Environment Variables
VITE_API_URL=http://localhost:5000/api
VITE_WS_URL=ws://localhost:5000
""")
        print(".env file created")
    else:
        print(".env file already exists")

def install_dependencies(client_dir):
    """Install Node.js dependencies."""
    print_step("Installing frontend dependencies")
    
    package_json_path = os.path.join(client_dir, "package.json")
    if os.path.exists(package_json_path):
        print("Installing dependencies with npm...")
        run_command(["npm", "install"], cwd=client_dir)
    else:
        print(f"Error: package.json not found in {client_dir}")
        sys.exit(1)

def main():
    """Main function."""
    print_header("Pi-nopoly Frontend Setup")
    
    # Determine client directory
    if os.path.exists("client"):
        client_dir = "client"
    elif os.path.exists("../client"):
        client_dir = "../client"
    else:
        print("Error: Could not find client directory")
        sys.exit(1)
    
    print(f"Using client directory: {os.path.abspath(client_dir)}")
    
    # Check Node.js and npm
    if check_node():
        create_env_file(client_dir)
        install_dependencies(client_dir)
        
        print_header("Frontend Setup Complete")
        print("To start the frontend development server:")
        print(f"1. Navigate to the client directory: cd {client_dir}")
        print("2. Run: npm run dev")
        print("\nThe frontend will be available at: http://localhost:3000")

if __name__ == "__main__":
    main() 