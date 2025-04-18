import logging
from sqlalchemy import text
from src.models import db

logger = logging.getLogger(__name__)

def run_migration():
    """
    Migration to add free_parking_fund column to game_state table.
    
    Returns:
        bool: True if migration was successful, False otherwise
    """
    try:
        logger.info("Starting migration to add free_parking_fund column to game_state table")
        
        # Check if column already exists to avoid duplicate migration
        with db.engine.connect() as connection:
            # Get the column info from SQLite's pragma table_info
            result = connection.execute(text("PRAGMA table_info(game_state)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "free_parking_fund" in columns:
                logger.info("Column free_parking_fund already exists in game_state table; skipping migration")
                return True
            
            # Add the free_parking_fund column with a default value of 0
            connection.execute(text("ALTER TABLE game_state ADD COLUMN free_parking_fund INTEGER DEFAULT 0"))
            connection.commit()
            
            logger.info("Successfully added free_parking_fund column to game_state table")
            
            # Verify column was added
            result = connection.execute(text("PRAGMA table_info(game_state)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "free_parking_fund" in columns:
                logger.info("Migration verification successful: free_parking_fund column exists")
                return True
            else:
                logger.error("Migration verification failed: free_parking_fund column not found after migration")
                return False
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}", exc_info=True)
        return False 