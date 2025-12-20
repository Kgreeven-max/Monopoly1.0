# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pinopoly v2 is a Jackbox-style Monopoly party game where players use phones as controllers while a TV displays the game board. The architecture follows a strict separation: TV Display is read-only, Controller handles player input, and the Game Server is the single source of truth.

## Commands

```bash
# Development
pnpm install          # Install dependencies (uses pnpm workspaces)
pnpm dev              # Start all dev servers (Turborepo)
pnpm build            # Build all packages
pnpm test             # Run all tests
pnpm typecheck        # TypeScript check all packages
pnpm lint             # Lint all packages

# Run single package
pnpm --filter game-server dev       # Run only game server
pnpm --filter @pinopoly/controller dev  # Run only controller app

# Database (requires DATABASE_URL)
pnpm db:migrate       # Run Prisma migrations
pnpm db:generate      # Generate Prisma client

# Docker
pnpm docker:up        # Start containers
pnpm docker:down      # Stop containers
```

## Architecture

### Jackbox Pattern (Critical)
- **TV Display** (`apps/tv-display`): Read-only view on port 3003. Receives `GAME_STATE` events only.
- **Controller** (`apps/controller`): Player input on port 3001. Emits actions, receives state updates.
- **Game Server** (`services/game-server`): Single source of truth on port 3000. All state changes happen here.

### Core Packages
- `packages/game-engine`: Pure game logic with reducer pattern. No I/O, fully deterministic with seeded RNG.
- `packages/shared`: Socket event constants, types, utilities shared across all apps.
- `packages/ui-components`: Shared React components.

### State Flow
1. Controller emits action (e.g., `game:rollDice`)
2. Server validates and runs through `gameReducer(state, action) => [newState, events]`
3. Server broadcasts `GAME_STATE` to all clients in the room
4. Clients update Zustand store from `GAME_STATE` only (never from animation events)

### Socket Events
All socket event names are defined in `packages/shared/src/index.ts` as `SocketEvents`. Use these constants instead of string literals.

Key patterns:
- `lobby:*` - Pre-game room management
- `game:*` - In-game actions and state updates
- `trade:*` - Trading between players
- `auction:*` - Property auctions

### Room Management
Games are identified by 6-character room codes (e.g., `ABC123`). The `RoomManager` class in the game server handles:
- Room creation via `POST /api/games`
- Player joining via `lobby:join` socket event
- Session persistence for reconnection support
- Host migration when host disconnects
- Turn timeouts (2 minutes default)

## Key Files

- `services/game-server/src/socket/RoomManager.ts` - Room and game lifecycle management
- `packages/game-engine/src/reducers/gameReducer.ts` - Core game logic reducer
- `packages/shared/src/index.ts` - Socket events and shared utilities
- `apps/controller/src/hooks/useSocket.ts` - Controller socket connection
- `apps/tv-display/src/hooks/useSocket.ts` - TV display socket connection

## Development Notes

### Dev Server Ports
| Service | Port |
|---------|------|
| Game Server (API + WebSocket) | 3000 |
| Controller | 3001 |
| Admin Console | 3002 |
| TV Display | 3003 |

### Database
PostgreSQL is optional for development. The game works with in-memory state. Set `DATABASE_URL` for persistence.

### Type Conventions
- Game phases use snake_case: `pre_roll`, `rolling`, `buy_decision`, `turn_end`
- Property field is `group` (not `colorGroup`)
- Property rent uses `baseRent` and `rentLevels` array
- Player bot status uses `botPersonality` (not `personality`)
- Game events use `payload` field (not `data`)
