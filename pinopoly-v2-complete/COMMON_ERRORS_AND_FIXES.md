# Common Errors and Fixes

This document contains common errors you might encounter when implementing Pinopoly V2 and their solutions.

## Backend Errors (Python/Flask)

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'src'`
**Cause:** Python can't find the src directory
**Fix:** 
```bash
cd backend
export PYTHONPATH=$PYTHONPATH:$(pwd)
# OR add to .env: PYTHONPATH=/app/src
```

**Error:** `ImportError: cannot import name 'Player' from 'src.domain.entities.player'`
**Cause:** Circular imports or missing __init__.py
**Fix:**
1. Check `__init__.py` exists in each directory
2. Check for circular imports between files
3. Use `from .player import Player` for relative imports

### Database Errors

**Error:** `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: players`
**Cause:** Database tables not created
**Fix:**
```bash
cd backend
python -c "from src.infrastructure.database.session import engine, Base; Base.metadata.create_all(engine)"
```

**Error:** `AttributeError: 'NoneType' object has no attribute 'id'`
**Cause:** Database query returning None
**Fix:** Add null checks:
```python
player = session.query(Player).filter_by(id=player_id).first()
if not player:
    raise ValueError(f"Player {player_id} not found")
```

### Flask Errors

**Error:** `RuntimeError: Working outside of application context`
**Cause:** Trying to use Flask features outside app context
**Fix:** Wrap in app context:
```python
with app.app_context():
    # database operations here
```

**Error:** `AssertionError: View function mapping is overwriting an existing endpoint function`
**Cause:** Duplicate route definitions
**Fix:** Check for duplicate `@app.route()` decorators with same path

### Socket.IO Errors

**Error:** `AttributeError: 'SocketIO' object has no attribute 'emit'`
**Cause:** SocketIO not properly initialized
**Fix:** Ensure socketio is created correctly:
```python
from flask_socketio import SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")
```

## Frontend Errors (React/TypeScript)

### TypeScript Errors

**Error:** `Cannot find module '@/components/GameBoard' or its corresponding type declarations`
**Cause:** Path mapping not configured
**Fix:** Check `tsconfig.json` has correct path mapping:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Error:** `Property 'gameState' does not exist on type '{}' `
**Cause:** Component props not typed
**Fix:** Define interface for props:
```typescript
interface GameBoardProps {
  gameState: GameState;
}
const GameBoard: React.FC<GameBoardProps> = ({ gameState }) => {
  // component code
};
```

### React Errors

**Error:** `React Hook "useState" is called conditionally`
**Cause:** Hooks called inside if statements or loops
**Fix:** Always call hooks at top level:
```typescript
// Wrong
if (condition) {
  const [state, setState] = useState();
}

// Correct
const [state, setState] = useState();
if (condition) {
  // use state here
}
```

**Error:** `Objects are not valid as a React child`  
**Cause:** Trying to render object directly
**Fix:** Convert to string or extract properties:
```typescript
// Wrong
<div>{player}</div>

// Correct
<div>{player.name}</div>
```

### WebSocket Connection Errors

**Error:** `WebSocket connection failed`
**Cause:** Backend not running or wrong URL
**Fix:** 
1. Verify backend is running on port 8000
2. Check WebSocket URL: `ws://localhost:8000`
3. Check CORS settings in backend

**Error:** `Cannot read property 'emit' of null`
**Cause:** Socket not connected yet
**Fix:** Add connection check:
```typescript
if (socket && socket.connected) {
  socket.emit('event', data);
}
```

## Docker Errors

**Error:** `ERROR: Couldn't connect to Docker daemon`
**Cause:** Docker not running
**Fix:** Start Docker Desktop or Docker service

**Error:** `ERROR: for backend  Cannot start service backend: Ports are not available`
**Cause:** Port 8000 already in use
**Fix:** 
```bash
# Find process using port
lsof -i :8000
# Kill process or change port in docker-compose.yml
```

**Error:** `ERROR: Service 'backend' failed to build`
**Cause:** Build context issues or missing files
**Fix:** 
1. Check Dockerfile exists in backend directory
2. Verify all COPY paths are correct
3. Check `.dockerignore` isn't excluding needed files

## Development Environment Errors

### Python Virtual Environment

**Error:** `bash: pip: command not found`
**Cause:** Virtual environment not activated
**Fix:**
```bash
cd backend
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows
```

**Error:** `ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied`
**Cause:** Installing packages globally without sudo
**Fix:** Use virtual environment or --user flag:
```bash
pip install --user package_name
```

### Node.js Errors

**Error:** `npm ERR! Cannot resolve dependency`
**Cause:** Package version conflicts
**Fix:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Error:** `Error: Cannot find module`
**Cause:** Package not installed or wrong import path
**Fix:**
1. Verify package in package.json
2. Run `npm install`
3. Check import path is correct

## Testing Errors

### Backend Testing

**Error:** `ImportError: No module named 'tests'`
**Cause:** Tests directory not a Python package
**Fix:** Add `__init__.py` to tests directory

**Error:** `fixture 'client' not found`
**Cause:** Missing test fixtures
**Fix:** Create `conftest.py` with fixtures:
```python
import pytest
from src.main import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
```

### Frontend Testing

**Error:** `TypeError: Cannot read property 'prototype' of undefined`
**Cause:** Missing test setup
**Fix:** Create `src/tests/setup.ts`:
```typescript
import '@testing-library/jest-dom';
```

## Database Migration Errors

**Error:** `alembic.util.exc.CommandError: Can't locate revision identified by`
**Cause:** Migration history mismatch
**Fix:**
```bash
cd backend
alembic stamp head
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Performance Issues

### Slow Database Queries
**Symptoms:** API responses > 1 second
**Fix:** Add database indexes:
```python
class Player(Base):
    __tablename__ = 'players'
    id = Column(String, primary_key=True, index=True)
    game_id = Column(String, ForeignKey('games.id'), index=True)
```

### Memory Leaks in React
**Symptoms:** Browser memory usage increasing over time
**Fix:** Cleanup useEffect hooks:
```typescript
useEffect(() => {
  const interval = setInterval(updateGameState, 1000);
  return () => clearInterval(interval); // Cleanup
}, []);
```

## Debugging Commands

### Backend Debugging
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Test database connection
python -c "from src.infrastructure.database.session import engine; print(engine.execute('SELECT 1').scalar())"

# Check Flask routes
python -c "from src.main import create_app; app = create_app(); print(app.url_map)"
```

### Frontend Debugging
```bash
# Check TypeScript compilation
npx tsc --noEmit

# Check for unused dependencies
npx depcheck

# Bundle analysis
npm run build && npx serve -s build
```

### Full System Health Check
```bash
# Backend health
curl http://localhost:8000/health

# Frontend health  
curl http://localhost:3000

# WebSocket connection
wscat -c ws://localhost:8000
```

## Quick Fixes Checklist

When something doesn't work, try these in order:

### Backend Issues
1. [ ] Is virtual environment activated?
2. [ ] Are all dependencies installed? (`pip install -r requirements-dev.txt`)
3. [ ] Is PYTHONPATH set correctly?
4. [ ] Do all `__init__.py` files exist?
5. [ ] Is database initialized? 
6. [ ] Are there circular imports?

### Frontend Issues  
1. [ ] Are dependencies installed? (`npm install`)
2. [ ] Is TypeScript configuration correct?
3. [ ] Are path mappings working?
4. [ ] Is the backend API running?
5. [ ] Are WebSocket connections established?

### Docker Issues
1. [ ] Is Docker running?
2. [ ] Are ports available?
3. [ ] Do Dockerfiles exist?
4. [ ] Are file paths correct in COPY commands?
5. [ ] Is docker-compose.yml valid YAML?

This troubleshooting guide should help resolve 90% of common development issues.