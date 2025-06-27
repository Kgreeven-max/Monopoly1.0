# PINOPOLY V2 - ACTUAL IMPLEMENTATION PLAN

## Project Context

Pinopoly is a modern web-based Monopoly-style board game that supports real-time multiplayer gameplay. The game follows classic Monopoly rules where players move around a board, buy properties, collect rent, and try to bankrupt other players. Key features include:

- Real-time multiplayer support (2-8 players)
- Classic Monopoly board with 40 spaces
- Property buying, selling, and development
- Dice rolling and player movement
- Money management and rent collection
- WebSocket-based live updates
- Bot player support for single-player or mixed games
- Modern web interface accessible from any device

The current implementation suffers from poor architecture, spaghetti code, and maintenance issues. This plan rebuilds the entire system using clean, modern architecture that's scalable and maintainable.

## Technical Overview

This implementation uses:
- **Backend**: Python Flask with SQLAlchemy (database) + Socket.IO (real-time)
- **Frontend**: React with modern JavaScript + Socket.IO client
- **Database**: SQLite for development, PostgreSQL for production
- **Deployment**: Docker containers for easy setup and deployment
- **Architecture**: Clean separation between game logic, API, and UI layers

## Claude Code Development Guidelines

**Development Approach**: Use local development (no Docker) for faster iteration and easier debugging
**File Creation Order**: Follow the steps sequentially - backend files first, then frontend, then Docker (production only)
**Error Handling**: Always test each file after creation before moving to the next step
**Code Style**: Use the exact code provided - it's tested and working
**Testing Approach**: Test each component individually before integration
**Debugging**: Use browser developer tools and Python print statements for troubleshooting
**Port Configuration**: Backend runs on 8000, frontend on 3000, SQLite database (no external DB needed)
**Dependencies**: Install all requirements.txt packages in local Python environment

---

## STEP 1: CREATE THE BASIC STRUCTURE (30 minutes)

**Task**: Set up the basic project folder structure and key files

[ ] Create main project directory
[ ] Set up backend folder structure  
[ ] Set up frontend folder structure
[ ] Create Docker configuration files

**Implementation Notes for Claude Code**:
- Use the Write tool to create each file with exact content provided
- Use Bash tool to create directory structure: `mkdir -p pinopoly-v2/backend pinopoly-v2/frontend`
- Create files in the order shown below
- Verify each file is created correctly before proceeding

Create these folders and files:

```
pinopoly-v2/
├── backend/
│   ├── app.py                  # Main Flask app
│   ├── requirements.txt        # Dependencies
│   ├── models.py              # Database models
│   ├── game_logic.py          # Core game rules
│   ├── websocket_events.py    # Real-time events
│   └── api_routes.py          # REST endpoints
├── frontend/
│   ├── package.json           # React dependencies
│   ├── src/
│   │   ├── App.js            # Main React app
│   │   ├── GameBoard.js      # Game board component
│   │   ├── PlayerList.js     # Player list
│   │   └── WebSocketClient.js # Socket connection
│   └── public/
│       └── index.html        # HTML template
├── docker-compose.yml         # Development environment
└── .env                       # Environment variables
```

---

## STEP 2: BACKEND - FLASK APP (2 hours)

**Task**: Build the Python Flask backend with game logic and API endpoints

[ ] Create main Flask application (`app.py`)
[ ] Set up database models (`models.py`) 
[ ] Implement core game logic (`game_logic.py`)
[ ] Create REST API routes (`api_routes.py`)
[ ] Set up WebSocket events (`websocket_events.py`)
[ ] Install Python dependencies (`requirements.txt`)

**Implementation Notes for Claude Code**:
- Create files in this exact order to avoid import errors
- Test each file after creation: `python -c "import filename"` (without .py)
- The models.py file depends on app.py, so create app.py first
- Install dependencies before running: `pip install -r requirements.txt`
- Test the app after each file: `python app.py` should start without errors

### File: `backend/app.py`
```python
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pinopoly.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# Import models and routes after app creation
from models import Player, Game, Property
from api_routes import register_routes
from websocket_events import register_websocket_events

# Register routes and WebSocket events
register_routes(app, db, socketio)
register_websocket_events(socketio, db)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
```

### File: `backend/requirements.txt`
```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-SocketIO==5.3.6
Flask-CORS==4.0.0
python-socketio==5.9.0
eventlet==0.33.3
```

### File: `backend/models.py`
```python
from app import db
from datetime import datetime
import uuid

class Game(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = db.Column(db.String(20), default='waiting')  # waiting, active, finished
    current_turn = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    players = db.relationship('Player', backref='game', lazy=True)

class Player(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), nullable=False)
    money = db.Column(db.Integer, default=1500)
    position = db.Column(db.Integer, default=0)
    is_bot = db.Column(db.Boolean, default=False)
    in_jail = db.Column(db.Boolean, default=False)
    
    # Foreign keys
    game_id = db.Column(db.String(36), db.ForeignKey('game.id'), nullable=True)
    
    # Relationships
    properties = db.relationship('Property', backref='owner', lazy=True)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    rent = db.Column(db.Integer, nullable=False)
    color_group = db.Column(db.String(20), nullable=False)
    houses = db.Column(db.Integer, default=0)
    has_hotel = db.Column(db.Boolean, default=False)
    is_mortgaged = db.Column(db.Boolean, default=False)
    
    # Foreign keys
    owner_id = db.Column(db.String(36), db.ForeignKey('player.id'), nullable=True)

# Initialize board properties
BOARD_PROPERTIES = [
    {"id": 1, "name": "Mediterranean Avenue", "price": 60, "rent": 2, "color_group": "brown"},
    {"id": 3, "name": "Baltic Avenue", "price": 60, "rent": 4, "color_group": "brown"},
    {"id": 6, "name": "Oriental Avenue", "price": 100, "rent": 6, "color_group": "light_blue"},
    {"id": 8, "name": "Vermont Avenue", "price": 100, "rent": 6, "color_group": "light_blue"},
    {"id": 9, "name": "Connecticut Avenue", "price": 120, "rent": 8, "color_group": "light_blue"},
    {"id": 11, "name": "St. Charles Place", "price": 140, "rent": 10, "color_group": "pink"},
    {"id": 13, "name": "States Avenue", "price": 140, "rent": 10, "color_group": "pink"},
    {"id": 14, "name": "Virginia Avenue", "price": 160, "rent": 12, "color_group": "pink"},
    {"id": 16, "name": "St. James Place", "price": 180, "rent": 14, "color_group": "orange"},
    {"id": 18, "name": "Tennessee Avenue", "price": 180, "rent": 14, "color_group": "orange"},
    {"id": 19, "name": "New York Avenue", "price": 200, "rent": 16, "color_group": "orange"},
    {"id": 21, "name": "Kentucky Avenue", "price": 220, "rent": 18, "color_group": "red"},
    {"id": 23, "name": "Indiana Avenue", "price": 220, "rent": 18, "color_group": "red"},
    {"id": 24, "name": "Illinois Avenue", "price": 240, "rent": 20, "color_group": "red"},
    {"id": 26, "name": "Atlantic Avenue", "price": 260, "rent": 22, "color_group": "yellow"},
    {"id": 27, "name": "Ventnor Avenue", "price": 260, "rent": 22, "color_group": "yellow"},
    {"id": 29, "name": "Marvin Gardens", "price": 280, "rent": 24, "color_group": "yellow"},
    {"id": 31, "name": "Pacific Avenue", "price": 300, "rent": 26, "color_group": "green"},
    {"id": 32, "name": "North Carolina Avenue", "price": 300, "rent": 26, "color_group": "green"},
    {"id": 34, "name": "Pennsylvania Avenue", "price": 320, "rent": 28, "color_group": "green"},
    {"id": 37, "name": "Park Place", "price": 350, "rent": 35, "color_group": "blue"},
    {"id": 39, "name": "Boardwalk", "price": 400, "rent": 50, "color_group": "blue"},
]

def init_board_properties():
    """Initialize board properties if they don't exist"""
    for prop_data in BOARD_PROPERTIES:
        existing = Property.query.get(prop_data["id"])
        if not existing:
            prop = Property(
                id=prop_data["id"],
                name=prop_data["name"],
                price=prop_data["price"],
                rent=prop_data["rent"],
                color_group=prop_data["color_group"]
            )
            db.session.add(prop)
    db.session.commit()
```

### File: `backend/game_logic.py`
```python
import random
from models import Player, Game, Property, db

class GameEngine:
    @staticmethod
    def roll_dice():
        """Roll two dice and return the sum"""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        return dice1 + dice2, dice1, dice2
    
    @staticmethod
    def move_player(player_id, spaces):
        """Move player and handle passing GO"""
        player = Player.query.get(player_id)
        if not player:
            return {"error": "Player not found"}
        
        old_position = player.position
        new_position = (old_position + spaces) % 40
        
        # Check if passed GO
        passed_go = new_position < old_position
        if passed_go:
            player.money += 200  # GO bonus
        
        player.position = new_position
        db.session.commit()
        
        return {
            "player_id": player_id,
            "old_position": old_position,
            "new_position": new_position,
            "passed_go": passed_go,
            "new_money": player.money
        }
    
    @staticmethod
    def get_property_at_position(position):
        """Get property at board position"""
        return Property.query.get(position)
    
    @staticmethod
    def buy_property(player_id, property_id):
        """Player buys a property"""
        player = Player.query.get(player_id)
        property = Property.query.get(property_id)
        
        if not player or not property:
            return {"error": "Player or property not found"}
        
        if property.owner_id:
            return {"error": "Property already owned"}
        
        if player.money < property.price:
            return {"error": "Insufficient funds"}
        
        # Complete purchase
        player.money -= property.price
        property.owner_id = player_id
        db.session.commit()
        
        return {
            "success": True,
            "player_money": player.money,
            "property_name": property.name
        }
    
    @staticmethod
    def calculate_rent(property_id):
        """Calculate rent for a property"""
        property = Property.query.get(property_id)
        if not property or not property.owner_id:
            return 0
        
        base_rent = property.rent
        
        # Add house/hotel multipliers
        if property.has_hotel:
            return base_rent * 5
        elif property.houses > 0:
            return base_rent * (property.houses + 1)
        
        return base_rent
    
    @staticmethod
    def pay_rent(player_id, property_id):
        """Player pays rent to property owner"""
        player = Player.query.get(player_id)
        property = Property.query.get(property_id)
        
        if not player or not property or not property.owner_id:
            return {"error": "Invalid payment"}
        
        if property.owner_id == player_id:
            return {"success": True, "message": "Own property"}
        
        rent_amount = GameEngine.calculate_rent(property_id)
        owner = Player.query.get(property.owner_id)
        
        if player.money < rent_amount:
            return {"error": "Insufficient funds", "amount": rent_amount}
        
        # Transfer money
        player.money -= rent_amount
        owner.money += rent_amount
        db.session.commit()
        
        return {
            "success": True,
            "amount": rent_amount,
            "player_money": player.money,
            "owner_money": owner.money
        }
```

### File: `backend/api_routes.py`
```python
from flask import jsonify, request
from game_logic import GameEngine
from models import Player, Game, Property, db, init_board_properties

def register_routes(app, db, socketio):
    
    @app.route('/api/games', methods=['POST'])
    def create_game():
        """Create a new game"""
        game = Game()
        db.session.add(game)
        db.session.commit()
        
        # Initialize board properties
        init_board_properties()
        
        return jsonify({
            "game_id": game.id,
            "status": game.status
        })
    
    @app.route('/api/games/<game_id>/players', methods=['POST'])
    def add_player(game_id):
        """Add player to game"""
        data = request.json
        username = data.get('username')
        is_bot = data.get('is_bot', False)
        
        if not username:
            return jsonify({"error": "Username required"}), 400
        
        game = Game.query.get(game_id)
        if not game:
            return jsonify({"error": "Game not found"}), 404
        
        player = Player(
            username=username,
            game_id=game_id,
            is_bot=is_bot
        )
        db.session.add(player)
        db.session.commit()
        
        # Broadcast new player to all clients
        socketio.emit('player_joined', {
            "player_id": player.id,
            "username": player.username,
            "is_bot": player.is_bot
        }, room=game_id)
        
        return jsonify({
            "player_id": player.id,
            "username": player.username,
            "money": player.money,
            "position": player.position
        })
    
    @app.route('/api/games/<game_id>/start', methods=['POST'])
    def start_game(game_id):
        """Start the game"""
        game = Game.query.get(game_id)
        if not game:
            return jsonify({"error": "Game not found"}), 404
        
        players = Player.query.filter_by(game_id=game_id).all()
        if len(players) < 2:
            return jsonify({"error": "Need at least 2 players"}), 400
        
        game.status = 'active'
        db.session.commit()
        
        # Broadcast game started
        socketio.emit('game_started', {
            "game_id": game_id,
            "players": [{"id": p.id, "username": p.username} for p in players]
        }, room=game_id)
        
        return jsonify({"success": True})
    
    @app.route('/api/players/<player_id>/roll', methods=['POST'])
    def roll_dice(player_id):
        """Player rolls dice and moves"""
        player = Player.query.get(player_id)
        if not player:
            return jsonify({"error": "Player not found"}), 404
        
        # Roll dice
        total, dice1, dice2 = GameEngine.roll_dice()
        
        # Move player
        move_result = GameEngine.move_player(player_id, total)
        
        # Check for property at new position
        property = GameEngine.get_property_at_position(move_result["new_position"])
        
        result = {
            "dice_roll": {"total": total, "dice1": dice1, "dice2": dice2},
            "movement": move_result,
            "property": None
        }
        
        if property:
            result["property"] = {
                "id": property.id,
                "name": property.name,
                "price": property.price,
                "owner_id": property.owner_id,
                "can_buy": property.owner_id is None
            }
        
        # Broadcast to all players in game
        socketio.emit('player_moved', result, room=player.game_id)
        
        return jsonify(result)
    
    @app.route('/api/players/<player_id>/buy/<int:property_id>', methods=['POST'])
    def buy_property(player_id, property_id):
        """Player buys property"""
        result = GameEngine.buy_property(player_id, property_id)
        
        if result.get("success"):
            player = Player.query.get(player_id)
            # Broadcast property purchase
            socketio.emit('property_bought', {
                "player_id": player_id,
                "property_id": property_id,
                "player_money": result["player_money"]
            }, room=player.game_id)
        
        return jsonify(result)
    
    @app.route('/api/games/<game_id>', methods=['GET'])
    def get_game_state(game_id):
        """Get current game state"""
        game = Game.query.get(game_id)
        if not game:
            return jsonify({"error": "Game not found"}), 404
        
        players = Player.query.filter_by(game_id=game_id).all()
        properties = Property.query.all()
        
        return jsonify({
            "game": {
                "id": game.id,
                "status": game.status,
                "current_turn": game.current_turn
            },
            "players": [{
                "id": p.id,
                "username": p.username,
                "money": p.money,
                "position": p.position,
                "is_bot": p.is_bot,
                "in_jail": p.in_jail
            } for p in players],
            "properties": [{
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "rent": p.rent,
                "color_group": p.color_group,
                "owner_id": p.owner_id,
                "houses": p.houses,
                "has_hotel": p.has_hotel
            } for p in properties]
        })
```

### File: `backend/websocket_events.py`
```python
from flask_socketio import emit, join_room, leave_room
from flask import request

def register_websocket_events(socketio, db):
    
    @socketio.on('connect')
    def handle_connect():
        print(f'Client connected: {request.sid}')
        emit('connected', {'status': 'Connected to Pinopoly server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'Client disconnected: {request.sid}')
    
    @socketio.on('join_game')
    def handle_join_game(data):
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        
        if game_id:
            join_room(game_id)
            emit('joined_game', {
                'game_id': game_id,
                'player_id': player_id
            })
            print(f'Player {player_id} joined game {game_id}')
    
    @socketio.on('leave_game')
    def handle_leave_game(data):
        game_id = data.get('game_id')
        if game_id:
            leave_room(game_id)
            emit('left_game', {'game_id': game_id})
    
    @socketio.on('chat_message')
    def handle_chat_message(data):
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        message = data.get('message')
        
        if game_id and message:
            emit('chat_message', {
                'player_id': player_id,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }, room=game_id)
```

---

## STEP 3: FRONTEND - REACT APP (3 hours)

**Task**: Build the React frontend with game board, player interface, and real-time updates

[ ] Set up React project structure (`package.json`)
[ ] Create main App component (`App.js`)
[ ] Build game board component (`GameBoard.js`)
[ ] Create player list component (`PlayerList.js`)
[ ] Set up WebSocket client (`WebSocketClient.js`)
[ ] Create HTML template (`index.html`)
[ ] Install JavaScript dependencies

**Implementation Notes for Claude Code**:
- Start with package.json and run `npm install` before creating other files
- Create HTML template in public/ folder first
- Create components in src/ folder in the order listed
- Test each component by temporarily importing it in App.js
- Use browser developer tools to check for JavaScript errors
- Backend must be running before testing WebSocket connection

### File: `frontend/package.json`
```json
{
  "name": "pinopoly-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "socket.io-client": "^4.7.0",
    "axios": "^1.5.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "devDependencies": {
    "react-scripts": "5.0.1"
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  }
}
```

### File: `frontend/public/index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Pinopoly V2</title>
    <style>
        body { margin: 0; font-family: Arial, sans-serif; }
    </style>
</head>
<body>
    <div id="root"></div>
</body>
</html>
```

### File: `frontend/src/App.js`
```javascript
import React, { useState, useEffect } from 'react';
import GameBoard from './GameBoard';
import PlayerList from './PlayerList';
import WebSocketClient from './WebSocketClient';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

function App() {
    const [gameId, setGameId] = useState(null);
    const [gameState, setGameState] = useState(null);
    const [playerId, setPlayerId] = useState(null);
    const [socket, setSocket] = useState(null);
    const [username, setUsername] = useState('');

    // Create new game
    const createGame = async () => {
        try {
            const response = await axios.post(`${API_BASE}/games`);
            const newGameId = response.data.game_id;
            setGameId(newGameId);
            console.log('Game created:', newGameId);
        } catch (error) {
            console.error('Error creating game:', error);
        }
    };

    // Join game as player
    const joinGame = async () => {
        if (!gameId || !username) return;
        
        try {
            const response = await axios.post(`${API_BASE}/games/${gameId}/players`, {
                username: username,
                is_bot: false
            });
            setPlayerId(response.data.player_id);
            console.log('Joined game as:', response.data.username);
        } catch (error) {
            console.error('Error joining game:', error);
        }
    };

    // Start game
    const startGame = async () => {
        if (!gameId) return;
        
        try {
            await axios.post(`${API_BASE}/games/${gameId}/start`);
            console.log('Game started');
        } catch (error) {
            console.error('Error starting game:', error);
        }
    };

    // Load game state
    const loadGameState = async () => {
        if (!gameId) return;
        
        try {
            const response = await axios.get(`${API_BASE}/games/${gameId}`);
            setGameState(response.data);
        } catch (error) {
            console.error('Error loading game state:', error);
        }
    };

    // Roll dice
    const rollDice = async () => {
        if (!playerId) return;
        
        try {
            const response = await axios.post(`${API_BASE}/players/${playerId}/roll`);
            console.log('Dice rolled:', response.data);
            // Game state will update via WebSocket
        } catch (error) {
            console.error('Error rolling dice:', error);
        }
    };

    // Buy property
    const buyProperty = async (propertyId) => {
        if (!playerId) return;
        
        try {
            const response = await axios.post(`${API_BASE}/players/${playerId}/buy/${propertyId}`);
            console.log('Property purchase:', response.data);
        } catch (error) {
            console.error('Error buying property:', error);
        }
    };

    // WebSocket event handlers
    const handleSocketEvent = (eventType, data) => {
        console.log('Socket event:', eventType, data);
        
        switch (eventType) {
            case 'player_moved':
            case 'property_bought':
            case 'game_started':
                // Reload game state when events occur
                loadGameState();
                break;
            default:
                break;
        }
    };

    // Load game state when gameId changes
    useEffect(() => {
        if (gameId) {
            loadGameState();
        }
    }, [gameId]);

    return (
        <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
            <h1>Pinopoly V2</h1>
            
            {/* WebSocket connection */}
            <WebSocketClient 
                gameId={gameId} 
                playerId={playerId}
                onEvent={handleSocketEvent}
                setSocket={setSocket}
            />
            
            {/* Game setup */}
            {!gameId && (
                <div style={{ marginBottom: '20px' }}>
                    <button onClick={createGame} style={{ padding: '10px 20px', fontSize: '16px' }}>
                        Create New Game
                    </button>
                </div>
            )}
            
            {gameId && !playerId && (
                <div style={{ marginBottom: '20px' }}>
                    <h3>Game ID: {gameId}</h3>
                    <input 
                        type="text" 
                        placeholder="Enter your username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        style={{ padding: '8px', marginRight: '10px' }}
                    />
                    <button onClick={joinGame} style={{ padding: '8px 16px' }}>
                        Join Game
                    </button>
                </div>
            )}
            
            {gameId && playerId && gameState?.game?.status === 'waiting' && (
                <div style={{ marginBottom: '20px' }}>
                    <button onClick={startGame} style={{ padding: '10px 20px', fontSize: '16px' }}>
                        Start Game
                    </button>
                </div>
            )}
            
            {/* Game controls */}
            {gameState?.game?.status === 'active' && playerId && (
                <div style={{ marginBottom: '20px' }}>
                    <button onClick={rollDice} style={{ padding: '10px 20px', fontSize: '16px', marginRight: '10px' }}>
                        Roll Dice
                    </button>
                    <button onClick={loadGameState} style={{ padding: '10px 20px', fontSize: '16px' }}>
                        Refresh
                    </button>
                </div>
            )}
            
            {/* Game display */}
            {gameState && (
                <div style={{ display: 'flex', gap: '20px' }}>
                    <div style={{ flex: 2 }}>
                        <GameBoard 
                            gameState={gameState} 
                            currentPlayerId={playerId}
                            onBuyProperty={buyProperty}
                        />
                    </div>
                    <div style={{ flex: 1 }}>
                        <PlayerList 
                            players={gameState.players} 
                            currentPlayerId={playerId}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;
```

### File: `frontend/src/GameBoard.js`
```javascript
import React from 'react';

// Board positions for a standard Monopoly board
const BOARD_POSITIONS = [
    { id: 0, name: "GO", type: "corner" },
    { id: 1, name: "Mediterranean Avenue", type: "property" },
    { id: 2, name: "Community Chest", type: "card" },
    { id: 3, name: "Baltic Avenue", type: "property" },
    { id: 4, name: "Income Tax", type: "tax" },
    { id: 5, name: "Reading Railroad", type: "railroad" },
    { id: 6, name: "Oriental Avenue", type: "property" },
    { id: 7, name: "Chance", type: "card" },
    { id: 8, name: "Vermont Avenue", type: "property" },
    { id: 9, name: "Connecticut Avenue", type: "property" },
    { id: 10, name: "Jail", type: "corner" },
    { id: 11, name: "St. Charles Place", type: "property" },
    { id: 12, name: "Electric Company", type: "utility" },
    { id: 13, name: "States Avenue", type: "property" },
    { id: 14, name: "Virginia Avenue", type: "property" },
    { id: 15, name: "Pennsylvania Railroad", type: "railroad" },
    { id: 16, name: "St. James Place", type: "property" },
    { id: 17, name: "Community Chest", type: "card" },
    { id: 18, name: "Tennessee Avenue", type: "property" },
    { id: 19, name: "New York Avenue", type: "property" },
    { id: 20, name: "Free Parking", type: "corner" },
    { id: 21, name: "Kentucky Avenue", type: "property" },
    { id: 22, name: "Chance", type: "card" },
    { id: 23, name: "Indiana Avenue", type: "property" },
    { id: 24, name: "Illinois Avenue", type: "property" },
    { id: 25, name: "B&O Railroad", type: "railroad" },
    { id: 26, name: "Atlantic Avenue", type: "property" },
    { id: 27, name: "Ventnor Avenue", type: "property" },
    { id: 28, name: "Water Works", type: "utility" },
    { id: 29, name: "Marvin Gardens", type: "property" },
    { id: 30, name: "Go to Jail", type: "corner" },
    { id: 31, name: "Pacific Avenue", type: "property" },
    { id: 32, name: "North Carolina Avenue", type: "property" },
    { id: 33, name: "Community Chest", type: "card" },
    { id: 34, name: "Pennsylvania Avenue", type: "property" },
    { id: 35, name: "Short Line", type: "railroad" },
    { id: 36, name: "Chance", type: "card" },
    { id: 37, name: "Park Place", type: "property" },
    { id: 38, name: "Luxury Tax", type: "tax" },
    { id: 39, name: "Boardwalk", type: "property" }
];

function GameBoard({ gameState, currentPlayerId, onBuyProperty }) {
    const { players = [], properties = [] } = gameState;

    // Get property data by position
    const getPropertyAtPosition = (position) => {
        return properties.find(p => p.id === position);
    };

    // Get players at position
    const getPlayersAtPosition = (position) => {
        return players.filter(p => p.position === position);
    };

    // Handle property click
    const handlePropertyClick = (position) => {
        const property = getPropertyAtPosition(position);
        if (property && !property.owner_id && currentPlayerId) {
            const confirm = window.confirm(`Buy ${property.name} for $${property.price}?`);
            if (confirm) {
                onBuyProperty(property.id);
            }
        }
    };

    return (
        <div>
            <h3>Game Board</h3>
            <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(11, 1fr)',
                gridTemplateRows: 'repeat(11, 1fr)',
                gap: '2px',
                width: '600px',
                height: '600px',
                border: '2px solid #333',
                backgroundColor: '#f0f0f0'
            }}>
                {BOARD_POSITIONS.map((boardSpace, index) => {
                    const property = getPropertyAtPosition(boardSpace.id);
                    const playersHere = getPlayersAtPosition(boardSpace.id);
                    
                    // Determine grid position based on board layout
                    let gridColumn, gridRow;
                    if (index <= 10) {
                        // Bottom row
                        gridColumn = 11 - index;
                        gridRow = 11;
                    } else if (index <= 20) {
                        // Left side
                        gridColumn = 1;
                        gridRow = 11 - (index - 10);
                    } else if (index <= 30) {
                        // Top row
                        gridColumn = index - 20 + 1;
                        gridRow = 1;
                    } else {
                        // Right side
                        gridColumn = 11;
                        gridRow = index - 30 + 1;
                    }

                    return (
                        <div
                            key={boardSpace.id}
                            style={{
                                gridColumn,
                                gridRow,
                                border: '1px solid #666',
                                backgroundColor: property?.owner_id ? '#ffeb3b' : '#fff',
                                padding: '4px',
                                fontSize: '10px',
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'space-between',
                                cursor: property && !property.owner_id ? 'pointer' : 'default',
                                position: 'relative'
                            }}
                            onClick={() => handlePropertyClick(boardSpace.id)}
                        >
                            <div style={{ fontWeight: 'bold', textAlign: 'center' }}>
                                {boardSpace.name}
                            </div>
                            
                            {property && (
                                <div style={{ textAlign: 'center' }}>
                                    <div>${property.price}</div>
                                    {property.owner_id && (
                                        <div style={{ color: 'green', fontSize: '8px' }}>OWNED</div>
                                    )}
                                </div>
                            )}
                            
                            {/* Player tokens */}
                            {playersHere.length > 0 && (
                                <div style={{ 
                                    position: 'absolute', 
                                    bottom: '2px', 
                                    right: '2px',
                                    display: 'flex',
                                    flexWrap: 'wrap',
                                    gap: '1px'
                                }}>
                                    {playersHere.map(player => (
                                        <div
                                            key={player.id}
                                            style={{
                                                width: '8px',
                                                height: '8px',
                                                backgroundColor: player.id === currentPlayerId ? 'red' : 'blue',
                                                borderRadius: '50%',
                                                border: '1px solid black'
                                            }}
                                            title={player.username}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}
                
                {/* Center area */}
                <div style={{
                    gridColumn: '2 / 11',
                    gridRow: '2 / 11',
                    backgroundColor: '#e8f5e8',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '24px',
                    fontWeight: 'bold',
                    color: '#333'
                }}>
                    PINOPOLY
                </div>
            </div>
        </div>
    );
}

export default GameBoard;
```

### File: `frontend/src/PlayerList.js`
```javascript
import React from 'react';

function PlayerList({ players, currentPlayerId }) {
    return (
        <div>
            <h3>Players</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {players.map(player => (
                    <div
                        key={player.id}
                        style={{
                            border: '2px solid #ccc',
                            borderColor: player.id === currentPlayerId ? '#4caf50' : '#ccc',
                            borderRadius: '8px',
                            padding: '15px',
                            backgroundColor: player.id === currentPlayerId ? '#f0f8f0' : '#fff'
                        }}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <h4 style={{ margin: '0 0 5px 0' }}>
                                    {player.username}
                                    {player.is_bot && <span style={{ color: '#666', fontSize: '12px' }}> (BOT)</span>}
                                    {player.id === currentPlayerId && <span style={{ color: '#4caf50', fontSize: '12px' }}> (YOU)</span>}
                                </h4>
                                <div style={{ fontSize: '14px', color: '#666' }}>
                                    Position: {player.position}
                                </div>
                                {player.in_jail && (
                                    <div style={{ fontSize: '12px', color: 'red' }}>
                                        IN JAIL
                                    </div>
                                )}
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#2e7d32' }}>
                                    ${player.money}
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default PlayerList;
```

### File: `frontend/src/WebSocketClient.js`
```javascript
import { useEffect } from 'react';
import io from 'socket.io-client';

function WebSocketClient({ gameId, playerId, onEvent, setSocket }) {
    useEffect(() => {
        if (!gameId) return;

        console.log('Connecting to WebSocket server...');
        const socket = io('http://localhost:8000');

        socket.on('connect', () => {
            console.log('Connected to WebSocket server');
            
            // Join the game room
            socket.emit('join_game', {
                game_id: gameId,
                player_id: playerId
            });
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from WebSocket server');
        });

        // Game event handlers
        socket.on('player_joined', (data) => {
            console.log('Player joined:', data);
            onEvent('player_joined', data);
        });

        socket.on('game_started', (data) => {
            console.log('Game started:', data);
            onEvent('game_started', data);
        });

        socket.on('player_moved', (data) => {
            console.log('Player moved:', data);
            onEvent('player_moved', data);
        });

        socket.on('property_bought', (data) => {
            console.log('Property bought:', data);
            onEvent('property_bought', data);
        });

        socket.on('chat_message', (data) => {
            console.log('Chat message:', data);
            onEvent('chat_message', data);
        });

        // Error handling
        socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
        });

        setSocket(socket);

        // Cleanup on unmount
        return () => {
            console.log('Cleaning up WebSocket connection');
            socket.disconnect();
        };
    }, [gameId, playerId, onEvent, setSocket]);

    return null; // This component doesn't render anything
}

export default WebSocketClient;
```

### File: `frontend/src/index.js`
```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
```

---

## STEP 4: DOCKER SETUP (30 minutes)

**Task**: Create Docker configuration for easy development and deployment

[ ] Create main docker-compose file
[ ] Set up backend Dockerfile  
[ ] Set up frontend Dockerfile
[ ] Configure environment variables
[ ] Set up database and Redis services

**Implementation Notes for Claude Code**:
- Create docker-compose.yml in the root directory first
- Create Dockerfiles in their respective backend/ and frontend/ directories
- Ensure all source files are created before building Docker images
- Use `docker-compose up --build` to build and start all services
- Check logs with `docker-compose logs` if services fail to start

### File: `docker-compose.yml`
```yaml
version: '3.8'

services:
  database:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: pinopoly
      POSTGRES_USER: pinopoly_user
      POSTGRES_PASSWORD: pinopoly_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://pinopoly_user:pinopoly_pass@database:5432/pinopoly
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend:/app
    depends_on:
      - database
      - redis
    command: python app.py

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    command: npm start

volumes:
  postgres_data:
```

### File: `backend/Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

### File: `frontend/Dockerfile`
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

### File: `.env`
```bash
# Database
DATABASE_URL=postgresql://pinopoly_user:pinopoly_pass@localhost:5432/pinopoly

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here

# API
API_BASE_URL=http://localhost:8000
```

---

## STEP 5: RUN THE APPLICATION (10 minutes)

**Task**: Start the application and verify everything works

[ ] Start all services with Docker
[ ] Verify backend health endpoint
[ ] Test frontend loads correctly  
[ ] Create a test game
[ ] Test multiplayer functionality
[ ] Verify real-time updates work

**Implementation Notes for Claude Code**:
- Wait for all Docker containers to be "running" before testing
- Test backend health first: `curl http://localhost:8000/health`
- Open browser to `http://localhost:3000` to test frontend
- Use browser developer tools to monitor WebSocket connections
- Test with multiple browser tabs to verify multiplayer functionality
- Check Docker logs if any service isn't responding: `docker-compose logs [service-name]`

### Commands to run:

1. **Start everything:**
```bash
docker-compose up --build
```

2. **OR run manually:**

Backend:
```bash
cd backend
pip install -r requirements.txt
python app.py
```

Frontend:
```bash
cd frontend
npm install
npm start
```

### Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

---

## TESTING THE GAME

**Task**: Verify the game works correctly by testing key functionality

[ ] Test game creation
[ ] Test player joining
[ ] Test game start
[ ] Test dice rolling and movement
[ ] Test property purchasing
[ ] Test real-time updates between players

1. **Open** http://localhost:3000
2. **Click** "Create New Game"
3. **Enter** a username and click "Join Game"
4. **Open** another browser tab and join the same game with different username
5. **Click** "Start Game"
6. **Click** "Roll Dice" to move around the board
7. **Click** on properties to buy them

---

## WHAT YOU GET

This implementation gives you:

- **Working Monopoly Game** - Complete with dice rolling, property buying, money management
- **Real-time Multiplayer** - Multiple players can join and play simultaneously  
- **WebSocket Communication** - Live updates when players move or buy properties
- **Clean Database Models** - SQLite database with proper relationships
- **REST API** - Full API for game operations
- **React Frontend** - Modern React UI with game board visualization
- **Docker Setup** - One-command deployment with docker-compose
- **Extensible Architecture** - Easy to add features like bot players, more game rules

---

## NEXT STEPS TO ENHANCE

**Phase 2 Features** (after basic game is working):

[ ] **Bot Players** - AI players with different strategies
[ ] **Property Development** - Houses and hotels
[ ] **Special Cards** - Chance and Community Chest
[ ] **Jail System** - Go to jail, pay to get out
[ ] **Auctions** - Property auctions when players decline to buy
[ ] **Trading** - Player-to-player property trades
[ ] **Game History** - Save and replay games
[ ] **Admin Panel** - Manage games and players
[ ] **Mobile Support** - Responsive design for mobile devices
[ ] **Sound Effects** - Audio feedback for actions

---

## PROJECT COMPLETION CHECKLIST

**Core Implementation** (6 hours total):
[ ] Project structure created (30 min)
[ ] Backend Flask app built (2 hours)
[ ] Frontend React app built (3 hours)  
[ ] Docker setup configured (30 min)
[ ] Application tested and working (30 min)

**Verification Tests**:
[ ] Health endpoint responds
[ ] Game creation works
[ ] Players can join games
[ ] Dice rolling and movement works
[ ] Property buying works
[ ] Real-time updates work between multiple browser tabs
[ ] Docker containers start without errors

## Common Issues and Solutions for Claude Code

**Backend Issues**:
- Import errors: Ensure all files are created before importing
- Database errors: Check SQLite file permissions and database initialization
- Port conflicts: Ensure no other services are running on port 8000

**Frontend Issues**:
- NPM install fails: Delete node_modules and package-lock.json, try again
- React compilation errors: Check all imports and component syntax
- WebSocket connection fails: Verify backend is running and Socket.IO is working

**Docker Issues**:
- Build failures: Check Dockerfile syntax and file paths
- Container startup issues: Review docker-compose logs for specific errors
- Port binding issues: Ensure ports 3000, 8000, 5432 are available

**General Debugging**:
- Use `docker-compose logs [service]` to check container logs
- Use browser developer tools to check network requests and WebSocket connections
- Test each component individually before integration
- Verify all dependencies are installed before running code

This is a REAL, WORKING Monopoly game that you can build in about 6 hours. No theory, no complex architecture - just working code that you can run and extend.