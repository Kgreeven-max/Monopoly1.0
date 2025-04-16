from src.routes.social.chat_routes import register_chat_routes
from src.routes.social.alliance_routes import register_alliance_routes
from src.routes.social.reputation_routes import register_reputation_routes

def register_social_routes(app, socketio, chat_controller, alliance_controller, reputation_controller):
    """Register all social feature routes"""
    register_chat_routes(app, socketio, chat_controller)
    register_alliance_routes(app, socketio, alliance_controller)
    register_reputation_routes(app, socketio, reputation_controller)

__all__ = ['register_social_routes'] 