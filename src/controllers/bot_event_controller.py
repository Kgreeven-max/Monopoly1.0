import logging
import random
import datetime
from flask_socketio import emit
from flask import request, current_app
from src.models import db
from src.models.player import Player
from src.models.property import Property
from src.models.game_state import GameState
from src.models.bot_events import (
    TradeProposal, PropertyAuction, MarketCrash, EconomicBoom, BotChallenge, 
    process_restore_market_prices, process_restore_property_prices
)

logger = logging.getLogger(__name__)

# Keep track of active events
active_events = {}

def register_bot_event_handlers(socketio, app_config):
    """Register socket event handlers for bot events"""
    
    @socketio.on('respond_to_trade_proposal')
    def handle_trade_response(data):
        """Handle a player response to a trade proposal"""
        player_id = data.get('player_id')
        pin = data.get('pin')
        trade_id = data.get('trade_id')
        accept = data.get('accept', False)
        
        # Validate player
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            emit('event_error', {
                'error': 'Invalid player credentials'
            })
            return
        
        # Check if trade is active
        if trade_id not in active_events or active_events[trade_id]['type'] != 'trade_proposal':
            emit('event_error', {
                'error': 'Trade offer no longer active'
            })
            return
        
        # Get trade proposal event object
        trade_event = active_events[trade_id]['event']
        
        # Execute trade if accepted
        result = trade_event.execute(accept)
        
        # Remove from active events
        del active_events[trade_id]
        
        # Broadcast result to all players
        socketio.emit('trade_proposal_result', {
            'trade_id': trade_id,
            'player_id': player_id,
            'player_name': player.username,
            'accepted': accept,
            'result': result
        })
    
    @socketio.on('respond_to_challenge')
    def handle_challenge_response(data):
        """Handle a player response to a bot challenge"""
        player_id = data.get('player_id')
        pin = data.get('pin')
        challenge_id = data.get('challenge_id')
        answer = data.get('answer')
        
        # Validate player
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            emit('event_error', {
                'error': 'Invalid player credentials'
            })
            return
        
        # Check if challenge is active
        if challenge_id not in active_events or active_events[challenge_id]['type'] != 'bot_challenge':
            emit('event_error', {
                'error': 'Challenge no longer active'
            })
            return
        
        # Get challenge data and event object
        challenge_event_info = active_events[challenge_id]
        challenge_data = challenge_event_info['data']
        challenge_event = challenge_event_info['event']
        bot_id = challenge_data.get('bot_id')
        bot = Player.query.get(bot_id)
        
        # Check answer (simplified for now, could be more complex depending on challenge type)
        challenge_type = challenge_data.get('challenge_type')
        correct = False
        
        if challenge_type == 'dice_prediction':
            correct = answer == challenge_data.get('correct_answer')
        elif challenge_type == 'property_quiz':
            correct = answer == challenge_data.get('correct_answer')
        elif challenge_type == 'price_guess':
            property_price = challenge_data.get('property_price', 0)
            # Allow for a small margin of error
            correct = abs(answer - property_price) <= 20
        elif challenge_type == 'quick_calculation':
            correct = answer == challenge_data.get('correct_answer')
        
        # If correct, award prize using the event object
        if correct:
            result = challenge_event.execute(player_id)
        else:
            result = {
                'success': False,
                'message': f"{player.username} gave an incorrect answer to {bot.username if bot else 'the bot'}'s challenge."
            }
        
        # Broadcast result to all players
        socketio.emit('challenge_result', {
            'challenge_id': challenge_id,
            'player_id': player_id,
            'player_name': player.username,
            'correct': correct,
            'result': result
        })
        
        # Remove player from pending list
        if 'pending_players' in challenge_data and player_id in challenge_data['pending_players']:
             challenge_data['pending_players'].remove(player_id)

        # Remove from active events if everyone has answered
        if not challenge_data.get('pending_players'):
            if challenge_id in active_events: # Check again in case timeout removed it
                del active_events[challenge_id]
                logger.info(f"Challenge {challenge_id} completed.")
    
    @socketio.on('market_event_info')
    def handle_market_event_info(data):
        """Provide information about active market events"""
        player_id = data.get('player_id')
        pin = data.get('pin')
        
        # Validate player
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            emit('event_error', {
                'error': 'Invalid player credentials'
            })
            return
        
        # Get information about active market events (crash/boom)
        market_events = {}
        
        # Check properties for discounts/premiums
        properties = Property.query.all()
        for prop in properties:
            if prop.discount_percentage > 0:
                group = prop.group_name
                if group not in market_events:
                    market_events[group] = {
                        'type': 'crash',
                        'percentage': prop.discount_percentage,
                        'properties': []
                    }
                market_events[group]['properties'].append({
                    'id': prop.id,
                    'name': prop.name,
                    'original_price': prop.current_price + prop.discount_amount,
                    'current_price': prop.current_price,
                    'discount': prop.discount_amount
                })
            
            if prop.premium_percentage > 0:
                group = prop.group_name
                if group not in market_events:
                    market_events[group] = {
                        'type': 'boom',
                        'percentage': prop.premium_percentage,
                        'properties': []
                    }
                market_events[group]['properties'].append({
                    'id': prop.id,
                    'name': prop.name,
                    'original_price': prop.current_price - prop.premium_amount,
                    'current_price': prop.current_price,
                    'premium': prop.premium_amount
                })
        
        # Return information
        emit('market_events_info', {
            'market_events': market_events
        }, room=request.sid)


def handle_bot_event(socketio, app_config, event_data):
    """Process a bot-triggered event"""
    event_type = event_data.get('event_type')
    
    # Generate unique ID for this event
    import uuid
    event_id = str(uuid.uuid4())
    
    if event_type == 'trade_proposal':
        return _handle_trade_proposal(event_id, event_data, socketio, app_config)
    elif event_type == 'property_auction':
        return _handle_property_auction(event_id, event_data, socketio, app_config)
    elif event_type == 'market_crash':
        return _handle_market_crash(event_id, event_data, socketio, app_config)
    elif event_type == 'economic_boom':
        return _handle_economic_boom(event_id, event_data, socketio, app_config)
    elif event_type == 'bot_challenge':
        return _handle_bot_challenge(event_id, event_data, socketio, app_config)
    else:
        logger.warning(f"Unknown bot event type: {event_type}")
        return {
            'success': False,
            'message': f"Unknown event type: {event_type}"
        }


def _handle_trade_proposal(event_id, event_data, socketio, app_config):
    """Handle a trade proposal from a bot"""
    if not event_data.get('success'):
        return event_data
    
    # Get dependencies
    game_state = app_config.get('game_state_instance')
    banker = app_config.get('banker')
    if not game_state or not banker:
         logger.error("Missing GameState or Banker for trade proposal.")
         return {'success': False, 'error': 'Server configuration error.'}
         
    bot_id = event_data.get('bot_id')
    target_player_id = event_data.get('target_player_id')
    
    offered_properties = []
    for prop_data in event_data.get('offered_properties', []):
        prop = Property.query.get(prop_data.get('id'))
        if prop:
            offered_properties.append(prop)
    
    requested_properties = []
    for prop_data in event_data.get('requested_properties', []):
        prop = Property.query.get(prop_data.get('id'))
        if prop:
            requested_properties.append(prop)
    
    # Create trade proposal object, passing dependencies
    trade_proposal = TradeProposal(game_state, bot_id, banker)
    target_player = Player.query.get(target_player_id)
    if not target_player:
        return {'success': False, 'error': 'Target player not found.'}
        
    trade_proposal.target_player = target_player
    trade_proposal.offered_properties = offered_properties
    trade_proposal.requested_properties = requested_properties
    trade_proposal.cash_amount = event_data.get('cash_amount', 0)
    trade_proposal.direction = event_data.get('cash_direction', 'pay')
    
    # Store event for later response
    active_events[event_id] = {
        'type': 'trade_proposal',
        'event': trade_proposal,
        'data': event_data
    }
    
    # Add event ID to data
    event_data['event_id'] = event_id
    
    # Send event to target player
    socketio.emit('bot_trade_proposal', event_data, room=f"player_{target_player_id}")
    
    # Send notification to all other players
    bot_player = Player.query.get(bot_id)
    bot_name = bot_player.username if bot_player else "A bot"
    message = event_data.get('message', f"{bot_name} has proposed a trade with {target_player.username}.")
    socketio.emit('game_notification', {
        'message': message,
        'event_type': 'trade_proposal',
        'timestamp': datetime.datetime.now().isoformat()
    })
    
    # Set a timeout for the trade (e.g., 2 minutes)
    import threading
    def cancel_trade():
        if event_id in active_events:
            logger.info(f"Trade proposal {event_id} expired.")
            del active_events[event_id]
            socketio.emit('trade_proposal_expired', {
                'event_id': event_id,
                'message': f"Trade offer from {bot_name} to {target_player.username} has expired."
            })
    
    timeout_duration = app_config.get('TRADE_TIMEOUT', 120)
    timer = threading.Timer(timeout_duration, cancel_trade)
    timer.daemon = True
    timer.start()
    
    return {
        'success': True,
        'message': f"Trade proposal sent to {target_player.username}",
        'event_id': event_id
    }


def _handle_property_auction(event_id, event_data, socketio, app_config):
    """Handle a property auction initiated by a bot"""
    if not event_data.get('success'):
        return event_data
        
    # Get dependencies
    game_state = app_config.get('game_state_instance')
    auction_system = app_config.get('auction_system')
    if not game_state or not auction_system:
         logger.error("Missing GameState or AuctionSystem for property auction.")
         return {'success': False, 'error': 'Server configuration error.'}
         
    bot_id = event_data.get('bot_id')
    property_id = event_data.get('property_id')
    minimum_bid = event_data.get('minimum_bid', 0)
    
    # Use AuctionSystem to start the auction directly
    result = auction_system.start_auction(property_id, minimum_bid=minimum_bid, initiated_by=f"bot_{bot_id}")
    
    # Broadcast auction result (AuctionSystem likely broadcasts details)
    if result.get('success'):
         logger.info(f"Bot {bot_id} initiated auction {result.get('auction_id')} for property {property_id}")
    else:
        logger.error(f"Bot {bot_id} failed to initiate auction for property {property_id}: {result.get('error')}")
        # Emit an error specific to the bot initiator?
        # socketio.emit('bot_auction_error', {'bot_id': bot_id, 'error': result.get('error')}, room=?) 
        
    return result


def _handle_market_crash(event_id, event_data, socketio, app_config):
    """Handle a market crash event"""
    if not event_data.get('success'):
        return event_data
        
    # Get dependencies
    game_state = app_config.get('game_state_instance')
    banker = app_config.get('banker')
    if not game_state or not banker:
         logger.error("Missing GameState or Banker for market crash.")
         return {'success': False, 'error': 'Server configuration error.'}
         
    bot_id = event_data.get('bot_id')
    crash_percentage = event_data.get('crash_percentage', 15)
    affected_groups = event_data.get('affected_groups', [])
    
    # Create market crash object, passing dependencies
    market_crash = MarketCrash(game_state, bot_id, banker)
    market_crash.crash_percentage = crash_percentage
    market_crash.affected_groups = affected_groups
    
    # Execute the market crash
    result = market_crash.execute()
    
    # Broadcast event to all players
    socketio.emit('market_event', {
        'event_id': event_id,
        'event_type': 'market_crash',
        'event_data': event_data,
        'result': result
    })
    
    return result


def _handle_economic_boom(event_id, event_data, socketio, app_config):
    """Handle an economic boom event"""
    if not event_data.get('success'):
        return event_data
        
    # Get dependencies
    game_state = app_config.get('game_state_instance')
    banker = app_config.get('banker')
    if not game_state or not banker:
         logger.error("Missing GameState or Banker for economic boom.")
         return {'success': False, 'error': 'Server configuration error.'}
         
    bot_id = event_data.get('bot_id')
    boom_percentage = event_data.get('boom_percentage', 15)
    affected_groups = event_data.get('affected_groups', [])
    
    # Create economic boom object, passing dependencies
    economic_boom = EconomicBoom(game_state, bot_id, banker)
    economic_boom.boom_percentage = boom_percentage
    economic_boom.affected_groups = affected_groups
    
    # Execute the economic boom
    result = economic_boom.execute()
    
    # Broadcast event to all players
    socketio.emit('market_event', {
        'event_id': event_id,
        'event_type': 'economic_boom',
        'event_data': event_data,
        'result': result
    })
    
    return result


def _handle_bot_challenge(event_id, event_data, socketio, app_config):
    """Handle a challenge from a bot"""
    if not event_data.get('success'):
        return event_data
        
    # Get dependencies
    game_state = app_config.get('game_state_instance')
    banker = app_config.get('banker')
    if not game_state or not banker:
         logger.error("Missing GameState or Banker for bot challenge.")
         return {'success': False, 'error': 'Server configuration error.'}
         
    bot_id = event_data.get('bot_id')
    challenge_type = event_data.get('challenge_type')
    reward = event_data.get('reward', {'type': 'cash', 'amount': 100})
    
    # Create bot challenge object, passing dependencies
    bot_challenge = BotChallenge(game_state, bot_id, banker)
    bot_challenge.challenge_type = challenge_type
    bot_challenge.reward = reward
    
    # Generate challenge data based on type
    challenge_data = bot_challenge.generate_challenge_data()
    if not challenge_data:
        logger.error(f"Failed to generate challenge data for type: {challenge_type}")
        return {'success': False, 'error': 'Failed to generate challenge data'}
        
    # Add bot info to challenge data
    bot_player = Player.query.get(bot_id)
    bot_name = bot_player.username if bot_player else "A bot"
    challenge_data['bot_id'] = bot_id
    challenge_data['bot_name'] = bot_name
    challenge_data['message'] = event_data.get('message', f"{bot_name} issues a challenge!")

    # Get human players as potential challengers
    human_players = Player.query.filter(
        Player.in_game == True,
        Player.is_bot == False
    ).all()
    
    if not human_players:
        logger.info("No human players available for the challenge.")
        return {'success': False, 'error': 'No human players to challenge'}
        
    challenge_data['pending_players'] = [p.id for p in human_players]
    
    # Store event for later responses
    active_events[event_id] = {
        'type': 'bot_challenge',
        'event': bot_challenge,
        'data': challenge_data
    }
    
    # Add event ID to data to be emitted
    emit_data = event_data.copy()
    emit_data['event_id'] = event_id
    emit_data['challenge_data'] = challenge_data
    emit_data['message'] = challenge_data['message']
    
    # Send challenge to all human players
    for player in human_players:
        socketio.emit('bot_challenge', emit_data, room=f"player_{player.id}")
    
    # Send notification to all players (including bots?)
    socketio.emit('game_notification', {
        'message': challenge_data['message'],
        'event_type': 'bot_challenge',
        'timestamp': datetime.datetime.now().isoformat()
    })
    
    # Set a timeout for the challenge
    import threading
    
    def end_challenge():
        if event_id in active_events:
            logger.info(f"Challenge {event_id} expired.")
            socketio.emit('challenge_expired', {
                'event_id': event_id,
                'message': f"Time's up! {bot_name}'s challenge has ended.",
            })
            
            del active_events[event_id]
    
    challenge_timeout = app_config.get('CHALLENGE_TIMEOUT', 60)
    timer = threading.Timer(challenge_timeout, end_challenge)
    timer.daemon = True
    timer.start()
    
    return {
        'success': True,
        'message': f"Challenge sent to {len(human_players)} players",
        'event_id': event_id
    }


def handle_scheduled_event(socketio, app_config, event_type, event_data):
    """Handle a scheduled event (e.g., restoring market prices)"""
    
    # Get dependencies
    game_state = app_config.get('game_state_instance')
    banker = app_config.get('banker')
    if not game_state or not banker:
         logger.error(f"Missing GameState or Banker for scheduled event: {event_type}")
         return {'success': False, 'error': 'Server configuration error.'}
         
    if event_type == "restore_market_prices":
        result = process_restore_market_prices(event_data, game_state, banker)
        
        socketio.emit('market_prices_restored', {
            'affected_groups': event_data.get('affected_groups', []),
            'result': result
        })
        
        return result
    elif event_type == "restore_property_prices":
        result = process_restore_property_prices(event_data, game_state, banker)
        
        socketio.emit('property_prices_restored', {
            'affected_properties': event_data.get('affected_properties', []),
            'result': result
        })
        
        return result
    
    return {
        'success': False,
        'message': f"Unknown scheduled event type: {event_type}"
    } 