# Debugging Guide for Pinopoly V2

This guide provides systematic debugging approaches for common issues in the Pinopoly V2 project.

## General Debugging Strategy

### 1. Reproduce the Issue
- [ ] Can you consistently reproduce the problem?
- [ ] What are the exact steps to reproduce?
- [ ] What environment are you using (dev/staging/production)?
- [ ] Are there any error messages in logs?

### 2. Gather Information
- [ ] Check application logs
- [ ] Check browser console (for frontend issues)
- [ ] Check network requests in browser DevTools
- [ ] Check database state
- [ ] Check system resources (CPU, memory, disk)

### 3. Isolate the Problem
- [ ] Is it frontend or backend related?
- [ ] Does it happen in all browsers/devices?
- [ ] Is it specific to certain users or data?
- [ ] Does it happen in different environments?

## Backend Debugging (Python/Flask)

### Application Not Starting

**Symptoms:** Server won't start or crashes immediately

**Debug Steps:**
```bash
# 1. Check Python environment
cd backend
source venv/bin/activate
python --version

# 2. Check dependencies
pip list
pip install -r requirements-dev.txt

# 3. Check syntax errors
python -m py_compile src/main.py

# 4. Check imports
python -c "from src.main import create_app; print('Imports OK')"

# 5. Start with verbose logging
FLASK_ENV=development python src/main.py
```

**Common Issues:**
- Missing dependencies: `pip install -r requirements-dev.txt`
- Wrong Python version: Use Python 3.11+
- Missing environment variables: Check `.env` file
- Port already in use: Change port or kill process on port 8000

### Database Connection Issues

**Symptoms:** Database connection errors, SQLAlchemy exceptions

**Debug Steps:**
```bash
# 1. Test database connection
python -c "
from src.infrastructure.database.session import engine
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('Database connection OK')
except Exception as e:
    print(f'Database error: {e}')
"

# 2. Check database exists
sqlite3 instance/monopoly.db ".tables"

# 3. Check migrations
cd backend
alembic current
alembic history

# 4. Reset database if needed
rm instance/monopoly.db
alembic upgrade head
```

### API Endpoint Debugging

**Symptoms:** 404, 500 errors, unexpected responses

**Debug Steps:**
```bash
# 1. Check route registration
python -c "
from src.main import create_app
app = create_app()
for rule in app.url_map.iter_rules():
    print(f'{rule.rule} -> {rule.endpoint}')
"

# 2. Test endpoint directly
curl -X POST http://localhost:8000/api/v1/players \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Player"}'

# 3. Check logs with debug info
tail -f logs/app.log

# 4. Add debug prints
# In your route handler:
print(f"Request data: {request.json}")
print(f"Processing player creation...")
```

**Add logging to route handlers:**
```python
import logging
logger = logging.getLogger(__name__)

@router.route('/players', methods=['POST'])
def create_player():
    logger.info(f"Create player request: {request.json}")
    try:
        # ... logic ...
        logger.info(f"Player created successfully: {player.id}")
        return jsonify(player.dict()), 201
    except Exception as e:
        logger.error(f"Error creating player: {e}", exc_info=True)
        raise
```

### WebSocket Connection Issues

**Symptoms:** Real-time updates not working, connection errors

**Debug Steps:**
```bash
# 1. Test WebSocket connection
npm install -g wscat
wscat -c ws://localhost:8000

# 2. Check Socket.IO events
# Add to backend websocket handler:
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connection_confirmed', {'status': 'connected'})
```

**Frontend WebSocket debugging:**
```javascript
// Add to frontend WebSocket code
socket.on('connect', () => {
  console.log('WebSocket connected:', socket.id);
});

socket.on('disconnect', (reason) => {
  console.log('WebSocket disconnected:', reason);
});

socket.on('connect_error', (error) => {
  console.error('WebSocket connection error:', error);
});
```

## Frontend Debugging (React/TypeScript)

### Component Not Rendering

**Symptoms:** Blank page, component not visible, console errors

**Debug Steps:**
```bash
# 1. Check for TypeScript errors
cd frontend
npm run type-check

# 2. Check for build errors
npm run build

# 3. Check browser console
# Open DevTools -> Console tab
```

**Add debug logging to components:**
```typescript
const GameBoard: React.FC<GameBoardProps> = ({ gameState }) => {
  console.log('GameBoard render:', { gameState });
  
  useEffect(() => {
    console.log('GameBoard mounted');
    return () => console.log('GameBoard unmounted');
  }, []);
  
  if (!gameState) {
    console.warn('GameBoard: gameState is null');
    return <div>Loading game state...</div>;
  }
  
  return (
    <div className="game-board">
      {/* component content */}
    </div>
  );
};
```

### State Management Issues

**Symptoms:** State not updating, incorrect state values

**Debug Steps:**
```typescript
// 1. Add state logging
const [gameState, setGameState] = useState<GameState | null>(null);

useEffect(() => {
  console.log('Game state changed:', gameState);
}, [gameState]);

// 2. Check state updates
const updateGameState = (newState: GameState) => {
  console.log('Updating game state:', { old: gameState, new: newState });
  setGameState(newState);
};

// 3. Use React DevTools
// Install React Developer Tools browser extension
// Inspect component state and props
```

### API Call Issues

**Symptoms:** Network errors, wrong data, loading states

**Debug Steps:**
```typescript
// Add comprehensive API debugging
const fetchGameState = async (gameId: string) => {
  console.log('Fetching game state for:', gameId);
  
  try {
    const response = await fetch(`/api/v1/games/${gameId}`);
    console.log('API response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('API error response:', errorText);
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    const data = await response.json();
    console.log('API response data:', data);
    return data;
    
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
};
```

## Integration Debugging

### Backend-Frontend Communication

**Debug API calls from frontend:**
```bash
# 1. Check network requests in browser
# DevTools -> Network tab -> XHR/Fetch

# 2. Test API endpoints directly
curl -X GET http://localhost:8000/api/v1/games/game-123

# 3. Check CORS settings
# In browser console:
fetch('http://localhost:8000/api/v1/health')
  .then(r => r.text())
  .then(console.log)
  .catch(console.error)
```

**Add request/response logging:**
```python
# Backend middleware for request logging
@app.before_request
def log_request():
    print(f"Request: {request.method} {request.url}")
    if request.is_json:
        print(f"Body: {request.json}")

@app.after_request
def log_response(response):
    print(f"Response: {response.status_code}")
    return response
```

### Database State Debugging

**Check database contents:**
```bash
# SQLite
sqlite3 instance/monopoly.db
.mode column
.headers on
SELECT * FROM players;
SELECT * FROM games;

# Or use Python
python -c "
from src.infrastructure.database.session import engine
import pandas as pd
df = pd.read_sql('SELECT * FROM players', engine)
print(df)
"
```

## Performance Debugging

### Slow API Responses

**Profile backend performance:**
```python
import time
import functools

def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper

# Use on slow functions
@timing_decorator
def slow_function():
    # ... function code ...
```

**Profile database queries:**
```python
# Add to SQLAlchemy configuration
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Log all SQL queries
    pool_pre_ping=True
)
```

### Memory Leaks

**Monitor memory usage:**
```bash
# Backend memory monitoring
pip install memory-profiler
python -m memory_profiler src/main.py

# Frontend memory monitoring
# Use browser DevTools -> Memory tab
```

## Docker Debugging

### Container Issues

**Debug Docker containers:**
```bash
# 1. Check container status
docker-compose ps

# 2. View container logs
docker-compose logs backend
docker-compose logs frontend

# 3. Execute commands in container
docker-compose exec backend bash
docker-compose exec frontend sh

# 4. Check container resources
docker stats

# 5. Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Network Issues

**Debug container networking:**
```bash
# 1. Check Docker networks
docker network ls
docker network inspect pinopoly_default

# 2. Test connectivity between containers
docker-compose exec frontend ping backend
docker-compose exec backend ping database

# 3. Check port mappings
docker port pinopoly_backend_1
```

## Production Debugging

### Log Analysis

**Structured logging setup:**
```python
import structlog
import logging

# Configure structured logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

logger = structlog.get_logger()

# Use in code
logger.info("Player created", player_id=player.id, game_id=game.id)
logger.error("Database error", error=str(e), query=query)
```

**Log aggregation for Docker:**
```yaml
# docker-compose.yml
services:
  backend:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

### Health Checks

**Add health check endpoints:**
```python
@app.route('/health')
def health_check():
    try:
        # Check database
        engine.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {e}'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'database': db_status,
            'redis': check_redis_health(),
        }
    })
```

## Debugging Tools and Commands

### Essential Commands
```bash
# Backend debugging
cd backend && python -c "from src.main import create_app; app = create_app(); print('App created successfully')"
cd backend && python -m pytest tests/ -v --tb=short
cd backend && python -m pytest tests/integration/ -v -s

# Frontend debugging
cd frontend && npm run type-check
cd frontend && npm run lint
cd frontend && npm run build

# Full system debugging
docker-compose logs -f
docker-compose exec backend python -c "print('Backend container OK')"
curl http://localhost:8000/health
curl http://localhost:3000
```

### Browser DevTools Tips
1. **Console**: Check for JavaScript errors and log messages
2. **Network**: Monitor API calls and response times
3. **Application**: Check localStorage, sessionStorage, cookies
4. **Performance**: Profile React component rendering
5. **Memory**: Check for memory leaks

### VS Code Debugging
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Flask",
            "type": "python",
            "request": "launch",
            "program": "backend/src/main.py",
            "env": {
                "FLASK_ENV": "development"
            },
            "console": "integratedTerminal"
        }
    ]
}
```

Remember: Always reproduce the issue first, then systematically narrow down the problem using logs, debugging tools, and incremental testing.