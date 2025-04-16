import logging
from datetime import datetime
from src.models import db
from src.models.social.chat import Channel, ChannelMember, Message, MessageReaction
from flask_socketio import emit, join_room, leave_room
from flask import request, current_app

logger = logging.getLogger(__name__)

class ChatController:
    """Controller for the enhanced chat system"""
    
    def __init__(self, socketio, app_config=None):
        """Initialize ChatController with SocketIO instance and optional app_config."""
        self.socketio = socketio
        self.app_config = app_config # Store app_config if provided
        self.EMOJI_REACTIONS = ["👍", "👎", "😂", "😮", "😢", "🎉", "💰", "🏠", "🎲", "🚓"]
        logger.info("ChatController initialized")
        
        # Potentially retrieve other dependencies from app_config here if needed
        # e.g., self.core_socket_controller = app_config.get('socket_controller')
    
    def create_channel(self, creator_id, name, description=None, members=None, channel_type='public'):
        """Create a new chat channel"""
        try:
            # Input validation
            if not name or len(name) < 3 or len(name) > 100:
                return {
                    "success": False,
                    "error": "Invalid channel name (must be 3-100 characters)"
                }
                
            if description and len(description) > 255:
                return {
                    "success": False,
                    "error": "Description too long (max 255 characters)"
                }
            
            if channel_type not in ['public', 'private', 'group']:
                return {
                    "success": False,
                    "error": "Invalid channel type"
                }
            
            # Create channel
            channel = Channel(
                name=name,
                description=description or f"Channel created by player {creator_id}",
                type=channel_type,
                created_by=creator_id
            )
            
            db.session.add(channel)
            db.session.flush()  # Flush to get channel ID
            
            # Add creator as member
            creator_member = ChannelMember(
                channel_id=channel.id,
                player_id=creator_id
            )
            db.session.add(creator_member)
            
            # Add additional members if provided
            if members:
                for member_id in members:
                    if member_id != creator_id:  # Creator already added
                        member = ChannelMember(
                            channel_id=channel.id,
                            player_id=member_id
                        )
                        db.session.add(member)
            
            db.session.commit()
            
            # Notify channel creation via WebSocket to relevant members
            self._notify_channel_creation(channel)
            
            return {
                "success": True,
                "channel_id": channel.id,
                "channel": channel.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating channel: {str(e)}")
            return {
                "success": False,
                "error": f"Error creating channel: {str(e)}"
            }
    
    def send_message(self, sender_id, channel_id, content, message_type='text'):
        """Send a message to a channel"""
        try:
            # Input validation
            if not content or len(content) > 1000:
                return {
                    "success": False,
                    "error": "Invalid message content (must be 1-1000 characters)"
                }
            
            # Check if channel exists
            channel = Channel.query.get(channel_id)
            if not channel:
                return {
                    "success": False,
                    "error": "Channel not found"
                }
            
            # Check if sender is a member of the channel (if not public)
            if channel.type != 'public' and not channel.is_member(sender_id):
                return {
                    "success": False,
                    "error": "You are not a member of this channel"
                }
            
            # Create message
            message = Message(
                channel_id=channel_id,
                sender_id=sender_id,
                content=content,
                type=message_type
            )
            
            db.session.add(message)
            db.session.commit()
            
            # Emit message to channel members
            self._broadcast_message(message)
            
            return {
                "success": True,
                "message_id": message.id,
                "message": message.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error sending message: {str(e)}")
            return {
                "success": False,
                "error": f"Error sending message: {str(e)}"
            }
    
    def add_reaction(self, player_id, message_id, emoji):
        """Add an emoji reaction to a message"""
        try:
            # Input validation
            if emoji not in self.EMOJI_REACTIONS:
                return {
                    "success": False,
                    "error": f"Invalid emoji. Allowed emojis: {', '.join(self.EMOJI_REACTIONS)}"
                }
            
            # Check if message exists
            message = Message.query.get(message_id)
            if not message:
                return {
                    "success": False,
                    "error": "Message not found"
                }
            
            # Check if player is a member of the channel
            channel = Channel.query.get(message.channel_id)
            if channel.type != 'public' and not channel.is_member(player_id):
                return {
                    "success": False,
                    "error": "You are not a member of this channel"
                }
            
            # Add reaction
            result = message.add_reaction(player_id, emoji)
            if not result:
                return {
                    "success": False,
                    "error": "You've already reacted with this emoji"
                }
            
            db.session.commit()
            
            # Emit reaction update to channel members
            self._broadcast_reaction(message, player_id, emoji)
            
            return {
                "success": True,
                "message_id": message_id,
                "emoji": emoji
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding reaction: {str(e)}")
            return {
                "success": False,
                "error": f"Error adding reaction: {str(e)}"
            }
    
    def remove_reaction(self, player_id, message_id, emoji):
        """Remove an emoji reaction from a message"""
        try:
            # Check if message exists
            message = Message.query.get(message_id)
            if not message:
                return {
                    "success": False,
                    "error": "Message not found"
                }
            
            # Remove reaction
            result = message.remove_reaction(player_id, emoji)
            if not result:
                return {
                    "success": False,
                    "error": "You don't have this reaction to remove"
                }
            
            db.session.commit()
            
            # Emit reaction update to channel members
            self._broadcast_reaction_removal(message, player_id, emoji)
            
            return {
                "success": True,
                "message_id": message_id,
                "emoji": emoji
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error removing reaction: {str(e)}")
            return {
                "success": False,
                "error": f"Error removing reaction: {str(e)}"
            }
    
    def join_channel(self, player_id, channel_id):
        """Join a channel"""
        try:
            # Check if channel exists
            channel = Channel.query.get(channel_id)
            if not channel:
                return {
                    "success": False,
                    "error": "Channel not found"
                }
            
            # Check if channel is joinable (public or group)
            if channel.type == 'private':
                return {
                    "success": False,
                    "error": "Cannot join a private channel directly"
                }
            
            # Add player as member
            if channel.add_member(player_id):
                db.session.commit()
                
                # Add player to socket.io room
                # Check if player is actually connected via CoreSocketController?
                core_controller = self.app_config.get('socket_controller')
                if core_controller:
                    status = core_controller.get_player_connection_status(player_id)
                    if status.get('success'):
                        socket_id = status.get('socket_id')
                        if socket_id:
                            # Use the socketio instance associated with this controller
                            self.socketio.server.enter_room(socket_id, f"channel_{channel_id}")
                            logger.info(f"Added SID {socket_id} for player {player_id} to room channel_{channel_id}")
                        else:
                            logger.warning(f"Could not find socket_id for player {player_id} when joining channel room.")
                    else:
                        logger.warning(f"Player {player_id} not connected, cannot join channel room via socket.")
                else:
                     logger.warning("CoreSocketController not found, cannot explicitly add player to channel room.")
                # join_room(f"channel_{channel_id}") # join_room works on the current request context sid
                
                # Notify channel members
                self.socketio.emit('player_joined_channel', {
                    "channel_id": channel_id,
                    "player_id": player_id
                }, room=f"channel_{channel_id}")
                
                return {
                    "success": True,
                    "channel_id": channel_id,
                    "channel": channel.to_dict()
                }
            else:
                return {
                    "success": False,
                    "error": "Already a member of this channel"
                }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error joining channel: {str(e)}")
            return {
                "success": False,
                "error": f"Error joining channel: {str(e)}"
            }
    
    def leave_channel(self, player_id, channel_id):
        """Leave a channel"""
        try:
            # Check if channel exists
            channel = Channel.query.get(channel_id)
            if not channel:
                return {
                    "success": False,
                    "error": "Channel not found"
                }
            
            # Remove player as member
            if channel.remove_member(player_id):
                db.session.commit()
                
                # Remove player from socket.io room
                core_controller = self.app_config.get('socket_controller')
                if core_controller:
                    status = core_controller.get_player_connection_status(player_id)
                    if status.get('success'):
                        socket_id = status.get('socket_id')
                        if socket_id:
                            self.socketio.server.leave_room(socket_id, f"channel_{channel_id}")
                            logger.info(f"Removed SID {socket_id} for player {player_id} from room channel_{channel_id}")
                        else:
                            logger.warning(f"Could not find socket_id for player {player_id} when leaving channel room.")
                    # No warning if not connected, they wouldn't be in the room anyway
                else:
                     logger.warning("CoreSocketController not found, cannot explicitly remove player from channel room.")
                # leave_room(f"channel_{channel_id}") # leave_room works on the current request context sid
                
                # Notify channel members
                self.socketio.emit('player_left_channel', {
                    "channel_id": channel_id,
                    "player_id": player_id
                }, room=f"channel_{channel_id}")
                
                return {
                    "success": True,
                    "channel_id": channel_id
                }
            else:
                return {
                    "success": False,
                    "error": "Not a member of this channel"
                }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error leaving channel: {str(e)}")
            return {
                "success": False,
                "error": f"Error leaving channel: {str(e)}"
            }
    
    def get_player_channels(self, player_id):
        """Get all channels a player is a member of"""
        try:
            # Get all public channels
            public_channels = Channel.query.filter_by(type='public').all()
            
            # Get player memberships
            memberships = ChannelMember.query.filter_by(player_id=player_id).all()
            
            # Get private/group channels from memberships
            private_channels = []
            for membership in memberships:
                channel = Channel.query.get(membership.channel_id)
                if channel and channel.type != 'public':
                    private_channels.append(channel)
            
            # Combine channels
            all_channels = {
                "public": [c.to_dict() for c in public_channels],
                "private": [c.to_dict() for c in private_channels]
            }
            
            return {
                "success": True,
                "channels": all_channels
            }
            
        except Exception as e:
            logger.error(f"Error getting player channels: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting player channels: {str(e)}"
            }
    
    def get_channel_history(self, channel_id, player_id=None, limit=50, before_message_id=None):
        """Get message history for a channel"""
        try:
            # Check if channel exists
            channel = Channel.query.get(channel_id)
            if not channel:
                return {
                    "success": False,
                    "error": "Channel not found"
                }
            
            # Check if player is a member of non-public channel
            if channel.type != 'public' and player_id and not channel.is_member(player_id):
                return {
                    "success": False,
                    "error": "You are not a member of this channel"
                }
            
            # Get messages
            query = Message.query.filter_by(channel_id=channel_id)
            
            # Apply pagination
            if before_message_id:
                before_message = Message.query.get(before_message_id)
                if before_message:
                    query = query.filter(Message.created_at < before_message.created_at)
            
            # Order by created_at descending, limit, then reverse for chronological order
            messages = query.order_by(Message.created_at.desc()).limit(limit).all()
            messages.reverse()  # Now in chronological order
            
            return {
                "success": True,
                "channel_id": channel_id,
                "messages": [m.to_dict() for m in messages],
                "has_more": len(messages) == limit
            }
            
        except Exception as e:
            logger.error(f"Error getting channel history: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting channel history: {str(e)}"
            }
    
    def _notify_channel_creation(self, channel):
        """Notify relevant players about channel creation"""
        channel_dict = channel.to_dict()
        
        if channel.type == 'public':
            # Broadcast to everyone
            self.socketio.emit('channel_created', channel_dict)
        else:
            # Notify only members
            for member in channel.members:
                 # Use CoreSocketController to find SID if possible?
                 core_controller = self.app_config.get('socket_controller')
                 if core_controller:
                     status = core_controller.get_player_connection_status(member.player_id)
                     if status.get('success'):
                         socket_id = status.get('socket_id')
                         if socket_id:
                             self.socketio.emit('channel_created', channel_dict, room=socket_id)
                         else:
                              logger.warning(f"Could not find socket ID for member {member.player_id} to notify channel creation.")
                 else:
                      # Fallback: emit to player-specific room (might not work if client isn't joined)
                      self.socketio.emit('channel_created', channel_dict, room=f"player_{member.player_id}")
    
    def _broadcast_message(self, message):
        """Broadcast a message to all relevant players"""
        message_dict = message.to_dict()
        
        # Get channel
        channel = Channel.query.get(message.channel_id)
        
        if channel.type == 'public':
            # Broadcast to everyone
            # TODO: Should this go to non-authenticated spectators too?
            self.socketio.emit('chat_message', message_dict) # Emits to all connected clients
        else:
            # Broadcast to channel members room
            self.socketio.emit('chat_message', message_dict, 
                              room=f"channel_{message.channel_id}")
        
        # Also update last_read for sender
        membership = ChannelMember.query.filter_by(
            channel_id=message.channel_id,
            player_id=message.sender_id
        ).first()
        
        if membership:
            membership.last_read = datetime.utcnow()
            db.session.commit()
    
    def _broadcast_reaction(self, message, player_id, emoji):
        """Broadcast a reaction to all relevant players"""
        # Get channel
        channel = Channel.query.get(message.channel_id)
        
        reaction_data = {
            "message_id": message.id,
            "player_id": player_id,
            "emoji": emoji,
            "channel_id": message.channel_id,
            "reactions": {r.emoji: r.count for r in message.get_reaction_counts()}
        }
        
        if channel.type == 'public':
            self.socketio.emit('message_reaction', reaction_data)
        else:
            self.socketio.emit('message_reaction', reaction_data, 
                              room=f"channel_{message.channel_id}")
    
    def _broadcast_reaction_removal(self, message, player_id, emoji):
        """Broadcast a reaction removal to all relevant players"""
        # Get channel
        channel = Channel.query.get(message.channel_id)
        
        reaction_data = {
            "message_id": message.id,
            "player_id": player_id,
            "emoji": emoji,
            "channel_id": message.channel_id,
            "removed": True,
            "reactions": {r.emoji: r.count for r in message.get_reaction_counts()}
        }
        
        if channel.type == 'public':
            self.socketio.emit('message_reaction', reaction_data)
        else:
            self.socketio.emit('message_reaction', reaction_data, 
                              room=f"channel_{message.channel_id}")

def register_chat_socket_handlers(socketio, app_config):
    """Register chat-related SocketIO event handlers."""
    
    # Retrieve the SocialController instance (which should be the ChatController)
    social_controller = app_config.get('social_controller')
    if not social_controller:
        logger.error("SocialController (ChatController) not found in app_config. Cannot register chat handlers.")
        return
        
    # Retrieve core controller for authentication/SID lookup
    core_controller = app_config.get('socket_controller')
    if not core_controller:
        logger.error("Core SocketController not found in app_config. Chat authentication may fail.")
        # Allow registration but log error, handlers might fail
        
    # Removed local instantiation: chat_controller = ChatController(socketio) 
    logger.info("Registering chat socket handlers using SocialController instance.")

    @socketio.on('chat_message')
    def handle_chat_message(data):
        """Handles incoming chat messages."""
        # Get authenticated sender_id from the CoreSocketController
        sender_id = core_controller._get_player_id_from_sid(request.sid) if core_controller else None
        channel_id = data.get('channel_id')
        content = data.get('content')
        
        if not sender_id: 
            logger.warning("Received chat_message from unauthenticated SID.")
            emit('error', {'message': 'Authentication required'}, room=request.sid)
            return

        if not channel_id or not content:
            emit('error', {'message': 'Missing channel_id or content'}, room=request.sid)
            return
            
        logger.debug(f"Received chat_message from {sender_id} for channel {channel_id}")
        # Use the retrieved social_controller instance
        result = social_controller.send_message(sender_id, channel_id, content)
        
        if not result['success']:
            emit('error', {'message': result.get('error', 'Failed to send message')}, room=request.sid)

    @socketio.on('join_channel')
    def handle_join_channel(data):
        """Handles requests to join a chat channel."""
        # Get authenticated player_id from the CoreSocketController
        player_id = core_controller._get_player_id_from_sid(request.sid) if core_controller else None
        channel_id = data.get('channel_id')
        
        if not player_id: 
            logger.warning("Received join_channel from unauthenticated SID.")
            emit('error', {'message': 'Authentication required'}, room=request.sid)
            return
            
        if not channel_id:
            emit('error', {'message': 'Missing channel_id'}, room=request.sid)
            return

        logger.debug(f"Player {player_id} attempting to join channel {channel_id}")
        # Use the retrieved social_controller instance
        result = social_controller.join_channel(player_id, channel_id)
        
        if result['success']:
            # Note: social_controller.join_channel now handles adding SID to room
            # room_name = f'channel_{channel_id}'
            # join_room(room_name) 
            # logger.info(f"Player {player_id} joined channel {channel_id} and SocketIO room {room_name}")
            emit('status', {'message': f'Successfully joined channel {channel_id}'}, room=request.sid)
            # Controller emits 'member_joined' event
        else:
            emit('error', {'message': result.get('error', 'Failed to join channel')}, room=request.sid)

    @socketio.on('leave_channel')
    def handle_leave_channel(data):
        """Handles requests to leave a chat channel."""
        # Get authenticated player_id from the CoreSocketController
        player_id = core_controller._get_player_id_from_sid(request.sid) if core_controller else None
        channel_id = data.get('channel_id')
        
        if not player_id: 
            logger.warning("Received leave_channel from unauthenticated SID.")
            emit('error', {'message': 'Authentication required'}, room=request.sid)
            return

        if not channel_id:
            emit('error', {'message': 'Missing channel_id'}, room=request.sid)
            return
            
        logger.debug(f"Player {player_id} attempting to leave channel {channel_id}")
        # Use the retrieved social_controller instance
        result = social_controller.leave_channel(player_id, channel_id)
        
        if result['success']:
            # Note: social_controller.leave_channel now handles removing SID from room
            # room_name = f'channel_{channel_id}'
            # leave_room(room_name)
            # logger.info(f"Player {player_id} left channel {channel_id} and SocketIO room {room_name}")
            emit('status', {'message': f'Successfully left channel {channel_id}'}, room=request.sid)
            # Controller emits 'member_left' event
        else:
            emit('error', {'message': result.get('error', 'Failed to leave channel')}, room=request.sid)

    @socketio.on('message_reaction')
    def handle_message_reaction(data):
        """Handles adding or removing reactions to messages."""
        # Get authenticated player_id from the CoreSocketController
        player_id = core_controller._get_player_id_from_sid(request.sid) if core_controller else None
        message_id = data.get('message_id')
        emoji = data.get('emoji')
        action = data.get('action', 'add') # 'add' or 'remove'
        
        if not player_id: 
            logger.warning("Received message_reaction from unauthenticated SID.")
            emit('error', {'message': 'Authentication required'}, room=request.sid)
            return

        if not message_id or not emoji:
            emit('error', {'message': 'Missing message_id or emoji'}, room=request.sid)
            return
            
        logger.debug(f"Player {player_id} reacting ('{action}') with '{emoji}' to message {message_id}")
        
        # Use the retrieved social_controller instance
        if action == 'add':
            result = social_controller.add_reaction(player_id, message_id, emoji)
        elif action == 'remove':
            result = social_controller.remove_reaction(player_id, message_id, emoji)
        else:
            emit('error', {'message': 'Invalid action specified'}, room=request.sid)
            return
            
        if not result['success']:
            emit('error', {'message': result.get('error', f'Failed to {action} reaction')}, room=request.sid)
        # Success is handled by the broadcast methods within the controller actions

    logger.info("Chat socket handlers registered") 