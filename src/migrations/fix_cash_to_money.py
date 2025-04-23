import logging
from sqlalchemy import inspect, text
from src.models import db

logger = logging.getLogger(__name__)

def run_migration():
    """
    Make sure Property model has current_price and current_rent columns,
    and initialize them with values from price and rent columns.
    """
    logger.info("Starting migration to fix cash/money references and add current_price/current_rent columns")
    
    # Get inspector to check columns
    inspector = inspect(db.engine)
    
    # Check if Property table has current_price column
    property_columns = [col['name'] for col in inspector.get_columns('properties')]
    needs_current_price = 'current_price' not in property_columns
    needs_current_rent = 'current_rent' not in property_columns
    
    if needs_current_price or needs_current_rent:
        try:
            # Add missing columns if needed
            with db.engine.connect() as conn:
                if needs_current_price:
                    logger.info("Adding current_price column to properties table")
                    conn.execute(text("ALTER TABLE properties ADD COLUMN current_price INTEGER"))
                    conn.execute(text("UPDATE properties SET current_price = price"))
                    
                if needs_current_rent:
                    logger.info("Adding current_rent column to properties table")
                    conn.execute(text("ALTER TABLE properties ADD COLUMN current_rent INTEGER"))
                    conn.execute(text("UPDATE properties SET current_rent = rent"))
                
                # Make sure the transaction is committed
                conn.commit()
                
            logger.info("Successfully added missing columns to properties table")
        except Exception as e:
            logger.error(f"Error adding columns: {str(e)}")
            return False
    else:
        logger.info("Property table already has current_price and current_rent columns")
    
    # Check if the column initialization worked correctly
    try:
        # Verify that current_price is properly set
        with db.engine.connect() as conn:
            if needs_current_price:
                result = conn.execute(text("SELECT COUNT(*) FROM properties WHERE current_price IS NULL AND price IS NOT NULL")).scalar()
                if result > 0:
                    logger.warning(f"Found {result} properties with NULL current_price but non-NULL price")
                    conn.execute(text("UPDATE properties SET current_price = price WHERE current_price IS NULL AND price IS NOT NULL"))
                    conn.commit()
                    
            if needs_current_rent:
                result = conn.execute(text("SELECT COUNT(*) FROM properties WHERE current_rent IS NULL AND rent IS NOT NULL")).scalar()
                if result > 0:
                    logger.warning(f"Found {result} properties with NULL current_rent but non-NULL rent")
                    conn.execute(text("UPDATE properties SET current_rent = rent WHERE current_rent IS NULL AND rent IS NOT NULL"))
                    conn.commit()
                    
        logger.info("Property columns are properly initialized")
        return True
    except Exception as e:
        logger.error(f"Error verifying column initialization: {str(e)}")
        return False 