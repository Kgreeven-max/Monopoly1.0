# src/models/bot_events/utils.py

import logging
from .. import db # Relative import
from ..property import Property # Relative import

logger = logging.getLogger(__name__)

def process_restore_market_prices(data):
    """Restore property prices after market events expire"""
    affected_groups = data.get("affected_groups", [])
    if not affected_groups:
        return {"success": True, "message": "No groups specified for market price restoration."}

    try:
        # Find all properties in affected groups
        properties_to_update = Property.query.filter(
            Property.group_name.in_(affected_groups)
        ).all()

        if not properties_to_update:
             logger.info(f"No properties found in groups {affected_groups} for price restoration.")
             return {"success": True, "message": "No properties found in specified groups."}

        for prop in properties_to_update:
            # Clear any discounts or premiums
            prop.discount_percentage = 0
            prop.discount_amount = 0
            prop.discount_expires_at = None
            prop.premium_percentage = 0
            prop.premium_amount = 0
            prop.premium_expires_at = None
        
        db.session.commit()
        logger.info(f"Restored market prices for properties in groups: {affected_groups}")
        
        return {
            "success": True,
            "message": f"Market prices have been restored for {', '.join(affected_groups)} properties."
        }
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error restoring market prices for groups {affected_groups}: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to restore market prices: {str(e)}"
        }

def process_restore_property_prices(data):
    """Process the restoration of property prices after a market timing event"""
    affected_groups = data.get("affected_groups", [])
    price_change = data.get("price_change", 0)
    
    if not affected_groups or price_change == 0:
         return {"success": False, "message": "Missing affected groups or price change for restoration."}

    try:
        # Get all properties in the affected groups
        affected_properties = Property.query.filter(
            Property.group_name.in_(affected_groups)
        ).all()
        
        if not affected_properties:
            logger.info(f"No properties found in groups {affected_groups} for market timing price restoration.")
            return {"success": True, "message": "No properties found in specified groups for restoration."}

        # Apply price changes to restore
        property_updates = []
        for prop in affected_properties:
            original_price = prop.current_price
            
            # Apply reverse price change
            new_price = int(original_price * (1 + price_change))
            
            # Ensure reasonable price (e.g., >= 60% of base price)
            min_price = int(prop.base_price * 0.6) if prop.base_price else 10 # Default min if base is 0
            new_price = max(new_price, min_price)
            
            # Update property price
            prop.current_price = new_price
            
            # Record update
            property_updates.append({
                "property_id": prop.id,
                "property_name": prop.name,
                "old_price": original_price,
                "new_price": new_price,
                "change_percent": int(price_change * 100)
            })
        
        # Commit changes
        db.session.commit()
        logger.info(f"Restored market timing prices for properties in groups: {affected_groups}")
        
        return {
            "success": True,
            "affected_properties": len(property_updates),
            "property_updates": property_updates
        }
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error restoring market timing prices for groups {affected_groups}: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to restore market timing prices: {str(e)}"
        } 