# Pinopoly v2 Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              NGINX (Reverse Proxy)                       │
│                           ports 80/443 - SSL termination                 │
└───────────────────────────────────────────────────────────────────────────┘
         │                    │                    │                    │
         ▼                    ▼                    ▼                    ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐         ┌─────────┐
    │   TV    │         │  Phone  │         │  Admin  │         │   API   │
    │ Display │         │Controller│        │ Console │         │  /ws    │
    │  :3001  │         │  :3002  │         │  :3003  │         │  :3000  │
    └─────────┘         └─────────┘         └─────────┘         └────┬────┘
         │                    │                    │                  │
         └────────────────────┴────────────────────┴──────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────┐
                            │     Game Server       │
                            │    (Node.js + TS)     │
                            │                       │
                            │  ┌─────────────────┐  │
                            │  │  Socket.IO      │  │
                            │  │  Room Manager   │  │
                            │  └────────┬────────┘  │
                            │           │           │
                            │  ┌────────▼────────┐  │
                            │  │  Game Engine    │  │
                            │  │  (Pure Logic)   │  │
                            │  └────────┬────────┘  │
                            │           │           │
                            │  ┌────────▼────────┐  │
                            │  │  Game Service   │  │
                            │  └─────────────────┘  │
                            └───────────┬───────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
             ┌───────────┐       ┌───────────┐       ┌───────────┐
             │ PostgreSQL│       │   Redis   │       │ Bot Worker│
             │  Master   │       │   Queue   │       │  (BullMQ) │
             │   DB      │       │           │       │           │
             └─────┬─────┘       └───────────┘       └───────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Schema  │ │ Schema  │ │ Schema  │
   │game_abc │ │game_def │ │game_xyz │
   └─────────┘ └─────────┘ └─────────┘
```

## Package Structure

```
pinopoly-v2/
├── apps/
│   ├── tv-display/          # React SPA - Main board view
│   ├── controller/          # React SPA - Phone controls
│   └── admin-console/       # React SPA - Admin dashboard
│
├── services/
│   └── game-server/         # Node.js backend
│       ├── src/
│       │   ├── socket/      # Socket.IO handling
│       │   ├── api/         # REST endpoints
│       │   ├── services/    # Business logic
│       │   ├── db/          # Database access
│       │   └── workers/     # Bot processing
│       └── prisma/          # Schema & migrations
│
├── packages/
│   ├── shared/              # Shared types & utilities
│   │   ├── types/           # TypeScript interfaces
│   │   ├── schemas/         # Zod validation
│   │   ├── constants/       # Game constants
│   │   └── utils/           # Helper functions
│   │
│   ├── game-engine/         # Pure game logic
│   │   ├── state/           # State types
│   │   ├── actions/         # Action definitions
│   │   ├── reducers/        # State reducers
│   │   ├── rules/           # Game rules
│   │   ├── bots/            # AI strategies
│   │   └── rng/             # Seeded randomness
│   │
│   └── ui-components/       # Shared React components
│
├── infra/
│   ├── docker/              # Dockerfiles
│   ├── migrations/          # SQL migrations
│   └── scripts/             # DevOps scripts
│
└── docs/                    # Documentation
```

## Data Flow

### 1. Player Joins Game

```
Phone App                  Game Server              Database
    │                           │                      │
    │ POST /api/games/join      │                      │
    │ { roomCode, name }        │                      │
    │ ────────────────────────► │                      │
    │                           │ Validate room code   │
    │                           │ ──────────────────► │
    │                           │ ◄────────────────── │
    │                           │                      │
    │ ◄──────────────────────── │                      │
    │ { playerId, token }       │                      │
    │                           │                      │
    │ WS connect + auth         │                      │
    │ ────────────────────────► │                      │
    │                           │ Join Socket room     │
    │                           │ Emit lobby:state     │
    │ ◄──────────────────────── │                      │
    │ { players[], status }     │                      │
```

### 2. Game Action (Roll Dice)

```
Controller        Game Server         Engine          Database
    │                  │                 │                │
    │ game:rollDice    │                 │                │
    │ ───────────────► │                 │                │
    │                  │ Validate turn   │                │
    │                  │ ─────────────► │                │
    │                  │                 │ Execute action │
    │                  │                 │ Return events  │
    │                  │ ◄───────────── │                │
    │                  │                 │                │
    │                  │ Persist state   │                │
    │                  │ ──────────────────────────────► │
    │                  │ ◄────────────────────────────── │
    │                  │                 │                │
    │                  │ Broadcast to room               │
    │ ◄──────────────── (game:diceRolled, game:state)    │
    │                  │                 │                │
    TV Display ◄───────┘                 │                │
```

### 3. Bot Turn (Async Worker)

```
Game Server           Redis Queue         Bot Worker        Engine
    │                      │                   │               │
    │ Detect bot's turn    │                   │               │
    │ Add job to queue     │                   │               │
    │ ───────────────────► │                   │               │
    │                      │ Job available     │               │
    │                      │ ─────────────────►│               │
    │                      │                   │ Get game state│
    │                      │                   │──────────────►│
    │                      │                   │◄──────────────│
    │                      │                   │               │
    │                      │                   │ Decide action │
    │                      │                   │──────────────►│
    │                      │                   │◄──────────────│
    │                      │                   │               │
    │ ◄────────────────────────────────────────│               │
    │ Execute bot action   │                   │               │
    │                      │                   │               │
```

## Component Details

### Game Engine (Pure Logic)

The game engine is completely isolated from I/O. It:
- Takes current state + action
- Returns new state + events
- Uses seeded RNG for determinism
- Is fully testable in isolation

```typescript
// packages/game-engine/src/reducers/gameReducer.ts

type GameReducer = (
  state: GameState,
  action: GameAction
) => [GameState, GameEvent[]];

// Example usage
const [newState, events] = gameReducer(currentState, {
  type: 'ROLL_DICE',
  payload: { playerId: 'abc123' }
});
```

### Room Manager

Manages concurrent games and player connections:

```typescript
// services/game-server/src/socket/RoomManager.ts

class RoomManager {
  private games: Map<string, GameRoom>;
  private playerToGame: Map<string, string>;

  createGame(hostId: string, config: GameConfig): GameRoom;
  joinGame(roomCode: string, socket: Socket, player: PlayerInfo): void;
  leaveGame(socketId: string): void;
  startGame(roomCode: string): void;
  processAction(roomCode: string, action: GameAction): void;
}
```

### Database Schema Strategy

**Master Database** (always exists):
- Users, sessions, game catalog
- Historical data, analytics
- Audit logs

**Per-Game Schemas** (created on game start):
- Live game state
- Current players, properties
- Active trades, auctions
- Event log for replay

```sql
-- Create schema for new game
CREATE SCHEMA game_abc123;

-- Populate with initial state
CREATE TABLE game_abc123.state (...);
CREATE TABLE game_abc123.players (...);
CREATE TABLE game_abc123.properties (...);

-- On game end: archive to master, drop schema
INSERT INTO master.game_snapshots ...;
DROP SCHEMA game_abc123 CASCADE;
```

## Security Model

### Authentication

```
┌─────────────────────────────────────────────────────────┐
│                     JWT Token Flow                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   Player joins:                                          │
│   1. POST /api/games/join { name, roomCode }             │
│   2. Server creates player record                        │
│   3. Server returns JWT { playerId, gameId, role }       │
│   4. Client stores JWT, uses for WebSocket auth          │
│                                                          │
│   Admin access:                                          │
│   1. POST /api/auth/admin { adminToken }                 │
│   2. Server validates against env ADMIN_TOKEN            │
│   3. Server returns JWT { role: 'admin' }                │
│   4. Full game control access                            │
│                                                          │
│   TV Display:                                            │
│   1. WS connect with { roomCode, role: 'display' }       │
│   2. Read-only access to game state                      │
│   3. No action permissions                               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Role Permissions

| Role | Create Game | Join | Actions | Admin |
|------|-------------|------|---------|-------|
| Player | Yes (as host) | Yes | Own turn only | No |
| Display | No | Read-only | None | No |
| Admin | Yes | Yes | Any | Yes |

## Frontend Architecture

### TV Display

Primary view for the game board, optimized for large screens.

```
┌─────────────────────────────────────────────────────────┐
│                         TV Display                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │                    Game Board                      │  │
│  │  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────────┐  │  │
│  │  │ GO  │     │     │     │     │     │  JAIL   │  │  │
│  │  ├─────┤     Board with                ├─────────┤  │  │
│  │  │     │     40 spaces                 │         │  │  │
│  │  │     │     and player                │         │  │  │
│  │  │     │     tokens                    │         │  │  │
│  │  ├─────┤                               ├─────────┤  │  │
│  │  │FREE │                               │GO TO    │  │  │
│  │  │PARK │                               │JAIL     │  │  │
│  │  └─────┴───────────────────────────────┴─────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐│
│  │ Player 1    │ │ Player 2    │ │   Current Turn      ││
│  │ $1500       │ │ $1200       │ │   Player 1's turn   ││
│  │ 🚗 [props]  │ │ 🎩 [props]  │ │   Waiting for roll  ││
│  └─────────────┘ └─────────────┘ └─────────────────────┘│
│                                                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │ QR Code to join: ABCD12    Economy: STABLE 📈      ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### Phone Controller

Mobile-first interface for player actions.

```
┌─────────────────────┐
│   Phone Controller  │
├─────────────────────┤
│                     │
│  ┌───────────────┐  │
│  │ Your Status   │  │
│  │ Money: $1,500 │  │
│  │ Position: GO  │  │
│  └───────────────┘  │
│                     │
│  ┌───────────────┐  │
│  │               │  │
│  │   🎲 ROLL     │  │
│  │               │  │
│  └───────────────┘  │
│                     │
│  ┌─────┐ ┌─────┐   │
│  │Props│ │Trade│   │
│  └─────┘ └─────┘   │
│                     │
│  ┌─────┐ ┌─────┐   │
│  │Bank │ │Build│   │
│  └─────┘ └─────┘   │
│                     │
│  ┌───────────────┐  │
│  │   END TURN    │  │
│  └───────────────┘  │
│                     │
└─────────────────────┘
```

### Admin Console

Full game control and monitoring.

```
┌──────────────────────────────────────────────────────────┐
│                      Admin Console                        │
├──────────────────────────────────────────────────────────┤
│  [Dashboard] [Games] [Players] [Analytics] [Logs]        │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Active Games (3)                                         │
│  ┌──────────────────────────────────────────────────────┐│
│  │ ABCD12 │ 4 players │ Round 15 │ [Pause] [End]       ││
│  │ EFGH34 │ 2 players │ Lobby    │ [View] [Delete]     ││
│  │ IJKL56 │ 6 players │ Round 42 │ [Pause] [End]       ││
│  └──────────────────────────────────────────────────────┘│
│                                                           │
│  Game ABCD12 - State Inspector                           │
│  ┌──────────────────────────────────────────────────────┐│
│  │ {                                                    ││
│  │   "round": 15,                                       ││
│  │   "currentPlayer": "player_1",                       ││
│  │   "phase": "buy_decision",                           ││
│  │   "economy": { "phase": "stable" },                  ││
│  │   ...                                                ││
│  │ }                                                    ││
│  └──────────────────────────────────────────────────────┘│
│                                                           │
│  Quick Actions:                                           │
│  [+$500 to Player] [Trigger Recession] [Skip Turn]       │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

## Scalability Considerations

### Current Design (1-10 games)

- Single game-server instance
- Single PostgreSQL database
- Redis for bot job queue only
- In-memory room management

### Future Scaling Path

If scaling beyond 10 concurrent games:

1. **Horizontal game-server scaling**
   - Redis adapter for Socket.IO
   - Sticky sessions via Nginx
   - Shared room state in Redis

2. **Database scaling**
   - Connection pooling (PgBouncer)
   - Read replicas for analytics
   - Partitioned audit logs

3. **Bot worker scaling**
   - Multiple worker instances
   - Queue priority by game age

## Monitoring & Observability

### Health Checks

```
GET /health
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 3600,
  "activeGames": 3,
  "connectedClients": 12,
  "database": "connected",
  "redis": "connected"
}
```

### Logging

Structured JSON logs with correlation IDs:

```json
{
  "level": "info",
  "message": "Player rolled dice",
  "gameId": "abc123",
  "playerId": "player_1",
  "correlationId": "req-xyz",
  "dice": [4, 3],
  "newPosition": 7,
  "timestamp": "2024-12-19T10:30:00Z"
}
```

---

*Architecture document for Pinopoly v2 - December 2024*
