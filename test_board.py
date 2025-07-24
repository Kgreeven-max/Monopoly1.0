#!/usr/bin/env python3
"""
Quick script to create a test game with bots
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from src.models.game_state import GameState
from src.models.player import Player
from src.controllers.game_controller import GameController
from src.controllers.bot_controller import BotController
import uuid

# app is already imported

with app.app_context():
    # Check if there's already a game
    game_state = GameState.query.first()
    
    if not game_state:
        # Create a new game
        game_id = str(uuid.uuid4())
        game_state = GameState(
            game_id=game_id,
            status='In Progress',
            current_player_id=None,
            turn_number=1,
            current_lap=1
        )
        # Don't set id=1, let it auto-increment
        db.session.add(game_state)
        db.session.commit()
        print(f"Created new game: {game_id}")
    else:
        game_id = game_state.game_id
        print(f"Using existing game: {game_id}")
    
    # Clear any existing players
    Player.query.update({'in_game': False})
    db.session.commit()
    
    # Create bot controller
    bot_controller = app.config.get('bot_controller')
    
    if bot_controller:
        # Add some bots
        bot1 = bot_controller.create_bot("Alice Bot", "conservative", "normal")
        bot2 = bot_controller.create_bot("Bob Bot", "aggressive", "normal")
        bot3 = bot_controller.create_bot("Charlie Bot", "strategic", "normal")
        bot4 = bot_controller.create_bot("Diana Bot", "opportunistic", "normal")
        
        print(f"Created bots: {[bot1.username, bot2.username, bot3.username, bot4.username]}")
        
        # Set first player as current
        game_state.current_player_id = bot1.id
        db.session.commit()
        
        print(f"Game ready! Visit http://localhost:3001/board to see the board")
        print(f"Game ID: {game_id}")
    else:
        print("Bot controller not found!")