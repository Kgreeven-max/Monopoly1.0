from src.controllers.social.chat_controller import ChatController
from src.controllers.social.alliance_controller import AllianceController
from src.controllers.social.reputation_controller import ReputationController

class SocialController:
    """Main controller for social features, integrating all social sub-controllers"""
    
    def __init__(self, socketio, app_config):
        """Initialize the social controller with SocketIO instance and app_config"""
        self.socketio = socketio
        self.app_config = app_config # Store app_config
        
        # Pass app_config to sub-controllers
        self.chat_controller = ChatController(socketio, app_config)
        # Assuming AllianceController and ReputationController might also need app_config
        self.alliance_controller = AllianceController(socketio, app_config)
        self.reputation_controller = ReputationController(socketio, app_config)
    
    # Chat system methods
    def create_channel(self, *args, **kwargs):
        """Create a new chat channel"""
        return self.chat_controller.create_channel(*args, **kwargs)
    
    def send_message(self, *args, **kwargs):
        """Send a message to a channel"""
        return self.chat_controller.send_message(*args, **kwargs)
    
    def add_reaction(self, *args, **kwargs):
        """Add a reaction to a message"""
        return self.chat_controller.add_reaction(*args, **kwargs)
    
    def remove_reaction(self, *args, **kwargs):
        """Remove a reaction from a message"""
        return self.chat_controller.remove_reaction(*args, **kwargs)
    
    def join_channel(self, *args, **kwargs):
        """Join a channel"""
        return self.chat_controller.join_channel(*args, **kwargs)
    
    def leave_channel(self, *args, **kwargs):
        """Leave a channel"""
        return self.chat_controller.leave_channel(*args, **kwargs)
    
    def get_player_channels(self, *args, **kwargs):
        """Get all channels a player is a member of"""
        return self.chat_controller.get_player_channels(*args, **kwargs)
    
    def get_channel_history(self, *args, **kwargs):
        """Get message history for a channel"""
        return self.chat_controller.get_channel_history(*args, **kwargs)
    
    # Alliance system methods
    def create_alliance(self, *args, **kwargs):
        """Create a new player alliance"""
        return self.alliance_controller.create_alliance(*args, **kwargs)
    
    def invite_player(self, *args, **kwargs):
        """Invite a player to join an alliance"""
        return self.alliance_controller.invite_player(*args, **kwargs)
    
    def respond_to_invite(self, *args, **kwargs):
        """Accept or decline an alliance invitation"""
        return self.alliance_controller.respond_to_invite(*args, **kwargs)
    
    def leave_alliance(self, *args, **kwargs):
        """Leave an alliance"""
        return self.alliance_controller.leave_alliance(*args, **kwargs)
    
    def get_player_alliances(self, *args, **kwargs):
        """Get all alliances a player is a member of"""
        return self.alliance_controller.get_player_alliances(*args, **kwargs)
    
    def get_alliance_details(self, *args, **kwargs):
        """Get detailed information about an alliance"""
        return self.alliance_controller.get_alliance_details(*args, **kwargs)
    
    def update_alliance(self, *args, **kwargs):
        """Update alliance information"""
        return self.alliance_controller.update_alliance(*args, **kwargs)
    
    def update_member_role(self, *args, **kwargs):
        """Update a member's role within an alliance"""
        return self.alliance_controller.update_member_role(*args, **kwargs)
    
    def calculate_alliance_benefits(self, *args, **kwargs):
        """Calculate benefits between two players based on shared alliances"""
        return self.alliance_controller.calculate_alliance_benefits(*args, **kwargs)
    
    # Reputation system methods
    def get_player_reputation(self, *args, **kwargs):
        """Get a player's reputation score"""
        return self.reputation_controller.get_player_reputation(*args, **kwargs)
    
    def record_reputation_event(self, *args, **kwargs):
        """Record a reputation-affecting event"""
        return self.reputation_controller.record_reputation_event(*args, **kwargs)
    
    def get_player_reputation_events(self, *args, **kwargs):
        """Get reputation events for a player"""
        return self.reputation_controller.get_player_reputation_events(*args, **kwargs)
    
    def get_credit_score(self, *args, **kwargs):
        """Get a player's credit score for loan considerations"""
        return self.reputation_controller.get_credit_score(*args, **kwargs)
    
    def adjust_reputation(self, *args, **kwargs):
        """Admin function to manually adjust a player's reputation"""
        return self.reputation_controller.adjust_reputation(*args, **kwargs)
    
    def reset_reputation(self, *args, **kwargs):
        """Admin function to reset a player's reputation to default values"""
        return self.reputation_controller.reset_reputation(*args, **kwargs)

__all__ = [
    'SocialController',
    'ChatController',
    'AllianceController',
    'ReputationController'
] 