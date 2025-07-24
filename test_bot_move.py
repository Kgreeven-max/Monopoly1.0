#!/usr/bin/env python3
"""
Quick script to trigger bot movement
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from src.models.game_state import GameState
from src.models.player import Player

with app.app_context():
    game_state = GameState.query.first()
    if game_state:
        print(f"Game ID: {game_state.game_id}")
        print(f"Status: {game_state.status}")
        print(f"Current player: {game_state.current_player_id}")
        
        # List all players
        players = Player.query.filter_by(in_game=True).all()
        print(f"\nPlayers in game ({len(players)}):")
        for p in players:
            print(f"  - {p.username} (ID: {p.id}, Position: {p.position}, Bot: {p.is_bot})")
            
        # Update current player if needed
        if players and game_state.current_player_id not in [p.id for p in players]:
            game_state.current_player_id = players[0].id
            from src.models import db
            db.session.commit()
            print(f"\nUpdated current player to: {game_state.current_player_id}")
            
        # Trigger bot to roll dice via game controller
        game_controller = app.config.get('game_controller')
        if game_controller and game_state.current_player_id:
            print(f"\nTriggering dice roll for player {game_state.current_player_id}...")
            result = game_controller.handle_roll_dice({'playerId': game_state.current_player_id})
            print(f"Result: {result}")
    else:
        print("No game found!")