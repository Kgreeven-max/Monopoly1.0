import logging
from sqlalchemy import Column, Text
from sqlalchemy.exc import OperationalError
from src.models import db
from sqlalchemy import inspect

def run_migration():
    """
    Adds the _community_chest_cards_json and game_log columns to the game_state table
    if they don't already exist.
    
    Returns:
        bool: True if migration was successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting migration to add _community_chest_cards_json and game_log columns")
    
    try:
        # Get inspector to check for existing columns
        inspector = inspect(db.engine)
        existing_columns = [column['name'] for column in inspector.get_columns('game_state')]
        
        # Check if the _community_chest_cards_json column already exists
        if '_community_chest_cards_json' not in existing_columns:
            logger.info("Adding _community_chest_cards_json column to game_state table")
            # Add the column
            db.engine.execute('ALTER TABLE game_state ADD COLUMN _community_chest_cards_json TEXT')
            logger.info("Successfully added _community_chest_cards_json column")
        else:
            logger.info("_community_chest_cards_json column already exists")
            
        # Check if the game_log column already exists
        if 'game_log' not in existing_columns:
            logger.info("Adding game_log column to game_state table")
            # Add the column
            db.engine.execute('ALTER TABLE game_state ADD COLUMN game_log TEXT')
            logger.info("Successfully added game_log column")
        else:
            logger.info("game_log column already exists")
            
        # Commit changes
        db.session.commit()
        logger.info("Migration completed successfully")
        return True
        
    except OperationalError as e:
        logger.error(f"Database error during migration: {str(e)}")
        db.session.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {str(e)}", exc_info=True)
        db.session.rollback()
        return False

if __name__ == "__main__":
    # Setup basic logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Import Flask app and push context
    from app import app
    with app.app_context():
        success = run_migration()
        print(f"Migration {'successful' if success else 'failed'}") 