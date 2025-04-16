# src/game_logic/game_logic.py
import random
import logging
from src.models import db
from src.models.player import Player
from src.models.game_state import GameState
from src.models.property import Property, PropertyType
from src.models.special_space import SpecialSpace # Import SpecialSpace model
from flask import current_app # For accessing socketio and other controllers

logger = logging.getLogger(__name__)

# --- Constants --- (Should ideally be loaded from config/db)
BOARD_SIZE = 40
JAIL_POSITION = 10
GO_TO_JAIL_POSITION = 30
GO_POSITION = 0
# INCOME_TAX_POSITION = 4 # Defined in SpecialSpace table
# LUXURY_TAX_POSITION = 38 # Defined in SpecialSpace table
# COMMUNITY_CHEST_POSITIONS = [2, 17, 33] # Defined in SpecialSpace table
# CHANCE_POSITIONS = [7, 22, 36] # Defined in SpecialSpace table
RAILROAD_POSITIONS = [5, 15, 25, 35]
UTILITY_POSITIONS = [12, 28]
# FREE_PARKING_POSITION = 20 # Defined in SpecialSpace table

# INCOME_TAX_AMOUNT = 200 # Defined in SpecialSpace table
# LUXURY_TAX_AMOUNT = 100 # Defined in SpecialSpace table
GO_SALARY = 200
MAX_DOUBLES = 3

# --- Default Property Data --- 
# (Simplified - rent levels, house costs etc. omitted for brevity)
# TODO: Move this to a configuration file (e.g., JSON) or DB initialization script
DEFAULT_PROPERTIES = [
    # Position, Name, Type, Group, Price, Base Rent, Mortgage
    (1, "Mediterranean Avenue", PropertyType.STREET, "Brown", 60, 2, 30),
    (3, "Baltic Avenue", PropertyType.STREET, "Brown", 60, 4, 30),
    (5, "Reading Railroad", PropertyType.RAILROAD, "Railroad", 200, 25, 100),
    (6, "Oriental Avenue", PropertyType.STREET, "LightBlue", 100, 6, 50),
    (8, "Vermont Avenue", PropertyType.STREET, "LightBlue", 100, 6, 50),
    (9, "Connecticut Avenue", PropertyType.STREET, "LightBlue", 120, 8, 60),
    (11, "St. Charles Place", PropertyType.STREET, "Pink", 140, 10, 70),
    (12, "Electric Company", PropertyType.UTILITY, "Utility", 150, 0, 75), # Rent calculated differently
    (13, "States Avenue", PropertyType.STREET, "Pink", 140, 10, 70),
    (14, "Virginia Avenue", PropertyType.STREET, "Pink", 160, 12, 80),
    (15, "Pennsylvania Railroad", PropertyType.RAILROAD, "Railroad", 200, 25, 100),
    (16, "St. James Place", PropertyType.STREET, "Orange", 180, 14, 90),
    (18, "Tennessee Avenue", PropertyType.STREET, "Orange", 180, 14, 90),
    (19, "New York Avenue", PropertyType.STREET, "Orange", 200, 16, 100),
    (21, "Kentucky Avenue", PropertyType.STREET, "Red", 220, 18, 110),
    (23, "Indiana Avenue", PropertyType.STREET, "Red", 220, 18, 110),
    (24, "Illinois Avenue", PropertyType.STREET, "Red", 240, 20, 120),
    (25, "B. & O. Railroad", PropertyType.RAILROAD, "Railroad", 200, 25, 100),
    (26, "Atlantic Avenue", PropertyType.STREET, "Yellow", 260, 22, 130),
    (27, "Ventnor Avenue", PropertyType.STREET, "Yellow", 260, 22, 130),
    (28, "Water Works", PropertyType.UTILITY, "Utility", 150, 0, 75), # Rent calculated differently
    (29, "Marvin Gardens", PropertyType.STREET, "Yellow", 280, 24, 140),
    (31, "Pacific Avenue", PropertyType.STREET, "Green", 300, 26, 150),
    (32, "North Carolina Avenue", PropertyType.STREET, "Green", 300, 26, 150),
    (34, "Pennsylvania Avenue", PropertyType.STREET, "Green", 320, 28, 160),
    (35, "Short Line", PropertyType.RAILROAD, "Railroad", 200, 25, 100),
    (37, "Park Place", PropertyType.STREET, "Blue", 350, 35, 175),
    (39, "Boardwalk", PropertyType.STREET, "Blue", 400, 50, 200),
]

# BOARD_LAYOUT is deprecated - query SpecialSpace and Property tables instead

class GameLogic:
    def __init__(self, app):
        self.app = app
        # Potentially load game configuration here if needed
        logger.info("GameLogic initialized.")
        # TODO: Validate BOARD_LAYOUT against Property data in DB on init?

    def initialize_board_properties(self, game_id):
        """Creates the default set of properties for a given game ID if they don't exist."""
        with self.app.app_context():
            existing_prop_count = Property.query.filter_by(game_id=game_id).count()
            if existing_prop_count > 0:
                logger.info(f"Properties for game {game_id} already exist. Skipping initialization.")
                return True # Already initialized

            logger.info(f"Initializing properties for game {game_id}...")
            try:
                for prop_data in DEFAULT_PROPERTIES:
                    pos, name, prop_type, group, price, rent, mortgage = prop_data
                    # Create Property object - Use keywords for clarity
                    new_prop = Property(
                        game_id=game_id,
                        position=pos,
                        name=name,
                        type=prop_type, 
                        color_group=group,
                        price=price,
                        rent_base=rent, # Assuming model uses rent_base
                        mortgage_value=mortgage
                        # TODO: Add house costs, rent levels etc. from full data
                    )
                    db.session.add(new_prop)
                
                db.session.commit()
                logger.info(f"Successfully initialized {len(DEFAULT_PROPERTIES)} properties for game {game_id}.")
                return True
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to initialize properties for game {game_id}: {e}", exc_info=True)
                return False

    def get_game_state(self, game_id=1):
        """Retrieves the current game state using the model's to_dict method."""
        with self.app.app_context():
            game_state = GameState.query.get(game_id)
            if not game_state:
                logger.error(f"Game state with id {game_id} not found.")
                return None
            
            # Ensure Player and Property data is also available if needed by GameState.to_dict()
            # If GameState.to_dict doesn't handle fetching related objects, fetch them here.
            # players = Player.query.filter_by(game_id=game_id).all()
            # properties = Property.query.filter_by(game_id=game_id).all()
            
            # Use the model's to_dict which now includes expected actions
            state_dict = game_state.to_dict()
            
            # Optionally add players and properties if not included in game_state.to_dict
            # state_dict['players'] = [p.to_dict() for p in players]
            # state_dict['properties'] = [prop.to_dict() for prop in properties]
            
            return state_dict

    # start_game logic seems better placed in GameController
    # def start_game(self, game_id=1): ...

    def roll_dice_and_move(self, player_id, game_id=1):
        """Handles the dice roll, movement, doubles logic, passing GO, and determines landing action."""
        with self.app.app_context():
            banker = current_app.config.get('banker')
            special_space_controller = current_app.config.get('special_space_controller')
            if not banker or not special_space_controller:
                 logger.error("Missing Banker or SpecialSpaceController dependency in GameLogic")
                 return {"success": False, "error": "Server configuration error"}
                
            game_state = GameState.query.get(game_id)
            player = Player.query.get(player_id)

            if not game_state or not player:
                logger.error(f"Game or Player not found for roll_dice (Game: {game_id}, Player: {player_id})")
                return {"success": False, "error": "Game or Player not found"}

            # --- 1. Check Turn & Jail Status ---
            if game_state.current_player_id != player_id:
                return {"success": False, "error": "Not your turn"}
                
            # Clear previous expected action before rolling (unless handling jail action)
            if not player.in_jail:
                 game_state.expected_action_type = None
                 game_state.expected_action_details = None
                 db.session.add(game_state) # Add to session

            if player.in_jail:
                 # TODO: Implement separate logic/endpoint for jail actions (pay/card/roll)
                 # For now, assume rolling in jail is an attempt to get out
                 dice1 = random.randint(1, 6)
                 dice2 = random.randint(1, 6)
                 doubles = dice1 == dice2
                 player.jail_turns += 1 # Increment jail turn count

                 if doubles:
                     player.in_jail = False
                     player.jail_turns = 0
                     player.consecutive_doubles_count = 0 # Reset doubles count after leaving jail
                     logger.info(f"Player {player_id} rolled doubles ({dice1},{dice2}) to get out of jail.")
                     # Proceed with normal move after getting out
                     roll_total = dice1 + dice2
                     # Fall through to movement logic below
                 elif player.jail_turns >= 3:
                      player.in_jail = False # Forced out after 3 turns
                      player.jail_turns = 0
                      player.consecutive_doubles_count = 0
                      # TODO: Force payment of $50 fine if this happens
                      fine = 50
                      payment_result = banker.player_pays_bank(player_id, fine, "Jail fine (3 turns)")
                      if not payment_result["success"]:
                           # Set expected action to manage assets for jail fine
                           game_state.expected_action_type = 'manage_assets_for_jail_fine'
                           game_state.expected_action_details = {'fine_amount': fine}
                           db.session.add(game_state)
                           db.session.commit()
                           logger.warning(f"Player {player_id} could not pay jail fine. Expecting asset management.")
                           return {"success": False, "error": "Could not pay jail fine", "dice_roll": [dice1, dice2], "doubles": doubles, "in_jail": True, "next_action": "manage_assets_or_bankrupt"} 
                      logger.info(f"Player {player_id} paid $50 fine after 3 jail turns.")
                      roll_total = dice1 + dice2
                      # Fall through to movement logic below
                 else:
                     # Still in jail, turn ends unless they rolled doubles
                     logger.info(f"Player {player_id} failed to roll doubles in jail ({dice1},{dice2}). Turns left: {3 - player.jail_turns}")
                     # Set expected action for next turn in jail
                     game_state.expected_action_type = 'jail_action_prompt' 
                     game_state.expected_action_details = {'turns_remaining': 3 - player.jail_turns}
                     db.session.add(game_state)
                     db.session.commit()
                     return {"success": True, "message": "Still in jail", "dice_roll": [dice1, dice2], "doubles": doubles, "in_jail": True, "next_action": "end_turn", "game_state": game_state.to_dict()}
            
            # --- 2. Roll Dice --- 
            dice1 = random.randint(1, 6)
            dice2 = random.randint(1, 6)
            roll_total = dice1 + dice2
            doubles = dice1 == dice2
            passed_go = False
            sent_to_jail_for_doubles = False
            logger.info(f"Player {player_id} rolled {dice1} + {dice2} = {roll_total} (Doubles: {doubles})")

            # --- 3. Handle Doubles --- 
            if doubles:
                player.consecutive_doubles_count += 1
                if player.consecutive_doubles_count >= MAX_DOUBLES:
                    logger.warning(f"Player {player_id} rolled {MAX_DOUBLES} doubles. Sending to jail.")
                    # Send to jail immediately
                    send_jail_result = special_space_controller.send_to_jail(player_id) # Use controller method
                    sent_to_jail_for_doubles = True
                    new_position = JAIL_POSITION # Overwrite potential move
                    player.consecutive_doubles_count = 0 # Reset counter
                    # Clear expected action as turn ends abruptly
                    game_state.expected_action_type = None 
                    game_state.expected_action_details = None
                    db.session.add(game_state)
                    db.session.commit() # Commit jail state
                    return {
                        "success": True, 
                        "message": f"Rolled {MAX_DOUBLES} doubles! Go to jail.",
                        "dice_roll": [dice1, dice2],
                        "doubles": True, 
                        "sent_to_jail": True,
                        "new_position": new_position,
                        "next_action": "end_turn", # Turn ends immediately
                        "game_state": game_state.to_dict()
                    }
            else:
                player.consecutive_doubles_count = 0 # Reset counter if not doubles

            # --- 4. Calculate Movement & Pass GO --- 
            current_position = player.position
            new_position = (current_position + roll_total) % BOARD_SIZE
            
            if new_position < current_position:
                logger.info(f"Player {player_id} passed GO.")
                passed_go = True
                salary_result = banker.bank_pays_player(player_id, GO_SALARY, "Passed GO")
                if not salary_result["success"]:
                     # This should ideally not happen unless bank logic fails
                     logger.error(f"Failed to pay GO salary to player {player_id}: {salary_result.get('error')}")
                     # Continue turn but log error

            # --- 5. Update Player Position --- 
            player.position = new_position
            db.session.add(player) # Add player changes to session
            db.session.commit() # Commit position update before determining action
            logger.info(f"Player {player_id} moved to position {new_position}.")

            # --- 6. Determine Landing Action & Set Expected State --- 
            landing_action_result = self.determine_action_for_space(player, game_state, new_position, roll_total)
            action_type = landing_action_result.get("action")

            # Set expected state based on action_type
            if action_type in ['buy_or_auction_prompt', 'draw_chance_card', 'draw_community_chest_card', 'pay_tax', 'insufficient_funds_for_rent', 'manage_assets_or_bankrupt']:
                 game_state.expected_action_type = action_type
                 # Pass relevant details needed for the action prompt/handler
                 details = {}
                 if action_type == 'buy_or_auction_prompt':
                     details['property_id'] = landing_action_result.get('property_id')
                 elif action_type == 'pay_tax':
                     details['tax_details'] = landing_action_result.get('tax_details')
                 elif action_type == 'insufficient_funds_for_rent':
                     details['rent_details'] = landing_action_result # Pass the whole result
                 elif action_type == 'manage_assets_or_bankrupt': # Generic asset management prompt
                     details['reason'] = landing_action_result.get('reason', 'unknown') # e.g., 'rent', 'tax', 'fine'
                     details['amount_due'] = landing_action_result.get('required', 0)
                 # Add details for card draws if needed (e.g., the space name)
                 game_state.expected_action_details = details
                 db.session.add(game_state)
                 db.session.commit() # Commit the expected action state
            else:
                 # If action is passive or resolves immediately (e.g., paid_rent, went_to_jail), clear expected state
                 game_state.expected_action_type = None
                 game_state.expected_action_details = None
            db.session.add(game_state)
            db.session.commit()
            
            # --- 7. Prepare and Return Result --- 
            final_result = {
                "success": True,
                "dice_roll": [dice1, dice2],
                "doubles": doubles,
                "passed_go": passed_go,
                "new_position": new_position,
                "consecutive_doubles": player.consecutive_doubles_count,
                "landing_action": landing_action_result
                # Include updated game state?
                # "game_state": self.get_game_state(game_id) 
            }
            
            # Determine next_action based on doubles or landing result
            if doubles and not sent_to_jail_for_doubles:
                 final_result["next_action"] = "roll_again"
                 # Don't clear expected action if rolling again, player might need to resolve landing first
                 # e.g. Land on Chance, draw card, THEN roll again if doubles
            else:
                 final_result["next_action"] = landing_action_result.get("next_action", "end_turn")
                      
            # Include final game state in the result for broadcasting
            final_result["game_state"] = game_state.to_dict() # Use to_dict which includes expected actions

            return final_result
            
    def determine_action_for_space(self, player, game_state, position, dice_roll_total=None):
        """Determine the necessary action when a player lands on a specific board position."""
        with self.app.app_context(): # Ensure app context for DB access and controller calls
            banker = current_app.config.get('banker')
            special_space_controller = current_app.config.get('special_space_controller')
            if not banker or not special_space_controller:
                 logger.error("Missing Banker or SpecialSpaceController dependency in determine_action_for_space")
                 return {"action": "error", "error": "Server configuration error"}

            # Check for Special Space first
            special_space = SpecialSpace.query.filter_by(position=position).first()
            if special_space:
                space_type = special_space.space_type
                logger.info(f"Player {player.id} landed on Special Space: {special_space.name} (Type: {space_type}) at {position}")
                if space_type == "go" or space_type == "jail" or space_type == "free_parking": # Passive landing spaces
                    return {"action": "passive_space", "space_name": special_space.name}
                elif space_type == "go_to_jail":
                     send_jail_result = special_space_controller.send_to_jail(player.id) # Use controller
                     # Turn should end after going to jail
                     return {"action": "went_to_jail", "message": "Went to Jail!", "next_action": "end_turn"}
                elif space_type == "chance" or space_type == "community_chest":
                     # The controller will handle drawing and executing the card via socket event
                     return {"action": f"draw_{space_type}_card", "space_name": special_space.name}
                elif space_type == "tax":
                     # The controller will handle tax payment via socket event or direct call
                     tax_details = special_space.get_action_data() # Assumes method exists
                     return {"action": "pay_tax", "space_name": special_space.name, "tax_details": tax_details}
                else:
                     logger.warning(f"Unhandled special space type: {space_type} at position {position}")
                     return {"action": "unknown_special_space", "space_type": space_type}

            # Check for Property
            property_obj = Property.query.filter_by(position=position, game_id=game_state.game_id).first()
            if property_obj:
                logger.info(f"Player {player.id} landed on Property: {property_obj.name} at {position}")
                if property_obj.owner_id is None:
                    # Property is unowned
                    return {
                        "action": "buy_or_auction_prompt", 
                        "property_id": property_obj.id, 
                        "property_name": property_obj.name,
                        "cost": property_obj.price
                    }
                elif property_obj.owner_id == player.id:
                # Landed on own property
                    return {"action": "landed_on_own_property", "property_name": property_obj.name}
                else:
                    # Property owned by another player
                    if property_obj.is_mortgaged:
                        return {"action": "landed_on_mortgaged_property", "property_name": property_obj.name, "owner_id": property_obj.owner_id}
                    else:
                        # Calculate and process rent
                        rent_amount = self._calculate_rent(property_obj, dice_roll_total, game_state.game_id)
                        owner = Player.query.get(property_obj.owner_id)
                        if not owner:
                            logger.error(f"Owner (ID: {property_obj.owner_id}) not found for property {property_obj.id}. Cannot process rent.")
                            return {"action": "error", "error": "Property owner not found"}
                            
                        logger.info(f"Player {player.id} owes ${rent_amount} rent to Player {owner.id} for {property_obj.name}")
                        # Use banker to attempt payment
                        payment_result = banker.player_pays_player(player.id, owner.id, rent_amount, f"Rent for {property_obj.name}")
                        
                        if payment_result["success"]:
                            # Rent paid successfully
                            # Notify via socket? Controller should handle this.
                            return {
                                "action": "paid_rent", 
                                "property_name": property_obj.name, 
                                "owner_id": owner.id,
                                "owner_name": owner.username,
                                "rent_amount": rent_amount
                            }
                        else:
                            # Insufficient funds - Needs bankruptcy check / logic
                            logger.warning(f"Player {player.id} has insufficient funds to pay ${rent_amount} rent for {property_obj.name}")
                            # TODO: Trigger bankruptcy process or asset liquidation prompt
                            return {
                                "action": "insufficient_funds_for_rent", 
                                "property_name": property_obj.name, 
                                "owner_id": owner.id, 
                                "owner_name": owner.username, 
                                "rent_amount": rent_amount,
                                "required": rent_amount,
                                "available": player.cash,
                                "next_action": "manage_assets_or_bankrupt" # Indicate need for player action
                            }
            
            # If not a special space or property, it's an error in board setup
            logger.error(f"No property or special space found at position {position}")
            return {"action": "error", "error": f"Invalid board position: {position}"}

    def _calculate_rent(self, property_obj: Property, dice_roll_total: int, game_id: int) -> int:
         """Calculates the rent owed for landing on a property."""
         if not property_obj.owner_id or property_obj.is_mortgaged:
             return 0

         owner = Player.query.get(property_obj.owner_id)
         if not owner:
             return 0 # Should not happen

         prop_type = property_obj.type
         
         if prop_type == PropertyType.STREET:
             # Base rent depends on development level
             rent = property_obj.get_rent() # Use property model method
             # Check for monopoly (owner owns all properties in the group)
             owned_group_props = Property.query.filter_by(owner_id=owner.id, color_group=property_obj.color_group, game_id=game_id).count()
             total_group_props = Property.query.filter_by(color_group=property_obj.color_group, game_id=game_id).count()
             
             if owned_group_props == total_group_props and property_obj.improvement_level == 0:
                 # Double rent for monopoly on undeveloped properties
                 logger.debug(f"Monopoly detected for {property_obj.color_group}. Rent doubled for {property_obj.name}.")
                 rent *= 2
             return rent
             
         elif prop_type == PropertyType.RAILROAD:
             # Rent depends on how many railroads the owner has
             owned_railroads = Property.query.filter_by(owner_id=owner.id, type=PropertyType.RAILROAD, game_id=game_id).count()
             rent_levels = {1: 25, 2: 50, 3: 100, 4: 200} # Standard railroad rents
             return rent_levels.get(owned_railroads, 0)
             
         elif prop_type == PropertyType.UTILITY:
             # Rent depends on dice roll and number of utilities owned
             if dice_roll_total is None:
                  logger.error("Dice roll required to calculate utility rent, but not provided.")
                  return 0 # Cannot calculate rent without dice roll
                  
             owned_utilities = Property.query.filter_by(owner_id=owner.id, type=PropertyType.UTILITY, game_id=game_id).count()
             multiplier = 10 if owned_utilities >= 2 else 4
             return dice_roll_total * multiplier
             
         else:
             logger.warning(f"Unknown property type '{prop_type}' for rent calculation.")
             return 0

    # end_player_turn logic moved to GameController
    # def end_player_turn(self, player_id, game_id=1): ...

# You will need to ensure GameState model has a next_player_turn method
# and Player model has 'is_in_jail' and 'consecutive_doubles_count' fields. 