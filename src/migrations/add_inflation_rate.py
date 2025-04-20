import logging
from sqlalchemy import text
from src.models import db

logger = logging.getLogger(__name__)

def run_migration():
    """Add inflation_rate and base_interest_rate columns to game_state table if they don't exist"""
    logger.info("Starting migration to add inflation_rate and base_interest_rate columns to game_state table")
    
    try:
        # Check if columns already exist to avoid duplicate migration
        with db.engine.connect() as connection:
            # Get the column info from SQLite's pragma table_info
            result = connection.execute(text("PRAGMA table_info(game_state)"))
            columns = [row[1] for row in result.fetchall()]
            
            # Add inflation_rate column if it doesn't exist
            if "inflation_rate" not in columns:
                logger.info("Adding inflation_rate column to game_state table")
                connection.execute(text("ALTER TABLE game_state ADD COLUMN inflation_rate REAL DEFAULT 0.03"))
                connection.commit()
            else:
                logger.info("Column inflation_rate already exists in game_state table; skipping")
            
            # Add base_interest_rate column if it doesn't exist
            if "base_interest_rate" not in columns:
                logger.info("Adding base_interest_rate column to game_state table")
                connection.execute(text("ALTER TABLE game_state ADD COLUMN base_interest_rate REAL DEFAULT 0.05"))
                connection.commit()
            else:
                logger.info("Column base_interest_rate already exists in game_state table; skipping")
            
            # Verify columns were added
            result = connection.execute(text("PRAGMA table_info(game_state)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "inflation_rate" in columns and "base_interest_rate" in columns:
                logger.info("Migration verification successful: columns exist")
                return True
            else:
                missing = []
                if "inflation_rate" not in columns:
                    missing.append("inflation_rate")
                if "base_interest_rate" not in columns:
                    missing.append("base_interest_rate")
                logger.error(f"Migration verification failed: columns {', '.join(missing)} not found after migration")
                return False
                
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}", exc_info=True)
        return False 