import logging
from flask import jsonify, Blueprint, request, current_app
from src.models import db, get_auction_system
from src.models.game_state import GameState
from src.models.player import Player
from src.models.property import Property

logger = logging.getLogger(__name__)
board_bp = Blueprint('board_api', __name__, url_prefix='/api/board')

class BoardController:
    """Controller for board display related data retrieval"""

    def __init__(self):
        # Lazy load auction system to avoid circular dependencies at import time
        self._auction_system = None

    @property
    def auction_system(self):
        if self._auction_system is None:
            self._auction_system = get_auction_system()
        return self._auction_system

    def get_active_auctions(self):
        """Retrieves active auctions."""
        try:
            result = self.auction_system.get_active_auctions()
            # The auction system already returns a dict with 'success' key
            return result 
        except Exception as e:
            logger.error(f"Error getting active auctions: {e}", exc_info=True)
            return {"success": False, "error": "Failed to retrieve auctions"}

    def get_auction_details(self, auction_id):
        """Retrieves details for a specific auction."""
        try:
            result = self.auction_system.get_auction(auction_id)
            # The auction system already returns a dict with 'success' key
            return result
        except Exception as e:
            logger.error(f"Error getting auction details for {auction_id}: {e}", exc_info=True)
            return {"success": False, "error": "Failed to retrieve auction details"}

    def check_property_development_requirements(self, property_id, target_level):
        """Checks development requirements for a specific property and calculates costs."""
        try:
            property_obj = Property.query.get(property_id)
            if not property_obj:
                return {"success": False, "error": "Property not found"}

            requirements_check = property_obj.check_development_requirements(target_level)
            game_state = GameState.query.first() # Or get_instance()

            if requirements_check.get("requirements_met"):
                current_level = property_obj.improvement_level
                costs = []
                total_cost = 0
                # Temporarily modify level to calculate costs - ensure this doesn't persist!
                original_level = property_obj.improvement_level 
                try:
                    for level in range(current_level + 1, target_level + 1):
                        property_obj.improvement_level = level - 1
                        cost = property_obj.calculate_improvement_cost(game_state)
                        costs.append({"level": level, "cost": cost})
                        total_cost += cost
                finally:
                    # Always reset the level, even if errors occur
                    property_obj.improvement_level = original_level
                
                requirements_check["development_costs"] = {
                    "level_costs": costs,
                    "total_cost": total_cost
                }

            response = {
                'success': True,
                'property': {
                    'id': property_obj.id,
                    'name': property_obj.name,
                    'group': property_obj.group_name,
                    'current_level': property_obj.improvement_level,
                    'max_level': property_obj.max_development_level
                },
                'requirements': requirements_check
            }
            return response
        except Exception as e:
            logger.error(f"Error checking dev requirements for prop {property_id}: {e}", exc_info=True)
            return {"success": False, "error": "Failed to check development requirements"}

    def get_property_development_info(self, group_name):
        """Retrieves property development information for a specific group."""
        try:
            properties = Property.query.filter_by(group_name=group_name).all()
            if not properties:
                return {"success": False, "error": "Property group not found"}

            sample_property = properties[0]
            zone_info = sample_property.ZONING_REGULATIONS.get(group_name.lower(), {})
            game_state = GameState.query.first() # Or get_instance()
            economic_state = game_state.inflation_state if game_state else "normal"
            economic_multiplier = sample_property.ECONOMIC_MULTIPLIERS.get(economic_state, 1.0)
            development_levels = sample_property.DEVELOPMENT_LEVELS

            result = {
                'success': True,
                'group_name': group_name,
                'properties': [p.to_dict() for p in properties],
                'zoning': {
                    'max_level': zone_info.get('max_level', 4),
                    'approval_required': zone_info.get('approval_required', False),
                    'study_required': zone_info.get('study_required', False),
                    'cost_modifier': zone_info.get('cost_modifier', 1.0)
                },
                'economic_state': {
                    'state': economic_state,
                    'multiplier': economic_multiplier,
                    'inflation_factor': game_state.inflation_factor if game_state else 1.0
                },
                'development_levels': development_levels
            }
            return result
        except Exception as e:
            logger.error(f"Error getting dev info for group {group_name}: {e}", exc_info=True)
            return {"success": False, "error": "Failed to get development info"}

    def get_property_development_status(self, property_id):
        """Retrieves current status and development capabilities of a property."""
        try:
            property_obj = Property.query.get(property_id)
            if not property_obj:
                return {"success": False, "error": "Property not found"}

            game_state = GameState.query.first()
            current_level = property_obj.improvement_level
            max_level = property_obj.max_development_level
            dev_level_data = property_obj.DEVELOPMENT_LEVELS.get(current_level, property_obj.DEVELOPMENT_LEVELS[0])

            can_improve = False
            improvement_cost = 0
            if current_level < max_level and property_obj.owner_id is not None:
                can_improve = True
                improvement_cost = property_obj.calculate_improvement_cost(game_state)

            owner_info = None
            if property_obj.owner_id:
                owner = Player.query.get(property_obj.owner_id)
                if owner:
                    owner_info = {
                        'id': owner.id,
                        'name': owner.username, # Corrected from name
                        'community_standing': owner.community_standing
                    }
            
            repair_cost = 0
            if property_obj.damage_amount > 0:
                repair_cost = property_obj.calculate_repair_cost(property_obj.damage_amount)
            
            response = {
                'success': True,
                'property': {
                    'id': property_obj.id,
                    'name': property_obj.name,
                    'group': property_obj.group_name,
                    'position': property_obj.position,
                    'price': property_obj.price,
                    'current_price': property_obj.current_price,
                    'rent': property_obj.rent,
                    'current_rent': property_obj.current_rent,
                    'owner': owner_info,
                    'is_mortgaged': property_obj.is_mortgaged
                },
                'development': {
                    'current_level': current_level,
                    'level_name': dev_level_data['name'],
                    'max_level': max_level,
                    'rent_multiplier': dev_level_data['rent_multiplier'],
                    'value_multiplier': dev_level_data['value_multiplier'],
                    'can_improve': can_improve,
                    'improvement_cost': improvement_cost,
                    'has_community_approval': property_obj.has_community_approval,
                    'has_environmental_study': property_obj.has_environmental_study,
                    'environmental_study_expires': property_obj.environmental_study_expires.isoformat() if property_obj.environmental_study_expires else None
                },
                'damage': {
                    'has_damage': property_obj.damage_amount > 0,
                    'damage_amount': property_obj.damage_amount,
                    'damage_percentage': round(property_obj.damage_amount / property_obj.current_price * 100, 1) if property_obj.current_price > 0 else 0,
                    'repair_cost': repair_cost,
                    'is_water_adjacent': property_obj.is_water_adjacent,
                    'max_damage_factor': dev_level_data['max_damage'],
                    'repair_cost_factor': dev_level_data['repair_cost_factor']
                }
            }
            return response
        except Exception as e:
            logger.error(f"Error getting dev status for prop {property_id}: {e}", exc_info=True)
            return {"success": False, "error": "Failed to get property development status"}

    # --- Placeholder methods for other actions ---
    def get_board_state(self):
        logger.warning("BoardController.get_board_state not fully implemented.")
        return {"success": False, "error": "Not Implemented"}

    def get_player_positions(self):
        logger.warning("BoardController.get_player_positions not fully implemented.")
        return {"success": False, "error": "Not Implemented"}

    def get_property_owners(self):
        logger.warning("BoardController.get_property_owners not fully implemented.")
        return {"success": False, "error": "Not Implemented"}

    def get_recent_events(self, limit):
        logger.warning("BoardController.get_recent_events not fully implemented.")
        return {"success": False, "error": "Not Implemented"}

    def register_display(self, device_info):
        logger.warning("BoardController.register_display not fully implemented.")
        return {"success": False, "error": "Not Implemented"}

    def get_economy_state(self):
        logger.warning("BoardController.get_economy_state not fully implemented.")
        return {"success": False, "error": "Not Implemented"}

    def player_action_on_property(self, player_id, property_id, action):
        """Handle player decision (buy/decline) on landing on unowned property"""
        player = Player.query.get(player_id)
        property_obj = Property.query.get(property_id)
        game_state = current_app.config.get('game_state_instance') # Get GameState
        banker = current_app.config.get('banker') # Get Banker
        auction_system = current_app.config.get('auction_system') # Get AuctionSystem

        if not all([player, property_obj, game_state, banker, auction_system]):
            missing = [name for name, obj in [
                ('Player', player), ('Property', property_obj), ('GameState', game_state), 
                ('Banker', banker), ('AuctionSystem', auction_system)
            ] if not obj]
            error_msg = f"Missing required components: {', '.join(missing)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

        # Check if player is the current player
        if game_state.current_player_id != player_id:
            return {"success": False, "error": "Not your turn"}
        
        # Check if property is owned
        if property_obj.owner_id is not None:
            return {"success": False, "error": "Property is already owned"}
            
        if action == 'buy':
            # Attempt purchase via Banker
            purchase_success = banker.process_property_purchase(player, property_obj, game_state)
            if purchase_success:
                return {"success": True, "message": f"Property {property_obj.name} purchased"}
            else:
                # If purchase fails (e.g., insufficient funds), property should go to auction
                if game_state.auction_required:
                    self.logger.info(f"Purchase failed for {property_obj.name}, initiating auction.")
                    # Start auction via AuctionSystem
                    auction_result = auction_system.start_auction(property_id)
                    if auction_result.get('success'):
                        return {"success": True, "message": f"Purchase failed, auction started for {property_obj.name}", "auction_started": True, "auction_id": auction_result.get('auction_id')}
                    else:
                         return {"success": False, "error": f"Purchase failed and auction could not be started: {auction_result.get('error')}"}
                else:
                    return {"success": False, "error": "Insufficient funds to purchase"}
                    
        elif action == 'decline':
            # If declined and auction is required, start auction
            if game_state.auction_required:
                self.logger.info(f"Player declined {property_obj.name}, initiating auction.")
                # Start auction via AuctionSystem
                auction_result = auction_system.start_auction(property_id)
                if auction_result.get('success'):
                     return {"success": True, "message": f"Declined purchase, auction started for {property_obj.name}", "auction_started": True, "auction_id": auction_result.get('auction_id')}
                else:
                    return {"success": False, "error": f"Auction could not be started: {auction_result.get('error')}"}
            else:
                 return {"success": True, "message": "Purchase declined"}
                 
        else:
            return {"success": False, "error": "Invalid action specified"} 