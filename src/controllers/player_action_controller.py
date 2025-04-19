# src/controllers/player_action_controller.py

import logging
from flask_socketio import emit # Removed join/leave room as they are not used here
from flask import request, current_app
from src.models import db
from src.models.player import Player
from src.models.game_state import GameState
from src.models.property import Property # Added Property model
# Removed GameLogic import as roll_dice is handled by GameController
# from ..services.game_logic import GameLogic 
# from .. import socketio, app # Removed socketio/app import, assume registered externally

logger = logging.getLogger(__name__)

# Note: This assumes controllers (GameController, PropertyController, SpecialSpaceController, Banker, AuctionController) 
# are registered in the app config or accessible via current_app

def register_player_action_handlers(socketio):
    """Registers player game action-related socket event handlers."""
    
    # Removed handle_end_turn - Handled by GameController
    # @socketio.on('end_turn')
    # def handle_end_turn(data): ...

    # Removed handle_roll_dice - Handled by GameController
    # @socketio.on('roll_dice')
    # def handle_roll_dice(data): ...

    @socketio.on('buy_property')
    def handle_buy_property(data):
        """Handles player decision to buy an unowned property they landed on."""
        player_id = data.get('playerId')
        property_id = data.get('propertyId')
        game_id = data.get('gameId', 1)
        player_sid = request.sid

        logger.info(f"Received buy_property request: Player {player_id}, Property {property_id}, Game {game_id} (SID: {player_sid})")

        # Retrieve dependencies
        banker = current_app.config.get('banker')
        property_controller = current_app.config.get('property_controller')
        game_controller = current_app.config.get('game_controller')

        if not banker or not property_controller or not game_controller:
            logger.error("Missing controller dependencies for buy_property")
            emit('game_error', {'error': 'Server configuration error'}, room=player_sid)
            return

        with current_app.app_context():
            try:
                game_state = GameState.query.get(game_id)
                player = Player.query.get(player_id)
                property_obj = Property.query.get(property_id)

                # --- Basic Validation --- 
                if not game_state or not player or not property_obj:
                     emit('game_error', {'error': "Game, Player, or Property not found."}, room=player_sid); return
                if game_state.current_player_id != player_id:
                    emit('game_error', {'error': "Not your turn."}, room=player_sid); return
                if property_obj.game_id != game_id:
                     emit('game_error', {'error': "Property does not belong to this game."}, room=player_sid); return
                if property_obj.owner_id is not None:
                    emit('game_error', {'error': "Property is already owned."}, room=player_sid); return
                if player.cash < property_obj.price:
                    emit('game_error', {'error': "Insufficient funds."}, room=player_sid); return
                
                # --- Action Validation --- 
                expected_type = 'buy_or_auction_prompt'
                if game_state.expected_action_type != expected_type:
                    logger.warning(f"Player {player_id} sent 'buy_property' but expected action was '{game_state.expected_action_type}'")
                    emit('game_error', {'error': f'Cannot buy now, expected action: {game_state.expected_action_type or "None"}'}, room=player_sid)
                    return
                # Check if the property matches the details
                if game_state.expected_action_details.get('property_id') != property_id:
                    logger.warning(f"Player {player_id} tried to buy property {property_id}, but expected was {game_state.expected_action_details.get('property_id')}")
                    emit('game_error', {'error': 'Mismatch between requested property and expected action.'}, room=player_sid)
                    return
                # --- End Action Validation --- 

                # --- Execution --- 
                payment_result = banker.player_pays_bank(player_id, property_obj.price, f"Purchase of {property_obj.name}")
                if not payment_result["success"]:
                     emit('game_error', {'error': payment_result.get('error', 'Payment failed')}, room=player_sid); return
                
                assign_result = property_controller.assign_property_to_player(property_id, player_id)
                if not assign_result["success"]:
                     logger.error(f"Failed property assignment after payment. Refunding player {player_id}.")
                     refund_result = banker.bank_pays_player(player_id, property_obj.price, f"Refund: Failed purchase of {property_obj.name}")
                     # Commit refund attempt regardless of success
                     db.session.commit() 
                     emit('game_error', {'error': assign_result.get('error', 'Failed to assign property ownership.')}, room=player_sid); return

                # Clear expected action state *after* successful action
                game_state.expected_action_type = None
                game_state.expected_action_details = None
                db.session.add(game_state) # Add changes before commit

                db.session.commit() # Commit payment, ownership, and cleared state
                logger.info(f"Player {player_id} purchased Property {property_id}.")

                # --- Emit Updates --- 
                socketio.emit('property_purchased', {'playerId': player_id, 'propertyId': property_id, 'propertyName': property_obj.name, 'cost': property_obj.price}, room=game_id) 
                updated_state = game_controller.get_game_state(game_id)
                if updated_state.get('success'): socketio.emit('game_state_update', updated_state, room=game_id)
                else: logger.error(f"Failed to get game state after property purchase: {updated_state.get('error')}")

                # --- End Turn --- 
                # End turn immediately after buying
                game_controller._internal_end_turn(player_id, game_id)
            
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error in handle_buy_property: {e}", exc_info=True)
                emit('game_error', {'error': 'Internal error during property purchase.'}, room=player_sid)

    @socketio.on('decline_buy')
    def handle_decline_buy(data):
        """Handles player decision to decline buying, potentially triggering auction."""
        player_id = data.get('playerId')
        property_id = data.get('propertyId')
        game_id = data.get('gameId', 1)
        player_sid = request.sid

        logger.info(f"Received decline_buy request: Player {player_id}, Property {property_id}, Game {game_id} (SID: {player_sid})")

        # Dependencies
        auction_controller = current_app.config.get('auction_controller')
        game_controller = current_app.config.get('game_controller')

        if not auction_controller or not game_controller: logger.error("Missing deps for decline_buy"); emit('game_error', {'error': 'Server config error'}, room=player_sid); return

        with current_app.app_context():
            try:
                game_state = GameState.query.get(game_id)
                player = Player.query.get(player_id)
                property_obj = Property.query.get(property_id)

                # --- Basic Validation --- 
                if not game_state or not player or not property_obj: emit('game_error', {'error': "Game/Player/Property not found."}, room=player_sid); return
                if game_state.current_player_id != player_id: emit('game_error', {'error': "Not your turn."}, room=player_sid); return
                if property_obj.game_id != game_id: emit('game_error', {'error': "Property not in this game."}, room=player_sid); return
                if property_obj.owner_id is not None: emit('game_error', {'error': "Property already owned."}, room=player_sid); return
                
                # --- Action Validation --- 
                expected_type = 'buy_or_auction_prompt'
                if game_state.expected_action_type != expected_type:
                    logger.warning(f"Player {player_id} sent 'decline_buy' but expected '{game_state.expected_action_type}'")
                    emit('game_error', {'error': f'Cannot decline now, expected: {game_state.expected_action_type or "None"}'}, room=player_sid)
                    return
                if game_state.expected_action_details.get('property_id') != property_id:
                    logger.warning(f"Player {player_id} declined property {property_id}, expected {game_state.expected_action_details.get('property_id')}")
                    emit('game_error', {'error': 'Property mismatch for decline action.'}, room=player_sid)
                    return
                # --- End Action Validation --- 

                # Clear the expected action state *before* proceeding, as the action is now resolved
                game_state.expected_action_type = None
                game_state.expected_action_details = None
                db.session.add(game_state)
                # Commit will happen below or within called controller methods

                # --- Execution --- 
                if game_state.auction_required:
                     logger.info(f"Player {player_id} declined buy for {property_id}. Starting auction.")
                     # The AuctionController should handle state updates and turn progression after auction
                     auction_result = auction_controller.start_auction(property_id, game_id)
                     if not auction_result.get('success'):
                          logger.error(f"Failed to start auction for {property_id}: {auction_result.get('error')}")
                          emit('game_error', {'error': auction_result.get('error', 'Failed to start auction.')}, room=game_id)
                          # If auction fails to start, the turn should probably end here
                          db.session.commit() # Commit the cleared expected state
                          game_controller._internal_end_turn(player_id, game_id)
                     # else: Auction started, state handled by AuctionController
                     # We commit the cleared expected state here if start_auction doesn't
                     else:
                          db.session.commit() 
                else:
                     logger.info(f"Player {player_id} declined buy for {property_id}. No auction. Ending turn.")
                     db.session.commit() # Commit cleared expected state
                     socketio.emit('property_remains_unowned', {'playerId': player_id, 'propertyId': property_id, 'propertyName': property_obj.name}, room=game_id)
                     game_controller._internal_end_turn(player_id, game_id)

            except Exception as e:
                db.session.rollback() 
                logger.error(f"Error handling decline_buy: {e}", exc_info=True)
                emit('game_error', {'error': 'Internal error while declining property.'}, room=player_sid)

    @socketio.on('improve_property')
    def handle_improve_property(data):
        """Socket event handler for property improvement (adding houses/hotels)"""
        player_id = data.get('playerId')
        property_id = data.get('propertyId')
        game_id = data.get('gameId', 1)
        improvement_type = data.get('improvementType', 'house')  # Default to 'house'
        player_sid = request.sid
        
        logger.info(f"Received improve_property request: Player {player_id}, Property {property_id}, Type {improvement_type}, Game {game_id}")
        
        property_controller = current_app.config.get('property_controller')
        if not property_controller:
            logger.error("Property controller not found in app config")
            emit('property_error', {'error': 'Server configuration error'}, room=player_sid)
            return
            
        with current_app.app_context():
            # Basic validation before passing to controller
            game_state = GameState.query.get(game_id)
            if not game_state:
                emit('property_error', {'error': 'Game not found'}, room=player_sid)
                return
                
            if game_state.current_player_id != player_id:
                emit('property_error', {'error': 'Not your turn'}, room=player_sid)
                return
                
            # Validate improvement type
            if improvement_type not in ['house', 'hotel']:
                emit('property_error', {'error': 'Invalid improvement type'}, room=player_sid)
                return
                
            try:
                # Call property controller to handle improvement
                result = property_controller.handle_property_improvement(
                    game_id=game_id,
                    player_id=player_id,
                    property_id=property_id,
                    improvement_type=improvement_type
                )
                
                if result.get('success'):
                    # The controller will emit events to all players
                    # but we can send a direct success confirmation to the requester
                    emit('property_improvement_result', {
                        'success': True,
                        'message': result.get('message', f'Successfully added {improvement_type} to property'),
                        'cost': result.get('cost', 0),
                        'improvement_type': improvement_type
                    }, room=player_sid)
                else:
                    emit('property_error', {
                        'error': result.get('error', f'Failed to add {improvement_type} to property')
                    }, room=player_sid)
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error handling property improvement: {str(e)}", exc_info=True)
                emit('property_error', {'error': f"Error improving property: {str(e)}"}, room=player_sid)

    @socketio.on('sell_improvement')
    def handle_sell_improvement(data):
        """Socket event handler for selling property improvements (houses/hotels)"""
        player_id = data.get('playerId')
        property_id = data.get('propertyId')
        game_id = data.get('gameId', 1)
        improvement_type = data.get('improvementType', 'house')  # Default to 'house'
        player_sid = request.sid
        
        logger.info(f"Received sell_improvement request: Player {player_id}, Property {property_id}, Type {improvement_type}, Game {game_id}")
        
        property_controller = current_app.config.get('property_controller')
        if not property_controller:
            logger.error("Property controller not found in app config")
            emit('property_error', {'error': 'Server configuration error'}, room=player_sid)
            return
            
        with current_app.app_context():
            # Basic validation before passing to controller
            game_state = GameState.query.get(game_id)
            if not game_state:
                emit('property_error', {'error': 'Game not found'}, room=player_sid)
                return
                
            if game_state.current_player_id != player_id:
                emit('property_error', {'error': 'Not your turn'}, room=player_sid)
                return
                
            # Validate improvement type
            if improvement_type not in ['house', 'hotel']:
                emit('property_error', {'error': 'Invalid improvement type'}, room=player_sid)
                return
                
            try:
                # Call property controller to handle selling improvement
                result = property_controller.handle_sell_improvement(
                    game_id=game_id,
                    player_id=player_id,
                    property_id=property_id,
                    improvement_type=improvement_type
                )
                
                if result.get('success'):
                    # The controller will emit events to all players
                    # but we can send a direct success confirmation to the requester
                    emit('property_improvement_sell_result', {
                        'success': True,
                        'message': result.get('message', f'Successfully sold {improvement_type} from property'),
                        'amount': result.get('amount', 0),
                        'improvement_type': improvement_type
                    }, room=player_sid)
                else:
                    emit('property_error', {
                        'error': result.get('error', f'Failed to sell {improvement_type} from property')
                    }, room=player_sid)
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error handling property improvement sale: {str(e)}", exc_info=True)
                emit('property_error', {'error': f"Error selling property improvement: {str(e)}"}, room=player_sid)

    @socketio.on('pay_jail_fine')
    def handle_pay_jail_fine(data):
        """Handles player choosing to pay the fine to get out of jail."""
        player_id = data.get('playerId')
        game_id = data.get('gameId', 1)
        player_sid = request.sid
        logger.info(f"Received pay_jail_fine request: Player {player_id}, Game {game_id} (SID: {player_sid})")

        banker = current_app.config.get('banker')
        if not banker: logger.error("Banker not found for pay_jail_fine"); emit('game_error', {'error':'Server config error'}, room=player_sid); return

        with current_app.app_context():
            game_state = GameState.query.get(game_id)
            player = Player.query.get(player_id)

            if not game_state or not player: emit('game_error', {'error': 'Game or Player not found'}, room=player_sid); return
            if game_state.current_player_id != player_id: emit('game_error', {'error': 'Not your turn'}, room=player_sid); return
            if not player.in_jail: emit('game_error', {'error': 'You are not in jail'}, room=player_sid); return
            
            # --- Action Validation --- 
            expected_type = 'jail_action_prompt'
            if game_state.expected_action_type != expected_type:
                 logger.warning(f"Player {player_id} sent 'pay_jail_fine' but expected '{game_state.expected_action_type}'")
                 emit('game_error', {'error': f'Cannot pay fine now, expected: {game_state.expected_action_type or "None"}'}, room=player_sid)
                 return
            # --- End Action Validation --- 
            
            fine_amount = 50 # TODO: Make this configurable?
            if player.cash < fine_amount:
                emit('game_error', {'error': 'Insufficient funds to pay jail fine.'}, room=player_sid)
                # Optionally set expected action to manage assets?
                # game_state.expected_action_type = 'manage_assets_for_jail_fine'
                # game_state.expected_action_details = {'fine_amount': fine_amount}
                # db.session.commit()
                return
            
            try:
                payment_result = banker.player_pays_bank(player_id, fine_amount, "Jail fine")
                if payment_result['success']:
                    player.in_jail = False
                    player.jail_turns = 0
                    # Clear expected action state AFTER successful action
                    game_state.expected_action_type = None
                    game_state.expected_action_details = None
                    db.session.add(player)
                    db.session.add(game_state)
                    db.session.commit()
                    logger.info(f"Player {player_id} paid jail fine and is out of jail.")
                    # Emit success and potentially updated game state
                    emit('jail_fine_paid', {'success': True, 'playerId': player_id, 'fineAmount': fine_amount}, room=player_sid)
                    # The player should now be allowed to roll, game state needs update broadcast
                    game_controller = current_app.config.get('game_controller')
                    if game_controller:
                         updated_state = game_controller.get_game_state(game_id)
                         if updated_state.get('success'): socketio.emit('game_state_update', updated_state, room=game_id)
                    # Frontend should likely enable roll dice button now
                else:
                    emit('game_error', {'error': payment_result.get('error', 'Failed to process fine payment.')}, room=player_sid)
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error processing pay_jail_fine for player {player_id}: {e}", exc_info=True)
                emit('game_error', {'error': 'Internal server error during fine payment.'}, room=player_sid)

    @socketio.on('use_get_out_of_jail_card')
    def handle_use_get_out_of_jail_card(data):
        """Handles player choosing to use a Get Out of Jail Free card."""
        player_id = data.get('playerId')
        game_id = data.get('gameId', 1)
        card_type = data.get('cardType') # 'chance' or 'community_chest' - needed if cards are separate
        player_sid = request.sid
        logger.info(f"Received use_get_out_of_jail_card request: Player {player_id}, Type: {card_type}, Game {game_id} (SID: {player_sid})")
        
        # TODO: Need CardDeck or equivalent access here
        # special_space_controller = current_app.config.get('special_space_controller') 
        # if not special_space_controller: ... error ...

        with current_app.app_context():
            game_state = GameState.query.get(game_id)
            player = Player.query.get(player_id)
            if not game_state or not player: emit('game_error', {'error': 'Game or Player not found'}, room=player_sid); return
            if game_state.current_player_id != player_id: emit('game_error', {'error': 'Not your turn'}, room=player_sid); return
            if not player.in_jail: emit('game_error', {'error': 'You are not in jail'}, room=player_sid); return
            
            # --- Action Validation --- 
            expected_type = 'jail_action_prompt'
            if game_state.expected_action_type != expected_type:
                 logger.warning(f"Player {player_id} sent 'use_get_out_of_jail_card' but expected '{game_state.expected_action_type}'")
                 emit('game_error', {'error': f'Cannot use card now, expected: {game_state.expected_action_type or "None"}'}, room=player_sid)
                 return
            # --- End Action Validation --- 

            # --- Card Ownership Check --- 
            # This logic depends heavily on how cards are tracked per player
            # Assuming a simple boolean flag on the Player model for now
            has_card = False
            if card_type == 'chance' and player.has_get_out_of_jail_chance:
                has_card = True
            elif card_type == 'community_chest' and player.has_get_out_of_jail_community:
                 has_card = True
            
            # Alternative: Query a PlayerCardInventory model if it exists

            if not has_card:
                 emit('game_error', {'error': f'You do not have a {card_type} Get Out of Jail Free card.'}, room=player_sid)
                 return
            # --- End Card Ownership Check ---
            
            try:
                # Consume the card
                if card_type == 'chance':
                    player.has_get_out_of_jail_chance = False
                    # TODO: Return the card to the corresponding deck's discard pile
                    # special_space_controller.chance_deck.return_card_by_type('get_out_of_jail') # Needs implementation in CardDeck
                else:
                    player.has_get_out_of_jail_community = False
                    # TODO: Return the card to the corresponding deck's discard pile
                    # special_space_controller.community_chest_deck.return_card_by_type('get_out_of_jail') # Needs implementation in CardDeck
                
                player.in_jail = False
                player.jail_turns = 0
                # Clear expected action state AFTER successful action
                game_state.expected_action_type = None
                game_state.expected_action_details = None
                db.session.add(player)
                db.session.add(game_state)
                db.session.commit()
                logger.info(f"Player {player_id} used a {card_type} Get Out of Jail Free card.")
                # Emit success and potentially updated game state
                emit('jail_card_used', {'success': True, 'playerId': player_id, 'cardType': card_type}, room=player_sid)
                # Player should now be allowed to roll
                game_controller = current_app.config.get('game_controller')
                if game_controller:
                     updated_state = game_controller.get_game_state(game_id)
                     if updated_state.get('success'): socketio.emit('game_state_update', updated_state, room=game_id)
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error processing use_get_out_of_jail_card for player {player_id}: {e}", exc_info=True)
                emit('game_error', {'error': 'Internal server error while using card.'}, room=player_sid)

    # Example: Repair property seems like a valid player action
    @socketio.on('repair_property')
    def handle_repair_property(data):
        property_controller = current_app.config.get('property_controller')
        if not property_controller:
             logger.error("PropertyController not available for repair_property"); return
        player_id=data.get('player_id'); pin=data.get('pin'); property_id=data.get('property_id'); repair_amount=data.get('repair_amount')
        player = Player.query.get(player_id)
        if not player or player.pin != pin: 
            emit('repair_error', {'error': 'Invalid player credentials'})
            return
        # Assuming repair_property method exists in PropertyController 
        # (May need creation/refactoring there based on original socket_controller logic)
        # result = property_controller.repair_property(player_id, property_id, repair_amount)
        logger.warning("repair_property handler needs corresponding PropertyController method")
        result = {"success": False, "error": "Repair function not fully implemented in PropertyController"} # Placeholder
        
        if result.get('success'): 
            emit('repair_completed', result) # Emit specific success event
        else: 
            emit('repair_error', result)

    # Example: Keep card draw handlers as they are likely player-initiated after a prompt
    @socketio.on('draw_chance_card')
    def handle_draw_chance_card(data):
        player_id = data.get('playerId') # Renamed for consistency
        game_id = data.get('gameId', 1)
        player_sid = request.sid
        logger.info(f"Received draw_chance_card request: Player {player_id}, Game {game_id}")
        
        special_space_controller = current_app.config.get('special_space_controller')
        if not special_space_controller: logger.error("SSC not found"); emit('game_error', {'error':'Server config error'}, room=player_sid); return

        with current_app.app_context():
            game_state = GameState.query.get(game_id)
            if not game_state: emit('game_error', {'error': 'Game not found'}, room=player_sid); return
            if game_state.current_player_id != player_id: emit('game_error', {'error': 'Not your turn'}, room=player_sid); return
            
            # --- Action Validation --- 
            expected_type = 'draw_chance_card'
            if game_state.expected_action_type != expected_type:
                 logger.warning(f"Player {player_id} sent 'draw_chance_card' but expected '{game_state.expected_action_type}'")
                 emit('game_error', {'error': f'Cannot draw Chance card now, expected: {game_state.expected_action_type or "None"}'}, room=player_sid)
                 return
            # --- End Action Validation --- 

            try: 
                # SpecialSpaceController method should handle drawing, executing, 
                # committing DB changes, emitting results, clearing expected state, and ending turn if needed.
                result = special_space_controller.process_chance_card(player_id, game_id)
                # This handler might not need to emit anything if SSC handles it.
            except Exception as e: 
                db.session.rollback()
                logger.error(f"Error handling draw_chance_card: {e}", exc_info=True)
                emit('card_error', {'error': f"Error processing Chance card: {str(e)}"}, room=player_sid) 

    @socketio.on('draw_community_chest_card')
    def handle_draw_community_chest_card(data):
        player_id = data.get('playerId') # Renamed for consistency
        game_id = data.get('gameId', 1)
        player_sid = request.sid
        logger.info(f"Received draw_community_chest_card request: Player {player_id}, Game {game_id}")

        special_space_controller = current_app.config.get('special_space_controller')
        if not special_space_controller: logger.error("SSC not found"); emit('game_error', {'error':'Server config error'}, room=player_sid); return

        with current_app.app_context():
            game_state = GameState.query.get(game_id)
            if not game_state: emit('game_error', {'error': 'Game not found'}, room=player_sid); return
            if game_state.current_player_id != player_id: emit('game_error', {'error': 'Not your turn'}, room=player_sid); return
            
            # --- Action Validation --- 
            expected_type = 'draw_community_chest_card'
            if game_state.expected_action_type != expected_type:
                 logger.warning(f"Player {player_id} sent 'draw_cc_card' but expected '{game_state.expected_action_type}'")
                 emit('game_error', {'error': f'Cannot draw CC card now, expected: {game_state.expected_action_type or "None"}'}, room=player_sid)
                 return
            # --- End Action Validation --- 

            try: 
                # SSC method should handle all logic, state changes, commits, emits, turn end.
                result = special_space_controller.process_community_chest_card(player_id, game_id)
            except Exception as e: 
                db.session.rollback()
                logger.error(f"Error handling draw_cc_card: {e}", exc_info=True)
                emit('card_error', {'error': f"Error processing Community Chest card: {str(e)}"}, room=player_sid)
                
    @socketio.on('declare_bankruptcy')
    def handle_declare_bankruptcy(data):
        """Socket event handler for bankruptcy declaration"""
        player_id = data.get('playerId')
        pin = data.get('pin')
        player_sid = request.sid
        logger.info(f"Received bankruptcy declaration request from player {player_id}")
        
        if not player_id or not pin:
            emit('bankruptcy_error', {'error': 'Player ID and PIN are required'}, room=player_sid)
            return
            
        player_controller = current_app.config.get('player_controller')
        if not player_controller:
            logger.error("Player controller not found in app config")
            emit('bankruptcy_error', {'error': 'Server configuration error'}, room=player_sid)
            return
            
        try:
            result = player_controller.handle_bankruptcy(player_id, pin)
            
            if result.get('success'):
                # Notify the player about bankruptcy result
                emit('bankruptcy_result', {
                    'success': True,
                    'message': 'Bankruptcy processed successfully',
                    'debt_forgiven': result.get('debt_forgiven', 0),
                    'properties_lost': result.get('properties_lost', 0),
                    'new_balance': result.get('new_balance', 0)
                }, room=player_sid)
                
                # No need to broadcast to game room as the player_controller emits player_updated event
            else:
                emit('bankruptcy_error', {
                    'error': result.get('error', 'Failed to process bankruptcy')
                }, room=player_sid)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing bankruptcy for player {player_id}: {str(e)}", exc_info=True)
            emit('bankruptcy_error', {'error': f"Error declaring bankruptcy: {str(e)}"}, room=player_sid)
            
    @socketio.on('handle_market_fluctuation')
    def handle_market_fluctuation(data):
        """Socket event handler for when a player lands on a market fluctuation space"""
        player_id = data.get('playerId')
        game_id = data.get('gameId', 1)
        player_sid = request.sid
        
        logger.info(f"Received handle_market_fluctuation request: Player {player_id}, Game {game_id}")
        
        # Get the special space controller
        special_space_controller = current_app.config.get('special_space_controller')
        if not special_space_controller:
            logger.error("Special space controller not found in app config")
            emit('game_error', {'error': 'Server configuration error'}, room=player_sid)
            return
            
        with current_app.app_context():
            # Basic validation
            game_state = GameState.query.get(game_id)
            if not game_state:
                emit('game_error', {'error': 'Game not found'}, room=player_sid)
                return
                
            if game_state.current_player_id != player_id:
                emit('game_error', {'error': 'Not your turn'}, room=player_sid)
                return
                
            # Verify expected action
            expected_type = 'market_fluctuation'
            if game_state.expected_action_type != expected_type:
                logger.warning(f"Player {player_id} sent 'handle_market_fluctuation' but expected '{game_state.expected_action_type}'")
                emit('game_error', {'error': f'Cannot process market fluctuation now, expected: {game_state.expected_action_type or "None"}'}, room=player_sid)
                return
                
            try:
                # Call the special space controller to handle market fluctuation
                result = special_space_controller.handle_market_fluctuation_space(game_id, player_id)
                
                if result.get('success'):
                    # The special space controller will emit events to all players
                    # and clear the expected action state
                    
                    # Send a direct confirmation to the requesting client
                    emit('market_fluctuation_result', {
                        'success': True,
                        'message': result.get('message', 'Market fluctuation processed'),
                    }, room=player_sid)
                    
                    # End turn after handling market fluctuation
                    game_controller = current_app.config.get('game_controller')
                    if game_controller:
                        game_controller._internal_end_turn(player_id, game_id)
                else:
                    emit('game_error', {
                        'error': result.get('error', 'Failed to process market fluctuation')
                    }, room=player_sid)
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error handling market fluctuation: {str(e)}", exc_info=True)
                emit('game_error', {'error': f"Error processing market fluctuation: {str(e)}"}, room=player_sid)

    @socketio.on('mortgage_property')
    def handle_mortgage_property(data):
        """Socket event handler for mortgaging a property"""
        player_id = data.get('playerId')
        property_id = data.get('propertyId')
        game_id = data.get('gameId', 1)
        player_sid = request.sid
        
        logger.info(f"Received mortgage_property request: Player {player_id}, Property {property_id}, Game {game_id}")
        
        property_controller = current_app.config.get('property_controller')
        if not property_controller:
            logger.error("Property controller not found in app config")
            emit('property_error', {'error': 'Server configuration error'}, room=player_sid)
            return
            
        with current_app.app_context():
            # Basic validation
            game_state = GameState.query.get(game_id)
            if not game_state:
                emit('property_error', {'error': 'Game not found'}, room=player_sid)
                return
                
            # Verify it's the player's turn (though mortgaging is often allowed outside of turn)
            current_player_turn = game_state.current_player_id == player_id
            
            try:
                # Call property controller to handle mortgaging
                result = property_controller.mortgage_property(
                    player_id=player_id,
                    pin=data.get('pin'),  # Optional, depends on your authentication
                    property_id=property_id
                )
                
                if result.get('success'):
                    # Send a direct confirmation to the requesting client
                    emit('mortgage_result', {
                        'success': True,
                        'message': result.get('message', 'Property mortgaged successfully'),
                        'amount': result.get('amount', 0),
                        'property_id': property_id
                    }, room=player_sid)
                    
                    # The property controller emits the property_mortgaged event to all players
                    # If an update to the game state is needed after this action
                    game_controller = current_app.config.get('game_controller')
                    if game_controller and current_player_turn:
                        updated_state = game_controller.get_game_state(game_id)
                        if updated_state.get('success'):
                            socketio.emit('game_state_update', updated_state, room=game_id)
                else:
                    emit('property_error', {
                        'error': result.get('error', 'Failed to mortgage property')
                    }, room=player_sid)
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error handling property mortgage: {str(e)}", exc_info=True)
                emit('property_error', {'error': f"Error mortgaging property: {str(e)}"}, room=player_sid)

    @socketio.on('unmortgage_property')
    def handle_unmortgage_property(data):
        """Socket event handler for unmortgaging a property"""
        player_id = data.get('playerId')
        property_id = data.get('propertyId')
        game_id = data.get('gameId', 1)
        player_sid = request.sid
        
        logger.info(f"Received unmortgage_property request: Player {player_id}, Property {property_id}, Game {game_id}")
        
        property_controller = current_app.config.get('property_controller')
        if not property_controller:
            logger.error("Property controller not found in app config")
            emit('property_error', {'error': 'Server configuration error'}, room=player_sid)
            return
            
        with current_app.app_context():
            # Basic validation
            game_state = GameState.query.get(game_id)
            if not game_state:
                emit('property_error', {'error': 'Game not found'}, room=player_sid)
                return
                
            # Verify it's the player's turn (though unmortgaging is often allowed outside of turn)
            current_player_turn = game_state.current_player_id == player_id
            
            try:
                # Call property controller to handle unmortgaging
                result = property_controller.unmortgage_property(
                    player_id=player_id,
                    pin=data.get('pin'),  # Optional, depends on your authentication
                    property_id=property_id
                )
                
                if result.get('success'):
                    # Send a direct confirmation to the requesting client
                    emit('unmortgage_result', {
                        'success': True,
                        'message': result.get('message', 'Property unmortgaged successfully'),
                        'amount': result.get('amount', 0),
                        'property_id': property_id
                    }, room=player_sid)
                    
                    # The property controller emits the property_unmortgaged event to all players
                    # If an update to the game state is needed after this action
                    game_controller = current_app.config.get('game_controller')
                    if game_controller and current_player_turn:
                        updated_state = game_controller.get_game_state(game_id)
                        if updated_state.get('success'):
                            socketio.emit('game_state_update', updated_state, room=game_id)
                else:
                    emit('property_error', {
                        'error': result.get('error', 'Failed to unmortgage property')
                    }, room=player_sid)
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error handling property unmortgage: {str(e)}", exc_info=True)
                emit('property_error', {'error': f"Error unmortgaging property: {str(e)}"}, room=player_sid)

# Note: Registration happens externally, e.g.:
# from src.controllers.player_action_controller import register_player_action_handlers
# register_player_action_handlers(socketio) 