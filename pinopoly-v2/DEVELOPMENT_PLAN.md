# Pinopoly v2 - Master Development Plan

> **Last Updated:** December 2024
> **Status:** Phases 1-7 Complete

---

## Project Overview

Pinopoly is a multiplayer Monopoly-style game with:
- **TV Display** - Shows the game board on a shared screen
- **Controller App** - Phone-based player controllers (Jackbox-style)
- **Admin Console** - Game management
- **Game Server** - WebSocket-based game logic

---

## Current Architecture (v2)

```
pinopoly-v2/
├── apps/
│   ├── controller/        # Phone controller (React + Vite)
│   ├── tv-display/        # TV board display (React + Vite)
│   └── admin-console/     # Admin panel (React + Vite)
├── packages/
│   ├── game-engine/       # Pure game logic + reducer
│   ├── shared/            # Shared types, socket events
│   └── ui-components/     # Shared UI components
└── services/
    └── game-server/       # Node.js + Socket.IO server
```

### Running Dev Servers
```bash
npm run dev   # Starts all services via Turborepo
```
- Controller: http://localhost:3001
- Admin Console: http://localhost:3002
- TV Display: http://localhost:3003
- Game Server: http://localhost:3000

---

# ✅ COMPLETED WORK

## Phase 1: Core Infrastructure (DONE)

- [x] Monorepo setup with Turborepo
- [x] Game engine with reducer pattern
- [x] Socket.IO server with room management
- [x] Basic controller and TV display apps
- [x] Shared types and events package

## Phase 2: Jackbox Pattern Refactor (DONE)

### Problem Solved
Multiple socket events were updating state, causing sync bugs and race conditions.

### Solution Implemented
**Single Source of Truth:** `GAME_STATE` is the ONLY event that updates state.

### Files Modified

| File | Status | Changes |
|------|--------|---------|
| `apps/controller/src/contexts/AnimationContext.tsx` | ✅ NEW | Animation state (dice, movement, cards) |
| `apps/controller/src/hooks/useSocket.ts` | ✅ REFACTORED | Only GAME_STATE updates state |
| `apps/controller/src/App.tsx` | ✅ UPDATED | Wrapped with AnimationProvider |
| `apps/tv-display/src/hooks/useSocket.ts` | ✅ REFACTORED | Only GAME_STATE updates state |
| `apps/tv-display/src/store/gameStore.ts` | ✅ UPDATED | setDiceRoll accepts null |
| `services/game-server/src/socket/RoomManager.ts` | ✅ VERIFIED | Animation events emit BEFORE GAME_STATE |

### Event Architecture

```
Client Action → Server → Reducer → Animation Events → GAME_STATE
                                   (UI effects)      (state update)
```

**State Events (Update Zustand store):**
| Event | Purpose |
|-------|---------|
| `GAME_STATE` | Single source of truth for ALL state |
| `JOINED_GAME` | Initial player setup + state |

**Animation Events (UI effects ONLY - no state updates):**
| Event | Purpose |
|-------|---------|
| `GAME_DICE_ROLLED` | Dice roll animation |
| `GAME_PLAYER_MOVED` | Token movement animation |
| `GAME_CARD_DRAWN` | Card reveal animation |

---

# 🚧 IN PROGRESS

## Phase 3: Notifications System

Add toast/notification UI for game events.

### Notifications Needed

| Event | Controller Notification | TV Display |
|-------|------------------------|------------|
| `AUCTION_STARTED` | "Auction started for Park Place!" | Show auction overlay |
| `AUCTION_BID_PLACED` | "Player X bid $200" | Update bid display |
| `AUCTION_ENDED` | "Player X won for $350" | Close overlay |
| `TRADE_PROPOSED` | "Player X wants to trade!" (recipient) | Show trade popup |
| `TRADE_ACCEPTED` | "Trade completed!" | Brief notification |
| `TRADE_REJECTED` | "Trade declined" | Brief notification |
| `ERROR` | Toast with error message | - |
| `PLAYER_JOINED` | - | "Player X joined!" |
| `PLAYER_LEFT` | - | "Player X disconnected" |

### Implementation Plan

1. **Create NotificationContext** (`apps/controller/src/contexts/NotificationContext.tsx`)
   ```typescript
   interface Notification {
     id: string;
     type: 'info' | 'success' | 'warning' | 'error';
     title: string;
     message?: string;
     duration?: number;
   }
   ```

2. **Create Toast Component** (`apps/controller/src/components/Toast.tsx`)
   - Stacks from bottom
   - Auto-dismiss after duration
   - Swipe to dismiss

3. **Add notification event listeners** in useSocket.ts
   ```typescript
   socket.on(SocketEvents.AUCTION_STARTED, (data) => {
     notify({ type: 'info', title: 'Auction Started', message: data.propertyName });
   });

   socket.on(SocketEvents.TRADE_PROPOSED, (data) => {
     if (data.recipientId === playerId) {
       notify({ type: 'warning', title: 'Trade Proposal', message: `${data.proposerName} wants to trade!` });
     }
   });

   socket.on(SocketEvents.ERROR, (data) => {
     notify({ type: 'error', title: 'Error', message: data.message });
   });
   ```

---

# 📋 FUTURE WORK

## Phase 4: Reconnection Support

Allow players to rejoin if they disconnect.

### Requirements
- Store playerId in localStorage
- Server keeps disconnected players for 5 minutes
- Rejoin sends current GAME_STATE

### Implementation
```typescript
// Client
socket.on('connect', () => {
  const savedPlayerId = localStorage.getItem('playerId');
  const savedRoomCode = localStorage.getItem('roomCode');

  if (savedPlayerId && savedRoomCode) {
    socket.emit('action:rejoin', { playerId: savedPlayerId, roomCode: savedRoomCode });
  }
});

// Server
socket.on('action:rejoin', ({ playerId, roomCode }) => {
  const room = rooms.get(roomCode);
  if (room?.state.players[playerId]) {
    socket.join(roomCode);
    room.playerSockets.set(playerId, socket.id);
    socket.emit(SocketEvents.JOINED_GAME, { playerId, gameState: room.state });
  }
});
```

## Phase 5: Host Migration

If host disconnects, migrate to another player.

### Implementation
```typescript
handleDisconnect(socket) {
  if (room.hostSocketId === socket.id) {
    // Find new host
    const newHost = room.state.playerOrder.find(
      id => room.playerSockets.has(id) && !room.state.players[id].isBot
    );
    if (newHost) {
      room.hostSocketId = room.playerSockets.get(newHost)!;
      this.io.to(room.code).emit(SocketEvents.GAME_STATE, room.state);
    }
  }
}
```

## Phase 6: Turn Timeouts

Auto-end turn if player is idle too long.

### Timeouts
- Turn: 2 minutes
- Auction bid: 30 seconds
- Disconnect grace: 5 minutes

## Phase 7: Polish

- [ ] Sound effects
- [ ] Haptic feedback on controller
- [ ] Player avatars
- [ ] Game history/replay
- [ ] Spectator mode

---

# 🗂️ KEY FILES REFERENCE

## Controller App
| File | Purpose |
|------|---------|
| `src/hooks/useSocket.ts` | Socket connection, GAME_STATE listener |
| `src/contexts/AnimationContext.tsx` | Animation state (dice, movement) |
| `src/store/playerStore.ts` | Zustand store for game state |
| `src/screens/GameScreen.tsx` | Main gameplay UI |
| `src/components/ActionPanel.tsx` | Roll, buy, end turn buttons |

## TV Display
| File | Purpose |
|------|---------|
| `src/hooks/useSocket.ts` | Socket connection, GAME_STATE listener |
| `src/store/gameStore.ts` | Zustand store |
| `src/components/board/GameBoard.tsx` | Board rendering |
| `src/components/board/PlayerToken.tsx` | Token positions |

## Game Server
| File | Purpose |
|------|---------|
| `src/socket/RoomManager.ts` | Room/game management, all event handlers |
| `src/socket/SocketServer.ts` | Socket.IO setup, auth |
| `src/config/index.ts` | Server configuration |

## Game Engine
| File | Purpose |
|------|---------|
| `src/state/reducer.ts` | Pure game reducer |
| `src/state/types.ts` | GameState, PlayerState, etc. |
| `src/state/actions.ts` | Action types |

## Shared
| File | Purpose |
|------|---------|
| `src/index.ts` | SocketEvents enum, utilities |

---

# 🏗️ ARCHITECTURE PRINCIPLES

1. **Single Source of Truth** - `GAME_STATE` is the only event that updates state
2. **Separation of Concerns** - Animations separate from state
3. **Pure Game Logic** - Game engine is pure functions, no side effects
4. **Monorepo Benefits** - Shared types, single version control
5. **Jackbox Pattern** - TV as display, phones as controllers

---

# 📝 NOTES

## TypeScript Errors (Pre-existing, not blocking)
- `import.meta.env` - Vite env type issue (works at runtime)
- Various type mismatches in components (colorGroup, rent, etc.)

## Files Safe to Delete (Outside v2)
The old codebase outside `pinopoly-v2/` can be deleted:
- `/src/` - Old Python backend
- `/client/` - Old React frontend
- `/board_organized/` - Experimental frontend
- `/deployment/` - Old deployment scripts
- `/tests/` - Old Python tests
- `app.py`, `reset_database.py`, etc.
