"""
Migration to add started_at and ended_at columns to the game_state table if they don't exist
"""

import logging
from sqlalchemy import text
from src.models import db

logger = logging.getLogger(__name__)

def run_migration():
    """Add started_at and ended_at columns to game_state table if they don't exist"""
    logger.info("Starting migration to add started_at and ended_at columns to game_state table")
    
    try:
        # Check if columns already exist to avoid duplicate migration
        with db.engine.connect() as connection:
            # Get the column info from SQLite's pragma table_info
            result = connection.execute(text("PRAGMA table_info(game_state)"))
            columns = [row[1] for row in result.fetchall()]
            
            # Add started_at column if it doesn't exist
            if "started_at" not in columns:
                logger.info("Adding started_at column to game_state table")
                connection.execute(text("ALTER TABLE game_state ADD COLUMN started_at TIMESTAMP"))
                connection.commit()
            else:
                logger.info("Column started_at already exists in game_state table; skipping")
            
            # Add ended_at column if it doesn't exist
            if "ended_at" not in columns:
                logger.info("Adding ended_at column to game_state table")
                connection.execute(text("ALTER TABLE game_state ADD COLUMN ended_at TIMESTAMP"))
                connection.commit()
            else:
                logger.info("Column ended_at already exists in game_state table; skipping")
            
            # Verify columns were added
            result = connection.execute(text("PRAGMA table_info(game_state)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "started_at" in columns and "ended_at" in columns:
                logger.info("Migration verification successful: columns exist")
                return True
            else:
                missing = []
                if "started_at" not in columns:
                    missing.append("started_at")
                if "ended_at" not in columns:
                    missing.append("ended_at")
                logger.error(f"Migration verification failed: columns {', '.join(missing)} not found after migration")
                return False
                
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}", exc_info=True)
        return False 