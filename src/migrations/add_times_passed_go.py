from src.models import db
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

def run_migration():
    """Add times_passed_go column to players table"""
    logger.info("Starting migration to add times_passed_go column to players table")
    
    try:
        # Check if column already exists using SQLite PRAGMA
        with db.engine.connect() as conn:
            # Get table info for players
            result = conn.execute(text("PRAGMA table_info(players)"))
            columns = [row[1] for row in result.fetchall()]  # Column name is the second element (index 1)
            
            times_passed_go_exists = 'times_passed_go' in columns
        
        # Add column if it doesn't exist
        if not times_passed_go_exists:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE players ADD COLUMN times_passed_go INTEGER DEFAULT 0"))
                logger.info("Successfully added times_passed_go column to players table")
        else:
            logger.info("Column times_passed_go already exists in players table; skipping migration")
        
        # Verify column was added
        with db.engine.connect() as conn:
            # Get updated table info
            result = conn.execute(text("PRAGMA table_info(players)"))
            columns = [row[1] for row in result.fetchall()]
            
            times_passed_go_verified = 'times_passed_go' in columns
        
        if times_passed_go_verified:
            logger.info("Migration verification successful: times_passed_go column exists")
            return True
        else:
            logger.error("Migration verification failed: times_passed_go column not found")
            return False
                
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False 