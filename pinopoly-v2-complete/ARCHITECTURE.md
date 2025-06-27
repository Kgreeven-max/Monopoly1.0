# 🏗️ Pinopoly V2 - Architecture Documentation

## Overview

Pinopoly V2 is built using **Clean Architecture** and **Domain-Driven Design** principles, ensuring maintainability, testability, and scalability. This document outlines the architectural decisions, patterns, and structure of the system.

## 🎯 Architectural Principles

### 1. Clean Architecture
The system is organized into four distinct layers with clear dependency rules:

```
Dependencies flow inward only →

┌─────────────────────────────────────────────┐
│              Presentation Layer              │ ← UI, API, WebSocket handlers
│         (Frameworks & Drivers)             │
├─────────────────────────────────────────────┤
│             Infrastructure Layer            │ ← Database, Cache, External APIs
│        (Interface Adapters)               │
├─────────────────────────────────────────────┤
│             Application Layer               │ ← Use Cases, DTOs, Orchestration
│          (Application Business Rules)      │
├─────────────────────────────────────────────┤
│              Domain Layer                   │ ← Entities, Value Objects, Domain Services
│        (Enterprise Business Rules)        │   (Core Business Logic)
└─────────────────────────────────────────────┘
```

### 2. Domain-Driven Design (DDD)
- **Ubiquitous Language**: Consistent terminology across code and business
- **Bounded Contexts**: Clear module boundaries
- **Aggregates**: Consistency boundaries for transactions
- **Domain Events**: Loose coupling between bounded contexts
- **Value Objects**: Immutable objects representing concepts

### 3. SOLID Principles
- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Subtypes must be substitutable for base types
- **Interface Segregation**: Clients shouldn't depend on unused interfaces
- **Dependency Inversion**: Depend on abstractions, not concretions

## 🧱 System Components

### Backend Architecture

#### Domain Layer (Core Business Logic)
```python
# Core entities representing business concepts
class Player:
    def __init__(self, id: PlayerId, name: str, money: Money):
        self._id = id
        self._name = name
        self._money = money
    
    def move_to(self, position: Position) -> PlayerMoved:
        # Business logic for player movement
        pass

class Property:
    def calculate_rent(self) -> Money:
        # Business rule for rent calculation
        pass

# Domain services for complex business logic
class GameEngine:
    def process_turn(self, game: Game, player: Player, dice_roll: DiceRoll) -> TurnResult:
        # Complex game logic that doesn't belong to a single entity
        pass
```

#### Application Layer (Use Cases)
```python
# Use cases orchestrate domain objects
class MovePlayerUseCase:
    def __init__(self, player_repo: PlayerRepository, game_repo: GameRepository):
        self._player_repo = player_repo
        self._game_repo = game_repo
    
    def execute(self, command: MovePlayerCommand) -> MovePlayerResult:
        player = self._player_repo.get_by_id(command.player_id)
        game = self._game_repo.get_by_id(command.game_id)
        
        # Business logic orchestration
        result = player.move(command.spaces)
        
        # Persist changes
        self._player_repo.save(player)
        
        return MovePlayerResult(result)
```

#### Infrastructure Layer (Technical Details)
```python
# Repository implementations
class SqlAlchemyPlayerRepository(PlayerRepository):
    def get_by_id(self, player_id: PlayerId) -> Player:
        # Database access implementation
        pass
    
    def save(self, player: Player) -> None:
        # Database persistence implementation
        pass

# WebSocket handlers
class GameWebSocketHandler:
    def __init__(self, move_player_use_case: MovePlayerUseCase):
        self._move_player_use_case = move_player_use_case
    
    @socketio.on('move_player')
    def handle_move_player(self, data):
        command = MovePlayerCommand.from_dict(data)
        result = self._move_player_use_case.execute(command)
        emit('player_moved', result.to_dict())
```

#### Presentation Layer (API & UI)
```python
# REST API endpoints
@app.route('/api/players/<int:player_id>/move', methods=['POST'])
def move_player(player_id: int):
    command = MovePlayerCommand(
        player_id=PlayerId(player_id),
        spaces=request.json['spaces']
    )
    result = move_player_use_case.execute(command)
    return jsonify(result.to_dict())
```

### Frontend Architecture

#### Component Structure
```typescript
// Feature-based component organization
interface GameBoardProps {
  gameState: GameState;
  onPlayerMove: (playerId: string, spaces: number) => void;
}

const GameBoard: React.FC<GameBoardProps> = ({ gameState, onPlayerMove }) => {
  // Component logic
  return (
    <div className="game-board">
      {/* Board rendering */}
    </div>
  );
};

// Custom hooks for business logic
const useGameState = (gameId: string) => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    // WebSocket connection and state management
  }, [gameId]);
  
  return { gameState, isLoading };
};
```

#### State Management
```typescript
// Zustand store for global state
interface GameStore {
  currentGame: Game | null;
  players: Player[];
  properties: Property[];
  
  // Actions
  setCurrentGame: (game: Game) => void;
  updatePlayer: (player: Player) => void;
  movePlayer: (playerId: string, position: number) => void;
}

const useGameStore = create<GameStore>((set, get) => ({
  currentGame: null,
  players: [],
  properties: [],
  
  setCurrentGame: (game) => set({ currentGame: game }),
  updatePlayer: (player) => set((state) => ({
    players: state.players.map(p => p.id === player.id ? player : p)
  })),
  movePlayer: (playerId, position) => set((state) => ({
    players: state.players.map(p => 
      p.id === playerId ? { ...p, position } : p
    )
  })),
}));
```

## 🔄 Data Flow

### Request Flow
```
1. User Action (Frontend)
   ↓
2. Component Event Handler
   ↓
3. Custom Hook / Store Action
   ↓
4. API Service Call
   ↓
5. Backend API Endpoint (Presentation Layer)
   ↓
6. Use Case (Application Layer)
   ↓
7. Domain Service/Entity (Domain Layer)
   ↓
8. Repository (Infrastructure Layer)
   ↓
9. Database/Cache
```

### Real-time Updates Flow
```
1. Domain Event Generated
   ↓
2. Event Publisher (Infrastructure)
   ↓
3. WebSocket Emission
   ↓
4. Frontend WebSocket Handler
   ↓
5. Store Update
   ↓
6. Component Re-render
```

## 🎮 Domain Model

### Core Entities

#### Game Aggregate
```python
class Game:
    """
    Game aggregate root managing the overall game state
    """
    def __init__(self, id: GameId, mode: GameMode):
        self._id = id
        self._mode = mode
        self._players: List[Player] = []
        self._board = Board()
        self._current_turn = 0
        self._status = GameStatus.WAITING
    
    def add_player(self, player: Player) -> None:
        if len(self._players) >= self._mode.max_players:
            raise MaxPlayersExceeded()
        self._players.append(player)
    
    def start_game(self) -> GameStarted:
        if len(self._players) < self._mode.min_players:
            raise InsufficientPlayers()
        
        self._status = GameStatus.ACTIVE
        return GameStarted(self._id, self._players)
    
    def process_turn(self, player_id: PlayerId, action: PlayerAction) -> TurnResult:
        # Complex turn processing logic
        pass
```

#### Player Aggregate
```python
class Player:
    """
    Player aggregate managing player state and actions
    """
    def __init__(self, id: PlayerId, name: str, starting_money: Money):
        self._id = id
        self._name = name
        self._money = starting_money
        self._position = Position(0)
        self._properties: List[PropertyId] = []
        self._status = PlayerStatus.ACTIVE
    
    def move(self, spaces: int, board_size: int) -> PlayerMoved:
        old_position = self._position
        self._position = Position((self._position.value + spaces) % board_size)
        
        passed_go = (old_position.value + spaces) >= board_size
        if passed_go:
            self._money = self._money.add(Money(200))  # Pass GO bonus
        
        return PlayerMoved(
            player_id=self._id,
            old_position=old_position,
            new_position=self._position,
            passed_go=passed_go
        )
    
    def buy_property(self, property: Property) -> PropertyPurchased:
        if not self._can_afford(property.price):
            raise InsufficientFunds()
        
        self._money = self._money.subtract(property.price)
        self._properties.append(property.id)
        
        return PropertyPurchased(self._id, property.id, property.price)
```

#### Property Aggregate
```python
class Property:
    """
    Property aggregate managing property ownership and development
    """
    def __init__(self, id: PropertyId, name: str, price: Money, group: PropertyGroup):
        self._id = id
        self._name = name
        self._price = price
        self._group = group
        self._owner: Optional[PlayerId] = None
        self._houses = 0
        self._has_hotel = False
        self._is_mortgaged = False
    
    def calculate_rent(self, dice_roll: Optional[int] = None) -> Money:
        if self._is_mortgaged or not self._owner:
            return Money(0)
        
        base_rent = self._group.calculate_base_rent(self._houses, self._has_hotel)
        
        # Apply multipliers for utilities, railroads, etc.
        return self._group.apply_rent_multipliers(base_rent, dice_roll)
    
    def develop(self, development_type: DevelopmentType) -> PropertyDeveloped:
        if development_type == DevelopmentType.HOUSE:
            if self._houses >= 4:
                raise MaximumHousesReached()
            self._houses += 1
        elif development_type == DevelopmentType.HOTEL:
            if self._houses != 4:
                raise HousesRequiredForHotel()
            self._houses = 0
            self._has_hotel = True
        
        return PropertyDeveloped(self._id, development_type)
```

### Value Objects

```python
class Money:
    """Immutable value object representing money"""
    def __init__(self, amount: int):
        if amount < 0:
            raise ValueError("Money cannot be negative")
        self._amount = amount
    
    def add(self, other: 'Money') -> 'Money':
        return Money(self._amount + other._amount)
    
    def subtract(self, other: 'Money') -> 'Money':
        if self._amount < other._amount:
            raise InsufficientFunds()
        return Money(self._amount - other._amount)

class Position:
    """Value object representing board position"""
    def __init__(self, value: int):
        if not (0 <= value <= 39):  # Standard Monopoly board
            raise ValueError("Position must be between 0 and 39")
        self._value = value
    
    @property
    def value(self) -> int:
        return self._value
```

### Domain Events

```python
class DomainEvent:
    """Base class for all domain events"""
    def __init__(self, aggregate_id: str, occurred_at: datetime):
        self.aggregate_id = aggregate_id
        self.occurred_at = occurred_at
        self.event_id = str(uuid.uuid4())

class PlayerMoved(DomainEvent):
    def __init__(self, player_id: PlayerId, old_position: Position, 
                 new_position: Position, passed_go: bool):
        super().__init__(str(player_id), datetime.utcnow())
        self.player_id = player_id
        self.old_position = old_position
        self.new_position = new_position
        self.passed_go = passed_go

class PropertyPurchased(DomainEvent):
    def __init__(self, player_id: PlayerId, property_id: PropertyId, price: Money):
        super().__init__(str(property_id), datetime.utcnow())
        self.player_id = player_id
        self.property_id = property_id
        self.price = price
```

## 🔌 Integration Patterns

### Repository Pattern
```python
class PlayerRepository(ABC):
    """Abstract repository interface"""
    @abstractmethod
    def get_by_id(self, player_id: PlayerId) -> Player:
        pass
    
    @abstractmethod
    def save(self, player: Player) -> None:
        pass
    
    @abstractmethod
    def find_by_game(self, game_id: GameId) -> List[Player]:
        pass

class SqlAlchemyPlayerRepository(PlayerRepository):
    """Concrete implementation using SQLAlchemy"""
    def __init__(self, session: Session):
        self._session = session
    
    def get_by_id(self, player_id: PlayerId) -> Player:
        model = self._session.query(PlayerModel).filter_by(id=str(player_id)).first()
        if not model:
            raise PlayerNotFound(player_id)
        return self._to_domain(model)
    
    def save(self, player: Player) -> None:
        model = self._to_model(player)
        self._session.merge(model)
        self._session.commit()
```

### Event-Driven Architecture
```python
class EventPublisher(ABC):
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        pass

class SocketIOEventPublisher(EventPublisher):
    def __init__(self, socketio: SocketIO):
        self._socketio = socketio
    
    def publish(self, event: DomainEvent) -> None:
        event_name = self._get_event_name(event)
        event_data = self._serialize_event(event)
        self._socketio.emit(event_name, event_data)

# Usage in use cases
class MovePlayerUseCase:
    def __init__(self, player_repo: PlayerRepository, event_publisher: EventPublisher):
        self._player_repo = player_repo
        self._event_publisher = event_publisher
    
    def execute(self, command: MovePlayerCommand) -> None:
        player = self._player_repo.get_by_id(command.player_id)
        event = player.move(command.spaces, command.board_size)
        
        self._player_repo.save(player)
        self._event_publisher.publish(event)
```

### CQRS (Command Query Responsibility Segregation)
```python
# Command side (writes)
class CreatePlayerCommand:
    def __init__(self, name: str, game_id: GameId):
        self.name = name
        self.game_id = game_id

class CreatePlayerHandler:
    def handle(self, command: CreatePlayerCommand) -> PlayerId:
        player = Player.create(command.name, Money(1500))
        self._player_repo.save(player)
        return player.id

# Query side (reads)
class PlayerQuery:
    def __init__(self, query_db: QueryDatabase):
        self._query_db = query_db
    
    def get_player_summary(self, player_id: PlayerId) -> PlayerSummaryDto:
        # Optimized read model query
        pass
    
    def get_leaderboard(self, game_id: GameId) -> List[PlayerRankingDto]:
        # Aggregated data query
        pass
```

## 🚀 Scalability Considerations

### Horizontal Scaling
- **Stateless Services**: All application services are stateless
- **Database Sharding**: Game data can be sharded by game_id
- **Redis Clustering**: Session and cache data distributed across Redis cluster
- **Load Balancing**: Multiple backend instances behind load balancer

### Performance Optimizations
- **Connection Pooling**: Database and Redis connection pools
- **Query Optimization**: Proper indexing and query patterns
- **Caching Strategy**: Multi-level caching (Redis, HTTP, CDN)
- **Lazy Loading**: Components and data loaded on demand

### Monitoring & Observability
- **Structured Logging**: JSON logs with correlation IDs
- **Metrics Collection**: Application and business metrics
- **Distributed Tracing**: Request tracing across services
- **Health Checks**: Comprehensive health monitoring

## 🔒 Security Architecture

### Authentication & Authorization
- **JWT Tokens**: Stateless authentication
- **Role-Based Access Control**: Player, Admin roles
- **API Rate Limiting**: Prevent abuse
- **Input Validation**: All inputs validated at boundaries

### Data Protection
- **Encryption at Rest**: Database encryption
- **Encryption in Transit**: HTTPS/WSS only
- **SQL Injection Prevention**: ORM query builders
- **XSS Protection**: Input sanitization

## 🧪 Testing Strategy

### Testing Pyramid
```
       ┌─────────────┐
       │   E2E Tests │  ← Few, high-value user scenarios
       │  (Slow)     │
    ┌──┴─────────────┴──┐
    │ Integration Tests │  ← API endpoints, database
    │   (Medium)        │
 ┌──┴───────────────────┴──┐
 │    Unit Tests           │  ← Domain logic, components
 │     (Fast)              │
 └─────────────────────────┘
```

### Test Categories
- **Unit Tests**: Domain entities, value objects, services
- **Integration Tests**: Repository implementations, API endpoints
- **E2E Tests**: Complete user workflows
- **Performance Tests**: Load testing with realistic scenarios
- **Security Tests**: Authentication, authorization, input validation

This architecture ensures that Pinopoly V2 is maintainable, testable, and can scale to handle multiple concurrent games with real-time updates.