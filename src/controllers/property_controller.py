from flask_socketio import emit
import logging
from flask import request, current_app
from src.models import db
from src.models.player import Player
from src.models.property import Property
from src.models.game_state import GameState
from src.models.transaction import Transaction
from src.models.banker import Banker
import json
import datetime

logger = logging.getLogger(__name__)

# --- PropertyController Class --- 

class PropertyController:
    """Controller for managing property-related actions (buying, selling, mortgaging)."""
    
    # Assuming dependencies based on app.py instantiation
    def __init__(self, db_session, banker, event_system, socketio):
        self.db = db_session
        self.banker = banker
        self.event_system = event_system
        self.socketio = socketio
        logger.info("PropertyController initialized.")

    # --- Placeholder Methods --- 

    def buy_property(self, player_id, pin, property_id):
        """Handles the logic for a player buying a property."""
        # --- Player Authentication ---
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            logger.warning(f"Buy property failed: Invalid credentials for player {player_id}")
            return {'success': False, 'error': 'Invalid player credentials.'}

        game_state = GameState.query.get(1) # Assuming game_id = 1
        prop = Property.query.get(property_id)

        if not player or not prop or not game_state:
            return {'success': False, 'error': 'Invalid player, property, or game state.'}

        # --- Validation Checks ---
        # 1. Is it the player's turn? 
        #    (Note: This might be better handled in GameLogic before even calling this,
        #     but double-checking here adds safety)
        if game_state.current_player_id != player_id:
            logger.warning(f"Player {player_id} attempted to buy property {property_id} out of turn.")
            return {'success': False, 'error': 'Not your turn.'}

        # 2. Is the player on the correct space? 
        #    (Again, GameLogic likely ensures this, but check)
        if player.position != prop.position:
            logger.warning(f"Player {player_id} at {player.position} tried to buy property {prop.name} at {prop.position}.")
            return {'success': False, 'error': 'You are not on the property space.'}

        # 3. Is the property actually unowned?
        if prop.owner_id is not None:
            logger.warning(f"Player {player_id} tried to buy already owned property {prop.name} (Owner: {prop.owner_id}).")
            return {'success': False, 'error': 'Property is already owned.'}

        # 4. Can the player afford the property?
        property_cost = prop.current_price # Use current price
        if player.money < property_cost:
            logger.info(f"Player {player_id} cannot afford property {prop.name} (Cost: {property_cost}, Cash: {player.money}).")
            return {'success': False, 'error': 'Insufficient funds.', 'cost': property_cost, 'cash': player.money}

        # --- Perform Purchase --- 
        try:
            # Use Banker to handle the transaction
            transaction_result = self.banker.player_pays_bank(player_id, property_cost, f"Purchase of {prop.name}")
            
            if not transaction_result['success']:
                # This shouldn't happen if the cash check above passed, but handle defensively
                logger.error(f"Banker transaction failed for buying property {prop.id} by player {player_id}: {transaction_result.get('error')}")
                return {'success': False, 'error': transaction_result.get('error', 'Transaction failed')}
            
            # Assign property ownership
            prop.owner_id = player_id
            self.db.session.add(prop)
            self.db.session.commit()
            
            logger.info(f"Player {player_id} successfully bought property {prop.name} (ID: {prop.id}) for ${property_cost}. New balance: ${player.money}")

            # --- Return Success --- 
            # Refresh player data to get updated cash
            player = Player.query.get(player_id) 
            return {
                'success': True,
                'message': f'Successfully purchased {prop.name}!',
                'property_id': prop.id,
                'property_name': prop.name,
                'new_owner_id': player_id,
                'cost': property_cost,
                'new_cash': player.money 
            }

        except Exception as e:
            self.db.session.rollback() # Rollback DB changes on error
            logger.error(f"Error buying property {property_id} for player {player_id}: {e}", exc_info=True)
            return {'success': False, 'error': f'An internal error occurred: {str(e)}'}

    def mortgage_property(self, player_id, pin, property_id):
        """Handles the logic for mortgaging a property."""
        # --- Player Authentication & Validation ---
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            logger.warning(f"Mortgage property failed: Invalid credentials for player {player_id}")
            return {'success': False, 'error': 'Invalid player credentials.'}
            
        prop = Property.query.get(property_id)
        if not prop:
            return {'success': False, 'error': 'Property not found.'}
            
        if prop.owner_id != player_id:
            logger.warning(f"Player {player_id} attempted to mortgage property {prop.id} they don't own.")
            return {'success': False, 'error': 'You do not own this property.'}
        
        if prop.is_mortgaged:
            logger.warning(f"Player {player_id} attempted to mortgage already mortgaged property {prop.id}.")
            return {'success': False, 'error': 'Property is already mortgaged.'}
            
        # TODO: Add check for improvements - cannot mortgage if improved?
        # if prop.improvement_level > 0:
        #     return {'success': False, 'error': 'Cannot mortgage property with improvements.'}

        mortgage_value = prop.get_mortgage_value() # Use method from Property model

        # --- Perform Mortgage --- 
        try:
            # Use Banker to handle the transaction (Bank gives money to player)
            transaction_result = self.banker.bank_pays_player(player_id, mortgage_value, f"Mortgage of {prop.name}")

            if not transaction_result['success']:
                 logger.error(f"Banker transaction failed for mortgaging property {prop.id} by player {player_id}: {transaction_result.get('error')}")
                 return {'success': False, 'error': transaction_result.get('error', 'Transaction failed')}

            prop.is_mortgaged = True
            self.db.session.add(prop)
            self.db.session.commit()

            logger.info(f"Player {player_id} successfully mortgaged property {prop.name} (ID: {prop.id}) for ${mortgage_value}. New balance: ${player.money}")

            # Refresh player data
            player = Player.query.get(player_id)
            return {
                'success': True,
                'message': f'Successfully mortgaged {prop.name}!',
                'property_id': prop.id,
                'property_name': prop.name,
                'mortgage_value': mortgage_value,
                'new_cash': player.money,
                'is_mortgaged': prop.is_mortgaged
            }

        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error mortgaging property {property_id} for player {player_id}: {e}", exc_info=True)
            return {'success': False, 'error': f'An internal error occurred: {str(e)}'}

    def unmortgage_property(self, player_id, pin, property_id):
        """Handles the logic for unmortgaging a property."""
         # --- Player Authentication & Validation ---
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            logger.warning(f"Unmortgage property failed: Invalid credentials for player {player_id}")
            return {'success': False, 'error': 'Invalid player credentials.'}
            
        prop = Property.query.get(property_id)
        if not prop:
            return {'success': False, 'error': 'Property not found.'}
            
        if prop.owner_id != player_id:
            logger.warning(f"Player {player_id} attempted to unmortgage property {prop.id} they don't own.")
            return {'success': False, 'error': 'You do not own this property.'}
        
        if not prop.is_mortgaged:
            logger.warning(f"Player {player_id} attempted to unmortgage property {prop.id} that is not mortgaged.")
            return {'success': False, 'error': 'Property is not mortgaged.'}

        unmortgage_cost = prop.get_unmortgage_cost() # Use method from Property model

        if player.money < unmortgage_cost:
             logger.info(f"Player {player_id} cannot afford to unmortgage property {prop.name} (Cost: {unmortgage_cost}, Cash: {player.money}).")
             return {'success': False, 'error': 'Insufficient funds to unmortgage.', 'cost': unmortgage_cost, 'cash': player.money}

        # --- Perform Unmortgage --- 
        try:
            # Use Banker to handle the transaction (Player pays bank)
            transaction_result = self.banker.player_pays_bank(player_id, unmortgage_cost, f"Unmortgage of {prop.name}")
            
            if not transaction_result['success']:
                 logger.error(f"Banker transaction failed for unmortgaging property {prop.id} by player {player_id}: {transaction_result.get('error')}")
                 return {'success': False, 'error': transaction_result.get('error', 'Transaction failed')}

            prop.is_mortgaged = False
            self.db.session.add(prop)
            self.db.session.commit()

            logger.info(f"Player {player_id} successfully unmortgaged property {prop.name} (ID: {prop.id}) for ${unmortgage_cost}. New balance: ${player.money}")

            # Refresh player data
            player = Player.query.get(player_id)
            return {
                'success': True,
                'message': f'Successfully unmortgaged {prop.name}!',
                'property_id': prop.id,
                'property_name': prop.name,
                'unmortgage_cost': unmortgage_cost,
                'new_cash': player.money,
                'is_mortgaged': prop.is_mortgaged
            }

        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error unmortgaging property {property_id} for player {player_id}: {e}", exc_info=True)
            return {'success': False, 'error': f'An internal error occurred: {str(e)}'}

    def repair_property(self, player_id, pin, property_id, repair_amount=None):
        """Handles the logic for repairing a damaged property."""
         # --- Player Authentication & Validation ---
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            logger.warning(f"Repair property failed: Invalid credentials for player {player_id}")
            return {'success': False, 'error': 'Invalid player credentials.'}
            
        prop = Property.query.get(property_id)
        if not prop:
            return {'success': False, 'error': 'Property not found.'}
            
        if prop.owner_id != player_id:
            logger.warning(f"Player {player_id} attempted to repair property {prop.id} they don't own.")
            return {'success': False, 'error': 'You do not own this property.'}
        
        if prop.damage_amount <= 0:
             logger.info(f"Player {player_id} attempted to repair property {prop.id} with no damage.")
             return {'success': False, 'error': 'Property is not damaged.'}

        # Determine repair cost
        actual_repair_cost = repair_amount if repair_amount is not None else prop.damage_amount
        
        # Validate repair amount is positive and not more than current damage
        if actual_repair_cost <= 0 or actual_repair_cost > prop.damage_amount:
             logger.warning(f"Player {player_id} attempted invalid repair amount ({actual_repair_cost}) on property {prop.id} (Damage: {prop.damage_amount})")
             return {'success': False, 'error': f'Invalid repair amount. Must be between 1 and {prop.damage_amount}.'}
             
        if player.money < actual_repair_cost:
             logger.info(f"Player {player_id} cannot afford repair cost {actual_repair_cost} for property {prop.id} (Cash: {player.money}).")
             return {'success': False, 'error': 'Insufficient funds for repair.', 'cost': actual_repair_cost, 'cash': player.money}

        # --- Perform Repair --- 
        try:
            # Assume player pays bank for repairs
            transaction_result = self.banker.player_pays_bank(player_id, actual_repair_cost, f"Repair of {prop.name}")

            if not transaction_result['success']:
                 logger.error(f"Banker transaction failed for repairing property {prop.id} by player {player_id}: {transaction_result.get('error')}")
                 return {'success': False, 'error': transaction_result.get('error', 'Transaction failed')}

            prop.damage_amount -= actual_repair_cost
            self.db.session.add(prop)
            self.db.session.commit()

            logger.info(f"Player {player_id} successfully repaired property {prop.name} (ID: {prop.id}) for ${actual_repair_cost}. Remaining damage: {prop.damage_amount}. New balance: ${player.money}")

            # Refresh player data
            player = Player.query.get(player_id)
            return {
                'success': True,
                'message': f'Successfully repaired {prop.name}!',
                'property_id': prop.id,
                'property_name': prop.name,
                'repair_cost': actual_repair_cost,
                'remaining_damage': prop.damage_amount,
                'new_cash': player.money
            }

        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error repairing property {property_id} for player {player_id}: {e}", exc_info=True)
            return {'success': False, 'error': f'An internal error occurred: {str(e)}'}

    def request_community_approval(self, player_id, pin, property_id):
        """
        Request community approval for higher-level property development.
        
        Args:
            player_id (int): The ID of the player requesting approval
            pin (str): The player's PIN for authentication
            property_id (int): The ID of the property for which to request approval
            
        Returns:
            dict: Result of the request
        """
        # Authenticate player
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            logger.warning(f"Request community approval failed: Invalid credentials for player {player_id}")
            return {'success': False, 'error': 'Invalid player credentials'}
        
        # Get property
        property_obj = Property.query.get(property_id)
        if not property_obj:
            logger.warning(f"Request community approval failed: Property {property_id} not found")
            return {'success': False, 'error': 'Property not found'}
        
        # Verify property is owned by the player
        if property_obj.owner_id != player_id:
            logger.warning(f"Request community approval failed: Player {player_id} doesn't own property {property_id}")
            return {'success': False, 'error': 'You do not own this property'}
        
        # Get game state for economic factors
        game_state = GameState.query.first()  # Assuming one game state
        
        # Calculate approval fee - based on property value and current economic conditions
        base_fee = int(property_obj.current_price * 0.10)  # 10% of property value
        if game_state and game_state.inflation_state == "boom":
            base_fee = int(base_fee * 1.25)  # 25% more expensive during boom
        elif game_state and game_state.inflation_state == "recession":
            base_fee = int(base_fee * 0.75)  # 25% cheaper during recession
        
        # Check if player can afford the fee
        if player.money < base_fee:
            logger.info(f"Request community approval failed: Player {player_id} can't afford fee ${base_fee}")
            return {
                'success': False,
                'error': 'Insufficient funds for approval request',
                'required': base_fee,
                'available': player.money
            }
        
        # Charge the player
        transaction_result = self.banker.player_pays_bank(player_id, base_fee, "Community approval request fee")
        if not transaction_result.get('success', False):
            logger.error(f"Banking transaction failed during community approval request: {transaction_result.get('error')}")
            return {'success': False, 'error': 'Payment processing failed'}
        
        # Process the approval request
        result = property_obj.request_community_approval(game_state)
        
        # Add detail to the result
        result['fee'] = base_fee
        result['property_name'] = property_obj.name
        
        # Log the result
        if result.get('success', False):
            logger.info(f"Community approval granted for property {property_id} at a cost of ${base_fee}")
            
            # Send a socket event
            if self.socketio:
                self.socketio.emit('community_approval_granted', {
                    'player_id': player_id,
                    'player_name': player.username,
                    'property_id': property_id,
                    'property_name': property_obj.name,
                    'fee': base_fee,
                    'approval_chance': result.get('approval_chance', 50),
                    'message': result.get('message', 'Community approval granted!')
                })
                
                # Update player money display
                self.socketio.emit('player_money_updated', {
                    'player_id': player_id,
                    'old_balance': player.money + base_fee,
                    'new_balance': player.money,
                    'change': -base_fee,
                    'reason': 'community_approval_fee'
                })
        else:
            logger.info(f"Community approval denied for property {property_id} despite fee of ${base_fee}")
            
            # Send a socket event
            if self.socketio:
                self.socketio.emit('community_approval_denied', {
                    'player_id': player_id,
                    'player_name': player.username,
                    'property_id': property_id,
                    'property_name': property_obj.name,
                    'fee': base_fee,
                    'approval_chance': result.get('approval_chance', 50),
                    'reason': result.get('reason', 'Community approval denied')
                })
        
        return result

    def commission_environmental_study(self, player_id, pin, property_id):
        """
        Commission an environmental study for highest-level property development.
        
        Args:
            player_id (int): The ID of the player commissioning the study
            pin (str): The player's PIN for authentication
            property_id (int): The ID of the property for which to commission the study
            
        Returns:
            dict: Result of the environmental study
        """
        # Authenticate player
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            logger.warning(f"Environmental study failed: Invalid credentials for player {player_id}")
            return {'success': False, 'error': 'Invalid player credentials'}
        
        # Get property
        property_obj = Property.query.get(property_id)
        if not property_obj:
            logger.warning(f"Environmental study failed: Property {property_id} not found")
            return {'success': False, 'error': 'Property not found'}
        
        # Verify property is owned by the player
        if property_obj.owner_id != player_id:
            logger.warning(f"Environmental study failed: Player {player_id} doesn't own property {property_id}")
            return {'success': False, 'error': 'You do not own this property'}
        
        # Get game state for economic factors
        game_state = GameState.query.first()  # Assuming one game state
        
        # Calculate study fee - based on property value and current economic conditions
        base_fee = int(property_obj.current_price * 0.15)  # 15% of property value
        if game_state and game_state.inflation_state == "boom":
            base_fee = int(base_fee * 1.25)  # 25% more expensive during boom
        elif game_state and game_state.inflation_state == "recession":
            base_fee = int(base_fee * 0.75)  # 25% cheaper during recession
        
        # Check if player can afford the fee
        if player.money < base_fee:
            logger.info(f"Environmental study failed: Player {player_id} can't afford fee ${base_fee}")
            return {
                'success': False,
                'error': 'Insufficient funds for environmental study',
                'required': base_fee,
                'available': player.money
            }
        
        # Charge the player
        transaction_result = self.banker.player_pays_bank(player_id, base_fee, "Environmental study fee")
        if not transaction_result.get('success', False):
            logger.error(f"Banking transaction failed during environmental study: {transaction_result.get('error')}")
            return {'success': False, 'error': 'Payment processing failed'}
        
        # Process the environmental study
        result = property_obj.commission_environmental_study(game_state)
        
        # Add detail to the result
        result['fee'] = base_fee
        result['property_name'] = property_obj.name
        
        # Log the result
        if result.get('success', False):
            logger.info(f"Environmental study completed for property {property_id} at a cost of ${base_fee}")
            
            # Send a socket event
            if self.socketio:
                self.socketio.emit('environmental_study_completed', {
                    'player_id': player_id,
                    'player_name': player.username,
                    'property_id': property_id,
                    'property_name': property_obj.name,
                    'fee': base_fee,
                    'expires': result.get('expires'),
                    'message': result.get('message', 'Environmental study completed!')
                })
                
                # Update player money display
                self.socketio.emit('player_money_updated', {
                    'player_id': player_id,
                    'old_balance': player.money + base_fee,
                    'new_balance': player.money,
                    'change': -base_fee,
                    'reason': 'environmental_study_fee'
                })
        else:
            logger.info(f"Environmental study failed for property {property_id}: {result.get('reason')}")
            
            # Send a socket event
            if self.socketio:
                self.socketio.emit('environmental_study_failed', {
                    'player_id': player_id,
                    'player_name': player.username,
                    'property_id': property_id,
                    'property_name': property_obj.name,
                    'fee': base_fee,
                    'reason': result.get('reason', 'Environmental study failed')
                })
        
        return result

    def handle_property_improvement(self, game_id, player_id, property_id, improvement_type="house"):
        """
        Handles the process of improving a property by adding a house or hotel.
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who is improving the property.
            property_id (str): The ID of the property to improve.
            improvement_type (str): The type of improvement ("house" or "hotel").
            
        Returns:
            dict: A dictionary with the results of the improvement action.
        """
        try:
            logger.info(f"Player {player_id} attempting to add {improvement_type} to property {property_id} in game {game_id}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logger.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logger.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get the property
            property_obj = Property.query.get(property_id)
            if not property_obj:
                logger.error(f"Property {property_id} not found")
                return {"success": False, "error": "Property not found"}
            
            # Verify the player owns the property
            if property_obj.owner_id != player_id:
                logger.warning(f"Player {player_id} does not own property {property_id}")
                return {"success": False, "error": "You don't own this property"}
            
            # Verify the property is not mortgaged
            if property_obj.is_mortgaged:
                logger.warning(f"Property {property_id} is mortgaged and cannot be improved")
                return {"success": False, "error": "Cannot improve a mortgaged property"}
            
            # Get player state from game_state
            player_state = next((p for p in game_state.players if p.get("id") == player_id), None)
            if not player_state:
                logger.error(f"Player state for {player_id} not found in game {game_id}")
                return {"success": False, "error": "Player state not found"}
            
            # Verify the property can be improved (has monopoly)
            # Check if player owns all properties in the group
            properties_in_group = Property.query.filter_by(group_name=property_obj.group_name).all()
            all_owned = all(prop.owner_id == player_id for prop in properties_in_group)
            if not all_owned:
                logger.warning(f"Player {player_id} does not own all properties in group {property_obj.group_name}")
                return {"success": False, "error": "You need to own all properties in the color group to improve"}
            
            # Check for even development rule
            if not self._check_even_development(game_state, player_id, property_id, improvement_type):
                return {"success": False, "error": "Properties must be developed evenly across a color group"}
            
            # Verify improvement type and corresponding requirements
            houses = property_obj.houses
            hotels = property_obj.hotels
            
            if improvement_type == "hotel":
                # Check if property already has a hotel
                if hotels > 0:
                    logger.warning(f"Property {property_id} already has a hotel")
                    return {"success": False, "error": "Property already has a hotel"}
                
                # Check if property has 4 houses (required before building a hotel)
                if houses != 4:
                    logger.warning(f"Property {property_id} needs 4 houses before building a hotel")
                    return {"success": False, "error": "Need 4 houses before building a hotel"}
                
                # Check if there are available hotels
                available_hotels = game_state.settings.get("available_hotels", 12)
                if available_hotels <= 0:
                    logger.warning(f"No hotels available in the bank")
                    return {"success": False, "error": "No hotels available in the bank"}
                
                # Calculate cost
                cost = property_obj.hotel_cost
                
            else:  # building a house
                # Check if property already has maximum houses (4)
                if houses >= 4:
                    logger.warning(f"Property {property_id} already has maximum houses (4)")
                    return {"success": False, "error": "Property already has maximum houses"}
                
                # Check if property has a hotel
                if hotels > 0:
                    logger.warning(f"Property {property_id} has a hotel and cannot add houses")
                    return {"success": False, "error": "Property has a hotel and cannot add houses"}
                
                # Check if there are available houses
                available_houses = game_state.settings.get("available_houses", 32)
                if available_houses <= 0:
                    logger.warning(f"No houses available in the bank")
                    return {"success": False, "error": "No houses available in the bank"}
                
                # Calculate cost
                cost = property_obj.house_cost
            
            # Check if player has enough money
            if player_state.get("balance", 0) < cost:
                logger.warning(f"Player {player_id} has insufficient funds ({player_state.get('balance', 0)}) for {improvement_type} ({cost})")
                return {"success": False, "error": f"Insufficient funds (need ${cost})"}
            
            # Process the improvement
            if improvement_type == "hotel":
                # Convert 4 houses to a hotel
                property_obj.houses = 0
                property_obj.hotels = 1
                
                # Return houses to the bank
                game_state.settings["available_houses"] = game_state.settings.get("available_houses", 32) + 4
                
                # Take a hotel from the bank
                game_state.settings["available_hotels"] = game_state.settings.get("available_hotels", 12) - 1
                
            else:  # building a house
                # Add a house
                property_obj.houses = houses + 1
                
                # Take a house from the bank
                game_state.settings["available_houses"] = game_state.settings.get("available_houses", 32) - 1
            
            # Update the rent based on new improvement level
            property_obj.update_rent()
            
            # Deduct the cost from player's balance
            player_state["balance"] -= cost
            player.money -= cost
            
            # Add to game log
            message = f"Player {player.username} built a {improvement_type} on {property_obj.name} for ${cost}"
            log_entry = {
                "type": "property_improvement",
                "player_id": player_id,
                "property_id": property_id,
                "improvement_type": improvement_type,
                "cost": cost,
                "houses": property_obj.houses,
                "hotels": property_obj.hotels,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Update game log
            current_log = json.loads(game_state.game_log) if game_state.game_log else []
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Save changes to the database
            self.db.session.add(property_obj)
            self.db.session.add(player)
            self.db.session.add(game_state)
            self.db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('property_improved', {
                'game_id': game_id,
                'player_id': player_id,
                'property_id': property_id,
                'property_name': property_obj.name,
                'improvement_type': improvement_type,
                'houses': property_obj.houses,
                'hotels': property_obj.hotels,
                'cost': cost,
                'new_rent': property_obj.rent,
                'player_balance': player_state.get('balance')
            }, room=game_id)
            
            logger.info(message)
            return {
                "success": True,
                "action": "property_improvement",
                "player_id": player_id,
                "property_id": property_id,
                "improvement_type": improvement_type,
                "cost": cost,
                "message": message
            }
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error improving property: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _check_even_development(self, game_state, player_id, property_id, improvement_type):
        """
        Checks if the improvement follows the even development rule.
        Properties in a color group must be developed evenly.
        
        Args:
            game_state (GameState): The current game state.
            player_id (str): The ID of the player.
            property_id (str): The ID of the property to improve.
            improvement_type (str): The type of improvement.
            
        Returns:
            bool: True if the improvement follows the even development rule, False otherwise.
        """
        # Get the property
        property_data = next((p for p in game_state.properties if p.get("id") == property_id), None)
        if not property_data:
            return False
        
        # Get the property group
        property_group = property_data.get("group")
        if not property_group:
            return False
        
        # Get all properties in the same group owned by the player
        group_properties = [p for p in game_state.properties 
                           if p.get("group") == property_group and p.get("owner_id") == player_id]
        
        if not group_properties:
            return False
        
        # Get current houses count for the property
        current_houses = property_data.get("houses", 0)
        
        if improvement_type == "house":
            # Check if adding a house follows the even development rule
            for p in group_properties:
                if p.get("id") != property_id and p.get("houses", 0) < current_houses:
                    # Another property in the group has fewer houses
                    return False
        
        elif improvement_type == "hotel":
            # Check if all properties in the group have 4 houses before building a hotel
            for p in group_properties:
                if p.get("id") != property_id and p.get("houses", 0) < 4 and p.get("hotels", 0) == 0:
                    # Another property in the group has fewer than 4 houses
                    return False
        
        return True
    
    def _update_property_rent(self, property_data):
        """
        Updates the property rent based on the current improvement level.
        
        Args:
            property_data (dict): The property data to update.
        """
        houses = property_data.get("houses", 0)
        hotels = property_data.get("hotels", 0)
        base_rent = property_data.get("base_rent", 0)
        
        if hotels > 0:
            # If there's a hotel, use the hotel rent
            property_data["rent"] = property_data.get("hotel_rent", base_rent * 5)
        elif houses > 0:
            # If there are houses, calculate rent based on house count
            house_rents = [
                property_data.get("house1_rent", base_rent * 1.5),
                property_data.get("house2_rent", base_rent * 2),
                property_data.get("house3_rent", base_rent * 3),
                property_data.get("house4_rent", base_rent * 4)
            ]
            
            # Use the appropriate rent based on house count (0-indexed)
            property_data["rent"] = house_rents[houses - 1]
        else:
            # No improvements, use base rent
            property_data["rent"] = base_rent

    def handle_sell_improvement(self, game_id, player_id, property_id, improvement_type="house"):
        """
        Handles the process of selling a property improvement (house or hotel).
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who is selling the improvement.
            property_id (str): The ID of the property to sell an improvement from.
            improvement_type (str): The type of improvement to sell ("house" or "hotel").
            
        Returns:
            dict: A dictionary with the results of the selling action.
        """
        try:
            logging.info(f"Player {player_id} attempting to sell {improvement_type} from property {property_id} in game {game_id}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get the property
            property_data = next((p for p in game_state.properties if p.get("id") == property_id), None)
            if not property_data:
                logging.error(f"Property {property_id} not found in game {game_id}")
                return {"success": False, "error": "Property not found"}
            
            # Verify the player owns the property
            if property_data.get("owner_id") != player_id:
                logging.warning(f"Player {player_id} does not own property {property_id}")
                return {"success": False, "error": "You don't own this property"}
            
            # Verify improvement exists on the property
            houses = property_data.get("houses", 0)
            hotels = property_data.get("hotels", 0)
            
            if improvement_type == "hotel":
                if hotels <= 0:
                    logging.warning(f"Property {property_id} has no hotel to sell")
                    return {"success": False, "error": "Property has no hotel to sell"}
            else:  # selling a house
                if houses <= 0:
                    logging.warning(f"Property {property_id} has no houses to sell")
                    return {"success": False, "error": "Property has no houses to sell"}
            
            # Check for even development rule in reverse
            if not self._check_even_selling(game_state, player_id, property_id, improvement_type):
                return {"success": False, "error": "Properties must be sold evenly across a color group"}
            
            # Calculate sale value (half of the original cost)
            if improvement_type == "hotel":
                sale_value = int(property_data.get("hotel_cost", 0) / 2)
            else:  # selling a house
                sale_value = int(property_data.get("house_cost", 0) / 2)
            
            # Process the sale
            if improvement_type == "hotel":
                # If there are enough houses in the bank, convert hotel to 4 houses
                available_houses = game_state.rules.get("available_houses", 32)
                
                if available_houses >= 4:
                    # Convert hotel to 4 houses
                    property_data["hotels"] = 0
                    property_data["houses"] = 4
                    
                    # Return the hotel to the bank
                    game_state.rules["available_hotels"] = game_state.rules.get("available_hotels", 12) + 1
                    
                    # Take 4 houses from the bank
                    game_state.rules["available_houses"] = available_houses - 4
                else:
                    # Not enough houses in the bank, just remove the hotel
                    property_data["hotels"] = 0
                    
                    # Return the hotel to the bank
                    game_state.rules["available_hotels"] = game_state.rules.get("available_hotels", 12) + 1
                    
                    # Log that houses weren't restored due to shortage
                    logging.warning(f"Hotel sold but not converted to houses due to house shortage in bank")
            else:  # selling a house
                # Remove a house
                property_data["houses"] = houses - 1
                
                # Return the house to the bank
                game_state.rules["available_houses"] = game_state.rules.get("available_houses", 32) + 1
            
            # Update the rent based on new improvement level
            self._update_property_rent(property_data)
            
            # Get the player state
            player_state = next((p for p in game_state.players if p.get("id") == player_id), None)
            if not player_state:
                logging.error(f"Player state for {player_id} not found in game {game_id}")
                return {"success": False, "error": "Player state not found"}
            
            # Add the sale value to player's balance
            player_state["balance"] += sale_value
            
            # Add to game log
            message = f"Player {player.username} sold a {improvement_type} from {property_data.get('name')} for ${sale_value}"
            log_entry = {
                "type": "property_improvement_sale",
                "player_id": player_id,
                "property_id": property_id,
                "improvement_type": improvement_type,
                "amount": sale_value,
                "houses": property_data.get("houses", 0),
                "hotels": property_data.get("hotels", 0),
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Update game log
            current_log = json.loads(game_state.game_log) if game_state.game_log else []
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Update the game state
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('property_improvement_sold', {
                'game_id': game_id,
                'player_id': player_id,
                'property_id': property_id,
                'property_name': property_data.get('name'),
                'improvement_type': improvement_type,
                'houses': property_data.get('houses', 0),
                'hotels': property_data.get('hotels', 0),
                'amount': sale_value,
                'new_rent': property_data.get('rent'),
                'player_balance': player_state.get('balance')
            }, room=game_id)
            
            logging.info(message)
            return {
                "success": True,
                "action": "property_improvement_sale",
                "player_id": player_id,
                "property_id": property_id,
                "improvement_type": improvement_type,
                "amount": sale_value,
                "message": message
            }
            
        except Exception as e:
            logging.error(f"Error selling property improvement: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _check_even_selling(self, game_state, player_id, property_id, improvement_type):
        """
        Checks if selling an improvement follows the even development rule in reverse.
        Properties in a color group must be sold evenly.
        
        Args:
            game_state (GameState): The current game state.
            player_id (str): The ID of the player.
            property_id (str): The ID of the property to sell an improvement from.
            improvement_type (str): The type of improvement to sell.
            
        Returns:
            bool: True if selling the improvement follows the even development rule, False otherwise.
        """
        # Get the property
        property_data = next((p for p in game_state.properties if p.get("id") == property_id), None)
        if not property_data:
            return False
        
        # Get the property group
        property_group = property_data.get("group")
        if not property_group:
            return False
        
        # Get all properties in the same group owned by the player
        group_properties = [p for p in game_state.properties 
                           if p.get("group") == property_group and p.get("owner_id") == player_id]
        
        if not group_properties:
            return False
        
        # Get current houses/hotels count for the property
        current_houses = property_data.get("houses", 0)
        current_hotels = property_data.get("hotels", 0)
        
        if improvement_type == "house":
            # Check if removing a house follows the even development rule in reverse
            new_house_count = current_houses - 1
            
            for p in group_properties:
                if p.get("id") != property_id and p.get("houses", 0) > new_house_count:
                    # Another property in the group would have more houses
                    return False
        
        elif improvement_type == "hotel":
            # For hotels, always allow selling as it converts back to houses
            # This is actually more complex in practice because we'd need to check 
            # if there are enough houses in the bank to perform the conversion,
            # but that logic is handled in the main method
            pass
        
        return True

    def get_all_properties(self):
        """Get all properties in the database"""
        try:
            properties = Property.query.all()
            
            # If no properties exist, initialize default properties
            if not properties:
                self.initialize_default_properties()
                properties = Property.query.all()
            
            return {
                "success": True,
                "properties": [property.to_dict() for property in properties]
            }
        except Exception as e:
            self.logger.error(f"Error getting all properties: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def initialize_default_properties(self):
        """Initialize default properties if none exist"""
        try:
            self.logger.info("Initializing default properties")
            
            # Check if properties already exist
            if Property.query.count() > 0:
                self.logger.info("Properties already exist, skipping initialization")
                return
            
            # Basic property types
            property_colors = [
                {"name": "Brown", "houses_price": 50},
                {"name": "Light Blue", "houses_price": 50},
                {"name": "Pink", "houses_price": 100},
                {"name": "Orange", "houses_price": 100},
                {"name": "Red", "houses_price": 150},
                {"name": "Yellow", "houses_price": 150},
                {"name": "Green", "houses_price": 200},
                {"name": "Blue", "houses_price": 200}
            ]
            
            # Create some default properties
            properties_data = [
                {"name": "Mediterranean Avenue", "price": 60, "position": 1, "group": "Brown"},
                {"name": "Baltic Avenue", "price": 60, "position": 3, "group": "Brown"},
                {"name": "Oriental Avenue", "price": 100, "position": 6, "group": "Light Blue"},
                {"name": "Vermont Avenue", "price": 100, "position": 8, "group": "Light Blue"},
                {"name": "Connecticut Avenue", "price": 120, "position": 9, "group": "Light Blue"},
                {"name": "St. Charles Place", "price": 140, "position": 11, "group": "Pink"},
                {"name": "States Avenue", "price": 140, "position": 13, "group": "Pink"},
                {"name": "Virginia Avenue", "price": 160, "position": 14, "group": "Pink"},
                {"name": "St. James Place", "price": 180, "position": 16, "group": "Orange"},
                {"name": "Tennessee Avenue", "price": 180, "position": 18, "group": "Orange"},
                {"name": "New York Avenue", "price": 200, "position": 19, "group": "Orange"},
                {"name": "Kentucky Avenue", "price": 220, "position": 21, "group": "Red"},
                {"name": "Indiana Avenue", "price": 220, "position": 23, "group": "Red"},
                {"name": "Illinois Avenue", "price": 240, "position": 24, "group": "Red"},
                {"name": "Atlantic Avenue", "price": 260, "position": 26, "group": "Yellow"},
                {"name": "Ventnor Avenue", "price": 260, "position": 27, "group": "Yellow"},
                {"name": "Marvin Gardens", "price": 280, "position": 29, "group": "Yellow"},
                {"name": "Pacific Avenue", "price": 300, "position": 31, "group": "Green"},
                {"name": "North Carolina Avenue", "price": 300, "position": 32, "group": "Green"},
                {"name": "Pennsylvania Avenue", "price": 320, "position": 34, "group": "Green"},
                {"name": "Park Place", "price": 350, "position": 37, "group": "Blue"},
                {"name": "Boardwalk", "price": 400, "position": 39, "group": "Blue"}
            ]
            
            # Create properties
            for prop_data in properties_data:
                group = prop_data["group"]
                color_data = next((c for c in property_colors if c["name"] == group), None)
                houses_price = color_data["houses_price"] if color_data else 100
                
                # Calculate rents based on price
                base_rent = int(prop_data["price"] * 0.1)  # 10% of price
                
                # Create property
                new_property = Property(
                    name=prop_data["name"],
                    price=prop_data["price"],
                    current_price=prop_data["price"],
                    position=prop_data["position"],
                    group=prop_data["group"],
                    rent=base_rent,
                    rent_1_house=base_rent * 5,
                    rent_2_houses=base_rent * 15,
                    rent_3_houses=base_rent * 30,
                    rent_4_houses=base_rent * 40,
                    rent_hotel=base_rent * 50,
                    houses_price=houses_price,
                    is_mortgaged=False,
                    houses=0,
                    owner_id=None
                )
                
                db.session.add(new_property)
            
            # Add railroad properties
            railroads = [
                {"name": "Reading Railroad", "position": 5},
                {"name": "Pennsylvania Railroad", "position": 15},
                {"name": "B&O Railroad", "position": 25},
                {"name": "Short Line", "position": 35}
            ]
            
            for railroad in railroads:
                new_railroad = Property(
                    name=railroad["name"],
                    price=200,
                    current_price=200,
                    position=railroad["position"],
                    group="Railroad",
                    rent=25,
                    rent_1_house=50,
                    rent_2_houses=100,
                    rent_3_houses=200,
                    rent_4_houses=200,
                    rent_hotel=200,
                    houses_price=0,
                    is_mortgaged=False,
                    houses=0,
                    owner_id=None
                )
                
                db.session.add(new_railroad)
            
            # Add utility properties
            utilities = [
                {"name": "Electric Company", "position": 12},
                {"name": "Water Works", "position": 28}
            ]
            
            for utility in utilities:
                new_utility = Property(
                    name=utility["name"],
                    price=150,
                    current_price=150,
                    position=utility["position"],
                    group="Utility",
                    rent=0,  # Special calculation based on dice roll
                    rent_1_house=0,
                    rent_2_houses=0,
                    rent_3_houses=0,
                    rent_4_houses=0,
                    rent_hotel=0,
                    houses_price=0,
                    is_mortgaged=False,
                    houses=0,
                    owner_id=None
                )
                
                db.session.add(new_utility)
            
            # Commit all properties to the database
            db.session.commit()
            
            self.logger.info(f"Successfully initialized {len(properties_data) + len(railroads) + len(utilities)} properties")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing default properties: {e}")
            db.session.rollback()
            return False

# --- Registration Function --- 

def register_property_events(socketio_instance, app_config):
    """Register all property-related socket events."""
    logger.info("Registering property socket events")
    
    # Get required controllers/services from app_config
    game_controller = app_config.get('game_controller')
    property_controller = app_config.get('property_controller')
    
    if not game_controller or not property_controller:
        logger.error("Missing required controllers for property socket events")
        return
        
    @socketio_instance.on('buy_property')
    def handle_buy_property(data, *args): # Accept potential extra arguments
        """Handle player buying a property"""
        logger.info(f"handle_buy_property received data: {data}") # Log received data
        if args:
            logger.info(f"handle_buy_property received extra args: {args}") # Log extra arguments if any
            
        player_id = data.get('playerId')
        property_id = data.get('propertyId')
        sid = request.sid
        
        if not player_id or property_id is None:
            emit('property_error', {'error': 'Missing player ID or property ID'}, room=sid)
            return
            
        logger.info(f"[PropertyController] Received buy_property event from Player ID: {player_id} for Property ID: {property_id} (SID: {sid})")

        # Access controllers/services via app context (safe within handler)
        game_logic = current_app.config.get('game_logic')
        
        if not game_logic:
            emit('property_error', {'error': 'Required service unavailable'}, room=sid)
            return
            
        result = property_controller.buy_property(player_id, property_id)
        
        if result['success']:
            emit('property_bought_confirmed', result, room=sid) 
            
            game_state_instance = GameState.query.get(1)
            if game_state_instance and game_state_instance.game_id:
                 updated_game_state = game_logic.get_game_state()
                 if updated_game_state:
                     # Use the passed socketio_instance to emit globally
                     socketio_instance.emit('game_state_update', updated_game_state, room=game_state_instance.game_id)
                     logger.info(f"Broadcasted game_state_update to room {game_state_instance.game_id} after property {property_id} purchase by {player_id}")
                 else:
                     logger.error(f"Failed to get updated game state after property purchase by {player_id}.")
        else:
            emit('property_error', result, room=sid) 

    @socketio_instance.on('mortgage_property')
    def handle_mortgage_property(data):
        """Handle player mortgaging a property"""
        player_id = data.get('playerId')
        pin = data.get('pin') # Get PIN for authentication
        property_id = data.get('propertyId')
        sid = request.sid

        if not player_id or not pin or property_id is None:
            emit('property_error', {'error': 'Missing player ID, PIN, or property ID'}, room=sid)
            return

        logger.info(f"[PropertyController] Received mortgage_property event from Player ID: {player_id} for Property ID: {property_id} (SID: {sid})")

        game_logic = current_app.config.get('game_logic')
        if not game_logic:
            emit('property_error', {'error': 'Required service unavailable'}, room=sid)
            return

        # --- Expected Action Validation ---
        game_state = GameState.query.get(1) # Assuming game_id = 1
        if game_state:
            allowed_states = [None, 'roll_dice', 'roll_again', 'manage_assets_or_bankrupt', 'insufficient_funds_for_rent', 'jail_action_prompt']
            current_expected = game_state.expected_action_type
            if current_expected not in allowed_states:
                 logger.warning(f"Player {player_id} tried to mortgage property {property_id} while action '{current_expected}' was expected.")
                 emit('property_error', {'error': f"Cannot manage assets now. Expected action: {current_expected}"}, room=sid)
                 return
        else:
            logger.error("Could not retrieve GameState for expected action validation in handle_mortgage_property.")
            emit('property_error', {'error': 'Server error: Could not validate game state'}, room=sid)
            return
        # --- End Expected Action Validation ---

        result = property_controller.mortgage_property(player_id, pin, property_id)

        if result.get('success'):
            emit('property_mortgaged_confirmed', result, room=sid)
            
            # Broadcast game state update
            game_state_instance = GameState.query.get(1)
            if game_state_instance and game_state_instance.game_id:
                 updated_game_state = game_logic.get_game_state()
                 if updated_game_state:
                     socketio_instance.emit('game_state_update', updated_game_state, room=game_state_instance.game_id)
                     logger.info(f"Broadcasted game_state_update after property {property_id} mortgage by {player_id}")
        else:
            emit('property_error', result, room=sid)

    @socketio_instance.on('unmortgage_property')
    def handle_unmortgage_property(data):
        """Handle player unmortgaging a property"""
        player_id = data.get('playerId')
        pin = data.get('pin')
        property_id = data.get('propertyId')
        sid = request.sid

        if not player_id or not pin or property_id is None:
            emit('property_error', {'error': 'Missing player ID, PIN, or property ID'}, room=sid)
            return

        logger.info(f"[PropertyController] Received unmortgage_property event from Player ID: {player_id} for Property ID: {property_id} (SID: {sid})")

        game_logic = current_app.config.get('game_logic')
        if not game_logic:
            emit('property_error', {'error': 'Required service unavailable'}, room=sid)
            return

        # --- Expected Action Validation ---
        game_state = GameState.query.get(1) # Assuming game_id = 1
        if game_state:
            allowed_states = [None, 'roll_dice', 'roll_again', 'manage_assets_or_bankrupt', 'insufficient_funds_for_rent', 'jail_action_prompt']
            current_expected = game_state.expected_action_type
            if current_expected not in allowed_states:
                 logger.warning(f"Player {player_id} tried to unmortgage property {property_id} while action '{current_expected}' was expected.")
                 emit('property_error', {'error': f"Cannot manage assets now. Expected action: {current_expected}"}, room=sid)
                 return
        else:
            logger.error("Could not retrieve GameState for expected action validation in handle_unmortgage_property.")
            emit('property_error', {'error': 'Server error: Could not validate game state'}, room=sid)
            return
        # --- End Expected Action Validation ---

        result = property_controller.unmortgage_property(player_id, pin, property_id)

        if result.get('success'):
            emit('property_unmortgaged_confirmed', result, room=sid)
            
            # Broadcast game state update
            game_state_instance = GameState.query.get(1)
            if game_state_instance and game_state_instance.game_id:
                 updated_game_state = game_logic.get_game_state()
                 if updated_game_state:
                     socketio_instance.emit('game_state_update', updated_game_state, room=game_state_instance.game_id)
                     logger.info(f"Broadcasted game_state_update after property {property_id} unmortgage by {player_id}")
        else:
            emit('property_error', result, room=sid)
            
    @socketio_instance.on('repair_property')
    def handle_repair_property(data):
        """Handle player repairing a property"""
        player_id = data.get('playerId')
        pin = data.get('pin')
        property_id = data.get('propertyId')
        repair_amount = data.get('repairAmount') # Optional: allows partial repair
        sid = request.sid

        if not player_id or not pin or property_id is None:
            emit('property_error', {'error': 'Missing player ID, PIN, or property ID'}, room=sid)
            return

        logger.info(f"[PropertyController] Received repair_property event from Player ID: {player_id} for Property ID: {property_id} (Amount: {repair_amount}) (SID: {sid})")

        game_logic = current_app.config.get('game_logic')
        if not game_logic:
            emit('property_error', {'error': 'Required service unavailable'}, room=sid)
            return

        # --- Expected Action Validation ---
        game_state = GameState.query.get(1) # Assuming game_id = 1
        if game_state:
            allowed_states = [None, 'roll_dice', 'roll_again', 'manage_assets_or_bankrupt', 'insufficient_funds_for_rent', 'jail_action_prompt']
            current_expected = game_state.expected_action_type
            if current_expected not in allowed_states:
                 logger.warning(f"Player {player_id} tried to repair property {property_id} while action '{current_expected}' was expected.")
                 emit('property_error', {'error': f"Cannot manage assets now. Expected action: {current_expected}"}, room=sid)
                 return
        else:
            logger.error("Could not retrieve GameState for expected action validation in handle_repair_property.")
            emit('property_error', {'error': 'Server error: Could not validate game state'}, room=sid)
            return
        # --- End Expected Action Validation ---

        result = property_controller.repair_property(player_id, pin, property_id, repair_amount)

        if result.get('success'):
            emit('property_repaired_confirmed', result, room=sid)
            
            # Broadcast game state update
            game_state_instance = GameState.query.get(1)
            if game_state_instance and game_state_instance.game_id:
                 updated_game_state = game_logic.get_game_state()
                 if updated_game_state:
                     socketio_instance.emit('game_state_update', updated_game_state, room=game_state_instance.game_id)
                     logger.info(f"Broadcasted game_state_update after property {property_id} repair by {player_id}")
        else:
            emit('property_error', result, room=sid)

    @socketio_instance.on('improve_property')
    def handle_improve_property(data):
        """Socket event handler for improving a property"""
        player_id = data.get('player_id')
        sid = request.sid
        
        logger.info(f"[Socket] Received 'improve_property' event from player {player_id}")
        
        # Call the game controller's method
        if game_controller:
            result = game_controller.handle_improve_property(data)
            
            if result.get('success'):
                # The game controller emits the property_improved event
                # We just need to send confirmation to the requesting client
                emit('action_result', {
                    'action': 'improve_property',
                    'success': True,
                    'message': result.get('message', 'Property improved successfully')
                }, room=sid)
            else:
                emit('action_error', {
                    'action': 'improve_property',
                    'error': result.get('error', 'Failed to improve property')
                }, room=sid)
        else:
            logger.error("Game controller not available for improve_property event")
            emit('action_error', {
                'action': 'improve_property',
                'error': 'Game controller not available'
            }, room=sid)
    
    @socketio_instance.on('sell_improvement')
    def handle_sell_improvement(data):
        """Socket event handler for selling a property improvement"""
        player_id = data.get('player_id')
        sid = request.sid
        
        logger.info(f"[Socket] Received 'sell_improvement' event from player {player_id}")
        
        # Call the game controller's method
        if game_controller:
            result = game_controller.handle_sell_improvement(data)
            
            if result.get('success'):
                # The game controller emits the property_improvement_sold event
                # We just need to send confirmation to the requesting client
                emit('action_result', {
                    'action': 'sell_improvement',
                    'success': True,
                    'message': result.get('message', 'Property improvement sold successfully')
                }, room=sid)
            else:
                emit('action_error', {
                    'action': 'sell_improvement',
                    'error': result.get('error', 'Failed to sell property improvement')
                }, room=sid)
        else:
            logger.error("Game controller not available for sell_improvement event")
            emit('action_error', {
                'action': 'sell_improvement',
                'error': 'Game controller not available'
            }, room=sid)

    logger.info("Property event handlers registered within register_property_events.")

# ... (other handlers like handle_decline_property, etc. should also be moved to top-level) 