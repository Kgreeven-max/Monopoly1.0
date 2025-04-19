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
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}")
        print(f"Error details: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        if exit_on_error:
            sys.exit(1)
        return False, None

def check_node():
    """Check if Node.js is installed and has correct version."""
    print_step("Checking Node.js installation")
    
    node_installed = shutil.which("node") is not None
    npm_installed = shutil.which("npm") is not None
    
    if not node_installed:
        print("Error: Node.js is not installed")
        print("Please install Node.js from https://nodejs.org/")
        print("Recommended version: 16.x or later")
        sys.exit(1)
    
    if not npm_installed:
        print("Error: npm is not installed")
        print("Please install npm (usually comes with Node.js)")
        sys.exit(1)
    
    # Check Node.js version
    try:
        success, output = run_command(["node", "--version"])
        if success and output:
            node_version = output.strip()
            print(f"Node.js version: {node_version}")
            
            # Extract version numbers
            version_parts = node_version.lstrip('v').split('.')
            if int(version_parts[0]) < 16:
                print("Warning: Recommended Node.js version is 16.x or later")
                print(f"Current version: {node_version}")
                response = input("Continue anyway? (y/n): ")
                if response.lower() != "y":
                    sys.exit(1)
    except Exception as e:
        print(f"Error checking Node.js version: {e}")
    
    # Check npm version
    try:
        success, output = run_command(["npm", "--version"])
        if success and output:
            npm_version = output.strip()
            print(f"npm version: {npm_version}")
    except Exception as e:
        print(f"Error checking npm version: {e}")
    
    return node_installed and npm_installed

def find_client_dir():
    """Find the client directory."""
    possible_dirs = ["client", "../client"]
    
    for dir_path in possible_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            package_json_path = os.path.join(dir_path, "package.json")
            if os.path.exists(package_json_path):
                return os.path.abspath(dir_path)
    
    print("Error: Could not find valid client directory with package.json")
    sys.exit(1)

def create_env_file(client_dir):
    """Create .env file in the client directory."""
    print_step("Creating frontend .env file")
    
    env_path = os.path.join(client_dir, ".env")
    env_example_path = os.path.join(client_dir, ".env.example")
    
    if not os.path.exists(env_path):
        if os.path.exists(env_example_path):
            print("Creating .env file from .env.example")
            with open(env_example_path, "r") as example_file:
                content = example_file.read()
            
            with open(env_path, "w") as env_file:
                env_file.write(content)
        else:
            print("Creating default .env file")
            with open(env_path, "w") as env_file:
                env_file.write("""# Pi-nopoly Frontend Environment Variables
VITE_API_URL=http://localhost:5000/api
VITE_WS_URL=ws://localhost:5000
""")
        print(".env file created successfully")
    else:
        print(".env file already exists")

def install_dependencies(client_dir):
    """Install Node.js dependencies."""
    print_step("Installing frontend dependencies")
    
    package_json_path = os.path.join(client_dir, "package.json")
    if os.path.exists(package_json_path):
        # Check if dependencies need to be installed
        node_modules_path = os.path.join(client_dir, "node_modules")
        if not os.path.exists(node_modules_path) or os.listdir(node_modules_path) == []:
            print("Installing dependencies with npm...")
            run_command(["npm", "install"], cwd=client_dir)
        else:
            print("Checking for outdated dependencies...")
            success, output = run_command(["npm", "outdated", "--json"], cwd=client_dir, exit_on_error=False)
            
            if success and output and output.strip() != "{}":
                print("Some dependencies are outdated")
                response = input("Update dependencies? (y/n): ")
                if response.lower() == "y":
                    run_command(["npm", "update"], cwd=client_dir)
            else:
                print("Dependencies are up to date")
                
            # Check for package-lock.json inconsistencies
            if os.path.exists(os.path.join(client_dir, "package-lock.json")):
                response = input("Run npm install to ensure dependencies are consistent with package-lock.json? (y/n): ")
                if response.lower() == "y":
                    run_command(["npm", "ci"], cwd=client_dir)
    else:
        print(f"Error: package.json not found in {client_dir}")
        sys.exit(1)

def verify_vite_config(client_dir):
    """Verify Vite configuration."""
    print_step("Verifying Vite configuration")
    
    vite_config_path = os.path.join(client_dir, "vite.config.js")
    if os.path.exists(vite_config_path):
        print("Vite configuration file found")
    else:
        print("Warning: vite.config.js not found")
        response = input("Create a basic Vite config file? (y/n): ")
        if response.lower() == "y":
            with open(vite_config_path, "w") as config_file:
                config_file.write("""import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
      '/socket.io': {
        target: 'ws://localhost:5000',
        ws: true,
      },
    },
  },
})
""")
            print("Basic Vite config file created")

def main():
    """Main function."""
    print_header("Pi-nopoly Frontend Setup")
    
    # Check Node.js and npm
    if check_node():
        # Find client directory
        client_dir = find_client_dir()
        print(f"Using client directory: {client_dir}")
        
        # Create .env file
        create_env_file(client_dir)
        
        # Verify Vite config
        verify_vite_config(client_dir)
        
        # Install dependencies
        install_dependencies(client_dir)
        
        print_header("Frontend Setup Complete")
        print("To start the frontend development server:")
        print(f"1. Navigate to the client directory: cd {client_dir}")
        print("2. Run: npm run dev")
        print("\nThe frontend will be available at: http://localhost:3000")

if __name__ == "__main__":
    main() 