# Pinopoly Testing Guide

This guide provides step-by-step instructions to test the Pinopoly game after the recent fixes.

## Prerequisites

1. Ensure Python 3.9+ is installed
2. Ensure Node.js 16+ is installed
3. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   cd client && npm install
   ```

## Step 1: Start the Backend Server

```bash
# From the root directory
python app.py
```

Expected output:
- Server should start on port 5001
- You should see "Starting server on port 5001 with debug mode disabled"
- No errors about missing attributes or database issues

## Step 2: Start the Frontend

In a new terminal:
```bash
cd client
npm run dev
```

Expected output:
- Frontend should start on http://localhost:3000
- No console errors

## Step 3: Create a New Game

1. Open browser to http://localhost:5001/admin
2. Login with admin PIN (check your .env or use default)
3. Click "Create New Game"
4. Settings:
   - Mode: Classic
   - Bot Count: 4
   - Click "Create Game"

Expected result:
- Game created successfully message
- Game ID displayed

## Step 4: Start the Game

1. In admin panel, click "Start Game"
2. Wait for confirmation

Expected result:
- Game status changes from "setup" to "active" or "running"
- Bots are registered and assigned turn order

## Step 5: Open the Game Board

1. Navigate to http://localhost:3000/board
2. Check browser console for errors

Expected result:
- Board should display without errors
- You should see:
  - "[BoardPage] Authentication successful" in console
  - Game state received with players
  - 4 bot players displayed on the board
  - No "property has no attribute" errors

## Step 6: Verify Game Play

Watch the bots play for a few turns:

Expected behavior:
- Bots should automatically roll dice
- Player tokens should move on the board
- No console errors about missing attributes
- Socket events should flow properly

## Common Issues and Solutions

### Issue 1: "No active game" error
**Solution**: Make sure you started the game in admin panel (Step 4)

### Issue 2: Board shows but no players
**Solution**: Check that game status is "active" not "setup"

### Issue 3: Property attribute errors
**Solution**: Our fixes should have resolved these. If you still see them:
- Check that socket_game_controller.py uses `houses` not `house_count`
- Check that it uses `hotel` not `has_hotel`
- Check that it uses `color_group` not `property_group`

### Issue 4: Socket connection errors
**Solution**: 
- Verify backend is running on port 5001
- Check that socket path is `/ws` in both frontend and backend
- Clear browser cache and retry

## Automated Test Script

You can also run this automated test:

```bash
# Create test script
cat > test_game_flow.py << 'EOF'
import requests
import time
import json

BASE_URL = "http://localhost:5001"
ADMIN_KEY = "pinopoly-admin"  # Update with your admin key

def test_game_flow():
    print("Testing Pinopoly game flow...")
    
    # 1. Create game
    print("\n1. Creating game...")
    response = requests.post(f"{BASE_URL}/api/admin/games", 
                           json={"mode": "classic", "bot_count": 4},
                           headers={"X-Admin-Key": ADMIN_KEY})
    
    if response.status_code != 201:
        print(f"Failed to create game: {response.text}")
        return
    
    game_data = response.json()
    game_id = game_data.get("game_id")
    print(f"Game created with ID: {game_id}")
    
    # 2. Start game
    print("\n2. Starting game...")
    response = requests.post(f"{BASE_URL}/api/game/start",
                           json={"admin_pin": ADMIN_KEY})
    
    if response.status_code != 200:
        print(f"Failed to start game: {response.text}")
        return
    
    print("Game started successfully!")
    
    # 3. Check game state
    print("\n3. Checking game state...")
    response = requests.get(f"{BASE_URL}/api/game/state")
    
    if response.status_code == 200:
        state = response.json()
        print(f"Game status: {state.get('status')}")
        print(f"Players: {len(state.get('players', []))}")
    else:
        print(f"Failed to get game state: {response.text}")
    
    print("\nTest completed! Check http://localhost:3000/board")

if __name__ == "__main__":
    test_game_flow()
EOF

# Run test
python test_game_flow.py
```

## Success Criteria

The game is working correctly if:
- ✅ No attribute errors in console
- ✅ Board displays with players
- ✅ Bots take turns automatically
- ✅ Player tokens animate on movement
- ✅ Socket connections remain stable
- ✅ Game state updates properly

## Next Steps

If all tests pass:
1. The core game functionality is working
2. You can proceed with additional features
3. Consider implementing the remaining improvements from the modernization plan

If tests fail:
1. Check the specific error messages
2. Refer to OVERHAUL_DOCUMENTATION.md for fixes
3. Verify all code changes were applied correctly