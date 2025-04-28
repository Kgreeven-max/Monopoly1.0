import logging
from datetime import datetime
from flask import current_app # For accessing app context dependencies like db, banker, socketio
from flask_socketio import emit # Add import for emit
from flask import request # Add import for request
import json

from src.models import db
from src.models.trade import Trade, TradeItem
from src.models.player import Player
from src.models.property import Property
from src.models.banker import Banker
from src.models.game_state import GameState # For getting game_id for socket rooms
from src.models.transaction import Transaction

logger = logging.getLogger(__name__)

class TradeController:
    """Controller for managing player-to-player trades."""

    def __init__(self, app_config):
        # Dependencies will be accessed via current_app.config within methods
        self.logger = logging.getLogger("trade_controller")
        self.logger.info("TradeController initialized.")
        self.app_config = app_config
        self.socketio = app_config.get('socketio')

    def _get_dependencies(self):
        """Helper to retrieve dependencies from app context."""
        banker = current_app.config.get('banker')
        socketio = current_app.config.get('socketio')
        if not banker or not socketio:
            self.logger.error("Missing dependencies (Banker or SocketIO) in app config.")
            raise ValueError("Banker or SocketIO not configured in the application.")
        return banker, socketio

    def create_trade_proposal(self, data):
        """Create a new trade proposal between players"""
        self.logger.info(f"Creating trade proposal: {data}")
        
        # Extract required data
        proposer_id = data.get('proposer_id')
        receiver_id = data.get('receiver_id')
        game_id = data.get('game_id')
        proposer_cash = data.get('proposer_cash', 0)
        receiver_cash = data.get('receiver_cash', 0)
        proposer_properties = data.get('proposer_properties', [])
        receiver_properties = data.get('receiver_properties', [])
        proposer_jail_cards = data.get('proposer_jail_cards', 0)
        receiver_jail_cards = data.get('receiver_jail_cards', 0)
        
        # Validate required data
        if not all([proposer_id, receiver_id, game_id]):
            self.logger.error(f"Missing required data for trade proposal: {data}")
            return {'success': False, 'error': 'Missing required data'}
        
        # Validate trade has content
        if not any([proposer_cash, receiver_cash, proposer_properties, receiver_properties, proposer_jail_cards, receiver_jail_cards]):
            self.logger.error(f"Empty trade proposal: {data}")
            return {'success': False, 'error': 'Trade proposal is empty'}
        
        try:
            # Verify game is active
            game_state = GameState.query.get(game_id)
            if not game_state or game_state.status != 'active':
                self.logger.warning(f"Cannot propose trade in inactive game {game_id}")
                return {'success': False, 'error': 'Game not active'}
            
            # Get players
            proposer = Player.query.get(proposer_id)
            receiver = Player.query.get(receiver_id)
            
            if not proposer or not receiver:
                self.logger.error(f"Player {proposer_id} or Player {receiver_id} not found")
                return {'success': False, 'error': 'Player not found'}
            
            # Verify players are in the game
            if not proposer.in_game or not receiver.in_game:
                self.logger.warning(f"Both players must be in the game")
                return {'success': False, 'error': 'Player not in game'}
            
            # Verify proposer has enough cash
            if proposer_cash > proposer.money:
                self.logger.warning(f"Proposer {proposer_id} has insufficient funds ({proposer.money}) for trade proposing {proposer_cash}")
                return {'success': False, 'error': 'Proposer has insufficient funds'}
            
            # Verify proposer owns the properties being offered
            proposer_property_objs = []
            for prop_id in proposer_properties:
                prop = Property.query.get(prop_id)
                if not prop or prop.owner_id != proposer_id:
                    self.logger.warning(f"Proposer {proposer_id} does not own property {prop_id}")
                    return {'success': False, 'error': f'Proposer does not own property {prop_id}'}
                
                # Verify property is not mortgaged
                if prop.is_mortgaged:
                    self.logger.warning(f"Cannot trade mortgaged property {prop_id}")
                    return {'success': False, 'error': f'Cannot trade mortgaged property: {prop.name}'}
                
                # Verify property has no buildings
                if prop.houses > 0 or prop.hotels > 0:
                    self.logger.warning(f"Cannot trade property {prop_id} with buildings")
                    return {'success': False, 'error': f'Cannot trade property with buildings: {prop.name}'}
                
                proposer_property_objs.append(prop)
            
            # Verify receiver owns the properties being requested
            receiver_property_objs = []
            for prop_id in receiver_properties:
                prop = Property.query.get(prop_id)
                if not prop or prop.owner_id != receiver_id:
                    self.logger.warning(f"Receiver {receiver_id} does not own property {prop_id}")
                    return {'success': False, 'error': f'Receiver does not own property {prop_id}'}
                
                # Verify property is not mortgaged
                if prop.is_mortgaged:
                    self.logger.warning(f"Cannot trade mortgaged property {prop_id}")
                    return {'success': False, 'error': f'Cannot trade mortgaged property: {prop.name}'}
                
                # Verify property has no buildings
                if prop.houses > 0 or prop.hotels > 0:
                    self.logger.warning(f"Cannot trade property {prop_id} with buildings")
                    return {'success': False, 'error': f'Cannot trade property with buildings: {prop.name}'}
                
                receiver_property_objs.append(prop)
            
            # Verify jail card counts
            if proposer_jail_cards > 0 and not proposer.has_jail_card:
                self.logger.warning(f"Proposer {proposer_id} does not have a jail card to trade")
                return {'success': False, 'error': 'Proposer does not have a jail card'}
            
            if receiver_jail_cards > 0 and not receiver.has_jail_card:
                self.logger.warning(f"Receiver {receiver_id} does not have a jail card to trade")
                return {'success': False, 'error': 'Receiver does not have a jail card'}
            
            # Create trade object
            trade = Trade(
                proposer_id=proposer_id,
                receiver_id=receiver_id,
                proposer_cash=proposer_cash,
                receiver_cash=receiver_cash,
                status='pending',
                details=json.dumps({
                    'proposer_jail_cards': proposer_jail_cards,
                    'receiver_jail_cards': receiver_jail_cards,
                    'game_id': game_id
                })
            )
            
            db.session.add(trade)
            db.session.flush()  # Get the trade ID before committing
            
            # Create trade items for properties
            for prop in proposer_property_objs:
                trade_item = TradeItem(
                    trade_id=trade.id,
                    property_id=prop.id,
                    is_from_proposer=True
                )
                db.session.add(trade_item)
            
            for prop in receiver_property_objs:
                trade_item = TradeItem(
                    trade_id=trade.id,
                    property_id=prop.id,
                    is_from_proposer=False
                )
                db.session.add(trade_item)
            
            db.session.commit()
            
            self.logger.info(f"Trade proposal {trade.id} created successfully between {proposer_id} and {receiver_id}")
            
            # Emit events
            if self.socketio:
                trade_data = trade.to_dict()
                
                # Add human-readable property names
                trade_data['proposer_property_names'] = [
                    Property.query.get(prop_id).name for prop_id in trade_data['proposer_properties']
                ]
                trade_data['receiver_property_names'] = [
                    Property.query.get(prop_id).name for prop_id in trade_data['receiver_properties']
                ]
                
                # Add player names
                trade_data['proposer_name'] = proposer.username
                trade_data['receiver_name'] = receiver.username
                
                self.socketio.emit('trade_proposed', {
                    'trade': trade_data,
                    'timestamp': datetime.now().isoformat()
                }, room=game_id)
                
                # Send a direct notification to the receiver
                self.socketio.emit('trade_notification', {
                    'type': 'new_proposal',
                    'trade_id': trade.id,
                    'proposer_name': proposer.username,
                    'message': f"{proposer.username} has proposed a trade to you.",
                    'timestamp': datetime.now().isoformat()
                }, room=f"player_{receiver_id}")
            
            return {
                'success': True,
                'message': 'Trade proposal created successfully',
                'trade_id': trade.id,
                'trade': trade.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating trade proposal: {e}", exc_info=True)
            return {'success': False, 'error': f'Internal error creating trade proposal: {str(e)}'}

    def accept_trade(self, data):
        """Accept a trade proposal"""
        self.logger.info(f"Accepting trade proposal: {data}")
        
        trade_id = data.get('trade_id')
        player_id = data.get('player_id')
        
        if not trade_id or not player_id:
            self.logger.error(f"Missing required data for accepting trade: {data}")
            return {'success': False, 'error': 'Missing required data'}
        
        try:
            # Get the trade
            trade = Trade.query.get(trade_id)
            if not trade:
                self.logger.error(f"Trade {trade_id} not found")
                return {'success': False, 'error': 'Trade not found'}
            
            # Verify player is the receiver
            if trade.receiver_id != player_id:
                self.logger.warning(f"Player {player_id} is not the receiver of trade {trade_id}")
                return {'success': False, 'error': 'Only trade recipient can accept'}
            
            # Verify trade is pending
            if trade.status != 'pending':
                self.logger.warning(f"Trade {trade_id} is not pending (status: {trade.status})")
                return {'success': False, 'error': f'Trade is not pending (status: {trade.status})'}
            
            # Get players
            proposer = Player.query.get(trade.proposer_id)
            receiver = Player.query.get(trade.receiver_id)
            
            if not proposer or not receiver:
                self.logger.error(f"Proposer {trade.proposer_id} or Receiver {trade.receiver_id} not found")
                return {'success': False, 'error': 'Player not found'}
            
            # Verify players are still in the game
            if not proposer.in_game or not receiver.in_game:
                self.logger.warning(f"Both players must be in the game")
                trade.status = 'expired'
                db.session.add(trade)
                db.session.commit()
                return {'success': False, 'error': 'Player not in game'}
            
            # Re-verify proposer has enough cash
            if trade.proposer_cash > proposer.money:
                self.logger.warning(f"Proposer {trade.proposer_id} has insufficient funds ({proposer.money}) for trade requiring {trade.proposer_cash}")
                return {'success': False, 'error': 'Proposer has insufficient funds'}
            
            # Re-verify receiver has enough cash
            if trade.receiver_cash > receiver.money:
                self.logger.warning(f"Receiver {trade.receiver_id} has insufficient funds ({receiver.money}) for trade requiring {trade.receiver_cash}")
                return {'success': False, 'error': 'Receiver has insufficient funds'}
            
            # Load details
            details = json.loads(trade.details) if trade.details else {}
            game_id = details.get('game_id')
            proposer_jail_cards = details.get('proposer_jail_cards', 0)
            receiver_jail_cards = details.get('receiver_jail_cards', 0)
            
            # Re-verify jail card counts
            if proposer_jail_cards > 0 and not proposer.has_jail_card:
                self.logger.warning(f"Proposer {trade.proposer_id} no longer has a jail card to trade")
                return {'success': False, 'error': 'Proposer no longer has a jail card'}
            
            if receiver_jail_cards > 0 and not receiver.has_jail_card:
                self.logger.warning(f"Receiver {trade.receiver_id} no longer has a jail card to trade")
                return {'success': False, 'error': 'Receiver no longer has a jail card'}
            
            # Re-verify ownership and status of all properties
            for item in trade.items:
                prop = Property.query.get(item.property_id)
                
                if not prop:
                    self.logger.error(f"Property {item.property_id} not found")
                    return {'success': False, 'error': f'Property {item.property_id} not found'}
                
                owner_id = trade.proposer_id if item.is_from_proposer else trade.receiver_id
                
                if prop.owner_id != owner_id:
                    self.logger.warning(f"Property {item.property_id} is no longer owned by {'proposer' if item.is_from_proposer else 'receiver'}")
                    return {'success': False, 'error': f"Property {prop.name} is no longer owned by the {'proposer' if item.is_from_proposer else 'receiver'}"}
                
                if prop.is_mortgaged:
                    self.logger.warning(f"Property {item.property_id} is now mortgaged")
                    return {'success': False, 'error': f'Property {prop.name} is now mortgaged'}
                
                if prop.houses > 0 or prop.hotels > 0:
                    self.logger.warning(f"Property {item.property_id} now has buildings")
                    return {'success': False, 'error': f'Property {prop.name} now has buildings'}
            
            # Begin trade execution
            # 1. Transfer cash
            if trade.proposer_cash > 0:
                proposer.money -= trade.proposer_cash
                receiver.money += trade.proposer_cash
                
                # Record transaction
                transaction = Transaction(
                    from_player_id=trade.proposer_id,
                    to_player_id=trade.receiver_id,
                    amount=trade.proposer_cash,
                    transaction_type='trade',
                    description=f"Trade payment from {proposer.username} to {receiver.username}"
                )
                db.session.add(transaction)
            
            if trade.receiver_cash > 0:
                receiver.money -= trade.receiver_cash
                proposer.money += trade.receiver_cash
                
                # Record transaction
                transaction = Transaction(
                    from_player_id=trade.receiver_id,
                    to_player_id=trade.proposer_id,
                    amount=trade.receiver_cash,
                    transaction_type='trade',
                    description=f"Trade payment from {receiver.username} to {proposer.username}"
                )
                db.session.add(transaction)
            
            # 2. Transfer properties
            for item in trade.items:
                prop = Property.query.get(item.property_id)
                if item.is_from_proposer:
                    prop.owner_id = trade.receiver_id
                else:
                    prop.owner_id = trade.proposer_id
                db.session.add(prop)
            
            # 3. Transfer jail cards
            if proposer_jail_cards > 0:
                proposer.has_jail_card = False
                receiver.has_jail_card = True
            
            if receiver_jail_cards > 0:
                receiver.has_jail_card = False
                proposer.has_jail_card = True
            
            # Update trade status
            trade.status = 'completed'
            trade.updated_at = datetime.now()
            
            # Save all changes
            db.session.add(proposer)
            db.session.add(receiver)
            db.session.add(trade)
            db.session.commit()
            
            self.logger.info(f"Trade {trade_id} accepted and completed successfully")
            
            # Emit events
            if self.socketio:
                # Get all involved property names
                proposer_property_names = []
                receiver_property_names = []
                
                for item in trade.items:
                    prop = Property.query.get(item.property_id)
                    if item.is_from_proposer:
                        proposer_property_names.append(prop.name)
                    else:
                        receiver_property_names.append(prop.name)
                
                trade_data = trade.to_dict()
                trade_data['proposer_name'] = proposer.username
                trade_data['receiver_name'] = receiver.username
                trade_data['proposer_property_names'] = proposer_property_names
                trade_data['receiver_property_names'] = receiver_property_names
                
                # Emit trade accepted event
                self.socketio.emit('trade_accepted', {
                    'trade': trade_data,
                    'timestamp': datetime.now().isoformat()
                }, room=game_id)
                
                # Emit player money updates
                if trade.proposer_cash > 0:
                    self.socketio.emit('player_money_updated', {
                        'player_id': proposer.id,
                        'old_balance': proposer.money + trade.proposer_cash,
                        'new_balance': proposer.money,
                        'change': -trade.proposer_cash,
                        'reason': 'trade_payment'
                    }, room=game_id)
                    
                    self.socketio.emit('player_money_updated', {
                        'player_id': receiver.id,
                        'old_balance': receiver.money - trade.proposer_cash,
                        'new_balance': receiver.money,
                        'change': trade.proposer_cash,
                        'reason': 'trade_payment'
                    }, room=game_id)
                
                if trade.receiver_cash > 0:
                    self.socketio.emit('player_money_updated', {
                        'player_id': receiver.id,
                        'old_balance': receiver.money + trade.receiver_cash,
                        'new_balance': receiver.money,
                        'change': -trade.receiver_cash,
                        'reason': 'trade_payment'
                    }, room=game_id)
                    
                    self.socketio.emit('player_money_updated', {
                        'player_id': proposer.id,
                        'old_balance': proposer.money - trade.receiver_cash,
                        'new_balance': proposer.money,
                        'change': trade.receiver_cash,
                        'reason': 'trade_payment'
                    }, room=game_id)
                
                # Emit property ownership changes
                for item in trade.items:
                    prop = Property.query.get(item.property_id)
                    new_owner_id = receiver.id if item.is_from_proposer else proposer.id
                    old_owner_id = proposer.id if item.is_from_proposer else receiver.id
                    new_owner_name = receiver.username if item.is_from_proposer else proposer.username
                    
                    self.socketio.emit('property_ownership_changed', {
                        'property_id': prop.id,
                        'property_name': prop.name,
                        'old_owner_id': old_owner_id,
                        'new_owner_id': new_owner_id,
                        'new_owner_name': new_owner_name,
                        'reason': 'trade',
                        'timestamp': datetime.now().isoformat()
                    }, room=game_id)
                
                # Send direct notifications to both players
                self.socketio.emit('trade_notification', {
                    'type': 'accepted',
                    'trade_id': trade.id,
                    'message': f"{receiver.username} accepted your trade proposal.",
                    'timestamp': datetime.now().isoformat()
                }, room=f"player_{proposer.id}")
                
                # Update game state for all players
                game_logic = self.app_config.get('game_logic')
                if game_logic and game_id and hasattr(game_logic, 'get_game_state'):
                    updated_state = game_logic.get_game_state(game_id)
                    if updated_state:
                        self.socketio.emit('game_state_update', updated_state, room=game_id)
            
            return {
                'success': True,
                'message': 'Trade accepted and completed successfully',
                'trade': trade.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error accepting trade: {e}", exc_info=True)
            return {'success': False, 'error': f'Internal error accepting trade: {str(e)}'}

    def reject_trade(self, data):
        """Reject a trade proposal"""
        self.logger.info(f"Rejecting trade proposal: {data}")
        
        trade_id = data.get('trade_id')
        player_id = data.get('player_id')
        
        if not trade_id or not player_id:
            self.logger.error(f"Missing required data for rejecting trade: {data}")
            return {'success': False, 'error': 'Missing required data'}
        
        try:
            # Get the trade
            trade = Trade.query.get(trade_id)
            if not trade:
                self.logger.error(f"Trade {trade_id} not found")
                return {'success': False, 'error': 'Trade not found'}
            
            # Verify player is the receiver
            if trade.receiver_id != player_id:
                self.logger.warning(f"Player {player_id} is not the receiver of trade {trade_id}")
                return {'success': False, 'error': 'Only trade recipient can reject'}
            
            # Verify trade is pending
            if trade.status != 'pending':
                self.logger.warning(f"Trade {trade_id} is not pending (status: {trade.status})")
                return {'success': False, 'error': f'Trade is not pending (status: {trade.status})'}
            
            # Update trade status
            trade.status = 'rejected'
            trade.updated_at = datetime.now()
            db.session.add(trade)
            db.session.commit()
            
            self.logger.info(f"Trade {trade_id} rejected successfully")
            
            # Emit events
            if self.socketio:
                # Load game_id from details
                details = json.loads(trade.details) if trade.details else {}
                game_id = details.get('game_id')
                
                # Get player names
                proposer = Player.query.get(trade.proposer_id)
                receiver = Player.query.get(trade.receiver_id)
                
                proposer_name = proposer.username if proposer else "Unknown"
                receiver_name = receiver.username if receiver else "Unknown"
                
                # Emit trade rejected event
                if game_id:
                    self.socketio.emit('trade_rejected', {
                        'trade_id': trade.id,
                        'proposer_id': trade.proposer_id,
                        'proposer_name': proposer_name,
                        'receiver_id': trade.receiver_id,
                        'receiver_name': receiver_name,
                        'timestamp': datetime.now().isoformat()
                    }, room=game_id)
                
                # Send direct notification to proposer
                self.socketio.emit('trade_notification', {
                    'type': 'rejected',
                    'trade_id': trade.id,
                    'message': f"{receiver_name} rejected your trade proposal.",
                    'timestamp': datetime.now().isoformat()
                }, room=f"player_{trade.proposer_id}")
            
            return {
                'success': True,
                'message': 'Trade rejected successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error rejecting trade: {e}", exc_info=True)
            return {'success': False, 'error': f'Internal error rejecting trade: {str(e)}'}

    def cancel_trade(self, data):
        """Cancel a trade proposal"""
        self.logger.info(f"Cancelling trade proposal: {data}")
        
        trade_id = data.get('trade_id')
        player_id = data.get('player_id')
        
        if not trade_id or not player_id:
            self.logger.error(f"Missing required data for cancelling trade: {data}")
            return {'success': False, 'error': 'Missing required data'}
        
        try:
            # Get the trade
            trade = Trade.query.get(trade_id)
            if not trade:
                self.logger.error(f"Trade {trade_id} not found")
                return {'success': False, 'error': 'Trade not found'}
            
            # Verify player is the proposer
            if trade.proposer_id != player_id:
                self.logger.warning(f"Player {player_id} is not the proposer of trade {trade_id}")
                return {'success': False, 'error': 'Only trade proposer can cancel'}
            
            # Verify trade is pending
            if trade.status != 'pending':
                self.logger.warning(f"Trade {trade_id} is not pending (status: {trade.status})")
                return {'success': False, 'error': f'Trade is not pending (status: {trade.status})'}
            
            # Update trade status
            trade.status = 'cancelled'
            trade.updated_at = datetime.now()
            db.session.add(trade)
            db.session.commit()
            
            self.logger.info(f"Trade {trade_id} cancelled successfully")
            
            # Emit events
            if self.socketio:
                # Load game_id from details
                details = json.loads(trade.details) if trade.details else {}
                game_id = details.get('game_id')
                
                # Get player names
                proposer = Player.query.get(trade.proposer_id)
                receiver = Player.query.get(trade.receiver_id)
                
                proposer_name = proposer.username if proposer else "Unknown"
                receiver_name = receiver.username if receiver else "Unknown"
                
                # Emit trade cancelled event
                if game_id:
                    self.socketio.emit('trade_cancelled', {
                        'trade_id': trade.id,
                        'proposer_id': trade.proposer_id,
                        'proposer_name': proposer_name,
                        'receiver_id': trade.receiver_id,
                        'receiver_name': receiver_name,
                        'timestamp': datetime.now().isoformat()
                    }, room=game_id)
                
                # Send direct notification to receiver
                self.socketio.emit('trade_notification', {
                    'type': 'cancelled',
                    'trade_id': trade.id,
                    'message': f"{proposer_name} cancelled their trade proposal.",
                    'timestamp': datetime.now().isoformat()
                }, room=f"player_{trade.receiver_id}")
            
            return {
                'success': True,
                'message': 'Trade cancelled successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error cancelling trade: {e}", exc_info=True)
            return {'success': False, 'error': f'Internal error cancelling trade: {str(e)}'}

    def get_pending_trades(self, player_id):
        """Get all pending trades for a player"""
        self.logger.debug(f"Getting pending trades for player {player_id}")
        
        try:
            # Get both proposed and received pending trades
            proposed_trades = Trade.query.filter_by(
                proposer_id=player_id,
                status='pending'
            ).order_by(Trade.created_at.desc()).all()
            
            received_trades = Trade.query.filter_by(
                receiver_id=player_id,
                status='pending'
            ).order_by(Trade.created_at.desc()).all()
            
            proposed_trades_data = [self._format_trade_for_api(trade) for trade in proposed_trades]
            received_trades_data = [self._format_trade_for_api(trade) for trade in received_trades]
            
            return {
                'success': True,
                'proposed_trades': proposed_trades_data,
                'received_trades': received_trades_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting pending trades: {e}", exc_info=True)
            return {'success': False, 'error': f'Internal error getting pending trades: {str(e)}'}

    def get_trade_history(self, player_id, limit=10):
        """Get trade history for a player"""
        self.logger.debug(f"Getting trade history for player {player_id}")
        
        try:
            # Get both proposed and received completed or rejected trades
            trades = Trade.query.filter(
                ((Trade.proposer_id == player_id) | (Trade.receiver_id == player_id)),
                Trade.status.in_(['completed', 'rejected', 'cancelled'])
            ).order_by(Trade.updated_at.desc()).limit(limit).all()
            
            trades_data = [self._format_trade_for_api(trade) for trade in trades]
            
            return {
                'success': True,
                'trades': trades_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting trade history: {e}", exc_info=True)
            return {'success': False, 'error': f'Internal error getting trade history: {str(e)}'}

    def _format_trade_for_api(self, trade):
        """Format a trade object for API response"""
        trade_dict = trade.to_dict()
        
        # Add human-readable property names
        trade_dict['proposer_property_names'] = []
        for prop_id in trade_dict['proposer_properties']:
            prop = Property.query.get(prop_id)
            if prop:
                trade_dict['proposer_property_names'].append(prop.name)
        
        trade_dict['receiver_property_names'] = []
        for prop_id in trade_dict['receiver_properties']:
            prop = Property.query.get(prop_id)
            if prop:
                trade_dict['receiver_property_names'].append(prop.name)
        
        # Add player names
        proposer = Player.query.get(trade.proposer_id)
        receiver = Player.query.get(trade.receiver_id)
        
        trade_dict['proposer_name'] = proposer.username if proposer else "Unknown"
        trade_dict['receiver_name'] = receiver.username if receiver else "Unknown"
        
        return trade_dict

    def propose_trade(self, proposer_id: int, pin: str, receiver_id: int, trade_data: dict) -> dict:
        """Propose a new trade between two players."""
        banker, socketio = self._get_dependencies()
        
        # --- Validation ---
        if proposer_id == receiver_id:
            return {"success": False, "error": "Cannot trade with yourself."}

        proposer = Player.query.get(proposer_id)
        receiver = Player.query.get(receiver_id)

        if not proposer or proposer.pin != pin:
            return {"success": False, "error": "Invalid proposer credentials."}
        if not receiver or not receiver.in_game:
            return {"success": False, "error": "Receiving player not found or not in game."}
            
        # Basic structure validation of trade_data
        proposer_items = trade_data.get('proposer_items', {})
        receiver_items = trade_data.get('receiver_items', {})
        proposer_cash = proposer_items.get('cash', 0)
        receiver_cash = receiver_items.get('cash', 0)
        proposer_prop_ids = proposer_items.get('properties', [])
        receiver_prop_ids = receiver_items.get('properties', [])
        # TODO: Add jail card validation later if implemented

        if not isinstance(proposer_cash, int) or proposer_cash < 0 or \
           not isinstance(receiver_cash, int) or receiver_cash < 0:
            return {"success": False, "error": "Invalid cash amount in trade."}
            
        if not all(isinstance(pid, int) for pid in proposer_prop_ids) or \
           not all(isinstance(pid, int) for pid in receiver_prop_ids):
             return {"success": False, "error": "Invalid property ID format in trade."}

        # Validate proposer can fulfill their side NOW
        validation = self._validate_trade_fulfillment(proposer, proposer_cash, proposer_prop_ids)
        if not validation["success"]:
             return {"success": False, "error": f"You cannot fulfill this trade: {validation['error']}"}
             
        # Validate receiver owns the properties they are offering
        receiver_validation = self._validate_trade_fulfillment(receiver, 0, receiver_prop_ids, check_cash=False)
        if not receiver_validation["success"]:
              return {"success": False, "error": f"Receiver does not own offered properties: {receiver_validation['error']}"}

        # --- Create Trade Record ---
        try:
            new_trade = Trade(
                proposer_id=proposer_id,
                receiver_id=receiver_id,
                proposer_cash=proposer_cash,
                receiver_cash=receiver_cash,
                status='pending'
                # Add details like jail cards later if needed
            )
            db.session.add(new_trade)
            
            # Add property items
            for prop_id in proposer_prop_ids:
                item = TradeItem(trade=new_trade, property_id=prop_id, is_from_proposer=True)
                db.session.add(item)
            for prop_id in receiver_prop_ids:
                item = TradeItem(trade=new_trade, property_id=prop_id, is_from_proposer=False)
                db.session.add(item)
                
            db.session.commit()
            self.logger.info(f"Trade {new_trade.id} proposed by player {proposer_id} to player {receiver_id}.")

            # --- Notify Receiver ---
            game_state = GameState.get_instance()
            if game_state:
                 # Find receiver's socket room/ID if necessary (might need SocketController integration)
                 # For now, emitting generally to the game room, client needs to filter
                 socketio.emit('trade_proposed', {
                     'trade': new_trade.to_dict(),
                     'proposer_name': proposer.username,
                     'receiver_id': receiver_id # Target specific client if possible
                 }, room=game_state.game_id) # Use game room
                 self.logger.info(f"Emitted trade_proposed for trade {new_trade.id} to room {game_state.game_id}")

            return {"success": True, "trade": new_trade.to_dict()}

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Database error proposing trade from {proposer_id} to {receiver_id}: {e}", exc_info=True)
            return {"success": False, "error": "Database error creating trade proposal."}

    def respond_to_trade(self, player_id: int, pin: str, trade_id: int, accept: bool) -> dict:
        """Respond to a pending trade proposal."""
        banker, socketio = self._get_dependencies()

        # --- Validation ---
        trade = Trade.query.get(trade_id)
        if not trade:
            return {"success": False, "error": "Trade not found."}
        if trade.status != 'pending':
            return {"success": False, "error": f"Trade is not pending (status: {trade.status})."}
        if trade.receiver_id != player_id:
            return {"success": False, "error": "You are not the recipient of this trade proposal."}

        receiver = Player.query.get(player_id)
        if not receiver or receiver.pin != pin:
            return {"success": False, "error": "Invalid receiver credentials."}
            
        proposer = Player.query.get(trade.proposer_id)
        if not proposer: # Should not happen if trade exists, but check
            return {"success": False, "error": "Proposing player not found."}


        # --- Process Response ---
        try:
            if not accept:
                trade.status = 'rejected'
                db.session.commit()
                self.logger.info(f"Trade {trade_id} rejected by player {player_id}.")
                # Notify proposer
                game_state = GameState.get_instance()
                if game_state:
                    socketio.emit('trade_rejected', {
                        'trade_id': trade_id,
                        'receiver_name': receiver.username,
                        'proposer_id': proposer.id # Target specific client if possible
                    }, room=game_state.game_id)
                return {"success": True, "message": "Trade rejected."}

            # --- Execute Accepted Trade ---
            # Re-validate fulfillment for BOTH players at the time of acceptance
            proposer_items = trade.items.filter_by(is_from_proposer=True).all()
            receiver_items = trade.items.filter_by(is_from_proposer=False).all()
            proposer_prop_ids = [item.property_id for item in proposer_items]
            receiver_prop_ids = [item.property_id for item in receiver_items]

            proposer_validation = self._validate_trade_fulfillment(proposer, trade.proposer_cash, proposer_prop_ids)
            if not proposer_validation["success"]:
                 trade.status = 'failed_validation' # Mark trade as failed
                 db.session.commit()
                 self.logger.warning(f"Trade {trade_id} acceptance failed: Proposer cannot fulfill. Reason: {proposer_validation['error']}")
                 # Notify both?
                 return {"success": False, "error": f"Trade failed: Proposer cannot fulfill trade. {proposer_validation['error']}"}
                 
            receiver_validation = self._validate_trade_fulfillment(receiver, trade.receiver_cash, receiver_prop_ids)
            if not receiver_validation["success"]:
                 trade.status = 'failed_validation'
                 db.session.commit()
                 self.logger.warning(f"Trade {trade_id} acceptance failed: Receiver cannot fulfill. Reason: {receiver_validation['error']}")
                 # Notify both?
                 return {"success": False, "error": f"Trade failed: You cannot fulfill trade. {receiver_validation['error']}"}

            # Perform the exchange
            description = f"Trade {trade_id} between {proposer.username} and {receiver.username}"

            # 1. Cash Exchange (using Banker)
            if trade.proposer_cash > 0:
                result = banker.player_pays_player(proposer.id, receiver.id, trade.proposer_cash, description + " (proposer cash)")
                if not result["success"]: raise ValueError(f"Banker error: {result['error']}") # Raise to trigger rollback
            if trade.receiver_cash > 0:
                result = banker.player_pays_player(receiver.id, proposer.id, trade.receiver_cash, description + " (receiver cash)")
                if not result["success"]: raise ValueError(f"Banker error: {result['error']}")

            # 2. Property Exchange
            for item in proposer_items:
                prop = Property.query.get(item.property_id)
                if not prop or prop.owner_id != proposer.id: raise ValueError(f"Property {item.property_id} inconsistency.")
                prop.owner_id = receiver.id
                # Reset mortgage status? Or trade mortgaged properties? Let's assume clear for now.
                prop.is_mortgaged = False 
                db.session.add(prop)
            for item in receiver_items:
                prop = Property.query.get(item.property_id)
                if not prop or prop.owner_id != receiver.id: raise ValueError(f"Property {item.property_id} inconsistency.")
                prop.owner_id = proposer.id
                prop.is_mortgaged = False
                db.session.add(prop)
                
            # TODO: Jail Card Exchange (if implemented)

            # Update Trade Status
            trade.status = 'completed'
            db.session.commit()
            self.logger.info(f"Trade {trade_id} completed between player {proposer.id} and {receiver.id}.")

            # Notify Both Players
            game_state = GameState.get_instance()
            if game_state:
                 socketio.emit('trade_completed', {
                     'trade': trade.to_dict(),
                     'proposer_name': proposer.username,
                     'receiver_name': receiver.username
                 }, room=game_state.game_id)

            return {"success": True, "message": "Trade completed successfully.", "trade": trade.to_dict()}

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error responding to trade {trade_id} by player {player_id}: {e}", exc_info=True)
            # Attempt to mark trade as failed if exception occurred during execution
            try:
                trade.status = 'failed_execution'
                db.session.commit()
            except Exception as e2:
                 self.logger.error(f"Failed to mark trade {trade_id} as failed after error: {e2}")
            return {"success": False, "error": "Internal server error processing trade response."}


    def cancel_trade(self, player_id: int, pin: str, trade_id: int) -> dict:
        """Cancel a pending trade proposal made by the player."""
        _, socketio = self._get_dependencies()
        
        # --- Validation ---
        trade = Trade.query.get(trade_id)
        if not trade:
            return {"success": False, "error": "Trade not found."}
        if trade.status != 'pending':
            return {"success": False, "error": f"Cannot cancel trade with status '{trade.status}'."}
        if trade.proposer_id != player_id:
            return {"success": False, "error": "Only the proposer can cancel this trade."}

        proposer = Player.query.get(player_id)
        if not proposer or proposer.pin != pin:
            return {"success": False, "error": "Invalid proposer credentials."}

        # --- Update Status ---
        try:
            trade.status = 'cancelled'
            db.session.commit()
            self.logger.info(f"Trade {trade_id} cancelled by proposer {player_id}.")

            # Notify Receiver
            receiver = Player.query.get(trade.receiver_id)
            game_state = GameState.get_instance()
            if receiver and game_state:
                 socketio.emit('trade_cancelled', {
                     'trade_id': trade_id,
                     'proposer_name': proposer.username,
                     'receiver_id': receiver.id # Target specific client if possible
                 }, room=game_state.game_id)

            return {"success": True, "message": "Trade cancelled."}

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Database error cancelling trade {trade_id} by player {player_id}: {e}", exc_info=True)
            return {"success": False, "error": "Database error cancelling trade."}

    def list_player_trades(self, player_id: int, pin: str) -> dict:
         """List pending trades involving the player (proposed or received)."""
         # --- Validation ---
         player = Player.query.get(player_id)
         if not player or player.pin != pin:
            return {"success": False, "error": "Invalid player credentials."}
            
         try:
            proposed_trades = Trade.query.filter_by(proposer_id=player_id, status='pending').all()
            received_trades = Trade.query.filter_by(receiver_id=player_id, status='pending').all()
            
            return {
                "success": True,
                "proposed": [t.to_dict() for t in proposed_trades],
                "received": [t.to_dict() for t in received_trades]
            }
         except Exception as e:
            self.logger.error(f"Database error listing trades for player {player_id}: {e}", exc_info=True)
            return {"success": False, "error": "Database error listing trades."}
            
    def get_trade_details(self, trade_id: int, player_id: int, pin: str) -> dict:
         """Get details for a specific trade if the player is involved."""
         # --- Validation ---
         player = Player.query.get(player_id)
         if not player or player.pin != pin:
            return {"success": False, "error": "Invalid player credentials."}

         trade = Trade.query.get(trade_id)
         if not trade:
            return {"success": False, "error": "Trade not found."}
            
         if trade.proposer_id != player_id and trade.receiver_id != player_id:
             return {"success": False, "error": "You are not involved in this trade."}
             
         return {"success": True, "trade": trade.to_dict()}
         
    def _validate_trade_fulfillment(self, player: Player, cash_offered: int, property_ids_offered: list, check_cash=True) -> dict:
        """Helper to check if a player can fulfill their side of a trade."""
        if check_cash and player.cash < cash_offered:
            return {"success": False, "error": f"Insufficient cash (needs ${cash_offered}, has ${player.cash})"}

        owned_props = {prop.id for prop in player.properties}
        for prop_id in property_ids_offered:
            if prop_id not in owned_props:
                 prop_name = Property.query.get(prop_id).name if Property.query.get(prop_id) else f"ID {prop_id}"
                 return {"success": False, "error": f"Does not own property '{prop_name}'"}
            # Check if property is mortgaged - trades usually involve clear properties
            prop = Property.query.get(prop_id)
            if prop.is_mortgaged:
                 return {"success": False, "error": f"Property '{prop.name}' is mortgaged"}
                 
        # TODO: Add check for jail cards if implemented
        
        return {"success": True}

    # Placeholder for admin approval logic if needed later
    def admin_approve_trade(self, trade_id):
         logger.warning("admin_approve_trade not implemented.")
         return {"success": False, "error": "Admin approval feature not implemented."}

def register_trade_socket_events(socketio, app_config):
    """Register socket event handlers for trade-related actions."""
    logger.info("Registering trade socket events")
    
    # Get required controllers/services from app_config
    trade_controller = app_config.get('trade_controller')
    
    if not trade_controller:
        logger.error("Missing trade controller for trade socket events")
        return
        
    @socketio.on('propose_trade')
    def handle_propose_trade(data):
        """Handle a player proposing a trade"""
        logger.info(f"[Socket] Received propose_trade event: {data}")
        player_id = data.get('player_id')
        pin = data.get('pin')
        receiver_id = data.get('receiver_id')
        trade_data = data.get('trade_data', {})
        sid = request.sid
        
        if not player_id or not pin or not receiver_id or not trade_data:
            emit('trade_error', {'error': 'Missing required trade data'}, room=sid)
            return
            
        result = trade_controller.propose_trade(player_id, pin, receiver_id, trade_data)
        
        if result.get('success'):
            emit('trade_action_result', {
                'action': 'propose',
                'success': True,
                'message': result.get('message', 'Trade proposed successfully')
            }, room=sid)
        else:
            emit('trade_error', {
                'action': 'propose',
                'error': result.get('error', 'Failed to propose trade')
            }, room=sid)
    
    @socketio.on('respond_to_trade')
    def handle_respond_to_trade(data):
        """Handle a player responding to a trade (accept/reject)"""
        logger.info(f"[Socket] Received respond_to_trade event: {data}")
        player_id = data.get('player_id')
        pin = data.get('pin')
        trade_id = data.get('trade_id')
        accept = data.get('accept', False)
        sid = request.sid
        
        if not player_id or not pin or not trade_id:
            emit('trade_error', {'error': 'Missing required response data'}, room=sid)
            return
            
        result = trade_controller.respond_to_trade(player_id, pin, trade_id, accept)
        
        if result.get('success'):
            emit('trade_action_result', {
                'action': 'respond',
                'accepted': accept,
                'success': True,
                'message': result.get('message', f"Trade {'accepted' if accept else 'rejected'} successfully")
            }, room=sid)
        else:
            emit('trade_error', {
                'action': 'respond',
                'error': result.get('error', f"Failed to {'accept' if accept else 'reject'} trade")
            }, room=sid)
    
    @socketio.on('cancel_trade')
    def handle_cancel_trade(data):
        """Handle a player cancelling a trade they proposed"""
        logger.info(f"[Socket] Received cancel_trade event: {data}")
        player_id = data.get('player_id')
        pin = data.get('pin')
        trade_id = data.get('trade_id')
        sid = request.sid
        
        if not player_id or not pin or not trade_id:
            emit('trade_error', {'error': 'Missing required cancellation data'}, room=sid)
            return
            
        result = trade_controller.cancel_trade(player_id, pin, trade_id)
        
        if result.get('success'):
            emit('trade_action_result', {
                'action': 'cancel',
                'success': True,
                'message': result.get('message', 'Trade cancelled successfully')
            }, room=sid)
        else:
            emit('trade_error', {
                'action': 'cancel',
                'error': result.get('error', 'Failed to cancel trade')
            }, room=sid)
    
    @socketio.on('get_pending_trades')
    def handle_get_pending_trades(data):
        """Handle request for pending trades"""
        logger.info(f"[Socket] Received get_pending_trades event: {data}")
        player_id = data.get('player_id')
        sid = request.sid
        
        if not player_id:
            emit('trade_error', {'error': 'Missing player ID'}, room=sid)
            return
            
        result = trade_controller.get_pending_trades(player_id)
        
        if result.get('success'):
            emit('pending_trades', {
                'trades': result.get('trades', [])
            }, room=sid)
        else:
            emit('trade_error', {
                'action': 'get_pending',
                'error': result.get('error', 'Failed to get pending trades')
            }, room=sid)
    
    @socketio.on('get_trade_history')
    def handle_get_trade_history(data):
        """Handle request for trade history"""
        logger.info(f"[Socket] Received get_trade_history event: {data}")
        player_id = data.get('player_id')
        limit = data.get('limit', 10)
        sid = request.sid
        
        if not player_id:
            emit('trade_error', {'error': 'Missing player ID'}, room=sid)
            return
            
        result = trade_controller.get_trade_history(player_id, limit)
        
        if result.get('success'):
            emit('trade_history', {
                'history': result.get('trades', [])
            }, room=sid)
        else:
            emit('trade_error', {
                'action': 'get_history',
                'error': result.get('error', 'Failed to get trade history')
            }, room=sid)
    
    logger.info("Trade socket events registered successfully") 