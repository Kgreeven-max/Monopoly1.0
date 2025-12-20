# Pinopoly Archaeology Report

This document captures the analysis of the original Python/Flask Pinopoly codebase, identifying patterns, issues, and features to be ported to v2.

## Timeline of Development

Based on git history analysis:

| Commit | Date | Description |
|--------|------|-------------|
| `508771e6` | Recent | Board size initialization, player position cache improvements |
| `bdb17bb8` | Recent | Added token/color fields to Player model, socket auth handlers |
| `b4aaca81` | Recent | Socket event refactoring, animation hooks, player movement system |
| `b4394db8` | Earlier | Server startup error handling, logging improvements |

## Original Architecture

### Backend (Python/Flask)

```
src/
├── controllers/          # 31 files - Business logic
├── models/              # 48 files - SQLAlchemy ORM
├── routes/              # 31 files - REST endpoints
├── migrations/          # 17 files - Custom migrations
├── game_logic/          # Core mechanics
├── services/            # Service layer
└── utils/               # Helpers
```

**Key Files:**
- `app.py` (1,500+ lines) - Monolithic entry point
- `src/models/game_state.py` (422 lines) - Singleton game state
- `src/models/player.py` (351 lines) - Player with finances
- `src/models/property.py` (665 lines) - Complex property system
- `src/controllers/game_controller.py` (2,337 lines) - Core game mechanics

### Frontend (React)

Two implementations exist:
1. `/client/` - Production (968-line BoardPage.jsx)
2. `/board_organized/` - Experimental (animation system)

## Critical Issues Found

### 1. Security Vulnerabilities

**Plaintext PIN Storage** (`src/models/player.py:10-11`)
```python
pin = db.Column(db.String(4))  # Stored as plaintext!
```
**Fix in v2:** Use bcrypt hashing, implement proper JWT auth.

### 2. Singleton Game State

**Single Game Limitation** (`src/models/game_state.py`)
```python
# Only one game can exist at a time
game_state = GameState.query.first()
```
**Fix in v2:** Per-game schemas, room-based isolation.

### 3. Mixed Socket Patterns

**Legacy Handler Coexistence** (`app.py:549`)
```python
# TEMPORARILY keep old handlers for other parts of the app
```
**Fix in v2:** Clean socket event architecture from start.

### 4. No Action Validation

**Missing Server-Side Validation**
- `expected_action_type` defined but not enforced
- Clients can send invalid actions
**Fix in v2:** Strict action validation in game engine.

### 5. Fragile Migrations

**Sequential Manual Migrations** (`app.py:142-380`)
```python
# 17 migrations run one by one with try-catch
try:
    add_credit_score()
except:
    pass
```
**Fix in v2:** Use Prisma migrations.

## Features to Port

### Core Game Mechanics

| Feature | Python Location | Complexity |
|---------|----------------|------------|
| Dice rolling | `game_logic.py` | Low |
| Player movement | `game_controller.py` | Medium |
| Property purchase | `property_controller.py` | Medium |
| Rent calculation | `property.py:200-300` | Medium |
| Jail mechanics | `game_controller.py` | Medium |
| Chance/Community | `special_space_controller.py` | Medium |
| House/hotel building | `property_controller.py` | Medium |
| Mortgage system | `property_controller.py` | Low |
| Bankruptcy | `game_controller.py` | High |

### Economic System

| Feature | Location | Port Priority |
|---------|----------|---------------|
| 4-state economy | `economic_cycle_controller.py` | High |
| Property value fluctuation | `property.py` | High |
| Dynamic interest rates | `finance_controller.py` | Medium |
| Economic events | `event_system.py` | Medium |

### Financial Instruments

| Instrument | Python Model | Notes |
|------------|--------------|-------|
| Loans | `src/models/loan.py` | Variable/fixed rates |
| CDs | `src/models/cd.py` | Maturity based on laps |
| HELOC | `src/models/loan.py` | Property-backed |
| Credit Score | `player.py` | 300-850 range |

### Bot AI System

**6 Personality Types** (`src/models/bots/`)

| Bot | Strategy | Key Behavior |
|-----|----------|--------------|
| Conservative | Risk-averse | High cash reserves, safe investments |
| Aggressive | High-risk | Leverages debt, rapid expansion |
| Strategic | Monopoly-focused | Prioritizes completing color groups |
| Opportunistic | Market-timing | Exploits auctions, economic cycles |
| Shark | Predatory | Targets weak players, aggressive trading |
| Investor | Long-term | CD-focused, steady wealth building |

**Base Bot Class** (`src/models/bots/base_bot.py` - 639 lines)
- `BotDecisionMaker` - Evaluates options
- `BotActionHandler` - Executes decisions
- Economic event response system
- Trade evaluation logic

### Admin Features

| Feature | Route | Controller |
|---------|-------|------------|
| Game creation | `/api/admin/game` | `admin_controller.py` |
| Player management | `/api/admin/players` | `player_admin_routes.py` |
| Bot creation | `/api/admin/bots` | `bot_admin_routes.py` |
| Economy control | `/api/admin/economy` | `economic_admin_routes.py` |
| Event triggering | `/api/admin/events` | `event_admin_routes.py` |

## Socket Events Catalog

### Client → Server

```typescript
// Lobby
'join_game' -> { playerName, gameCode }
'ready_up' -> { playerId }
'start_game' -> { hostId }

// Game Actions
'roll_dice' -> { playerId }
'end_turn' -> { playerId }
'buy_property' -> { playerId, propertyId }
'decline_property' -> { playerId, propertyId }
'build_house' -> { playerId, propertyId }
'mortgage_property' -> { playerId, propertyId }
'pay_rent' -> { playerId, amount, toPlayerId }

// Auction
'place_bid' -> { playerId, amount }
'pass_auction' -> { playerId }

// Trading
'propose_trade' -> { from, to, offer, request }
'accept_trade' -> { tradeId }
'reject_trade' -> { tradeId }
```

### Server → Client

```typescript
// State Updates
'game_state' -> CompleteGameState  // Full snapshot
'player_joined' -> PlayerInfo
'player_left' -> { playerId }
'turn_changed' -> { currentPlayerId }

// Actions
'dice_rolled' -> { playerId, dice1, dice2, total }
'player_moved' -> { playerId, from, to, passedGo }
'property_bought' -> { playerId, propertyId }
'rent_paid' -> { from, to, amount }
'card_drawn' -> { playerId, card }

// Auction
'auction_started' -> AuctionState
'bid_placed' -> { playerId, amount }
'auction_ended' -> { winnerId, amount }
```

## Database Schema Mapping

### GameState → New Schema

| Old Field | New Field | Notes |
|-----------|-----------|-------|
| `game_id` | `id` | UUID |
| `status` | `status` | Add 'lobby' state |
| `current_player_id` | `currentPlayerIndex` | Index instead of ID |
| `player_order` | `playerOrder` | Array instead of CSV |
| `turn_number` | `round` | Rename |
| `economic_state` | `economy.phase` | Nested object |
| `expected_action_type` | `phase` | Enum TurnPhase |

### Player → New Schema

| Old Field | New Field | Notes |
|-----------|-----------|-------|
| `id` | `id` | UUID |
| `username` | `name` | Rename |
| `pin` | - | Remove (use JWT) |
| `money` | `money` | Same |
| `position` | `position` | Same |
| `is_bot` | `isBot` | camelCase |
| `bot_personality` | `botPersonality` | camelCase |
| `in_jail` | `inJail` | camelCase |
| `jail_turns` | `jailTurns` | camelCase |
| `credit_score` | `creditScore` | camelCase |

### Property → New Schema

| Old Field | New Field | Notes |
|-----------|-----------|-------|
| `id` | `id` | Number (position) |
| `name` | `name` | Same |
| `color_group` | `group` | Enum ColorGroup |
| `price` | `price` | Same |
| `owner_id` | `ownerId` | camelCase |
| `houses` | `houses` | 0-5 (5 = hotel) |
| `is_mortgaged` | `isMortgaged` | camelCase |
| `current_value` | `currentValue` | Economy-adjusted |

## What to Keep vs Rebuild

### KEEP (Port Logic)

1. **Rent Calculation** (`property.py:200-300`)
   - Base rent, monopoly bonus, per-house rates
   - Railroad/utility special rules

2. **Economic Cycle Logic** (`economic_cycle_controller.py`)
   - Phase transitions (recession→stable→growth→boom)
   - Property value multipliers
   - Interest rate adjustments

3. **Bot Decision Framework** (`base_bot.py`)
   - Property evaluation scoring
   - Trade offer analysis
   - Risk assessment algorithms

4. **Special Space Actions** (`special_space_controller.py`)
   - Chance/Community Chest cards
   - Tax calculations
   - Jail mechanics

### REBUILD (New Implementation)

1. **Authentication** - JWT instead of PIN
2. **Game State Management** - Redux-like reducer pattern
3. **Socket Layer** - Clean event contracts
4. **Database** - PostgreSQL + Prisma
5. **Frontend** - Three separate apps (TV, controller, admin)
6. **Testing** - Comprehensive unit/integration/E2E

## Lessons Learned

### What Worked Well
- Separation of controllers/models/routes
- Socket.IO for real-time updates
- Bot personality system
- Economic simulation depth

### What to Avoid
- Monolithic entry point (app.py)
- Singleton game state
- Manual migrations
- Mixed old/new patterns
- Plaintext credentials
- Missing action validation

## Migration Priority

### Phase 1: Critical Path
1. Game state types and reducer
2. Dice rolling and movement
3. Property purchase/rent
4. Turn management

### Phase 2: Core Features
1. Jail mechanics
2. Chance/Community Chest
3. House/hotel building
4. Mortgage system

### Phase 3: Advanced Features
1. Auction system
2. Trading system
3. Financial instruments
4. Economic cycles

### Phase 4: AI System
1. Bot base class
2. 6 personality strategies
3. Trade evaluation
4. Economic awareness

---

*Generated from codebase analysis - December 2024*
