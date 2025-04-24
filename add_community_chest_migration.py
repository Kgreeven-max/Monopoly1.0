import os
import sqlite3
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_migration():
    """
    Add _community_chest_cards_json and game_log columns to the game_state table
    """
    logger.info("Starting migration to add community chest cards columns...")
    
    # Find SQLite database files
    db_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.db') or file.endswith('.sqlite') or file.endswith('.sqlite3'):
                db_files.append(os.path.join(root, file))
    
    if not db_files:
        logger.error("No database files found.")
        return False
    
    logger.info(f"Found {len(db_files)} database files: {db_files}")
    success = False
    
    for db_path in db_files:
        try:
            logger.info(f"Attempting migration on {db_path}")
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if game_state table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='game_state'")
            if not cursor.fetchone():
                logger.info(f"No game_state table in {db_path}, skipping")
                conn.close()
                continue
            
            # Check if columns already exist
            cursor.execute(f"PRAGMA table_info(game_state)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add _community_chest_cards_json column if it doesn't exist
            if '_community_chest_cards_json' not in columns:
                logger.info(f"Adding _community_chest_cards_json column to {db_path}")
                cursor.execute("ALTER TABLE game_state ADD COLUMN _community_chest_cards_json TEXT")
                logger.info("Successfully added _community_chest_cards_json column")
            else:
                logger.info("_community_chest_cards_json column already exists")
            
            # Add game_log column if it doesn't exist
            if 'game_log' not in columns:
                logger.info(f"Adding game_log column to {db_path}")
                cursor.execute("ALTER TABLE game_state ADD COLUMN game_log TEXT")
                logger.info("Successfully added game_log column")
            else:
                logger.info("game_log column already exists")
            
            # Commit changes and close connection
            conn.commit()
            conn.close()
            logger.info(f"Migration completed successfully for {db_path}")
            success = True
            
        except Exception as e:
            logger.error(f"Error processing {db_path}: {str(e)}")
    
    return success

if __name__ == "__main__":
    result = run_migration()
    if result:
        print("Migration completed successfully!")
    else:
        print("Migration failed or no databases were modified.") 