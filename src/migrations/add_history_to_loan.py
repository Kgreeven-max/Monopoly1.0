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
    """Add history column to loans table"""
    logger.info("Starting migration to add history column to loans table")
    
    try:
        # Check if the table exists
        check_table_query = text("SELECT name FROM sqlite_master WHERE type='table' AND name='loans'")
        table_exists = db.session.execute(check_table_query).fetchone() is not None
        
        if not table_exists:
            logger.info("Table 'loans' doesn't exist yet, will be created with history column")
            return True
            
        # Check if the column already exists
        if check_column_exists('history', 'loans'):
            logger.info("Column history already exists in loans table; skipping migration")
            return True
        
        # Add history column
        query = text("""
            ALTER TABLE loans
            ADD COLUMN history TEXT
        """)
        db.session.execute(query)
        
        db.session.commit()
        logger.info("Successfully added history column to loans table")
        
        # Verify the migration was successful
        if check_column_exists('history', 'loans'):
            logger.info("Migration verification successful: history column exists")
            
            # Initialize history for existing loans
            init_query = text("""
                UPDATE loans 
                SET history = '[]'
                WHERE history IS NULL
            """)
            db.session.execute(init_query)
            db.session.commit()
            logger.info("Initialized history column for existing loans")
            
            return True
        else:
            logger.error("Migration verification failed: history column doesn't exist")
            return False
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        db.session.rollback()
        return False 