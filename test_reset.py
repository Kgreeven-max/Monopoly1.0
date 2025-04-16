import requests
import json
import os

# Get admin key from environment or use default
ADMIN_KEY = os.environ.get('ADMIN_KEY', 'pinopoly-admin')
BASE_URL = 'http://127.0.0.1:5000'

def test_admin_reset():
    """Test the admin reset game functionality"""
    print(f"Testing admin reset with key: {ADMIN_KEY}")
    
    # Make POST request to reset endpoint
    response = requests.post(
        f"{BASE_URL}/api/admin/reset", 
        headers={
            'Content-Type': 'application/json',
            'X-Admin-Key': ADMIN_KEY
        },
        data=json.dumps({})
    )
    
    # Print response details
    print(f"Status code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Raw response: {response.text}")
    
    return response

if __name__ == "__main__":
    test_admin_reset() 