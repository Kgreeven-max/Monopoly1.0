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
from pathlib import Path

def print_header(text):
    """Print a header with decoration."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_step(text):
    """Print a step."""
    print(f"\n>> {text}")

def run_command(command, exit_on_error=True):
    """Run a shell command and return result."""
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
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

def check_python_version():
    """Check if Python version is compatible."""
    print_step("Checking Python version")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("Error: Python 3.9+ is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    print(f"Python version {version.major}.{version.minor}.{version.micro} is compatible")

def check_pip():
    """Check if pip is installed."""
    print_step("Checking pip installation")
    if shutil.which("pip") is None and shutil.which("pip3") is None:
        print("Error: pip is not installed")
        sys.exit(1)
    
    # Determine pip command (pip or pip3)
    pip_cmd = "pip3" if shutil.which("pip3") else "pip"
    print(f"Using {pip_cmd} for package installation")
    return pip_cmd

def setup_virtual_env(pip_cmd):
    """Create and activate a virtual environment."""
    print_step("Setting up virtual environment")
    
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        run_command([sys.executable, "-m", "venv", "venv"])
    else:
        print("Virtual environment already exists")
    
    # Return activation command for the user
    if platform.system() == "Windows":
        return ".\\venv\\Scripts\\activate"
    else:
        return "source venv/bin/activate"

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
DATABASE_URI=sqlite:///pinopoly.sqlite
DEBUG=True
PORT=5000
ADAPTIVE_DIFFICULTY_ENABLED=true
POLICE_PATROL_ENABLED=true
REMOTE_PLAY_ENABLED=false
""")
            print("Basic .env file created")
    else:
        print(".env file already exists")

def install_dependencies(pip_cmd):
    """Install Python dependencies."""
    print_step("Installing Python dependencies")
    
    if os.path.exists("requirements.txt"):
        # Try to install with --no-binary=pillow to avoid the build error
        success = run_command([pip_cmd, "install", "-r", "requirements.txt", "--no-binary=:all:"], exit_on_error=False)
        
        if not success:
            print("\nTrying alternate installation method...")
            # If first method fails, try installing individual packages
            deps = [
                "Flask==2.3.3", 
                "Flask-SocketIO==5.3.6", 
                "Flask-SQLAlchemy==3.1.1",
                "Flask-Migrate==4.0.5", 
                "SQLAlchemy==2.0.23", 
                "eventlet==0.33.3",
                "python-engineio==4.8.0", 
                "python-socketio==5.10.0", 
                "gunicorn==21.2.0",
                "psutil==5.9.6", 
                "cryptography==41.0.5", 
                "python-dotenv==1.0.0",
                "pyjwt==2.8.0", 
                "requests==2.31.0", 
                "urllib3==2.0.7",
                "qrcode==7.4.2"
            ]
            
            # Try installing all except Pillow
            for dep in deps:
                run_command([pip_cmd, "install", dep], exit_on_error=False)
            
            # Try installing Pillow with special options
            run_command([pip_cmd, "install", "pillow==10.1.0", "--no-binary=pillow"], exit_on_error=False)
    else:
        print("Error: requirements.txt file not found")
        sys.exit(1)

def check_database():
    """Check if database exists and create it if needed."""
    print_step("Checking database")
    
    if not os.path.exists("pinopoly.db"):
        print("Database file doesn't exist. It will be created when you run the application.")
    else:
        print("Database file exists")

def main():
    """Main function."""
    print_header("Pi-nopoly Backend Setup")
    
    # Check current directory
    expected_dirs = ["src", "docs", "client"]
    current_dir_items = os.listdir(".")
    
    if not all(d in current_dir_items for d in expected_dirs):
        print("Warning: This doesn't appear to be the Pi-nopoly root directory.")
        print("Expected to find these directories:", expected_dirs)
        print("Current directory contains:", current_dir_items)
        
        response = input("Continue anyway? (y/n): ")
        if response.lower() != "y":
            sys.exit(1)
    
    # Run setup steps
    check_python_version()
    pip_cmd = check_pip()
    activate_cmd = setup_virtual_env(pip_cmd)
    create_env_file()
    print("\nTo complete installation, please do the following:")
    print(f"1. Activate the virtual environment: {activate_cmd}")
    print("2. Then run this script again to install dependencies")
    
    if "VIRTUAL_ENV" in os.environ:
        print("\nVirtual environment is already activated.")
        install_dependencies(pip_cmd)
        check_database()
        
        print_header("Setup Complete")
        print("To run the application:")
        print("1. Ensure virtual environment is activated")
        print("2. Run: python app.py")
    else:
        print("\nPlease activate the virtual environment and run this script again.")

if __name__ == "__main__":
    main() 