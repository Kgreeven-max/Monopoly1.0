#!/usr/bin/env python
"""
Pi-nopoly Backend Setup Script
This script helps set up the Python environment for Pi-nopoly.
"""

import os
import sys
import subprocess
import platform
import shutil
import json
import re
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

def check_python_version():
    """Check if Python version is compatible."""
    print_step("Checking Python version")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("Error: Python 3.9+ is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    print(f"Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_pip():
    """Check if pip is installed and determine appropriate command."""
    print_step("Checking pip installation")
    
    pip_command = None
    for cmd in ["pip", "pip3"]:
        if shutil.which(cmd) is not None:
            try:
                success, output = run_command([cmd, "--version"], exit_on_error=False)
                if success:
                    pip_command = cmd
                    print(f"Using {cmd}: {output.strip()}")
                    break
            except Exception:
                continue
    
    if pip_command is None:
        print("Error: pip is not installed or not in PATH")
        print("Please install pip or ensure it's available in your PATH")
        sys.exit(1)
    
    return pip_command

def setup_virtual_env(pip_cmd):
    """Create and activate a virtual environment."""
    print_step("Setting up virtual environment")
    
    venv_dir = "venv"
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        run_command([sys.executable, "-m", "venv", venv_dir])
    else:
        print("Virtual environment already exists")
    
    # Determine activation command and path to pip in the virtual environment
    if platform.system() == "Windows":
        activate_cmd = os.path.join(venv_dir, "Scripts", "activate")
        venv_pip = os.path.join(venv_dir, "Scripts", "pip")
    else:
        activate_cmd = f"source {os.path.join(venv_dir, 'bin', 'activate')}"
        venv_pip = os.path.join(venv_dir, "bin", "pip")
    
    if os.path.exists(venv_pip):
        print(f"Virtual environment pip found at: {venv_pip}")
    else:
        print("Warning: pip not found in virtual environment. Setup may be incomplete.")
    
    # Check if the virtual environment is active
    if "VIRTUAL_ENV" not in os.environ:
        print(f"\nVirtual environment is not active.")
        print(f"To activate: {activate_cmd}")
        if platform.system() != "Windows":
            print("After activation, run this script again to continue setup.")
    
    return activate_cmd, venv_pip

def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    print_step("Setting up environment file")
    
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print("Creating .env file from .env.example")
            with open(".env.example", "r") as example_file:
                content = example_file.read()
            
            with open(".env", "w") as env_file:
                env_file.write(content)
            print(".env file created")
        else:
            print("Warning: .env.example file not found")
            
            # Create a basic .env file with minimal settings
            print("Creating basic .env file")
            with open(".env", "w") as env_file:
                env_file.write("""# Pi-nopoly Environment Variables
SECRET_KEY=pinopoly-development-key
ADMIN_KEY=pinopoly-admin
DISPLAY_KEY=pinopoly-display
DATABASE_PATH=pinopoly.db
SQLALCHEMY_DATABASE_URI=sqlite:///pinopoly.sqlite
DEBUG=True
PORT=5000
ADAPTIVE_DIFFICULTY_ENABLED=true
ADAPTIVE_DIFFICULTY_INTERVAL=15
POLICE_PATROL_ENABLED=true
POLICE_PATROL_INTERVAL=45
ECONOMIC_CYCLE_ENABLED=true
ECONOMIC_CYCLE_INTERVAL=5
PROPERTY_VALUES_FOLLOW_ECONOMY=true
FREE_PARKING_FUND=true
REMOTE_PLAY_ENABLED=false
REMOTE_PLAY_TIMEOUT=60
""")
            print("Basic .env file created")
    else:
        print(".env file already exists")

def parse_requirements(requirements_path):
    """Parse requirements.txt file and returns a list of package requirements."""
    if not os.path.exists(requirements_path):
        return []
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    # Remove comments and empty lines
    lines = []
    for line in content.splitlines():
        line = line.strip()
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        # Remove inline comments
        if '#' in line:
            line = line.split('#')[0].strip()
        lines.append(line)
    
    return lines

def install_dependencies(pip_cmd, venv_pip=None):
    """Install Python dependencies."""
    print_step("Installing Python dependencies")
    
    # Determine which pip to use
    pip_to_use = venv_pip if venv_pip and os.path.exists(venv_pip) else pip_cmd
    
    if "VIRTUAL_ENV" not in os.environ and venv_pip:
        print("Warning: Virtual environment is not active, but trying to use venv pip")
        print("For best results, activate the virtual environment first")
    
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        # Parse requirements
        requirements = parse_requirements(requirements_file)
        if not requirements:
            print("No valid requirements found in requirements.txt")
            return
        
        print(f"Installing {len(requirements)} packages...")
        
        # Try to upgrade pip first for better installation compatibility
        run_command([pip_to_use, "install", "--upgrade", "pip"], exit_on_error=False)
        
        # Standard installation approach
        success, _ = run_command([pip_to_use, "install", "-r", requirements_file], exit_on_error=False)
        
        if not success:
            print("\nTrying an alternative installation approach...")
            
            # Install packages one by one
            failed_packages = []
            for req in requirements:
                pkg_success, _ = run_command([pip_to_use, "install", req], exit_on_error=False)
                if not pkg_success:
                    failed_packages.append(req)
            
            if failed_packages:
                print("\nThe following packages could not be installed:")
                for pkg in failed_packages:
                    print(f"  - {pkg}")
                
                print("\nPlease try installing them manually, or check for compatibility issues.")
            else:
                print("\nAll dependencies installed successfully through individual installation.")
        else:
            print("\nAll dependencies installed successfully.")
    else:
        print("Error: requirements.txt file not found")
        sys.exit(1)

def check_database():
    """Check if database exists and create it if needed."""
    print_step("Checking database")
    
    # Get database path from .env if available
    db_path = "pinopoly.db"  # Default path
    if os.path.exists(".env"):
        with open(".env", "r") as env_file:
            content = env_file.read()
            match = re.search(r'DATABASE_PATH\s*=\s*(.+)', content)
            if match:
                db_path = match.group(1).strip()
    
    if not os.path.exists(db_path):
        print(f"Database file ({db_path}) doesn't exist. It will be created when you run the application.")
    else:
        print(f"Database file exists: {db_path}")

def check_project_directory():
    """Check if current directory appears to be the Pi-nopoly project root."""
    expected_dirs = ["src", "client", "static", "templates"]
    expected_files = ["app.py", "requirements.txt"]
    
    current_dir_items = os.listdir(".")
    
    missing_dirs = [d for d in expected_dirs if d not in current_dir_items]
    missing_files = [f for f in expected_files if f not in current_dir_items]
    
    if missing_dirs or missing_files:
        print("Warning: This may not be the Pi-nopoly root directory.")
        
        if missing_dirs:
            print("Missing expected directories:", ", ".join(missing_dirs))
        
        if missing_files:
            print("Missing expected files:", ", ".join(missing_files))
        
        response = input("Continue anyway? (y/n): ")
        if response.lower() != "y":
            sys.exit(1)
    
    return True

def setup_development_database():
    """Set up a development database if needed."""
    print_step("Setting up development database")
    
    # Check if Flask is installed in the current environment
    try:
        import flask
        print("Flask is installed in the current environment")
        
        if os.path.exists("app.py"):
            response = input("Would you like to initialize the database with Flask-Migrate? (y/n): ")
            if response.lower() == "y":
                try:
                    # Try to run Flask-Migrate commands
                    run_command([sys.executable, "-c", "from flask_migrate import init, migrate, upgrade; from app import app, db; init(); migrate(); upgrade()"], exit_on_error=False)
                    print("Database initialized with Flask-Migrate")
                except Exception as e:
                    print(f"Error initializing database: {e}")
                    print("You'll need to run Flask-Migrate commands manually after starting the application")
    except ImportError:
        print("Flask is not installed in the current environment")
        print("Database initialization will be done when you run the application")

def main():
    """Main function."""
    print_header("Pi-nopoly Backend Setup")
    
    # Check current directory
    check_project_directory()
    
    # Check Python version
    check_python_version()
    
    # Check pip
    pip_cmd = check_pip()
    
    # Setup virtual environment
    activate_cmd, venv_pip = setup_virtual_env(pip_cmd)
    
    # Create environment file
    create_env_file()
    
    # Determine if we're in a virtual environment
    in_venv = "VIRTUAL_ENV" in os.environ
    
    if in_venv:
        print("\nVirtual environment is active.")
        
        # Install dependencies
        install_dependencies(pip_cmd, venv_pip)
        
        # Check database
        check_database()
        
        # Set up development database
        setup_development_database()
        
        print_header("Setup Complete")
        print("To run the application:")
        print("1. Ensure virtual environment is activated")
        print("2. Run: python app.py")
    else:
        print("\nVirtual environment is not active.")
        print(f"Please activate it with: {activate_cmd}")
        print("Then run this script again to complete the setup.")
        
        if platform.system() == "Windows":
            print("\nOn Windows, you may need to adjust PowerShell execution policy:")
            print("Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser")

if __name__ == "__main__":
    main() 