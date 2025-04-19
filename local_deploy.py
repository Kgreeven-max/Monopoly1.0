#!/usr/bin/env python
"""
Local Deployment Script for Pi-nopoly

This script sets up and runs both the frontend and backend components locally.
It handles environment setup, dependency installation, and starts both services.
"""

import os
import sys
import subprocess
import platform
import time
import webbrowser
from pathlib import Path
import signal

# Global variables
FRONTEND_PORT = 3000
BACKEND_PORT = 5000
VENV_DIR = "venv"
PROCESSES = []

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Windows vs Unix differences
IS_WINDOWS = platform.system() == "Windows"
PYTHON_CMD = "python" if IS_WINDOWS else "python3"
VENV_PYTHON = os.path.join(VENV_DIR, "Scripts", "python") if IS_WINDOWS else os.path.join(VENV_DIR, "bin", "python")
VENV_PIP = os.path.join(VENV_DIR, "Scripts", "pip") if IS_WINDOWS else os.path.join(VENV_DIR, "bin", "pip")
ACTIVATE_VENV = os.path.join(VENV_DIR, "Scripts", "activate") if IS_WINDOWS else os.path.join(VENV_DIR, "bin", "activate")

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.ENDC}\n")

def print_success(text):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    """Print an error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    """Print a warning message"""
    print(f"{Colors.WARNING}! {text}{Colors.ENDC}")

def print_info(text):
    """Print an info message"""
    print(f"{Colors.BLUE}→ {text}{Colors.ENDC}")

def run_command(command, cwd=None, shell=False, check=True):
    """Run a command and return the process"""
    if not shell and isinstance(command, str):
        command = command.split()
    
    try:
        process = subprocess.run(
            command, 
            cwd=cwd, 
            shell=shell, 
            check=check, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        return process
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        print_error(f"Output: {e.stdout}")
        print_error(f"Error: {e.stderr}")
        return e

def run_background_command(command, cwd=None, shell=False):
    """Run a command in the background and return the process"""
    if not shell and isinstance(command, str):
        command = command.split()
    
    if IS_WINDOWS and not shell:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            shell=shell,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            shell=shell
        )
    
    PROCESSES.append(process)
    return process

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print_header("Checking Prerequisites")
    
    # Check Python version
    try:
        python_version = run_command(f"{PYTHON_CMD} --version").stdout.strip()
        print_success(f"Found {python_version}")
    except:
        print_error("Python 3.9+ is required but not found")
        sys.exit(1)
    
    # Check Node.js version
    try:
        node_version = run_command("node --version").stdout.strip()
        print_success(f"Found Node.js {node_version}")
    except:
        print_error("Node.js 16+ is required but not found")
        sys.exit(1)
    
    # Check npm version
    try:
        npm_version = run_command("npm --version").stdout.strip()
        print_success(f"Found npm {npm_version}")
    except:
        print_error("npm is required but not found")
        sys.exit(1)

def setup_backend():
    """Set up the Python backend environment"""
    print_header("Setting Up Backend Environment")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists(VENV_DIR):
        print_info("Creating virtual environment...")
        run_command(f"{PYTHON_CMD} -m venv {VENV_DIR}")
        print_success("Virtual environment created")
    else:
        print_info("Virtual environment already exists")
    
    # Install dependencies
    print_info("Installing backend dependencies...")
    if IS_WINDOWS:
        run_command(f"{VENV_PIP} install -r requirements.txt")
    else:
        run_command(f'source {ACTIVATE_VENV} && {VENV_PIP} install -r requirements.txt', shell=True)
    print_success("Backend dependencies installed")
    
    # Ensure .env file exists
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print_info("Creating .env file from .env.example...")
            with open(".env.example", "r") as example_file:
                with open(".env", "w") as env_file:
                    env_file.write(example_file.read())
            print_success(".env file created")
        else:
            print_warning("No .env.example file found. You may need to create a .env file manually.")

def setup_frontend():
    """Set up the React frontend environment"""
    print_header("Setting Up Frontend Environment")
    
    client_dir = Path("client")
    if not client_dir.exists():
        print_error("Client directory not found")
        sys.exit(1)
    
    # Install frontend dependencies
    print_info("Installing frontend dependencies...")
    run_command("npm install", cwd=client_dir)
    print_success("Frontend dependencies installed")

def start_backend():
    """Start the Flask backend server"""
    print_header("Starting Backend Server")
    
    print_info(f"Starting Flask server on port {BACKEND_PORT}...")
    
    if IS_WINDOWS:
        backend_process = run_background_command([VENV_PYTHON, "app.py"])
    else:
        # For Unix, we need to activate the virtual environment first
        backend_process = run_background_command(f'source {ACTIVATE_VENV} && {VENV_PYTHON} app.py', shell=True)
    
    # Give the server a moment to start
    time.sleep(2)
    print_success(f"Backend server running at http://localhost:{BACKEND_PORT}")
    return backend_process

def start_frontend():
    """Start the React frontend development server"""
    print_header("Starting Frontend Server")
    
    client_dir = Path("client")
    print_info(f"Starting React development server on port {FRONTEND_PORT}...")
    
    frontend_process = run_background_command("npm run dev", cwd=client_dir, shell=True)
    
    # Give the server a moment to start
    time.sleep(5)
    print_success(f"Frontend server running at http://localhost:{FRONTEND_PORT}")
    return frontend_process

def open_browser():
    """Open the default web browser to the application"""
    print_info("Opening application in web browser...")
    webbrowser.open(f"http://localhost:{FRONTEND_PORT}")

def cleanup_processes(signum=None, frame=None):
    """Clean up all started processes"""
    print_header("Shutting Down")
    
    print_info("Stopping all processes...")
    for process in PROCESSES:
        if process.poll() is None:  # If process is still running
            try:
                if IS_WINDOWS:
                    process.terminate()
                else:
                    process.kill()
                print_info(f"Process {process.pid} terminated")
            except Exception as e:
                print_warning(f"Failed to terminate process {process.pid}: {e}")
    
    print_success("All processes stopped")
    if signum is not None:  # If called as a signal handler
        sys.exit(0)

def main():
    """Main function to run the deployment script"""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, cleanup_processes)
    signal.signal(signal.SIGTERM, cleanup_processes)
    
    print_header("Pi-nopoly Local Deployment")
    print_info("This script will set up and run both the frontend and backend components.")
    
    try:
        # Check prerequisites
        check_prerequisites()
        
        # Set up the environments
        setup_backend()
        setup_frontend()
        
        # Start the servers
        backend_process = start_backend()
        frontend_process = start_frontend()
        
        # Open in browser
        open_browser()
        
        print_header("Deployment Complete")
        print_info("Both servers are now running.")
        print_info(f"Frontend: http://localhost:{FRONTEND_PORT}")
        print_info(f"Backend: http://localhost:{BACKEND_PORT}")
        print_info("Press Ctrl+C to stop all servers.")
        
        # Keep the script running until interrupted
        while all(process.poll() is None for process in PROCESSES):
            time.sleep(1)
        
        # If we get here, one of the processes stopped unexpectedly
        print_warning("One of the servers stopped unexpectedly.")
        cleanup_processes()
        
    except KeyboardInterrupt:
        print_info("\nShutting down gracefully...")
        cleanup_processes()
    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        cleanup_processes()
        sys.exit(1)

if __name__ == "__main__":
    main() 