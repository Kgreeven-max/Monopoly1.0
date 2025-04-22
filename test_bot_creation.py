import requests
import json
import random

def create_bot():
    # Generate a unique bot name with a random suffix
    random_suffix = str(random.randint(1000, 9999))
    bot_name = f"TestStrategicBot_{random_suffix}"
    
    url = "http://localhost:5000/api/create-bot"
    payload = {
        "admin_pin": "pinopoly-admin",
        "name": bot_name,
        "type": "strategic", 
        "difficulty": "normal"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Attempting to create bot with name: {bot_name}")
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("Bot created successfully!")
    else:
        print(f"Failed to create bot: {response.text}")
    
    # Write debug info to a file
    with open("bot_create_debug.txt", "w") as f:
        f.write(f"Attempted to create bot: {bot_name}\n")
        f.write(f"Status Code: {response.status_code}\n")
        f.write(f"Response: {response.text}\n")

if __name__ == "__main__":
    create_bot() 