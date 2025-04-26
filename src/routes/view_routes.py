from flask import Blueprint, render_template, jsonify, request, redirect, url_for, current_app, Response, session
from flask_login import login_required, current_user
import os
import logging
import json

view_routes = Blueprint('view_routes', __name__)

# Set up logger
logger = logging.getLogger(__name__)

@view_routes.route('/board')
def board_view():
    """Main game board view for spectators and admin displays."""
    return render_template('board.html')

@view_routes.route('/player/<player_id>')
def player_view(player_id):
    """Individual player's view."""
    return render_template('player.html', player_id=player_id)

@view_routes.route('/admin')
def admin_view():
    """Admin dashboard view."""
    return render_template('admin.html')

@view_routes.route('/games/<int:game_id>/state')
def get_game_state(game_id):
    """API endpoint to directly fetch the current game state."""
    game_logic = current_app.config.get('game_logic')
    if not game_logic:
        logger.error(f"GameLogic not found for game state request for game {game_id}")
        return jsonify({"error": "Game logic unavailable"}), 500
    
    try:
        # Get the current game state
        game_state = game_logic.get_game_state(game_id)
        if not game_state:
            logger.error(f"Failed to retrieve game state for game {game_id}")
            return jsonify({"error": "Could not retrieve game state"}), 404
        
        # Log successful request
        logger.info(f"Successfully retrieved game state for game {game_id} via API")
        return jsonify(game_state)
    except Exception as e:
        logger.error(f"Error retrieving game state: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500 