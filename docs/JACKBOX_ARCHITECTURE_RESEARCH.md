# Jackbox Architecture Research & Recommendations

## Executive Summary

Jackbox games use a **three-tier broker architecture** that cleanly separates concerns between the TV display (Game Host), player phones (Clients), and a central message broker (Server). This document analyzes how Jackbox works and provides specific recommendations for refactoring Pinopoly to follow these patterns.

---

## How Jackbox Actually Works

### The Three Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         JACKBOX ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐   │
│   │   TV/HOST    │         │    BROKER    │         │    PHONES    │   │
│   │   (Game)     │◄───────►│   (Server)   │◄───────►│  (Clients)   │   │
│   └──────────────┘         └──────────────┘         └──────────────┘   │
│                                                                         │
│   - Runs game engine       - Manages rooms          - Simple web UI     │
│   - Shows main display     - Routes messages        - jackbox.tv        │
│   - Controls game flow     - Tracks connections     - No app download   │
│   - Owns game state        - Validates codes        - Player-specific   │
│                            - Broadcasts events       view               │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Insight: The TV is the HOST, Not a Client

**This is where your current architecture differs fundamentally.**

In Jackbox:
- The **TV/Host** is the authoritative game engine that OWNS the state
- The **Broker** is a dumb message router that knows nothing about game rules
- The **Phones** are dumb input devices that display what they're told

In your current Pinopoly architecture:
- The **Server** owns the game state (database)
- **All clients** (TV and phones) are treated equally
- The server runs all game logic

### Jackbox Protocol Flow

```
1. GAME CREATION
   ┌──────────┐                    ┌──────────┐
   │   TV     │ ──create_room───► │  Broker  │
   │   Host   │ ◄──room_code───── │          │
   └──────────┘   (e.g. "ABCD")   └──────────┘

2. PLAYER JOINS
   ┌──────────┐                    ┌──────────┐
   │  Phone   │ ──join("ABCD",──► │  Broker  │ ──player_joined──► TV
   │          │    "Alice")        │          │
   │          │ ◄──welcome + ───── │          │
   │          │   player_view      │          │
   └──────────┘                    └──────────┘

3. GAMEPLAY (Player Action)
   ┌──────────┐                    ┌──────────┐                    ┌──────────┐
   │  Phone   │ ──submit_answer──► │  Broker  │ ──forward_to───► │    TV    │
   │ (Alice)  │                    │          │    host           │   Host   │
   └──────────┘                    └──────────┘                    └──────────┘

4. GAMEPLAY (State Update)
   ┌──────────┐                    ┌──────────┐                    ┌──────────┐
   │    TV    │ ──broadcast_to───► │  Broker  │ ──update_view───► │  Phones  │
   │   Host   │    all_players     │          │   (each player    │  (all)   │
   │          │                    │          │    gets their     │          │
   │          │ ──update_display─► │          │    own view)      │          │
   │          │    (to self)       │          │                    │          │
   └──────────┘                    └──────────┘                    └──────────┘
```

### Critical Design Patterns

#### 1. **Players Get Personalized Views**
Each phone only sees what it needs to see:
- In Fibbage: Only you see your submitted lie
- In Quiplash: Only you see your prompt to answer
- Voting screens show options but not who submitted what

#### 2. **TV Shows Shared State**
The TV displays the "public" game state everyone can see.

#### 3. **Simple Client Components**
Jackbox keeps phone UI deliberately limited:
- Text input
- Button selection
- Drawing canvas
- That's basically it

#### 4. **No App Required**
Players visit `jackbox.tv`, enter 4-character room code, done.

---

## What's Wrong with Pinopoly's Current Architecture

Based on analysis of your codebase:

### Problem 1: No Clear Host/Client Separation

**Current State:**
```
All Clients ──WebSocket──► Server (owns state)
                               │
                               ▼
                          Database
```

**Issue:** Every client is treated the same. There's no "TV display" vs "phone controller" distinction.

### Problem 2: Full State Broadcast to Everyone

```python
# socket_game_controller.py
socketio.emit('game_state', state, room=game.game_id)
```

Every client gets the **complete game state** including:
- All players' money
- All properties
- All cards (including ones players shouldn't see)
- Everything

**Jackbox approach:** Each client gets only the data they need.

### Problem 3: No State Versioning

Your clients have no way to know if they have stale state:
```javascript
// What if this arrives out of order?
socket.on('game_state_update', handleGameStateUpdate)
socket.on('dice_rolled', handleDiceRolled)
```

### Problem 4: Database Queries on Every Action

```python
def build_complete_game_state():
    # Query all players
    # Query all properties
    # Query game state
    # Rebuild everything
```

This happens on EVERY action, causing latency and potential race conditions.

### Problem 5: Multiple Overlapping Socket Handlers

You have THREE socket controller files that can handle the same events:
- `socket_core.py`
- `socket_controller.py`
- `socket_game_controller.py`

This creates confusion about which handler runs.

---

## Recommended Architecture Refactor

### New Architecture: Jackbox-Style

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PROPOSED PINOPOLY ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────┐      ┌────────────────┐      ┌────────────────┐    │
│  │   TV DISPLAY   │      │     SERVER     │      │  PHONE CLIENTS │    │
│  │   (Host Mode)  │      │    (Broker)    │      │  (Player Mode) │    │
│  ├────────────────┤      ├────────────────┤      ├────────────────┤    │
│  │ - Game board   │      │ - Room codes   │      │ - Your hand    │    │
│  │ - All tokens   │      │ - Message      │      │ - Action btns  │    │
│  │ - Public info  │      │   routing      │      │ - Your money   │    │
│  │ - Animations   │      │ - Connection   │      │ - Buy/sell UI  │    │
│  │ - Dice display │      │   tracking     │      │ - Trade UI     │    │
│  │                │      │ - Game state   │      │                │    │
│  │                │      │   (minimal)    │      │                │    │
│  └───────▲────────┘      └───────▲────────┘      └───────▲────────┘    │
│          │                       │                       │              │
│          │    ┌──────────────────┼──────────────────┐    │              │
│          │    │                  │                  │    │              │
│          └────┤     WebSocket    │    WebSocket     ├────┘              │
│               │     (display     │    (actions      │                   │
│               │      updates)    │     + personal   │                   │
│               │                  │      state)      │                   │
│               └──────────────────┴──────────────────┘                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Implementation Plan

#### Phase 1: Separate Client Types

**Create two client modes:**

```javascript
// TV Display Mode (board_organized/)
const clientType = 'display';

// Phone Controller Mode (client/)
const clientType = 'controller';
```

**Server tracks client types:**
```python
connected_clients = {
    'room_ABCD': {
        'display': [socket_id_1],      # TV
        'controllers': [socket_id_2, socket_id_3, ...]  # Phones
    }
}
```

#### Phase 2: Implement Personal State Views

**Instead of:**
```python
# Bad: Everyone gets everything
emit('game_state', full_state, room=game_id)
```

**Do this:**
```python
# Good: TV gets display state
emit('display_update', build_display_state(game), room=f'{game_id}_display')

# Good: Each player gets their personal view
for player in players:
    personal_state = build_player_view(game, player)
    emit('player_update', personal_state, room=f'player_{player.id}')
```

**Personal state example:**
```python
def build_player_view(game, player):
    return {
        'your_turn': game.current_player_id == player.id,
        'your_money': player.balance,
        'your_properties': [p for p in properties if p.owner_id == player.id],
        'available_actions': get_available_actions(game, player),
        'cards_in_hand': player.get_cards(),  # Only YOUR cards
        # NOT other players' money, NOT other players' cards
    }

def build_display_state(game):
    return {
        'board': get_board_state(),
        'player_positions': {p.id: p.position for p in players},
        'player_tokens': {p.id: p.token for p in players},
        'current_player': game.current_player_id,
        'dice_result': game.last_dice_roll,
        'public_properties': get_property_ownership(),
        # Public info only
    }
```

#### Phase 3: Add State Versioning

```python
class GameState:
    state_version = db.Column(db.Integer, default=0)

    def increment_version(self):
        self.state_version += 1
        return self.state_version
```

```javascript
// Client-side
let lastKnownVersion = 0;

socket.on('state_update', (data) => {
    if (data.version <= lastKnownVersion) {
        console.log('Ignoring stale update');
        return;
    }
    lastKnownVersion = data.version;
    applyUpdate(data);
});
```

#### Phase 4: Implement Action Acknowledgments

**Current (problematic):**
```javascript
// Fire and forget
socket.emit('roll_dice', { player_id });
// UI updates immediately, hopes server accepts
```

**Better (Jackbox-style):**
```javascript
// Request-Response pattern
socket.emit('roll_dice', { player_id }, (response) => {
    if (response.success) {
        // Server accepted, update will come via broadcast
    } else {
        showError(response.error);
    }
});
```

```python
@socketio.on('roll_dice')
def handle_roll_dice(data):
    result = game_logic.roll_dice(data['player_id'])

    if result.success:
        # Broadcast updates to appropriate clients
        broadcast_game_updates(game)
        return {'success': True, 'dice': result.dice}
    else:
        return {'success': False, 'error': result.error}
```

#### Phase 5: Simplify Phone UI

**Current phone interface:** Full game board, complex state
**Jackbox-style phone interface:** Just action buttons

```jsx
// Phone controller - simple and focused
function PhoneController({ playerId }) {
    const { yourTurn, availableActions, yourMoney } = usePlayerState(playerId);

    if (!yourTurn) {
        return <WaitingScreen message="Waiting for other players..." />;
    }

    return (
        <div className="controller">
            <MoneyDisplay amount={yourMoney} />
            <ActionButtons actions={availableActions} />
        </div>
    );
}

// Actions are simple buttons
function ActionButtons({ actions }) {
    return actions.map(action => (
        <button onClick={() => doAction(action.type)}>
            {action.label}
        </button>
    ));
}
```

---

## Room Code System (Like Jackbox)

### Simple 4-Character Codes

```python
import random
import string

def generate_room_code():
    """Generate a 4-character room code like Jackbox"""
    # Avoid confusing characters (0/O, 1/I/L)
    chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    return ''.join(random.choice(chars) for _ in range(4))
```

### Join Flow

```
1. Host visits pinopoly.com/host → Creates room → Gets code "XYZW"
2. Players visit pinopoly.com → Enter "XYZW" → Join as controller
3. TV shows board, phones show personal controls
```

---

## Message Protocol Design

### Standardized Message Format

```python
# All messages follow this structure
message = {
    'type': 'action' | 'update' | 'error' | 'ack',
    'version': 42,           # State version for ordering
    'timestamp': 1234567890,
    'payload': { ... }       # Actual data
}
```

### Action Messages (Phone → Server)

```python
# Player action
{
    'type': 'action',
    'action': 'roll_dice',
    'player_id': 'abc123',
    'payload': {}
}

# Buy property
{
    'type': 'action',
    'action': 'buy_property',
    'player_id': 'abc123',
    'payload': {'property_id': 5}
}
```

### Update Messages (Server → Clients)

```python
# To TV display
{
    'type': 'display_update',
    'version': 43,
    'payload': {
        'event': 'player_moved',
        'player_id': 'abc123',
        'from_position': 5,
        'to_position': 12,
        'dice': [4, 3]
    }
}

# To specific player's phone
{
    'type': 'player_update',
    'version': 43,
    'payload': {
        'your_turn': True,
        'available_actions': ['roll_dice'],
        'your_money': 1500
    }
}
```

---

## Comparison: Current vs Proposed

| Aspect | Current Pinopoly | Jackbox-Style |
|--------|------------------|---------------|
| Client types | All same | Display vs Controller |
| State distribution | Full to everyone | Personalized views |
| State ownership | Server/DB | Server (but cached in memory) |
| Message ordering | None | Version numbers |
| Action confirmation | Fire & forget | Request/Response |
| Phone complexity | Full game board | Simple controls |
| Room codes | 6 chars | 4 chars |
| Reconnection | Fragile | Robust with state recovery |

---

## Quick Wins (Implement First)

### 1. Add Client Type Registration (30 min)
```python
@socketio.on('register_client')
def handle_register(data):
    client_type = data.get('type', 'controller')  # 'display' or 'controller'
    room = data['room_code']

    if client_type == 'display':
        join_room(f'{room}_display')
    else:
        join_room(f'{room}_controllers')
    join_room(room)  # Also join main room
```

### 2. Add State Version (15 min)
```python
# In GameState model
state_version = db.Column(db.Integer, default=0)

# Increment on every change
game_state.state_version += 1
db.session.commit()
```

### 3. Separate Display Updates (1 hr)
```python
def broadcast_updates(game):
    # TV gets animation-friendly update
    emit('display_update', build_display_state(game),
         room=f'{game.game_id}_display')

    # Each player gets personal state
    for player in game.players:
        emit('player_update', build_player_view(game, player),
             room=f'player_{player.id}')
```

---

## Sources

- [Jackbox Games Design Principles (Built In Chicago)](https://www.builtinchicago.org/articles/jackbox-games-design-party-pack)
- [Party-Box Framework (GitHub)](https://github.com/hammre/party-box)
- [Johnbox Private Server Implementation (GitHub)](https://github.com/InvoxiPlayGames/johnbox)
- [Jill Box - React + Python Jackbox Clone (GitHub)](https://github.com/axlan/jill_box)
- [Tarbox Development Blog](https://tarcangul.github.io/blogs/how-do-you-make-jackbox/)
- [Unity Forum - Jackbox Style Game Discussion](https://forum.unity.com/threads/connecting-browser-clients-to-unity-for-a-jackbox-style-game.605320/)

---

## Next Steps

1. **Immediate**: Add client type registration to distinguish TV from phones
2. **This week**: Implement personalized state views
3. **This sprint**: Add state versioning and action acknowledgments
4. **Next sprint**: Build simplified phone controller UI

The fundamental shift is thinking of phones as **input devices** that send actions and receive **personalized** updates, while the TV is a **display** that shows the shared game state. The server becomes a **message broker** rather than the source of all truth for UI state.
