# Pinopoly

A modernized Monopoly-like game implemented with a Python/Flask backend and React frontend.

## Project Structure

This project follows a domain-oriented organization, grouping files by their functional purpose:

```
pinopoly/
├── frontend/                      # React frontend application
│   ├── src/
│       ├── pages/                 # Top-level game views
│       ├── game-board/            # Board UI & interaction
│       ├── game-logic/            # Game mechanics
│       ├── game-state/            # State management
│       └── components/            # Shared components
│
├── backend/                       # Flask backend
│   ├── api/                       # API endpoints & socket handlers
│   ├── game_engine/               # Core game logic
│   ├── models/                    # Database models
│   └── controllers/               # Business logic
│
├── shared/                        # Shared resources
├── scripts/                       # Utility scripts
├── docs/                          # Documentation
└── tests/                         # Tests
```

## Functional Areas

### Game Board (🟦)

Files related to rendering and interacting with the game board itself:
- Board layout/rendering
- Player tokens and movement
- Property and special space visualization

### Game Logic (🟨)

Implements the rules and mechanics of the game:
- Turn management
- Dice rolling
- Financial mechanics (loans, bankruptcy, market fluctuations)
- Property development and mortgaging
- Trading and auctions
- Special events

### Game State (🔴)

Manages persistent game data and state synchronization:
- Game contexts and reducers
- Socket communication
- API services
- Database models and migrations

## Getting Started

1. Setup the backend:
   ```
   cd backend
   pip install -r requirements.txt
   python init_db.py
   ```

2. Setup the frontend:
   ```
   cd frontend
   npm install
   ```

3. Run the application:
   ```
   # Terminal 1: Backend
   cd backend
   python app.py
   
   # Terminal 2: Frontend
   cd frontend
   npm run dev
   ```

## Development

### Frontend (React)

The frontend is built with React and follows a domain-oriented structure:
- Each game domain has its own directory
- Components are grouped by purpose, not just by type
- Styles live with their components

### Backend (Flask)

The backend uses Flask and is organized by domains:
- API routes handle HTTP endpoints
- Socket handlers manage real-time communication
- Game engine contains the core game logic
- Controllers manage the application logic

## Documentation

See the `docs/` directory for detailed documentation about different aspects of the project.

## Testing

Run the tests:
```
# Backend tests
cd tests/backend
pytest

# Frontend tests
cd frontend
npm test
```

## License

See the LICENSE file for details. 