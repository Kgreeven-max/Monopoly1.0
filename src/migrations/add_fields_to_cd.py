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
    """Add is_variable_rate and history columns to certificates_of_deposit table"""
    logger.info("Starting migration to add columns to certificates_of_deposit table")
    
    try:
        # Check if the table exists
        check_table_query = text("SELECT name FROM sqlite_master WHERE type='table' AND name='certificates_of_deposit'")
        table_exists = db.session.execute(check_table_query).fetchone() is not None
        
        if not table_exists:
            logger.info("Table 'certificates_of_deposit' doesn't exist yet, will be created with needed columns")
            return True
        
        # Check and add is_variable_rate column if needed
        if not check_column_exists('is_variable_rate', 'certificates_of_deposit'):
            logger.info("Adding is_variable_rate column to certificates_of_deposit table")
            add_variable_rate_query = text("""
                ALTER TABLE certificates_of_deposit
                ADD COLUMN is_variable_rate BOOLEAN DEFAULT 0
            """)
            db.session.execute(add_variable_rate_query)
            db.session.commit()
            logger.info("Added is_variable_rate column to certificates_of_deposit table")
        else:
            logger.info("is_variable_rate column already exists")
        
        # Check and add history column if needed
        if not check_column_exists('history', 'certificates_of_deposit'):
            logger.info("Adding history column to certificates_of_deposit table")
            add_history_query = text("""
                ALTER TABLE certificates_of_deposit
                ADD COLUMN history TEXT
            """)
            db.session.execute(add_history_query)
            db.session.commit()
            logger.info("Added history column to certificates_of_deposit table")
        else:
            logger.info("history column already exists")
        
        # Verify the migration was successful
        is_variable_rate_exists = check_column_exists('is_variable_rate', 'certificates_of_deposit')
        history_exists = check_column_exists('history', 'certificates_of_deposit')
        
        if is_variable_rate_exists and history_exists:
            logger.info("Migration verification successful: all columns exist")
            return True
        else:
            missing_columns = []
            if not is_variable_rate_exists:
                missing_columns.append('is_variable_rate')
            if not history_exists:
                missing_columns.append('history')
            
            logger.error(f"Migration verification failed: missing columns: {', '.join(missing_columns)}")
            return False
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        db.session.rollback()
        return False 