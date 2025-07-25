#!/usr/bin/env python3
"""Test script to verify player animations are working"""

import requests
import time
import json

BASE_URL = "http://localhost:5001"

def test_player_animations():
    """Test that player movements trigger animations"""
    print("Testing player animation system...")
    
    # Get the current game state
    response = requests.get(f"{BASE_URL}/api/game/state")
    if response.status_code != 200:
        print(f"Failed to get game state: {response.status_code}")
        return
    
    game_data = response.json()
    game_id = game_data.get('gameId')
    players = game_data.get('players', [])
    
    if not players:
        print("No players found in game")
        return
    
    print(f"Found {len(players)} players in game {game_id}")
    
    # Test rolling dice for each player
    for i, player in enumerate(players):
        player_id = player['id']
        print(f"\nTesting animation for Player {player_id} ({player['name']})...")
        
        # Roll dice
        roll_data = {"playerId": player_id}
        print(f"  Rolling dice...")
        response = requests.post(f"{BASE_URL}/api/game/roll", json=roll_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Rolled {result.get('dice', [])} - Player should animate from position {player['position']} to {result.get('newPosition', '?')}")
        else:
            print(f"  ✗ Failed to roll: {response.text}")
        
        # Wait a bit between players to see animations
        if i < len(players) - 1:
            print("  Waiting 3 seconds before next player...")
            time.sleep(3)
    
    print("\n✨ Animation test complete! Check the frontend to verify smooth bouncing movements.")

if __name__ == "__main__":
    test_player_animations()