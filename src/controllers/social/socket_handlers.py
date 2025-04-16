import logging
from flask_socketio import emit, join_room, leave_room
from src.models.social.chat import Channel, ChannelMember, Message, MessageReaction
from src.models.social.alliance import Alliance, AllianceMember, AllianceInvite
from src.models.social.reputation import ReputationScore, ReputationEvent
from src.models.player import Player
from src.models import db
from flask import current_app, request
# from src.controllers.social.auth import verify_socket_token # Module not found and function unused

logger = logging.getLogger(__name__)

def register_social_socket_handlers(socketio, social_controller):
    """Register additional socket handlers for social features.
    
    This function is meant to be called from the SocketController after 
    initializing the SocialController.
    
    Args:
        socketio: The Flask-SocketIO instance
        social_controller: An instance of SocialController
    """
    
    @socketio.on('channel_typing')
    def handle_channel_typing(data):
        """Broadcast typing indicator in a channel"""
        player_id = data.get('player_id')
        channel_id = data.get('channel_id')
        is_typing = data.get('typing', True)
        
        if not player_id or not channel_id:
            return
        
        # Verify player is in the channel
        membership = ChannelMember.query.filter_by(
            player_id=player_id,
            channel_id=channel_id
        ).first()
        
        if not membership:
            return
        
        player = Player.query.get(player_id)
        if not player:
            return
        
        # Broadcast typing indicator to all users in the channel
        socketio.emit('channel_typing_update', {
            'channel_id': channel_id,
            'player_id': player_id,
            'player_name': player.username,
            'typing': is_typing,
            'timestamp': social_controller.get_timestamp()
        }, room=f"channel_{channel_id}")
    
    @socketio.on('alliance_proposal')
    def handle_alliance_proposal(data):
        """Handle proposal of a new alliance benefit"""
        alliance_id = data.get('alliance_id')
        proposer_id = data.get('proposer_id')
        benefit_type = data.get('benefit_type')
        benefit_value = data.get('benefit_value')
        description = data.get('description')
        
        if not all([alliance_id, proposer_id, benefit_type, benefit_value]):
            emit('proposal_error', {
                'error': 'Missing required parameters'
            })
            return
        
        # Use the social controller to handle the proposal
        result = social_controller.propose_alliance_benefit(
            alliance_id=alliance_id,
            proposer_id=proposer_id,
            benefit_type=benefit_type,
            benefit_value=benefit_value,
            description=description
        )
        
        if not result.get('success'):
            emit('proposal_error', {
                'error': result.get('error', 'Error creating proposal')
            })
    
    @socketio.on('alliance_vote')
    def handle_alliance_vote(data):
        """Handle voting on an alliance proposal"""
        proposal_id = data.get('proposal_id')
        voter_id = data.get('voter_id')
        vote = data.get('vote')  # 'yes', 'no', or 'abstain'
        
        if not all([proposal_id, voter_id, vote]):
            emit('vote_error', {
                'error': 'Missing required parameters'
            })
            return
        
        # Use the social controller to handle the vote
        result = social_controller.vote_on_proposal(
            proposal_id=proposal_id,
            voter_id=voter_id,
            vote=vote
        )
        
        if not result.get('success'):
            emit('vote_error', {
                'error': result.get('error', 'Error recording vote')
            })
    
    @socketio.on('reputation_feedback')
    def handle_reputation_feedback(data):
        """Handle player providing reputation feedback for another player"""
        rater_id = data.get('rater_id')
        rated_id = data.get('rated_id')
        rating = data.get('rating')  # 1-5 star rating
        category = data.get('category', 'general')
        context = data.get('context', '')
        
        if not all([rater_id, rated_id, rating]):
            emit('feedback_error', {
                'error': 'Missing required parameters'
            })
            return
        
        # Use the social controller to record the reputation feedback
        result = social_controller.record_reputation_feedback(
            rater_id=rater_id,
            rated_id=rated_id,
            rating=rating,
            category=category,
            context=context
        )
        
        if not result.get('success'):
            emit('feedback_error', {
                'error': result.get('error', 'Error recording feedback')
            })
    
    @socketio.on('join_public_channels')
    def handle_join_public_channels(data):
        """Join a player to all public channels automatically"""
        player_id = data.get('player_id')
        
        if not player_id:
            emit('channel_error', {
                'error': 'Missing player_id parameter'
            })
            return
        
        # Get all public channels
        public_channels = Channel.query.filter_by(
            channel_type='public'
        ).all()
        
        joined_channels = []
        
        # Join player to each public channel
        for channel in public_channels:
            # Skip if already a member
            existing = ChannelMember.query.filter_by(
                player_id=player_id,
                channel_id=channel.id
            ).first()
            
            if existing:
                continue
                
            # Join the channel in the database
            result = social_controller.join_channel(player_id, channel.id)
            
            if result.get('success'):
                # Add to websocket room
                join_room(f"channel_{channel.id}")
                joined_channels.append({
                    'id': channel.id,
                    'name': channel.name
                })
        
        # Send success response with joined channels
        emit('public_channels_joined', {
            'success': True,
            'channels': joined_channels
        })
    
    @socketio.on('search_players')
    def handle_search_players(data):
        """Search for players to invite to a channel or alliance"""
        search_term = data.get('search_term', '')
        exclude_ids = data.get('exclude_ids', [])
        limit = data.get('limit', 10)
        
        # Search for players
        players = Player.query.filter(
            Player.username.ilike(f'%{search_term}%')
        ).limit(limit).all()
        
        # Filter out excluded players
        filtered_players = [
            {
                'id': p.id,
                'username': p.username
            } for p in players if p.id not in exclude_ids
        ]
        
        # Return results
        emit('player_search_results', {
            'success': True,
            'players': filtered_players
        })

    return socketio 