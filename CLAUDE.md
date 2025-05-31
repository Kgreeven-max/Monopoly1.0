# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pinopoly is a modernized Monopoly-like game with Flask backend and React frontend. It features real-time multiplayer gameplay with WebSocket communication, AI bot players, economic simulation, and advanced financial instruments.

## Common Development Commands

### Backend (Python/Flask)
```bash
# Setup backend environment
python scripts/setup_python_backend.py

# Initialize database
python deployment/init_db.py

# Run the main application
python deployment/run_pinopoly.py

# Run tests
python scripts/run_tests.py

# Run test coverage
python scripts/run_coverage.py

# Run specific test
python scripts/run_tests.py -t test_module_name
```

### Frontend (React/Vite)
```bash
# Setup frontend (from client/ directory)
cd client
npm install

# Development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

### Database Management
```bash
# Create migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Reset database (use reset_database.py script)
python reset_database.py
```

## Architecture Overview

### Backend Structure
- **Controllers**: Business logic for game mechanics, bots, finance, etc. (`src/controllers/`)
- **Models**: SQLAlchemy database models (`src/models/`)
- **Routes**: API endpoints organized by domain (`src/routes/`)
- **Game Logic**: Core game mechanics (`src/game_logic/`)
- **Socket Events**: Real-time communication handlers (`src/controllers/socket_*`)

### Key Controllers
- `game_controller.py`: Core game state management
- `bot_controller.py`: AI player management with 6 bot personalities
- `finance_controller.py`: Loans, CDs, HELOC, bankruptcy system
- `socket_core.py`: WebSocket connection management
- `economic_cycle_controller.py`: Economic simulation

### Frontend Structure
- **React Components**: UI components in `client/src/components/`
- **Game Logic**: Client-side game utilities
- **Pages**: Route-based page components
- **Socket Integration**: Real-time communication with backend

### Database Models
- `Player`: Human and bot players with financial data
- `Property`: Board properties with development levels
- `Game`/`GameState`: Game session management
- `Loan`/`CD`: Financial instruments
- `Event`: Economic and special events

## Development Patterns

### Adding New Features
1. Create model in `src/models/` if database changes needed
2. Add controller logic in `src/controllers/`
3. Create API routes in `src/routes/`
4. Add Socket events if real-time updates needed
5. Update frontend components as needed
6. Add tests in `tests/`

### Socket Event Pattern
Real-time events follow this pattern:
```python
@socketio.on('event_name')
def handle_event(data):
    # Process event
    emit('response_event', response_data, broadcast=True)
```

### Bot System
Six bot personalities with different strategies:
- Conservative, Aggressive, Strategic, Opportunistic, Shark, Investor
- Located in `src/models/bots/`
- Managed by `AdaptiveDifficultyController`

### Financial System
Complex financial instruments including:
- Loans with variable interest rates
- Certificates of Deposit (CDs)
- Home Equity Line of Credit (HELOC)
- Bankruptcy system
- Community Fund

## Key Configuration

### Environment Variables
Required in `.env` file:
- `SECRET_KEY`: Flask secret key
- `ADMIN_KEY`: Admin authentication
- `DATABASE_URI`: Database connection string
- `ADAPTIVE_DIFFICULTY_ENABLED`: Enable bot difficulty adjustment
- `POLICE_PATROL_ENABLED`: Enable crime system patrols

### Game Features
- Economic cycles affecting property values and rent
- Crime system with 5 crime types and detection mechanics
- Property development with 5 levels
- Auction system for property sales
- Special spaces (Chance, Community Chest, Tax, etc.)
- Remote multiplayer support via Cloudflare Tunnel

## Testing

### Backend Tests
- Unit tests in `tests/` directory
- Integration tests for game flows
- API endpoint tests
- Run with `python scripts/run_tests.py`

### Frontend Tests
- Linting with ESLint: `npm run lint`
- Located in `client/` directory

## Important Notes

### Socket Communication
The game heavily relies on WebSocket communication for real-time updates. Socket events are handled in:
- `src/controllers/socket_controller.py`: Main socket event registration
- `src/controllers/socket_core.py`: Core connection management
- Individual controller files for domain-specific events

### Game State Management
Game state is managed through:
- `GameState` model for persistent state
- `GameController` for game logic
- Socket events for real-time synchronization

### Bot AI System
AI bots use sophisticated decision-making algorithms:
- Different strategies for property valuation
- Auction bidding behaviors
- Financial instrument usage
- Adaptive difficulty based on human player performance

### Database Migrations
Always create migrations for schema changes:
1. Make model changes
2. Run `flask db migrate -m "Description"`
3. Review generated migration
4. Apply with `flask db upgrade`