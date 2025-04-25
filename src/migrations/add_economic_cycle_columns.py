from src.models import db
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

def run_migration():
    """Add economic_cycle_position and economic_cycle_period columns to game_state table"""
    logger.info("Starting migration to add economic_cycle_position and economic_cycle_period columns to game_state table")
    
    try:
        # Check if columns already exist using SQLite PRAGMA
        with db.engine.connect() as conn:
            # Get table info for game_state
            result = conn.execute(text("PRAGMA table_info(game_state)"))
            columns = [row[1] for row in result.fetchall()]  # Column name is the second element (index 1)
            
            economic_cycle_position_exists = 'economic_cycle_position' in columns
            economic_cycle_period_exists = 'economic_cycle_period' in columns
        
        # Add columns that don't exist
        with db.engine.connect() as conn:
            if not economic_cycle_position_exists:
                conn.execute(text("ALTER TABLE game_state ADD COLUMN economic_cycle_position FLOAT DEFAULT 0.0"))
                logger.info("Successfully added economic_cycle_position column to game_state table")
            else:
                logger.info("Column economic_cycle_position already exists in game_state table; skipping")
            
            if not economic_cycle_period_exists:
                conn.execute(text("ALTER TABLE game_state ADD COLUMN economic_cycle_period INTEGER DEFAULT 5"))
                logger.info("Successfully added economic_cycle_period column to game_state table")
            else:
                logger.info("Column economic_cycle_period already exists in game_state table; skipping")
        
        # Verify columns were added
        with db.engine.connect() as conn:
            # Get updated table info
            result = conn.execute(text("PRAGMA table_info(game_state)"))
            columns = [row[1] for row in result.fetchall()]
            
            economic_cycle_position_verified = 'economic_cycle_position' in columns
            economic_cycle_period_verified = 'economic_cycle_period' in columns
        
        if economic_cycle_position_verified and economic_cycle_period_verified:
            logger.info("Migration verification successful: all columns exist")
            return True
        else:
            missing_columns = []
            if not economic_cycle_position_verified:
                missing_columns.append("economic_cycle_position")
            if not economic_cycle_period_verified:
                missing_columns.append("economic_cycle_period")
            logger.error(f"Migration verification failed: missing columns: {', '.join(missing_columns)}")
            return False
                
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False 