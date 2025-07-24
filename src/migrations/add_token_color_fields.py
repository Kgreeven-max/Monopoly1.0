"""Add token and color fields to players table"""

import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

def run_migration(db):
    """Add token and color fields to players table"""
    logger.info("Starting migration to add token and color fields to players table")
    
    try:
        # Check if token column exists
        result = db.session.execute(text("PRAGMA table_info(players);"))
        columns = [row[1] for row in result]
        
        # Add token column if it doesn't exist
        if 'token' not in columns:
            logger.info("Adding token column to players table")
            db.session.execute(text("""
                ALTER TABLE players ADD COLUMN token VARCHAR(20) DEFAULT 'car';
            """))
            db.session.commit()
            logger.info("Successfully added token column")
        else:
            logger.info("Column token already exists in players table; skipping")
            
        # Add color column if it doesn't exist
        if 'color' not in columns:
            logger.info("Adding color column to players table")
            db.session.execute(text("""
                ALTER TABLE players ADD COLUMN color VARCHAR(7) DEFAULT '#999999';
            """))
            db.session.commit()
            logger.info("Successfully added color column")
        else:
            logger.info("Column color already exists in players table; skipping")
            
        # Assign different tokens and colors to existing bots
        bots = db.session.execute(text("SELECT id, username FROM players WHERE is_bot = 1")).fetchall()
        tokens = ['car', 'shoe', 'dog', 'hat', 'iron', 'ship']
        colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']
        
        for i, bot in enumerate(bots):
            token = tokens[i % len(tokens)]
            color = colors[i % len(colors)]
            db.session.execute(text("""
                UPDATE players 
                SET token = :token, color = :color 
                WHERE id = :id
            """), {'token': token, 'color': color, 'id': bot[0]})
            logger.info(f"Updated bot {bot[1]} with token={token}, color={color}")
            
        db.session.commit()
        
        # Verify migration
        result = db.session.execute(text("PRAGMA table_info(players);"))
        columns = [row[1] for row in result]
        
        if 'token' in columns and 'color' in columns:
            logger.info("Migration verification successful: token and color columns exist")
            return True
        else:
            logger.error("Migration verification failed: columns not found")
            return False
            
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        db.session.rollback()
        return False