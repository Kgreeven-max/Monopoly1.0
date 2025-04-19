import logging
from src.models import db
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy import text

logger = logging.getLogger(__name__)

def run_migration():
    """Add credit_score column to Player table
    
    This migration adds a credit_score attribute to track player financial reputation.
    
    Returns:
        True if migration successful, False otherwise
    """
    try:
        # Check if migration has already been applied
        connection = db.engine.connect()
        
        # Check if the player table exists first
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'player' not in tables and 'players' not in tables:
            logger.info("Player table doesn't exist yet. Migration will be applied when table is created.")
            return True
            
        # Try to get the table name - it could be 'player' or 'players'
        table_name = 'player' if 'player' in tables else 'players'
            
        # Check if credit_score already exists
        try:
            columns = [column['name'] for column in inspector.get_columns(table_name)]
            
            if 'credit_score' in columns:
                logger.info("Migration 'add_credit_score' already applied.")
                return True
                
            # Add the credit_score column
            sql = text(f"ALTER TABLE {table_name} ADD COLUMN credit_score INTEGER DEFAULT 700")
            connection.execute(sql)
            connection.close()
            
            logger.info(f"Successfully added credit_score column to {table_name} table.")
            return True
        except NoSuchTableError:
            logger.info("Player table doesn't exist yet. Migration will be applied when table is created.")
            return True
            
    except Exception as e:
        logger.error(f"Error in add_credit_score migration: {e}", exc_info=True)
        return False 