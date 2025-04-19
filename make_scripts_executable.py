#!/usr/bin/env python
"""
Make Scripts Executable
This script makes all utility scripts executable on Unix/Linux systems.
"""

import os
import stat
import platform
import sys
from pathlib import Path
import glob

def print_header(text):
    """Print a header with decoration."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

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
    print_header("Making Scripts Executable")
    
    # Check if running on Windows
    if platform.system() == "Windows":
        print("This script is not needed on Windows systems.")
        print("Windows does not use file permissions for script execution.")
        sys.exit(0)
    
    # Files to make executable
    script_patterns = [
        "setup_*.py",           # Setup scripts
        "make_*.py",            # Script executability helpers
        "run_*.py",             # Testing and utility runners
        "kill_server.py"        # Server killing utility
    ]
    
    # Find all matching files
    files_to_process = []
    for pattern in script_patterns:
        files_to_process.extend(glob.glob(pattern))
    
    if not files_to_process:
        print("No script files found.")
        sys.exit(1)
    
    print(f"Found {len(files_to_process)} script files to process:")
    for file in files_to_process:
        print(f"  - {file}")
    
    print()
    success = True
    successful_files = []
    
    for file in files_to_process:
        if make_executable(file):
            successful_files.append(file)
        else:
            success = False
    
    if success:
        print_header("All Scripts Now Executable")
        print("You can run them directly with:")
        for file in successful_files:
            print(f"  ./{file}")
    else:
        print_header("Some Scripts Could Not Be Made Executable")
        print("You can still run all scripts with:")
        print("  python <script_name>")
        
        if successful_files:
            print("\nThese scripts were successfully made executable:")
            for file in successful_files:
                print(f"  ./{file}")
    
    # Self-check: make this script executable too
    this_script = os.path.basename(__file__)
    if this_script not in files_to_process:
        print(f"\nNow making this script ({this_script}) executable too...")
        make_executable(this_script)

if __name__ == "__main__":
    main() 