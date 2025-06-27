# API Examples for Pinopoly V2

This document provides working examples of all API endpoints with request/response formats.

## Base URL
- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

## Authentication
Most endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Player Management API

### Create Player
**POST** `/api/v1/players`

**Request:**
```json
{
  "name": "Alice Johnson",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

**Response (201 Created):**
```json
{
  "id": "player-12345",
  "name": "Alice Johnson",
  "avatar_url": "https://example.com/avatar.jpg",
  "money": 1500,
  "position": 0,
  "properties": [],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/players \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "avatar_url": "https://example.com/avatar.jpg"
  }'
```

### Get Player
**GET** `/api/v1/players/{player_id}`

**Response (200 OK):**
```json
{
  "id": "player-12345",
  "name": "Alice Johnson",
  "avatar_url": "https://example.com/avatar.jpg",
  "money": 1350,
  "position": 7,
  "properties": ["property-1", "property-5"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:45:00Z"
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/players/player-12345 \
  -H "Authorization: Bearer <your_jwt_token>"
```

### Update Player
**PUT** `/api/v1/players/{player_id}`

**Request:**
```json
{
  "name": "Alice Smith",
  "avatar_url": "https://example.com/new-avatar.jpg"
}
```

**Response (200 OK):**
```json
{
  "id": "player-12345",
  "name": "Alice Smith",
  "avatar_url": "https://example.com/new-avatar.jpg",
  "money": 1350,
  "position": 7,
  "properties": ["property-1", "property-5"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### Move Player
**POST** `/api/v1/players/{player_id}/move`

**Request:**
```json
{
  "spaces": 7
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "player_id": "player-12345",
  "old_position": 5,
  "new_position": 12,
  "spaces_moved": 7,
  "passed_go": false,
  "money_earned": 0,
  "landed_on": {
    "space_id": 12,
    "space_name": "Electric Company",
    "space_type": "UTILITY"
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/players/player-12345/move \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -d '{"spaces": 7}'
```

## Game Management API

### Create Game
**POST** `/api/v1/games`

**Request:**
```json
{
  "name": "Friday Night Game",
  "max_players": 6,
  "settings": {
    "starting_money": 1500,
    "salary": 200,
    "free_parking_money": 500
  }
}
```

**Response (201 Created):**
```json
{
  "id": "game-67890",
  "name": "Friday Night Game",
  "status": "waiting",
  "max_players": 6,
  "current_players": 0,
  "settings": {
    "starting_money": 1500,
    "salary": 200,
    "free_parking_money": 500
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Get Game State
**GET** `/api/v1/games/{game_id}`

**Response (200 OK):**
```json
{
  "id": "game-67890",
  "name": "Friday Night Game",
  "status": "in_progress",
  "current_turn": "player-12345",
  "turn_number": 15,
  "players": [
    {
      "id": "player-12345",
      "name": "Alice Johnson",
      "money": 1350,
      "position": 12,
      "properties": ["property-1", "property-5"],
      "in_jail": false
    },
    {
      "id": "player-67890",
      "name": "Bob Wilson", 
      "money": 1200,
      "position": 8,
      "properties": ["property-3", "property-7", "property-15"],
      "in_jail": true,
      "jail_turns": 1
    }
  ],
  "board": {
    "spaces": [
      {
        "id": 0,
        "name": "GO",
        "type": "GO"
      },
      {
        "id": 1,
        "name": "Mediterranean Avenue",
        "type": "PROPERTY",
        "price": 60,
        "rent": [2, 10, 30, 90, 160, 250],
        "owner": "player-12345",
        "houses": 0,
        "color_group": "brown"
      }
    ]
  },
  "dice": [4, 3],
  "last_action": {
    "type": "MOVE",
    "player_id": "player-12345",
    "timestamp": "2024-01-15T10:45:00Z",
    "details": "Moved 7 spaces to Electric Company"
  }
}
```

### Join Game
**POST** `/api/v1/games/{game_id}/join`

**Request:**
```json
{
  "player_id": "player-12345"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Player joined game successfully",
  "game_id": "game-67890",
  "player_id": "player-12345",
  "player_position": 2
}
```

### Start Game
**POST** `/api/v1/games/{game_id}/start`

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Game started successfully",
  "game_id": "game-67890",
  "first_player": "player-12345",
  "turn_order": ["player-12345", "player-67890", "player-11111"]
}
```

## Property Management API

### Get Property Details
**GET** `/api/v1/properties/{property_id}`

**Response (200 OK):**
```json
{
  "id": "property-1",
  "name": "Mediterranean Avenue",
  "type": "PROPERTY",
  "position": 1,
  "price": 60,
  "rent": [2, 10, 30, 90, 160, 250],
  "house_price": 50,
  "hotel_price": 50,
  "mortgage_value": 30,
  "color_group": "brown",
  "owner": "player-12345",
  "houses": 2,
  "hotels": 0,
  "mortgaged": false
}
```

### Buy Property
**POST** `/api/v1/properties/{property_id}/buy`

**Request:**
```json
{
  "player_id": "player-12345"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Property purchased successfully",
  "property_id": "property-1",
  "player_id": "player-12345",
  "purchase_price": 60,
  "player_money_remaining": 1440
}
```

### Build House
**POST** `/api/v1/properties/{property_id}/build`

**Request:**
```json
{
  "player_id": "player-12345",
  "building_type": "house",
  "quantity": 2
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Houses built successfully",
  "property_id": "property-1",
  "buildings_added": 2,
  "total_houses": 2,
  "cost": 100,
  "player_money_remaining": 1250
}
```

## Game Actions API

### Roll Dice
**POST** `/api/v1/games/{game_id}/roll-dice`

**Request:**
```json
{
  "player_id": "player-12345"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "dice": [4, 3],
  "total": 7,
  "is_double": false,
  "player_id": "player-12345",
  "move_result": {
    "old_position": 5,
    "new_position": 12,
    "passed_go": false,
    "money_earned": 0,
    "landed_on": {
      "space_id": 12,
      "space_name": "Electric Company",
      "space_type": "UTILITY"
    }
  }
}
```

### End Turn
**POST** `/api/v1/games/{game_id}/end-turn`

**Request:**
```json
{
  "player_id": "player-12345"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Turn ended successfully",
  "previous_player": "player-12345",
  "next_player": "player-67890",
  "turn_number": 16
}
```

### Pay Rent
**POST** `/api/v1/games/{game_id}/pay-rent`

**Request:**
```json
{
  "player_id": "player-12345",
  "property_id": "property-3",
  "amount": 50
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Rent paid successfully",
  "payer": "player-12345",
  "receiver": "player-67890",
  "amount": 50,
  "property_name": "Oriental Avenue",
  "payer_money_remaining": 1200,
  "receiver_money_new": 1350
}
```

## Trading API

### Create Trade Offer
**POST** `/api/v1/trades`

**Request:**
```json
{
  "proposer_id": "player-12345",
  "receiver_id": "player-67890",
  "proposer_offers": {
    "money": 200,
    "properties": ["property-1", "property-5"],
    "get_out_of_jail_cards": 1
  },
  "receiver_offers": {
    "money": 0,
    "properties": ["property-3"],
    "get_out_of_jail_cards": 0
  },
  "message": "I'll give you $200 and two properties for Oriental Avenue"
}
```

**Response (201 Created):**
```json
{
  "id": "trade-99999",
  "status": "pending",
  "proposer_id": "player-12345",
  "receiver_id": "player-67890",
  "proposer_offers": {
    "money": 200,
    "properties": ["property-1", "property-5"],
    "get_out_of_jail_cards": 1
  },
  "receiver_offers": {
    "money": 0,
    "properties": ["property-3"],
    "get_out_of_jail_cards": 0
  },
  "message": "I'll give you $200 and two properties for Oriental Avenue",
  "created_at": "2024-01-15T11:00:00Z",
  "expires_at": "2024-01-15T11:15:00Z"
}
```

### Accept Trade
**POST** `/api/v1/trades/{trade_id}/accept`

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Trade completed successfully",
  "trade_id": "trade-99999",
  "completed_at": "2024-01-15T11:05:00Z"
}
```

## Authentication API

### Login
**POST** `/api/v1/auth/login`

**Request:**
```json
{
  "username": "alice@example.com",
  "password": "secure_password"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user-12345",
    "username": "alice@example.com",
    "display_name": "Alice Johnson"
  }
}
```

### Refresh Token
**POST** `/api/v1/auth/refresh`

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

## WebSocket Events

### Connection
```javascript
// Client connects
socket.emit('join_game', { game_id: 'game-67890', player_id: 'player-12345' });

// Server response
socket.on('game_joined', {
  success: true,
  game_id: 'game-67890',
  player_id: 'player-12345'
});
```

### Player Movement
```javascript
// Client requests move
socket.emit('player_move', {
  game_id: 'game-67890',
  player_id: 'player-12345',
  dice: [4, 3]
});

// Server broadcasts to all players
socket.on('player_moved', {
  game_id: 'game-67890',
  player_id: 'player-12345',
  old_position: 5,
  new_position: 12,
  dice: [4, 3],
  passed_go: false
});
```

### Game State Updates
```javascript
// Server broadcasts game state changes
socket.on('game_state_updated', {
  game_id: 'game-67890',
  update_type: 'property_purchased',
  data: {
    player_id: 'player-12345',
    property_id: 'property-1',
    price: 60
  },
  timestamp: '2024-01-15T11:10:00Z'
});
```

## Error Responses

### Validation Error (400 Bad Request)
```json
{
  "error": "Validation Error",
  "message": "Invalid request data",
  "details": [
    {
      "field": "name",
      "message": "Name is required"
    },
    {
      "field": "spaces",
      "message": "Spaces must be between 1 and 12"
    }
  ]
}
```

### Not Found (404 Not Found)
```json
{
  "error": "Not Found",
  "message": "Player with ID 'player-99999' not found"
}
```

### Business Logic Error (400 Bad Request)
```json
{
  "error": "Business Rule Violation",
  "message": "Cannot purchase property: insufficient funds",
  "details": {
    "required_amount": 200,
    "player_money": 150,
    "shortage": 50
  }
}
```

### Server Error (500 Internal Server Error)
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "request_id": "req-12345-67890"
}
```

## Testing with Postman

### Import Collection
Save this as `pinopoly-v2.postman_collection.json`:

```json
{
  "info": {
    "name": "Pinopoly V2 API",
    "description": "Complete API collection for Pinopoly V2"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    },
    {
      "key": "auth_token",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "Create Player",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "url": "{{base_url}}/api/v1/players",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"name\": \"Test Player\",\n  \"avatar_url\": \"https://example.com/avatar.jpg\"\n}"
        }
      }
    }
  ]
}
```

### Environment Variables
```json
{
  "name": "Pinopoly V2 Development",
  "values": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    },
    {
      "key": "auth_token",
      "value": "Bearer your_jwt_token_here"
    }
  ]
}
```

This API documentation provides comprehensive examples for all endpoints, making it easy to understand and test the Pinopoly V2 API.