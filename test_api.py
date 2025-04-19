import requests
import sys
import json

base_url = "http://localhost:5000/api"

def test_health_api():
    """Test the health API endpoint"""
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health API - Status code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error testing health API: {str(e)}")
        return False

def test_properties_api():
    """Test the properties API endpoints"""
    try:
        # Get all properties
        response = requests.get(f"{base_url}/properties")
        print(f"\nProperties API - Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data['properties'])} properties")
            
            # Get property by ID
            property_id = 1
            response = requests.get(f"{base_url}/property/{property_id}")
            print(f"\nProperty {property_id} API - Status code: {response.status_code}")
            if response.status_code == 200:
                property_data = response.json()
                print(f"Property name: {property_data['property']['name']}")
                return True
            else:
                print(f"Error: {response.text}")
                return False
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error testing properties API: {str(e)}")
        return False

def test_players_api():
    """Test the players API endpoints"""
    try:
        # Get all players
        response = requests.get(f"{base_url}/players")
        print(f"\nPlayers API - Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data['players'])} players")
            
            # Get player by ID
            player_id = 1
            response = requests.get(f"{base_url}/player/{player_id}")
            print(f"\nPlayer {player_id} API - Status code: {response.status_code}")
            if response.status_code == 200:
                player_data = response.json()
                print(f"Player name: {player_data['player']['name']}")
                
                # Test player authentication
                player_auth_data = {
                    "player_id": player_id,
                    "pin": player_data['player']['pin']
                }
                
                response = requests.post(
                    f"{base_url}/player/auth", 
                    json=player_auth_data,
                    headers={"Content-Type": "application/json"}
                )
                print(f"\nPlayer Auth API - Status code: {response.status_code}")
                if response.status_code == 200:
                    auth_data = response.json()
                    print(f"Authentication successful for player: {auth_data['player']['name']}")
                    
                    # Test with wrong PIN
                    wrong_auth_data = {
                        "player_id": player_id,
                        "pin": "wrong-pin"
                    }
                    response = requests.post(
                        f"{base_url}/player/auth", 
                        json=wrong_auth_data,
                        headers={"Content-Type": "application/json"}
                    )
                    print(f"\nPlayer Auth API (wrong PIN) - Status code: {response.status_code}")
                    if response.status_code == 401:
                        print("Authentication correctly failed with wrong PIN")
                        return True
                    else:
                        print(f"Authentication should have failed but returned: {response.status_code}")
                        return False
                else:
                    print(f"Error: {response.text}")
                    return False
            else:
                print(f"Error: {response.text}")
                return False
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error testing players API: {str(e)}")
        return False

def run_all_tests():
    """Run all API tests"""
    print("TESTING PINOPOLY APIs")
    print("=====================")
    
    health_result = test_health_api()
    properties_result = test_properties_api()
    players_result = test_players_api()
    
    print("\nTEST SUMMARY")
    print("============")
    print(f"Health API:     {'✅ PASS' if health_result else '❌ FAIL'}")
    print(f"Properties API: {'✅ PASS' if properties_result else '❌ FAIL'}")
    print(f"Players API:    {'✅ PASS' if players_result else '❌ FAIL'}")
    
    # Overall result
    overall_result = health_result and properties_result and players_result
    print(f"\nOVERALL RESULT: {'✅ PASS' if overall_result else '❌ FAIL'}")
    
    return overall_result

if __name__ == "__main__":
    result = run_all_tests()
    sys.exit(0 if result else 1) 