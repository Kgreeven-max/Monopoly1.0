import os
import glob
import shutil
from datetime import datetime

def reset_database():
    """
    Find and delete all SQLite database files in the project.
    Makes a backup before deletion.
    """
    # Define database file patterns to look for
    db_patterns = ['*.db', '*.sqlite', '*.sqlite3']
    
    # Create a backup directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f'db_backup_{timestamp}'
    os.makedirs(backup_dir, exist_ok=True)
    
    print(f"Scanning for database files...")
    db_files = []
    
    # Recursively search for database files in the current directory and subdirectories
    for pattern in db_patterns:
        db_files.extend(glob.glob(f'**/{pattern}', recursive=True))
    
    # If no database files found, exit
    if not db_files:
        print("No database files found.")
        return
    
    # Display found database files
    print(f"Found {len(db_files)} database files:")
    for db_file in db_files:
        print(f" - {db_file}")
    
    # Confirm deletion
    confirm = input(f"Are you sure you want to delete these files? A backup will be created in '{backup_dir}'. (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    # Create backups and delete files
    print(f"Creating backups and deleting database files...")
    for db_file in db_files:
        try:
            # Create backup
            backup_path = os.path.join(backup_dir, os.path.basename(db_file))
            shutil.copy2(db_file, backup_path)
            print(f" - Backed up {db_file} to {backup_path}")
            
            # Delete original
            os.remove(db_file)
            print(f" - Deleted {db_file}")
        except Exception as e:
            print(f" - Error processing {db_file}: {str(e)}")
    
    print(f"Database reset complete. Backups saved to {backup_dir}/")
    print(f"Run 'python app.py' to start with a fresh database.")

if __name__ == "__main__":
    reset_database() 