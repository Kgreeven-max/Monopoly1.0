# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with the Pinopoly codebase.

## Project Overview

Pinopoly is a modernized Monopoly-like game built with:
- **Backend**: Python/Flask with SQLAlchemy ORM, WebSocket support via Flask-SocketIO
- **Frontend**: React with Vite bundler (dual frontend architecture)
- **Database**: SQLite for development, configurable for production
- **Real-time**: WebSocket communication for multiplayer gameplay
- **Features**: AI bot players, economic simulation, financial instruments, crime system

## Common Development Commands

### Backend Setup & Running
```bash
# Initial setup
python scripts/setup_python_backend.py
python deployment/init_db.py

# Run the application (main entry point)
python app.py
# Or use the deployment script
python deployment/run_pinopoly.py

# Testing
python scripts/run_tests.py
python scripts/run_coverage.py
python scripts/run_tests.py -t specific_test

# Database management
flask db migrate -m "Description"
flask db upgrade
python reset_database.py  # Full reset
```

### Frontend Development
```bash
# Main frontend (production)
cd client
npm install
npm run dev      # Development server on port 3001
npm run build    # Production build
npm run lint     # Code linting

# Enhanced frontend (experimental)
cd board_organized
npm install
npm run dev      # Development server
npm run build    # Production build
```

## Architecture Overview

### Application Entry Point
- **Single app.py**: The main application entry point is `/app.py` at the root level
- Previous duplicate `src/app.py` has been renamed to `src/app_old.py` to avoid conflicts
- All initialization, configuration, and route registration happens in the main `app.py`

### Backend Structure (`/src/`)
```
src/
├── controllers/          # Business logic controllers
│   ├── game_controller.py         # Core game mechanics
│   ├── bot_controller.py          # AI player management
│   ├── finance_controller.py      # Financial instruments
│   ├── socket_controller.py       # Socket event registration
│   ├── socket_core.py            # WebSocket connection management
│   ├── socket_game_controller.py # Unified game state emissions
│   └── economic_cycle_controller.py # Economic simulation
├── models/              # SQLAlchemy database models
│   ├── player.py               # Player model (human & bot)
│   ├── property.py             # Board properties
│   ├── game_state.py           # Game session state
│   └── bots/                   # Bot personality implementations
├── routes/              # REST API endpoints
├── game_logic/          # Core game mechanics
└── utils/               # Utility functions
```

### Frontend Architecture (Dual System)

#### 1. Main Frontend (`/client/`)
- Production-ready React application
- Standard game board implementation
- Stable feature set

#### 2. Enhanced Frontend (`/board_organized/`)
- Experimental version with advanced animations
- GSAP integration for smooth transitions
- Enhanced UX with animation hooks
- Features:
  - `AnimationContext.jsx` - Global animation state
  - `AnimatedGameContext.jsx` - Animation-aware game context
  - Custom hooks: `usePlayerAnimation.js`, `useSimplePlayerAnimation.js`
  - Enhanced board components with visual effects

### Database Schema
- **GameState**: Singleton game state management
- **Player**: Human and bot players with financial data
- **Property**: Board spaces with ownership and development
- **Loan/CD/HELOC**: Financial instruments
- **Transaction**: Financial transaction history
- **Event**: Economic and special events

## Key Technical Patterns

### WebSocket Communication
The game uses Socket.IO for real-time updates:

```python
# Backend event handler pattern
@socketio.on('event_name')
def handle_event(data):
    # Process event
    emit('response_event', response_data, room=room_id)
```

```javascript
// Frontend socket pattern
socket.on('game_state', (state) => {
    setGameState(state);
});
socket.emit('action', { playerId, data });
```

### Game State Management

#### Backend Pattern
- Single source of truth: `GameState` model
- Unified state emission: `socket_game_controller.build_complete_game_state()`
- All actions emit complete state after changes

#### Frontend Pattern
- Single state object in React
- Socket events update entire state
- No partial state updates

### Bot AI System
Six bot personalities with distinct strategies:
- **Conservative**: Safe property investments
- **Aggressive**: High-risk, high-reward
- **Strategic**: Monopoly-focused
- **Opportunistic**: Auction specialist
- **Shark**: Predatory financial tactics
- **Investor**: Long-term wealth building

### Animation System (board_organized)
- **BoardPositionCache**: Pre-calculates all board positions
- **Player movement**: Smooth transitions with bounce effects
- **Token stacking**: Multiple players on same space
- **Performance**: Uses CSS transforms, not DOM manipulation

## Critical Implementation Notes

### Player Movement Animation
When implementing player movement:
1. Use pre-calculated positions (BoardPositionCache)
2. Animate with CSS transforms for performance
3. Queue movements to prevent overlapping animations
4. Show dice roll before movement
5. Bounce through each space, don't teleport

### Socket Event Flow
1. Frontend sends action (e.g., 'roll_dice')
2. Backend processes action in controller
3. Backend emits complete 'game_state'
4. Frontend updates entire state from emission
5. Animations triggered by state changes

### Common Pitfalls to Avoid
- **Don't** query DOM for positions during animations
- **Don't** use partial state updates
- **Don't** create new socket events without updating both ends
- **Don't** modify game state outside of controllers
- **Don't** use synchronous database queries in socket handlers

### Testing Approach
1. Backend: Unit tests for controllers and models
2. API: Integration tests for game flows
3. Frontend: ESLint for code quality
4. Socket: Use test scripts (test_board.py, test_bot_move.py)

## Environment Configuration

### Required .env Variables
```
SECRET_KEY=your-secret-key
ADMIN_KEY=admin-authentication-key
DATABASE_URI=sqlite:///instance/monopoly.db
ADAPTIVE_DIFFICULTY_ENABLED=true
POLICE_PATROL_ENABLED=true
```

### Feature Flags
- `ADAPTIVE_DIFFICULTY_ENABLED`: Bot difficulty adjustment
- `POLICE_PATROL_ENABLED`: Crime detection system
- `PROPERTY_VALUES_FOLLOW_ECONOMY`: Dynamic property values
- `COMMUNITY_FUND_ENABLED`: Community fund feature

## Current Known Issues

### Player Token Display
The Player model needs a 'token' attribute for board display:
```python
# In socket_game_controller.py line 61
'token': getattr(player, 'token', None) or 'car',
```

### Animation Synchronization
Ensure dice roll completes before movement animation starts.

## Development Workflow

### Adding New Features
1. Create/modify models in `src/models/`
2. Add controller logic in `src/controllers/`
3. Create API routes in `src/routes/`
4. Add Socket.IO events if real-time needed
5. Update frontend to handle new events
6. Write tests in `tests/`
7. Update this documentation

### Debugging Tools
- Backend logs: Check console output
- Frontend: React Developer Tools
- Socket: Socket.IO client debug mode
- Database: SQLite browser for direct inspection

## Quick Reference

### Key Files for Common Tasks
- **Game flow**: `src/controllers/game_controller.py`
- **Player actions**: `src/controllers/socket_controller.py`
- **Board display**: `client/src/pages/BoardPage.jsx`
- **Animations**: `board_organized/hooks/usePlayerAnimation.js`
- **Game state**: `src/models/game_state.py`
- **Socket events**: `src/controllers/socket_game_controller.py`

### Testing Game Features
```bash
# Create test game with bots
python test_board.py

# Trigger bot movement
python test_bot_move.py

# Watch server logs for debugging
python deployment/run_pinopoly.py
```

## Architecture Decisions

### Why Dual Frontend?
- `client/`: Stable, production-ready features
- `board_organized/`: Experimental animations and UX improvements
- Allows testing new features without breaking production

### Why Single Game State?
- Eliminates state synchronization bugs
- Simplifies debugging
- Clear source of truth
- Better performance with complete updates

### Why Pre-calculated Positions?
- Eliminates DOM queries during animation
- Consistent positioning across renders
- Better performance
- Easier testing

---

*Last updated: Based on recent refactoring for animation system and WebSocket architecture*