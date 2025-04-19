#!/usr/bin/env python
"""
Make Setup Scripts Executable
This script makes the setup scripts executable on Unix/Linux systems.
"""

import os
import stat
import platform
import sys

def make_executable(file_path):
    """Make a file executable."""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return False
    
    # Get current permissions
    current_mode = os.stat(file_path).st_mode
    
    # Add executable permission for user, group, and others
    executable_mode = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    
    try:
        os.chmod(file_path, executable_mode)
        print(f"Made {file_path} executable.")
        return True
    except Exception as e:
        print(f"Error making {file_path} executable: {e}")
        return False

def main():
    """Main function."""
    print("Making setup scripts executable...")
    
    # Check if running on Windows
    if platform.system() == "Windows":
        print("This script is not needed on Windows systems.")
        print("Windows does not use file permissions for script execution.")
        sys.exit(0)
    
    # Files to make executable
    files = ["setup_frontend.py", "setup_python_backend.py"]
    
    success = True
    for file in files:
        if not make_executable(file):
            success = False
    
    if success:
        print("\nAll setup scripts are now executable.")
        print("You can run them with:")
        print("./setup_python_backend.py")
        print("./setup_frontend.py")
    else:
        print("\nThere were errors making some scripts executable.")
        print("You can still run them with:")
        print("python setup_python_backend.py")
        print("python setup_frontend.py")

if __name__ == "__main__":
    main() 