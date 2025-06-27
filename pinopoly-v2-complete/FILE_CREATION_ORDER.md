# File Creation Order for Claude Code

This is the exact order to create files for the Pinopoly V2 project. Each step includes the command to run and expected output.

## Phase 1: Project Structure (5 minutes)

### Step 1: Create main directories
```bash
mkdir -p pinopoly-v2/{backend,frontend,docs,scripts,monitoring,deployment}
cd pinopoly-v2
```

### Step 2: Create backend structure
```bash
mkdir -p backend/src/{domain/{entities,repositories,services,events},application/{use_cases,dto},infrastructure/{database,cache,websockets},presentation/{api/v1,websockets}}
mkdir -p backend/{tests/{unit,integration,e2e},migrations,scripts}
```

### Step 3: Create frontend structure  
```bash
mkdir -p frontend/src/{components/{ui,layout},pages,features/{game,players,properties},hooks,services,store,types,utils}
mkdir -p frontend/{tests,public}
```

## Phase 2: Core Configuration (10 minutes)

### Step 4: Backend requirements
**Create:** `backend/requirements.txt`
**Verify:** `cd backend && pip install -r requirements.txt` should work

### Step 5: Frontend package.json
**Create:** `frontend/package.json` 
**Verify:** `cd frontend && npm install` should work

### Step 6: Environment files
**Create:** `backend/.env` and `frontend/.env`
**Verify:** Both files should exist and contain proper variables

## Phase 3: Backend Implementation (90 minutes)

### Step 7: Database models (15 minutes)
**Order:**
1. `backend/src/infrastructure/database/models/__init__.py`
2. `backend/src/infrastructure/database/models/base.py`
3. `backend/src/infrastructure/database/models/player.py`
4. `backend/src/infrastructure/database/models/property.py`
5. `backend/src/infrastructure/database/models/game.py`

**Verify after each:** `python -c "from src.infrastructure.database.models.X import *"`

### Step 8: Domain entities (20 minutes)
**Order:**
1. `backend/src/domain/entities/__init__.py`
2. `backend/src/domain/entities/value_objects.py`
3. `backend/src/domain/entities/player.py`
4. `backend/src/domain/entities/property.py`
5. `backend/src/domain/entities/game.py`

**Verify after each:** `python -c "from src.domain.entities.X import *"`

### Step 9: Repository interfaces (15 minutes)
**Order:**
1. `backend/src/domain/repositories/__init__.py`
2. `backend/src/domain/repositories/base.py`
3. `backend/src/domain/repositories/player_repository.py`
4. `backend/src/domain/repositories/game_repository.py`

### Step 10: Repository implementations (20 minutes)
**Order:**
1. `backend/src/infrastructure/database/repositories/__init__.py`
2. `backend/src/infrastructure/database/repositories/player_repository.py`
3. `backend/src/infrastructure/database/repositories/game_repository.py`

### Step 11: Use cases (20 minutes)
**Order:**
1. `backend/src/application/use_cases/__init__.py`
2. `backend/src/application/use_cases/create_player.py`
3. `backend/src/application/use_cases/start_game.py`
4. `backend/src/application/use_cases/move_player.py`

## Phase 4: API Layer (30 minutes)

### Step 12: API routes
**Order:**
1. `backend/src/presentation/api/v1/routers/__init__.py`
2. `backend/src/presentation/api/v1/routers/players.py`
3. `backend/src/presentation/api/v1/routers/games.py`

### Step 13: Main app
**Create:** `backend/src/main.py`
**Verify:** `python backend/src/main.py` should start server

## Phase 5: Frontend Implementation (60 minutes)

### Step 14: Basic React setup (15 minutes)
**Order:**
1. `frontend/src/main.tsx`
2. `frontend/src/App.tsx`
3. `frontend/public/index.html`

**Verify:** `cd frontend && npm run dev` should start dev server

### Step 15: Services (15 minutes)
**Order:**
1. `frontend/src/services/api.ts`
2. `frontend/src/services/websocket.ts`

### Step 16: Game components (30 minutes)
**Order:**
1. `frontend/src/features/game/types.ts`
2. `frontend/src/features/game/components/GameBoard.tsx`
3. `frontend/src/features/game/components/PlayerToken.tsx`
4. `frontend/src/pages/GamePage.tsx`

## Phase 6: Testing & Verification (30 minutes)

### Step 17: Backend tests
**Order:**
1. `backend/tests/conftest.py`
2. `backend/tests/unit/test_player.py`
3. `backend/tests/integration/test_api.py`

**Verify:** `cd backend && pytest` should pass

### Step 18: Frontend tests
**Order:**
1. `frontend/src/tests/setup.ts`
2. `frontend/src/tests/GameBoard.test.tsx`

**Verify:** `cd frontend && npm test` should pass

## Phase 7: Docker & Deployment (20 minutes)

### Step 19: Docker files
**Order:**
1. `backend/Dockerfile`
2. `frontend/Dockerfile` 
3. `docker-compose.yml`

**Verify:** `docker-compose up -d` should start all services

## Important Notes for Claude Code

### After creating each file:
1. **Always verify imports work** before moving to next file
2. **Check for syntax errors** with appropriate linter
3. **Test the file loads** in Python/Node environment

### If errors occur:
1. **Check dependencies** are installed
2. **Verify file paths** are correct
3. **Check import statements** match actual file locations

### Common verification commands:
```bash
# Backend verification
cd backend && python -c "import src.main; print('Backend OK')"

# Frontend verification  
cd frontend && npm run type-check

# Full system test
docker-compose up -d && curl http://localhost:8000/health
```

### File creation tips:
- Create `__init__.py` files immediately after creating Python directories
- Install dependencies before creating files that import them
- Use absolute imports in Python files
- Test each major component before moving to the next phase

This order ensures dependencies are available when needed and reduces import errors.