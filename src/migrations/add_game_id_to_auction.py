import logging
from sqlalchemy import text
from src.models import db

logger = logging.getLogger(__name__)

def check_column_exists(column_name, table_name):
    """Check if a column exists in a table (SQLite compatible)"""
    try:
        query = text(f"PRAGMA table_info({table_name})")
        columns = db.session.execute(query).fetchall()
        return any(column[1] == column_name for column in columns)
    except Exception as e:
        logger.error(f"Error checking if column exists: {str(e)}")
        return False

def run_migration():
    """Add game_id column to auctions table"""
    logger.info("Starting migration to add game_id column to auctions table")
    
    try:
        # Check if the table exists
        check_table_query = text("SELECT name FROM sqlite_master WHERE type='table' AND name='auctions'")
        table_exists = db.session.execute(check_table_query).fetchone() is not None
        
        if not table_exists:
            logger.info("Table 'auctions' doesn't exist yet, will be created with game_id column")
            return True
            
        # Check if the column already exists
        if check_column_exists('game_id', 'auctions'):
            logger.info("Column game_id already exists in auctions table; skipping migration")
            return True
        
        # Add game_id column
        query = text("""
            ALTER TABLE auctions
            ADD COLUMN game_id INTEGER
        """)
        db.session.execute(query)
        
        # SQLite doesn't support adding constraints in ALTER TABLE
        # We'll need to add any constraints when creating a new auction
        
        db.session.commit()
        logger.info("Successfully added game_id column to auctions table")
        
        # Verify the migration was successful
        if check_column_exists('game_id', 'auctions'):
            logger.info("Migration verification successful: game_id column exists")
            return True
        else:
            logger.error("Migration verification failed: game_id column doesn't exist")
            return False
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        db.session.rollback()
        return False 