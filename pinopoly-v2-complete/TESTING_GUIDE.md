# Testing Guide for Pinopoly V2

This guide provides comprehensive testing instructions for all components of the Pinopoly V2 project.

## Testing Philosophy

- **Test-Driven Development (TDD)**: Write tests before implementation
- **Testing Pyramid**: Unit tests (70%) > Integration tests (20%) > E2E tests (10%)
- **Fast Feedback**: Tests should run quickly and provide clear error messages
- **Isolated Tests**: Each test should be independent and not rely on external state

## Backend Testing (Python/pytest)

### Setup and Configuration

**Install test dependencies:**
```bash
cd backend
pip install -r requirements-dev.txt
```

**Test configuration** (`pytest.ini`):
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

### Unit Tests

**Test Domain Entities** (`tests/unit/domain/test_player.py`):
```python
import pytest
from src.domain.entities.player import Player
from src.domain.entities.value_objects import PlayerId, Money, Position

class TestPlayer:
    def test_create_player(self):
        player = Player(
            id=PlayerId("player-1"),
            name="Alice",
            money=Money(1500)
        )
        assert player.name == "Alice"
        assert player.money.amount == 1500
        assert player.position.value == 0

    def test_player_movement(self):
        player = Player(PlayerId("player-1"), "Alice", Money(1500))
        result = player.move(7)
        
        assert player.position.value == 7
        assert result.new_position.value == 7
        assert not result.passed_go

    def test_player_passes_go(self):
        player = Player(PlayerId("player-1"), "Alice", Money(1500))
        player.position = Position(35)  # Near GO
        
        result = player.move(7)  # Should pass GO
        
        assert player.position.value == 2  # (35 + 7) % 40
        assert result.passed_go
        assert player.money.amount == 1700  # +200 for passing GO

    def test_player_buy_property(self):
        player = Player(PlayerId("player-1"), "Alice", Money(1500))
        property_price = Money(200)
        
        can_buy = player.can_afford(property_price)
        assert can_buy
        
        player.spend_money(property_price)
        assert player.money.amount == 1300
```

**Run unit tests:**
```bash
cd backend
pytest tests/unit/ -v
pytest tests/unit/domain/test_player.py::TestPlayer::test_player_movement -v
```

**Test Use Cases** (`tests/unit/application/test_move_player_use_case.py`):
```python
import pytest
from unittest.mock import Mock
from src.application.use_cases.move_player import MovePlayerUseCase
from src.domain.entities.player import Player
from src.domain.entities.value_objects import PlayerId, Money

class TestMovePlayerUseCase:
    def setup_method(self):
        self.player_repo = Mock()
        self.game_repo = Mock()
        self.use_case = MovePlayerUseCase(self.player_repo, self.game_repo)

    def test_move_player_success(self):
        # Arrange
        player = Player(PlayerId("player-1"), "Alice", Money(1500))
        self.player_repo.get_by_id.return_value = player
        
        # Act
        result = self.use_case.execute("player-1", 7)
        
        # Assert
        assert result.success
        assert result.new_position == 7
        self.player_repo.save.assert_called_once_with(player)

    def test_move_player_not_found(self):
        # Arrange
        self.player_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Player player-1 not found"):
            self.use_case.execute("player-1", 7)
```

### Integration Tests

**Test API Endpoints** (`tests/integration/test_player_api.py`):
```python
import pytest
import json
from src.main import create_app
from src.infrastructure.database.session import engine, Base

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['DATABASE_URL'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            Base.metadata.create_all(engine)
            yield client
            Base.metadata.drop_all(engine)

class TestPlayerAPI:
    def test_create_player(self, client):
        response = client.post('/api/v1/players', 
            json={'name': 'Alice'},
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Alice'
        assert 'id' in data

    def test_move_player(self, client):
        # First create a player
        response = client.post('/api/v1/players', json={'name': 'Alice'})
        player_data = json.loads(response.data)
        player_id = player_data['id']
        
        # Then move the player
        response = client.post(f'/api/v1/players/{player_id}/move',
            json={'spaces': 7}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['new_position'] == 7

    def test_get_player(self, client):
        # Create player
        response = client.post('/api/v1/players', json={'name': 'Alice'})
        player_data = json.loads(response.data)
        player_id = player_data['id']
        
        # Get player
        response = client.get(f'/api/v1/players/{player_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Alice'
```

**Run integration tests:**
```bash
cd backend
pytest tests/integration/ -v
```

### Database Tests

**Test Repository Implementation** (`tests/integration/test_player_repository.py`):
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.database.models.base import Base
from src.infrastructure.database.repositories.player_repository import SQLAlchemyPlayerRepository
from src.domain.entities.player import Player
from src.domain.entities.value_objects import PlayerId, Money

@pytest.fixture
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

class TestPlayerRepository:
    def test_save_and_get_player(self, db_session):
        repo = SQLAlchemyPlayerRepository(db_session)
        player = Player(PlayerId("player-1"), "Alice", Money(1500))
        
        # Save player
        repo.save(player)
        
        # Get player
        retrieved_player = repo.get_by_id(PlayerId("player-1"))
        
        assert retrieved_player.name == "Alice"
        assert retrieved_player.money.amount == 1500
```

## Frontend Testing (React/Vitest)

### Setup and Configuration

**Install test dependencies:**
```bash
cd frontend
npm install
```

**Test configuration** (`vitest.config.ts`):
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/tests/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

**Test setup** (`src/tests/setup.ts`):
```typescript
import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock WebSocket
global.WebSocket = vi.fn(() => ({
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  send: vi.fn(),
  close: vi.fn(),
}))

// Mock fetch
global.fetch = vi.fn()
```

### Component Tests

**Test GameBoard Component** (`src/tests/components/GameBoard.test.tsx`):
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { GameBoard } from '@/features/game/components/GameBoard'
import { GameState } from '@/types/game'

const mockGameState: GameState = {
  id: 'game-1',
  players: [
    { id: 'player-1', name: 'Alice', position: 0, money: 1500 },
    { id: 'player-2', name: 'Bob', position: 5, money: 1500 }
  ],
  currentPlayerIndex: 0,
  board: {
    spaces: Array.from({ length: 40 }, (_, i) => ({
      id: i,
      name: `Space ${i}`,
      type: i === 0 ? 'GO' : 'PROPERTY'
    }))
  }
}

describe('GameBoard', () => {
  it('renders game board with correct spaces', () => {
    const onPlayerAction = vi.fn()
    
    render(
      <GameBoard 
        gameState={mockGameState}
        currentPlayerId="player-1"
        onPlayerAction={onPlayerAction}
      />
    )
    
    expect(screen.getByText('GO')).toBeInTheDocument()
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
  })

  it('calls onPlayerAction when roll dice button is clicked', () => {
    const onPlayerAction = vi.fn()
    
    render(
      <GameBoard 
        gameState={mockGameState}
        currentPlayerId="player-1"
        onPlayerAction={onPlayerAction}
      />
    )
    
    fireEvent.click(screen.getByText('Roll Dice'))
    
    expect(onPlayerAction).toHaveBeenCalledWith({ type: 'ROLL_DICE' })
  })

  it('displays current player indicator', () => {
    const onPlayerAction = vi.fn()
    
    render(
      <GameBoard 
        gameState={mockGameState}
        currentPlayerId="player-1"
        onPlayerAction={onPlayerAction}
      />
    )
    
    expect(screen.getByText('Current Player: Alice')).toBeInTheDocument()
  })
})
```

**Test Custom Hooks** (`src/tests/hooks/useGameSocket.test.tsx`):
```typescript
import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useGameSocket } from '@/hooks/useGameSocket'

// Mock socket.io-client
vi.mock('socket.io-client', () => ({
  io: vi.fn(() => ({
    on: vi.fn(),
    off: vi.fn(),
    emit: vi.fn(),
    close: vi.fn(),
    connected: true
  }))
}))

describe('useGameSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('establishes socket connection', () => {
    const { result } = renderHook(() => useGameSocket('game-1'))
    
    expect(result.current.connected).toBe(true)
  })

  it('emits player move event', () => {
    const { result } = renderHook(() => useGameSocket('game-1'))
    
    act(() => {
      result.current.movePlayer('player-1', 7)
    })
    
    expect(result.current.socket?.emit).toHaveBeenCalledWith('player_move', {
      playerId: 'player-1',
      spaces: 7
    })
  })
})
```

**Run frontend tests:**
```bash
cd frontend
npm test
npm run test:coverage
```

### E2E Tests (Playwright)

**Setup Playwright:**
```bash
cd frontend
npm install @playwright/test
npx playwright install
```

**E2E Test Configuration** (`playwright.config.ts`):
```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

**E2E Game Flow Test** (`tests/e2e/game-flow.spec.ts`):
```typescript
import { test, expect } from '@playwright/test'

test.describe('Game Flow', () => {
  test('complete game setup and first turn', async ({ page }) => {
    // Navigate to home page
    await page.goto('/')
    
    // Create new game
    await page.click('[data-testid="create-game"]')
    await page.fill('[data-testid="player-name"]', 'Alice')
    await page.click('[data-testid="add-player"]')
    await page.fill('[data-testid="player-name"]', 'Bob')
    await page.click('[data-testid="add-player"]')
    
    // Start game
    await page.click('[data-testid="start-game"]')
    
    // Verify game board is displayed
    await expect(page.locator('[data-testid="game-board"]')).toBeVisible()
    await expect(page.locator('text=Alice')).toBeVisible()
    await expect(page.locator('text=Bob')).toBeVisible()
    
    // First player rolls dice
    await page.click('[data-testid="roll-dice"]')
    
    // Verify player moved
    await expect(page.locator('[data-testid="dice-result"]')).toBeVisible()
    
    // End turn
    await page.click('[data-testid="end-turn"]')
    
    // Verify turn changed
    await expect(page.locator('text=Current Player: Bob')).toBeVisible()
  })

  test('property purchase flow', async ({ page }) => {
    // Set up game with player on a property
    await page.goto('/game/test-game')
    
    // Mock player landing on purchasable property
    await page.evaluate(() => {
      window.testUtils.movePlayerToProperty('player-1', 1)
    })
    
    // Purchase property
    await page.click('[data-testid="buy-property"]')
    
    // Verify property ownership
    await expect(page.locator('[data-testid="property-owner"]')).toContainText('Alice')
    
    // Verify money deducted
    await expect(page.locator('[data-testid="player-money"]')).toContainText('$1340')
  })
})
```

**Run E2E tests:**
```bash
cd frontend
npm run test:e2e
```

## Test Data and Fixtures

**Test Data Factory** (`backend/tests/factories.py`):
```python
import factory
from src.domain.entities.player import Player
from src.domain.entities.value_objects import PlayerId, Money

class PlayerFactory(factory.Factory):
    class Meta:
        model = Player
    
    id = factory.Sequence(lambda n: PlayerId(f"player-{n}"))
    name = factory.Faker('first_name')
    money = factory.LazyFunction(lambda: Money(1500))

# Usage in tests
def test_player_creation():
    player = PlayerFactory()
    assert player.money.amount == 1500
```

**Frontend Test Utils** (`frontend/src/tests/utils.tsx`):
```typescript
import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'
import { BrowserRouter } from 'react-router-dom'

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }
```

## Testing Commands Reference

### Backend Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/domain/test_player.py

# Run with coverage
pytest --cov=src tests/

# Run only unit tests
pytest -m unit

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x

# Run tests matching pattern
pytest -k "test_player"
```

### Frontend Testing
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test file
npm test GameBoard.test.tsx

# Run E2E tests
npm run test:e2e

# Run E2E tests in headed mode
npm run test:e2e -- --headed
```

## Continuous Integration

**GitHub Actions workflow** (`.github/workflows/test.yml`):
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=src tests/

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm test
      - name: E2E tests
        run: |
          cd frontend
          npm run test:e2e
```

This comprehensive testing guide ensures all components of Pinopoly V2 are thoroughly tested with fast feedback loops and reliable CI/CD pipelines.