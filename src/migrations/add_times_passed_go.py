from src.models import db
import logging

logger = logging.getLogger(__name__)

def run_migration():
    """Add times_passed_go column to players table"""
    logger.info("Starting migration to add times_passed_go column to players table")
    
    try:
        # Check if column already exists
        with db.engine.connect() as conn:
            result = conn.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='players' AND column_name='times_passed_go'
            """)
            if result.fetchone():
                logger.info("Column times_passed_go already exists in players table; skipping migration")
                return True
        
        # Add the column
        with db.engine.connect() as conn:
            conn.execute("ALTER TABLE players ADD COLUMN times_passed_go INTEGER DEFAULT 0")
            logger.info("Successfully added times_passed_go column to players table")
        
        # Verify column was added
        with db.engine.connect() as conn:
            result = conn.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='players' AND column_name='times_passed_go'
            """)
            if result.fetchone():
                logger.info("Migration verification successful: times_passed_go column exists")
                return True
            else:
                logger.error("Migration verification failed: times_passed_go column not found")
                return False
                
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False 