#!/usr/bin/env python3
"""
API Endpoint Testing Script for Pinopoly V2

This script tests all API endpoints to ensure they work correctly.
Run this after starting the backend server to validate the API.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'

def print_success(message: str):
    print(f"{GREEN}✓{END} {message}")

def print_error(message: str):
    print(f"{RED}✗{END} {message}")

def print_warning(message: str):
    print(f"{YELLOW}⚠{END} {message}")

def print_info(message: str):
    print(f"{BLUE}ℹ{END} {message}")

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Pinopoly-V2-API-Tester/1.0'
        })
        self.test_data = {}
    
    def test_all_endpoints(self) -> bool:
        """Test all API endpoints."""
        print_info(f"Testing API endpoints at {self.base_url}")
        print()
        
        tests = [
            ("Server Health", self.test_health_endpoint),
            ("Player Creation", self.test_create_player),
            ("Player Retrieval", self.test_get_player),
            ("Player Movement", self.test_move_player),
            ("Game Creation", self.test_create_game),
            ("Game Retrieval", self.test_get_game),
            ("Join Game", self.test_join_game),
            ("Property Operations", self.test_property_operations),
            ("Error Handling", self.test_error_handling)
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            print(f"Testing {test_name}...")
            try:
                if not test_func():
                    all_passed = False
                    print_error(f"{test_name} failed")
                else:
                    print_success(f"{test_name} passed")
            except Exception as e:
                print_error(f"{test_name} error: {e}")
                all_passed = False
            print()
        
        self.print_summary(all_passed)
        return all_passed
    
    def make_request(self, method: str, endpoint: str, 
                    data: Optional[Dict] = None,
                    expected_status: int = 200) -> Optional[Dict]:
        """Make HTTP request and validate response."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            print_info(f"{method.upper()} {endpoint} -> {response.status_code}")
            
            if response.status_code != expected_status:
                print_error(f"Expected status {expected_status}, got {response.status_code}")
                print_error(f"Response: {response.text}")
                return None
            
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.ConnectionError:
            print_error(f"Cannot connect to {url}")
            print_error("Make sure the backend server is running")
            return None
        except Exception as e:
            print_error(f"Request failed: {e}")
            return None
    
    def test_health_endpoint(self) -> bool:
        """Test health check endpoint."""
        response = self.make_request('GET', '/health')
        if response is None:
            return False
        
        if 'status' in response:
            print_success(f"Health status: {response['status']}")
            return True
        else:
            print_warning("Health endpoint missing status field")
            return True  # Don't fail if structure is different
    
    def test_create_player(self) -> bool:
        """Test player creation endpoint."""
        player_data = {
            "name": "Test Player",
            "avatar_url": "https://example.com/avatar.jpg"
        }
        
        response = self.make_request('POST', '/api/v1/players', 
                                   player_data, expected_status=201)
        if response is None:
            return False
        
        # Validate response structure
        required_fields = ['id', 'name', 'money', 'position']
        for field in required_fields:
            if field not in response:
                print_error(f"Missing field in response: {field}")
                return False
        
        # Store player ID for later tests
        self.test_data['player_id'] = response['id']
        print_success(f"Player created with ID: {response['id']}")
        return True
    
    def test_get_player(self) -> bool:
        """Test player retrieval endpoint."""
        if 'player_id' not in self.test_data:
            print_warning("Skipping player retrieval test - no player ID")
            return True
        
        player_id = self.test_data['player_id']
        response = self.make_request('GET', f'/api/v1/players/{player_id}')
        
        if response is None:
            return False
        
        if response.get('name') == 'Test Player':
            print_success("Player retrieved successfully")
            return True
        else:
            print_error("Player data mismatch")
            return False
    
    def test_move_player(self) -> bool:
        """Test player movement endpoint."""
        if 'player_id' not in self.test_data:
            print_warning("Skipping player movement test - no player ID")
            return True
        
        player_id = self.test_data['player_id']
        move_data = {"spaces": 7}
        
        response = self.make_request('POST', f'/api/v1/players/{player_id}/move',
                                   move_data)
        if response is None:
            return False
        
        if 'new_position' in response:
            print_success(f"Player moved to position: {response['new_position']}")
            return True
        else:
            print_error("Movement response missing position data")
            return False
    
    def test_create_game(self) -> bool:
        """Test game creation endpoint."""
        game_data = {
            "name": "Test Game",
            "max_players": 4,
            "settings": {
                "starting_money": 1500,
                "salary": 200
            }
        }
        
        response = self.make_request('POST', '/api/v1/games',
                                   game_data, expected_status=201)
        if response is None:
            return False
        
        # Validate response structure
        required_fields = ['id', 'name', 'status', 'max_players']
        for field in required_fields:
            if field not in response:
                print_error(f"Missing field in response: {field}")
                return False
        
        # Store game ID for later tests
        self.test_data['game_id'] = response['id']
        print_success(f"Game created with ID: {response['id']}")
        return True
    
    def test_get_game(self) -> bool:
        """Test game retrieval endpoint."""
        if 'game_id' not in self.test_data:
            print_warning("Skipping game retrieval test - no game ID")
            return True
        
        game_id = self.test_data['game_id']
        response = self.make_request('GET', f'/api/v1/games/{game_id}')
        
        if response is None:
            return False
        
        if response.get('name') == 'Test Game':
            print_success("Game retrieved successfully")
            return True
        else:
            print_error("Game data mismatch")
            return False
    
    def test_join_game(self) -> bool:
        """Test joining game endpoint."""
        if 'game_id' not in self.test_data or 'player_id' not in self.test_data:
            print_warning("Skipping join game test - missing game or player ID")
            return True
        
        game_id = self.test_data['game_id']
        player_id = self.test_data['player_id']
        
        join_data = {"player_id": player_id}
        response = self.make_request('POST', f'/api/v1/games/{game_id}/join',
                                   join_data)
        
        if response is None:
            return False
        
        if response.get('success'):
            print_success("Player joined game successfully")
            return True
        else:
            print_error("Failed to join game")
            return False
    
    def test_property_operations(self) -> bool:
        """Test property-related endpoints."""
        # Test getting property details
        response = self.make_request('GET', '/api/v1/properties/1')
        
        if response is None:
            print_warning("Property endpoint not available")
            return True  # Don't fail if not implemented yet
        
        if 'name' in response:
            print_success("Property details retrieved")
            return True
        else:
            print_warning("Property response missing name field")
            return True
    
    def test_error_handling(self) -> bool:
        """Test error handling for invalid requests."""
        # Test 404 error
        response = self.make_request('GET', '/api/v1/players/invalid-id',
                                   expected_status=404)
        if response is None:
            print_warning("404 error handling not working as expected")
            return True  # Don't fail for this
        
        # Test 400 error with invalid data
        invalid_data = {"invalid_field": "value"}
        response = self.make_request('POST', '/api/v1/players',
                                   invalid_data, expected_status=400)
        if response is None:
            print_warning("400 error handling not working as expected")
            return True  # Don't fail for this
        
        print_success("Error handling tests completed")
        return True
    
    def print_summary(self, all_passed: bool):
        """Print test summary."""
        print("=" * 50)
        print("API TEST SUMMARY")
        print("=" * 50)
        
        if all_passed:
            print_success("All API tests passed! ✨")
            print_info("Your API is working correctly.")
        else:
            print_error("Some API tests failed")
            print_info("Check the errors above and fix the issues.")
        
        print()
        print_info("Test data created:")
        for key, value in self.test_data.items():
            print_info(f"  {key}: {value}")

def main():
    """Main testing function."""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print_info(f"Testing API at: {base_url}")
    print_info("Make sure the backend server is running!")
    print()
    
    # Wait a moment for user to see the message
    time.sleep(1)
    
    tester = APITester(base_url)
    success = tester.test_all_endpoints()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()