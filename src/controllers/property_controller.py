from flask_socketio import emit
import logging
from flask import request, current_app
from src.models import db
from src.models.player import Player
from src.models.property import Property
from src.models.game_state import GameState
from src.models.transaction import Transaction
from src.models.banker import Banker

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

    # Add methods for building houses/hotels, etc.

# --- Registration Function --- 

def register_property_events(socketio_instance, app_config):
    """Register property-related socket event handlers"""
    
    # Retrieve dependencies from app_config
    # Note: These might not be needed directly here if handlers access via current_app,
    # but keeping the retrieval for validation/logging.
    game_state = app_config.get('game_state_instance')
    auction_system = app_config.get('auction_system')
    banker = app_config.get('banker') 

    # Validate dependencies
    if not game_state:
        logger.error("GameState not found in app config (checked by register_property_events).")
    if not auction_system:
        logger.error("AuctionSystem not found in app config (checked by register_property_events).")
    if not banker:
        logger.error("Banker not found in app config (checked by register_property_events).")

    # --- Define handlers INSIDE the registration function --- 
        
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
        property_controller = current_app.config.get('property_controller')
        game_logic = current_app.config.get('game_logic')
        
        if not property_controller or not game_logic:
            emit('property_error', {'error': 'Required controller or service unavailable'}, room=sid)
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

        property_controller = current_app.config.get('property_controller')
        game_logic = current_app.config.get('game_logic')
        if not property_controller or not game_logic:
            emit('property_error', {'error': 'Required controller or service unavailable'}, room=sid)
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

        property_controller = current_app.config.get('property_controller')
        game_logic = current_app.config.get('game_logic')
        if not property_controller or not game_logic:
            emit('property_error', {'error': 'Required controller or service unavailable'}, room=sid)
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

        property_controller = current_app.config.get('property_controller')
        game_logic = current_app.config.get('game_logic')
        if not property_controller or not game_logic:
            emit('property_error', {'error': 'Required controller or service unavailable'}, room=sid)
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

    logger.info("Property event handlers registered within register_property_events.")

# ... (other handlers like handle_decline_property, etc. should also be moved to top-level) 