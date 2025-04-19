import logging
from sqlalchemy import text
from src.models import db
from datetime import datetime

logger = logging.getLogger(__name__)

def run_migration():
    """
    Migration to add updated_at column to players table.
    
    Returns:
        bool: True if migration was successful, False otherwise
    """
    try:
        logger.info("Starting migration to add updated_at column to players table")
        
        # Check if column already exists to avoid duplicate migration
        with db.engine.connect() as connection:
            # Get the column info from SQLite's pragma table_info
            result = connection.execute(text("PRAGMA table_info(players)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "updated_at" in columns:
                logger.info("Column updated_at already exists in players table; skipping migration")
                return True
            
            # Add the updated_at column with default value of current timestamp
            current_timestamp = datetime.utcnow().isoformat()
            connection.execute(text(f"ALTER TABLE players ADD COLUMN updated_at TIMESTAMP DEFAULT '{current_timestamp}'"))
            connection.commit()
            
            logger.info("Successfully added updated_at column to players table")
            
            # Verify column was added
            result = connection.execute(text("PRAGMA table_info(players)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "updated_at" in columns:
                logger.info("Migration verification successful: updated_at column exists")
                return True
            else:
                logger.error("Migration verification failed: updated_at column not found after migration")
                return False
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}", exc_info=True)
        return False 