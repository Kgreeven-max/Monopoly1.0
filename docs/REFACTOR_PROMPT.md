# Pinopoly V2 Architecture Refactor Prompt

Copy and paste this entire prompt to refactor your codebase.

---

## MASTER REFACTOR PROMPT

You are refactoring a Monopoly-style multiplayer game to use a Jackbox-inspired architecture. The goal is to fix persistent synchronization issues by implementing clear separation between TV displays and phone controllers, proper state versioning, action acknowledgments, and personalized state distribution.

## Project Context

This is a monorepo with the following structure:

```
/pinopoly-v2/
├── apps/
│   ├── controller/          # Phone/mobile controller app
│   ├── tv-display/          # TV/large screen display app
│   └── admin-console/       # Admin dashboard
├── packages/
│   ├── game-engine/         # Pure game logic (reducers, rules, state)
│   ├── shared/              # Shared types, enums, utilities
│   └── ui-components/       # Reusable React components
├── services/
│   └── game-server/         # Node.js/Express + Socket.IO backend
└── infra/                   # Docker, nginx, postgres configs
```

## Current Problems to Solve

1. **No client type distinction** - TV and phones are treated identically
2. **Full state broadcast** - Every client gets complete game state on every action
3. **No state versioning** - Messages can arrive out of order, causing desync
4. **No action acknowledgments** - UI updates before server confirms actions
5. **Race conditions** - Multiple socket handlers, unclear event flow

## Architecture to Implement

### The Three-Tier Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TARGET ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   TV DISPLAY              SERVER (BROKER)           PHONE CONTROLLER    │
│   ┌──────────────┐       ┌──────────────┐          ┌──────────────┐    │
│   │ Board view   │       │ RoomManager  │          │ Action panel │    │
│   │ All tokens   │◄─────►│ State store  │◄────────►│ Your money   │    │
│   │ Dice anim    │       │ Event router │          │ Your props   │    │
│   │ Public info  │       │ Validation   │          │ Mini board   │    │
│   │ QR code      │       │ Versioning   │          │ Your turn UI │    │
│   └──────────────┘       └──────────────┘          └──────────────┘    │
│                                                                         │
│   Receives:               Manages:                  Receives:           │
│   - display_update        - Game state             - player_update      │
│   - dice_result           - Room codes             - your_turn          │
│   - player_positions      - Client registry        - available_actions  │
│   - turn_change           - Message routing        - action_result      │
│                           - State versions                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## PHASE 1: Server-Side Changes

### File: `/services/game-server/src/socket/RoomManager.ts`

**Current state:** Handles socket events but broadcasts full state to all clients equally.

**Required changes:**

1. **Add client type registry:**

```typescript
interface ConnectedClient {
  socketId: string;
  odplayerId: string | null;
  clientType: 'display' | 'controller' | 'spectator';
  roomCode: string;
  lastStateVersion: number;
}

private clients: Map<string, ConnectedClient> = new Map();
```

2. **Add state versioning:**

```typescript
interface RoomState {
  gameState: GameState;
  stateVersion: number;  // ADD THIS
  lastUpdated: number;   // ADD THIS
}

// Increment on every state change
private incrementVersion(roomCode: string): number {
  const room = this.rooms.get(roomCode);
  if (room) {
    room.stateVersion = (room.stateVersion || 0) + 1;
    room.lastUpdated = Date.now();
    return room.stateVersion;
  }
  return 0;
}
```

3. **Implement client type registration:**

```typescript
// New socket event handler
socket.on('register_client', (data: {
  roomCode: string;
  clientType: 'display' | 'controller';
  playerId?: string;
}) => {
  this.clients.set(socket.id, {
    socketId: socket.id,
    playerId: data.playerId || null,
    clientType: data.clientType,
    roomCode: data.roomCode,
    lastStateVersion: 0
  });

  // Join appropriate rooms
  socket.join(data.roomCode);  // Main room
  socket.join(`${data.roomCode}_${data.clientType}s`);  // Type-specific room

  if (data.playerId) {
    socket.join(`player_${data.playerId}`);  // Personal room
  }

  // Send initial state based on client type
  if (data.clientType === 'display') {
    this.sendDisplayState(socket, data.roomCode);
  } else {
    this.sendPlayerState(socket, data.roomCode, data.playerId);
  }
});
```

4. **Create separate state builders:**

```typescript
private buildDisplayState(roomCode: string): DisplayState {
  const room = this.rooms.get(roomCode);
  if (!room) return null;

  const { gameState, stateVersion } = room;

  return {
    version: stateVersion,
    timestamp: Date.now(),
    board: {
      spaces: gameState.board.spaces,
      propertyOwnership: gameState.board.spaces.map(s => ({
        spaceId: s.id,
        ownerId: s.ownerId,
        houses: s.houses,
        hotel: s.hotel,
        isMortgaged: s.isMortgaged
      }))
    },
    players: gameState.players.map(p => ({
      id visita: p.id,
      name: p.name,
      token: p.token,
      color: p.color,
      position: p.position,
      isInJail: p.isInJail,
      isBankrupt: p.isBankrupt,
      isBot: p.isBot,
      // PUBLIC info only - not detailed money/cards
      moneyRange: this.getMoneyRange(p.money), // "low", "medium", "high"
    })),
    currentPlayerId: gameState.currentPlayerId,
    turnPhase: gameState.turnPhase,
    diceResult: gameState.lastDiceRoll,
    gamePhase: gameState.phase,
    roomCode: roomCode
  };
}

private buildPlayerState(roomCode: string, playerId: string): PlayerState {
  const room = this.rooms.get(roomCode);
  if (!room) return null;

  const { gameState, stateVersion } = room;
  const player = gameState.players.find(p => p.id === playerId);
  if (!player) return null;

  const isYourTurn = gameState.currentPlayerId === playerId;

  return {
    version: stateVersion,
    timestamp: Date.now(),
    you: {
      id: player.id,
      name: player.name,
      money: player.money,  // YOUR exact money
      position: player.position,
      properties: player.properties,  // YOUR properties with full details
      cards: player.cards,  // YOUR cards (others can't see)
      isInJail: player.isInJail,
      jailTurns: player.jailTurns,
      getOutOfJailCards: player.getOutOfJailCards
    },
    isYourTurn: isYourTurn,
    availableActions: isYourTurn ? this.getAvailableActions(gameState, player) : [],
    turnPhase: gameState.turnPhase,
    gamePhase: gameState.phase,
    // Summary of other players (not full details)
    otherPlayers: gameState.players
      .filter(p => p.id !== playerId)
      .map(p => ({
        id: p.id,
        name: p.name,
        position: p.position,
        propertyCount: p.properties.length,
        isBankrupt: p.isBankrupt
      }))
  };
}

private getAvailableActions(gameState: GameState, player: Player): Action[] {
  const actions: Action[] = [];

  switch (gameState.turnPhase) {
    case 'pre_roll':
      actions.push({ type: 'roll_dice', label: 'Roll Dice' });
      if (player.getOutOfJailCards > 0 && player.isInJail) {
        actions.push({ type: 'use_jail_card', label: 'Use Get Out of Jail Card' });
      }
      break;
    case 'post_roll':
      const currentSpace = gameState.board.spaces[player.position];
      if (currentSpace.type === 'property' && !currentSpace.ownerId) {
        actions.push({ type: 'buy_property', label: `Buy ${currentSpace.name}`, data: { propertyId: currentSpace.id, price: currentSpace.price } });
        actions.push({ type: 'auction_property', label: 'Start Auction' });
      }
      actions.push({ type: 'end_turn', label: 'End Turn' });
      break;
    case 'awaiting_payment':
      actions.push({ type: 'pay', label: `Pay $${gameState.pendingPayment?.amount}` });
      if (player.properties.length > 0) {
        actions.push({ type: 'mortgage', label: 'Mortgage Property' });
      }
      break;
    // Add more phases as needed
  }

  // Always available actions
  if (player.properties.length > 0) {
    actions.push({ type: 'manage_properties', label: 'Manage Properties' });
  }
  actions.push({ type: 'trade', label: 'Propose Trade' });

  return actions;
}
```

5. **Replace broadcast with targeted emissions:**

```typescript
// OLD - Don't do this
private broadcastGameState(roomCode: string) {
  const state = this.rooms.get(roomCode)?.gameState;
  this.io.to(roomCode).emit('game_state', state);  // BAD: Everyone gets everything
}

// NEW - Do this instead
private broadcastUpdates(roomCode: string) {
  const version = this.incrementVersion(roomCode);

  // Send to TV displays
  const displayState = this.buildDisplayState(roomCode);
  this.io.to(`${roomCode}_displays`).emit('display_update', displayState);

  // Send to each player's phone
  const room = this.rooms.get(roomCode);
  if (room) {
    room.gameState.players.forEach(player => {
      if (!player.isBot) {
        const playerState = this.buildPlayerState(roomCode, player.id visita);
        this.io.to(`player_${player.id}`).emit('player_update', playerState);
      }
    });
  }
}
```

6. **Implement action acknowledgments:**

```typescript
socket.on('player_action', async (data: {
  action: string;
  playerId: string;
  payload?: any;
}, callback: (response: ActionResponse) => void) => {
  try {
    // Validate the action is legal
    const validation = this.validateAction(data);
    if (!validation.valid) {
      callback({
        success: false,
        error: validation.error,
        errorCode: validation.errorCode
      });
      return;
    }

    // Execute the action
    const result = this.executeAction(data);

    // Acknowledge success to the sender
    callback({
      success: true,
      result: result,
      newVersion: this.rooms.get(data.roomCode)?.stateVersion
    });

    // Broadcast updates to all clients
    this.broadcastUpdates(data.roomCode);

  } catch (error) {
    callback({
      success: false,
      error: 'Server error processing action',
      errorCode: 'SERVER_ERROR'
    });
  }
});
```

### File: `/services/game-server/src/socket/SocketServer.ts`

**Add room/client cleanup:**

```typescript
io.on('connection', (socket) => {
  console.log(`Client connected: ${socket.id}`);

  socket.on('disconnect', () => {
    const client = this.roomManager.getClient(socket.id);
    if (client) {
      // Handle based on client type
      if (client.clientType === 'controller' && client.playerId) {
        // Start reconnection timer for players
        this.roomManager.startReconnectionTimer(client.playerId, 60000);
      } else if (client.clientType === 'display') {
        // TV disconnected - notify players
        this.roomManager.notifyDisplayDisconnected(client.roomCode);
      }
      this.roomManager.removeClient(socket.id);
    }
  });
});
```

### File: `/packages/shared/src/index.ts`

**Add new event types:**

```typescript
export enum SocketEvents {
  // Connection events
  REGISTER_CLIENT = 'register_client',
  CLIENT_REGISTERED = 'client_registered',

  // State events (versioned)
  DISPLAY_UPDATE = 'display_update',
  PLAYER_UPDATE = 'player_update',

  // Action events (with acknowledgment)
  PLAYER_ACTION = 'player_action',
  ACTION_RESULT = 'action_result',

  // Game flow events
  TURN_STARTED = 'turn_started',
  TURN_ENDED = 'turn_ended',
  DICE_ROLLED = 'dice_rolled',
  PLAYER_MOVED = 'player_moved',

  // Room events
  PLAYER_JOINED = 'player_joined',
  PLAYER_LEFT = 'player_left',
  PLAYER_RECONNECTED = 'player_reconnected',
  PLAYER_DISCONNECTED = 'player_disconnected',
  GAME_STARTED = 'game_started',
  GAME_ENDED = 'game_ended',

  // Error events
  ERROR = 'error',
  INVALID_ACTION = 'invalid_action',

  // Legacy (deprecate these)
  GAME_STATE = 'game_state',  // @deprecated - use DISPLAY_UPDATE and PLAYER_UPDATE
}

export interface DisplayState {
  version: number;
  timestamp: number;
  board: BoardState;
  players: PublicPlayerInfo[];
  currentPlayerId: string;
  turnPhase: TurnPhase;
  diceResult: [number, number] | null;
  gamePhase: GamePhase;
  roomCode: string;
}

export interface PlayerState {
  version: number;
  timestamp: number;
  you: PrivatePlayerInfo;
  isYourTurn: boolean;
  availableActions: Action[];
  turnPhase: TurnPhase;
  gamePhase: GamePhase;
  otherPlayers: PublicPlayerInfo[];
}

export interface Action {
  type: string;
  label: string;
  data?: Record<string, any>;
  disabled?: boolean;
  disabledReason?: string;
}

export interface ActionResponse {
  success: boolean;
  result?: any;
  newVersion?: number;
  error?: string;
  errorCode?: string;
}

export type ClientType = 'display' | 'controller' | 'spectator';
```

---

## PHASE 2: TV Display App Changes

### File: `/apps/tv-display/src/hooks/useSocket.ts`

**Refactor for display-specific events:**

```typescript
import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { SocketEvents, DisplayState } from '@pinopoly/shared';
import { useGameStore } from '../store/gameStore';

export function useSocket(roomCode: string | null) {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastVersion, setLastVersion] = useState(0);

  const {
    setDisplayState,
    setPlayers,
    setCurrentPlayer,
    setDiceResult,
    addToEventLog
  } = useGameStore();

  useEffect(() => {
    if (!roomCode) return;

    const socket = io(import.meta.env.VITE_WS_URL || 'http://localhost:3000', {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      setIsConnected(true);

      // Register as display client
      socket.emit(SocketEvents.REGISTER_CLIENT, {
        roomCode,
        clientType: 'display'
      });
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    // Handle display-specific updates
    socket.on(SocketEvents.DISPLAY_UPDATE, (state: DisplayState) => {
      // Ignore stale updates
      if (state.version <= lastVersion) {
        console.log(`Ignoring stale update: ${state.version} <= ${lastVersion}`);
        return;
      }

      setLastVersion(state.version);
      setDisplayState(state);
    });

    // Handle specific events for animations
    socket.on(SocketEvents.DICE_ROLLED, (data: {
      playerId: string;
      dice: [number, number];
      version: number;
    }) => {
      if (data.version <= lastVersion) return;
      setDiceResult(data.dice);
      addToEventLog(`${data.playerId} rolled ${data.dice[0]} + ${data.dice[1]}`);
    });

    socket.on(SocketEvents.PLAYER_MOVED, (data: {
      playerId: string;
      from: number;
      to: number;
      passedGo: boolean;
      version: number;
    }) => {
      if (data.version <= lastVersion) return;
      // Trigger movement animation
      // The display state will update positions, animation system picks it up
      if (data.passedGo) {
        addToEventLog(`${data.playerId} passed GO!`);
      }
    });

    socket.on(SocketEvents.PLAYER_JOINED, (data: { player: PublicPlayerInfo }) => {
      addToEventLog(`${data.player.name} joined the game`);
    });

    socket.on(SocketEvents.PLAYER_DISCONNECTED, (data: { playerId: string; playerName: string }) => {
      addToEventLog(`${data.playerName} disconnected`);
    });

    socket.on(SocketEvents.PLAYER_RECONNECTED, (data: { playerId: string; playerName: string }) => {
      addToEventLog(`${data.playerName} reconnected`);
    });

    socket.on(SocketEvents.GAME_STARTED, () => {
      addToEventLog('Game started!');
    });

    socket.on(SocketEvents.GAME_ENDED, (data: { winnerId: string; winnerName: string }) => {
      addToEventLog(`Game over! ${data.winnerName} wins!`);
    });

    return () => {
      socket.disconnect();
    };
  }, [roomCode]);

  return {
    socket: socketRef.current,
    isConnected,
    stateVersion: lastVersion
  };
}
```

### File: `/apps/tv-display/src/store/gameStore.ts`

**Update store for display-specific state:**

```typescript
import { create } from 'zustand';
import { DisplayState, PublicPlayerInfo } from '@pinopoly/shared';

interface GameStore {
  // Connection state
  roomCode: string | null;
  isConnected: boolean;
  stateVersion: number;

  // Display state
  displayState: DisplayState | null;
  players: PublicPlayerInfo[];
  currentPlayerId: string | null;
  diceResult: [number, number] | null;
  turnPhase: string;
  gamePhase: string;

  // Event log
  eventLog: EventLogEntry[];

  // Actions
  setRoomCode: (code: string) => void;
  setConnected: (connected: boolean) => void;
  setDisplayState: (state: DisplayState) => void;
  setDiceResult: (dice: [number, number] | null) => void;
  addToEventLog: (message: string) => void;
  clearEventLog: () => void;
  reset: () => void;
}

interface EventLogEntry {
  id: string;
  message: string;
  timestamp: number;
}

export const useGameStore = create<GameStore>((set, get) => ({
  roomCode: null,
  isConnected: false,
  stateVersion: 0,
  displayState: null,
  players: [],
  currentPlayerId: null,
  diceResult: null,
  turnPhase: 'waiting',
  gamePhase: 'lobby',
  eventLog: [],

  setRoomCode: (code) => set({ roomCode: code }),

  setConnected: (connected) => set({ isConnected: connected }),

  setDisplayState: (state) => {
    // Only update if newer version
    if (state.version <= get().stateVersion) return;

    set({
      stateVersion: state.version,
      displayState: state,
      players: state.players,
      currentPlayerId: state.currentPlayerId,
      diceResult: state.diceResult,
      turnPhase: state.turnPhase,
      gamePhase: state.gamePhase,
    });
  },

  setDiceResult: (dice) => set({ diceResult: dice }),

  addToEventLog: (message) => set((state) => ({
    eventLog: [
      { id: crypto.randomUUID(), message, timestamp: Date.now() },
      ...state.eventLog.slice(0, 49)  // Keep last 50 entries
    ]
  })),

  clearEventLog: () => set({ eventLog: [] }),

  reset: () => set({
    roomCode: null,
    isConnected: false,
    stateVersion: 0,
    displayState: null,
    players: [],
    currentPlayerId: null,
    diceResult: null,
    turnPhase: 'waiting',
    gamePhase: 'lobby',
    eventLog: [],
  }),
}));
```

### File: `/apps/tv-display/src/screens/GameScreen.tsx`

**Simplify to display-only concerns:**

```typescript
import React from 'react';
import { useGameStore } from '../store/gameStore';
import { GameBoard } from '../components/board/GameBoard';
import { PlayerPanel } from '../components/PlayerPanel';
import { DiceDisplay } from '../components/DiceDisplay';
import { TurnIndicator } from '../components/TurnIndicator';
import { EventLog } from '../components/EventLog';
import { QRCode } from '../components/QRCode';

export function GameScreen() {
  const {
    displayState,
    players,
    currentPlayerId,
    diceResult,
    turnPhase,
    roomCode,
    eventLog
  } = useGameStore();

  if (!displayState) {
    return <div className="loading">Loading game...</div>;
  }

  const currentPlayer = players.find(p => p.id === currentPlayerId);

  return (
    <div className="game-screen">
      {/* Main board area */}
      <div className="board-container">
        <GameBoard
          spaces={displayState.board.spaces}
          players={players}
          propertyOwnership={displayState.board.propertyOwnership}
        />
      </div>

      {/* Side panel */}
      <div className="side-panel">
        <TurnIndicator
          currentPlayer={currentPlayer}
          turnPhase={turnPhase}
        />

        <DiceDisplay
          result={diceResult}
          isRolling={turnPhase === 'rolling'}
        />

        <PlayerPanel players={players} currentPlayerId={currentPlayerId} />

        <EventLog entries={eventLog} />

        {/* QR code for easy joining */}
        <div className="join-info">
          <QRCode value={`https://play.pinopoly.com/join/${roomCode}`} size={100} />
          <div className="room-code">Room: {roomCode}</div>
        </div>
      </div>
    </div>
  );
}
```

---

## PHASE 3: Phone Controller App Changes

### File: `/apps/controller/src/hooks/useSocket.ts`

**Refactor for player-specific events with acknowledgments:**

```typescript
import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { SocketEvents, PlayerState, ActionResponse } from '@pinopoly/shared';
import { usePlayerStore } from '../store/playerStore';

export function useSocket() {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastVersion, setLastVersion] = useState(0);
  const [pendingAction, setPendingAction] = useState<string | null>(null);

  const {
    roomCode,
    playerId,
    setPlayerState,
    setYourTurn,
    setAvailableActions,
    setError,
  } = usePlayerStore();

  // Send action with acknowledgment
  const sendAction = useCallback((action: string, payload?: any): Promise<ActionResponse> => {
    return new Promise((resolve, reject) => {
      if (!socketRef.current?.connected) {
        reject({ success: false, error: 'Not connected' });
        return;
      }

      setPendingAction(action);

      socketRef.current.emit(
        SocketEvents.PLAYER_ACTION,
        { action, playerId, roomCode, payload },
        (response: ActionResponse) => {
          setPendingAction(null);

          if (response.success) {
            resolve(response);
          } else {
            setError(response.error || 'Action failed');
            reject(response);
          }
        }
      );

      // Timeout after 10 seconds
      setTimeout(() => {
        if (pendingAction === action) {
          setPendingAction(null);
          reject({ success: false, error: 'Action timed out' });
        }
      }, 10000);
    });
  }, [playerId, roomCode, pendingAction]);

  useEffect(() => {
    if (!roomCode || !playerId) return;

    const socket = io(import.meta.env.VITE_WS_URL || 'http://localhost:3000', {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      setIsConnected(true);

      // Register as controller client
      socket.emit(SocketEvents.REGISTER_CLIENT, {
        roomCode,
        clientType: 'controller',
        playerId
      });
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    // Handle player-specific updates
    socket.on(SocketEvents.PLAYER_UPDATE, (state: PlayerState) => {
      // Ignore stale updates
      if (state.version <= lastVersion) {
        console.log(`Ignoring stale update: ${state.version} <= ${lastVersion}`);
        return;
      }

      setLastVersion(state.version);
      setPlayerState(state);
      setYourTurn(state.isYourTurn);
      setAvailableActions(state.availableActions);
    });

    // Handle turn notifications
    socket.on(SocketEvents.TURN_STARTED, (data: { playerId: string }) => {
      if (data.playerId === playerId) {
        // Vibrate phone when it's your turn
        if (navigator.vibrate) {
          navigator.vibrate([200, 100, 200]);
        }
      }
    });

    socket.on(SocketEvents.ERROR, (error: { message: string; code: string }) => {
      setError(error.message);
    });

    return () => {
      socket.disconnect();
    };
  }, [roomCode, playerId]);

  return {
    socket: socketRef.current,
    isConnected,
    sendAction,
    pendingAction,
    stateVersion: lastVersion
  };
}
```

### File: `/apps/controller/src/store/playerStore.ts`

**Update store for player-specific state:**

```typescript
import { create } from 'zustand';
import { PlayerState, Action, PrivatePlayerInfo } from '@pinopoly/shared';

interface PlayerStore {
  // Connection state
  roomCode: string | null;
  playerId: string | null;
  playerName: string | null;
  isConnected: boolean;
  stateVersion: number;

  // Player state
  playerState: PlayerState | null;
  you: PrivatePlayerInfo | null;
  isYourTurn: boolean;
  availableActions: Action[];
  turnPhase: string;
  gamePhase: string;

  // UI state
  error: string | null;
  pendingAction: string | null;

  // Actions
  setRoomCode: (code: string) => void;
  setPlayerId: (id: string) => void;
  setPlayerName: (name: string) => void;
  setConnected: (connected: boolean) => void;
  setPlayerState: (state: PlayerState) => void;
  setYourTurn: (isYourTurn: boolean) => void;
  setAvailableActions: (actions: Action[]) => void;
  setError: (error: string | null) => void;
  setPendingAction: (action: string | null) => void;
  reset: () => void;
}

export const usePlayerStore = create<PlayerStore>((set, get) => ({
  roomCode: null,
  playerId: null,
  playerName: null,
  isConnected: false,
  stateVersion: 0,
  playerState: null,
  you: null,
  isYourTurn: false,
  availableActions: [],
  turnPhase: 'waiting',
  gamePhase: 'lobby',
  error: null,
  pendingAction: null,

  setRoomCode: (code) => set({ roomCode: code.toUpperCase() }),

  setPlayerId: (id) => set({ playerId: id }),

  setPlayerName: (name) => set({ playerName: name }),

  setConnected: (connected) => set({ isConnected: connected }),

  setPlayerState: (state) => {
    // Only update if newer version
    if (state.version <= get().stateVersion) return;

    set({
      stateVersion: state.version,
      playerState: state,
      you: state.you,
      isYourTurn: state.isYourTurn,
      availableActions: state.availableActions,
      turnPhase: state.turnPhase,
      gamePhase: state.gamePhase,
    });
  },

  setYourTurn: (isYourTurn) => set({ isYourTurn }),

  setAvailableActions: (actions) => set({ availableActions: actions }),

  setError: (error) => set({ error }),

  setPendingAction: (action) => set({ pendingAction: action }),

  reset: () => set({
    roomCode: null,
    playerId: null,
    playerName: null,
    isConnected: false,
    stateVersion: 0,
    playerState: null,
    you: null,
    isYourTurn: false,
    availableActions: [],
    turnPhase: 'waiting',
    gamePhase: 'lobby',
    error: null,
    pendingAction: null,
  }),
}));
```

### File: `/apps/controller/src/screens/GameScreen.tsx`

**Simplify to action-focused controller:**

```typescript
import React from 'react';
import { usePlayerStore } from '../store/playerStore';
import { useSocket } from '../hooks/useSocket';
import { ActionPanel } from '../components/ActionPanel';
import { StatusBar } from '../components/StatusBar';
import { PropertySheet } from '../components/PropertySheet';
import { MiniBoard } from '../components/MiniBoard';  // Optional mini board view
import { WaitingOverlay } from '../components/WaitingOverlay';

export function GameScreen() {
  const {
    you,
    isYourTurn,
    availableActions,
    turnPhase,
    gamePhase,
    playerState,
    error
  } = usePlayerStore();

  const { sendAction, pendingAction, isConnected } = useSocket();

  if (!you || !playerState) {
    return <div className="loading">Connecting to game...</div>;
  }

  const handleAction = async (actionType: string, payload?: any) => {
    try {
      await sendAction(actionType, payload);
    } catch (err) {
      console.error('Action failed:', err);
    }
  };

  return (
    <div className="controller-screen">
      {/* Status bar at top */}
      <StatusBar
        money={you.money}
        propertyCount={you.properties.length}
        isConnected={isConnected}
      />

      {/* Main content area */}
      <div className="main-content">
        {isYourTurn ? (
          <ActionPanel
            actions={availableActions}
            onAction={handleAction}
            pendingAction={pendingAction}
            turnPhase={turnPhase}
          />
        ) : (
          <WaitingOverlay
            message="Waiting for other players..."
            currentPlayerName={playerState.otherPlayers.find(
              p => p.id === playerState.currentPlayerId
            )?.name}
          />
        )}
      </div>

      {/* Optional: Mini board view (collapsible) */}
      <MiniBoard
        players={[you, ...playerState.otherPlayers]}
        yourPosition={you.position}
      />

      {/* Property management sheet (slides up) */}
      <PropertySheet
        properties={you.properties}
        onMortgage={(propId) => handleAction('mortgage', { propertyId: propId })}
        onUnmortgage={(propId) => handleAction('unmortgage', { propertyId: propId })}
        onBuildHouse={(propId) => handleAction('build_house', { propertyId: propId })}
      />

      {/* Error display */}
      {error && (
        <div className="error-toast">{error}</div>
      )}
    </div>
  );
}
```

### File: `/apps/controller/src/components/ActionPanel.tsx`

**Clean action button component:**

```typescript
import React from 'react';
import { Action } from '@pinopoly/shared';
import { DiceButton } from './DiceButton';

interface ActionPanelProps {
  actions: Action[];
  onAction: (actionType: string, payload?: any) => void;
  pendingAction: string | null;
  turnPhase: string;
}

export function ActionPanel({ actions, onAction, pendingAction, turnPhase }: ActionPanelProps) {
  // Group actions by type
  const primaryActions = actions.filter(a =>
    ['roll_dice', 'buy_property', 'end_turn', 'pay'].includes(a.type)
  );
  const secondaryActions = actions.filter(a =>
    ['auction_property', 'mortgage', 'trade', 'manage_properties'].includes(a.type)
  );

  return (
    <div className="action-panel">
      <div className="turn-status">
        <h2>Your Turn!</h2>
        <p className="phase-hint">{getPhaseHint(turnPhase)}</p>
      </div>

      {/* Primary actions - big buttons */}
      <div className="primary-actions">
        {primaryActions.map(action => (
          action.type === 'roll_dice' ? (
            <DiceButton
              key={action.type}
              onClick={() => onAction(action.type)}
              disabled={pendingAction !== null || action.disabled}
              loading={pendingAction === action.type}
            />
          ) : (
            <button
              key={action.type}
              className={`action-btn primary ${action.type}`}
              onClick={() => onAction(action.type, action.data)}
              disabled={pendingAction !== null || action.disabled}
            >
              {pendingAction === action.type ? 'Processing...' : action.label}
            </button>
          )
        ))}
      </div>

      {/* Secondary actions - smaller buttons */}
      {secondaryActions.length > 0 && (
        <div className="secondary-actions">
          {secondaryActions.map(action => (
            <button
              key={action.type}
              className="action-btn secondary"
              onClick={() => onAction(action.type, action.data)}
              disabled={pendingAction !== null || action.disabled}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function getPhaseHint(turnPhase: string): string {
  switch (turnPhase) {
    case 'pre_roll':
      return 'Roll the dice to move';
    case 'post_roll':
      return 'Decide what to do with this property';
    case 'awaiting_payment':
      return 'You need to pay rent';
    case 'in_jail':
      return 'Try to get out of jail';
    default:
      return '';
  }
}
```

---

## PHASE 4: Join Flow Refactor

### File: `/apps/controller/src/screens/JoinScreen.tsx`

**Simple room code entry:**

```typescript
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePlayerStore } from '../store/playerStore';

export function JoinScreen() {
  const [roomCode, setRoomCode] = useState('');
  const [playerName, setPlayerName] = useState('');
  const [error, setError] = useState('');
  const [isJoining, setIsJoining] = useState(false);

  const { setRoomCode: storeRoomCode, setPlayerName: storePlayerName } = usePlayerStore();
  const navigate = useNavigate();

  const handleJoin = async () => {
    if (roomCode.length !== 4) {
      setError('Room code must be 4 characters');
      return;
    }
    if (playerName.trim().length < 2) {
      setError('Please enter your name');
      return;
    }

    setIsJoining(true);
    setError('');

    try {
      // Validate room exists
      const response = await fetch(`/api/rooms/${roomCode.toUpperCase()}/validate`);
      const data = await response.json();

      if (!data.valid) {
        setError(data.error || 'Room not found');
        setIsJoining(false);
        return;
      }

      // Store and navigate
      storeRoomCode(roomCode.toUpperCase());
      storePlayerName(playerName.trim());
      navigate('/lobby');

    } catch (err) {
      setError('Could not connect to server');
      setIsJoining(false);
    }
  };

  return (
    <div className="join-screen">
      <h1>Join Game</h1>

      <div className="input-group">
        <label>Room Code</label>
        <input
          type="text"
          value={roomCode}
          onChange={(e) => setRoomCode(e.target.value.toUpperCase().slice(0, 4))}
          placeholder="ABCD"
          maxLength={4}
          className="room-code-input"
          autoCapitalize="characters"
          autoComplete="off"
        />
      </div>

      <div className="input-group">
        <label>Your Name</label>
        <input
          type="text"
          value={playerName}
          onChange={(e) => setPlayerName(e.target.value)}
          placeholder="Enter your name"
          maxLength={20}
        />
      </div>

      {error && <div className="error-message">{error}</div>}

      <button
        onClick={handleJoin}
        disabled={isJoining || roomCode.length !== 4}
        className="join-button"
      >
        {isJoining ? 'Joining...' : 'Join Game'}
      </button>
    </div>
  );
}
```

### File: `/apps/tv-display/src/screens/WelcomeScreen.tsx`

**TV creates room and shows code:**

```typescript
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import { QRCode } from '../components/QRCode';

export function WelcomeScreen() {
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState('');
  const { roomCode, setRoomCode } = useGameStore();
  const navigate = useNavigate();

  const createRoom = async () => {
    setIsCreating(true);
    setError('');

    try {
      const response = await fetch('/api/rooms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hostType: 'display' })
      });

      const data = await response.json();

      if (data.roomCode) {
        setRoomCode(data.roomCode);
      } else {
        setError('Failed to create room');
      }
    } catch (err) {
      setError('Could not connect to server');
    } finally {
      setIsCreating(false);
    }
  };

  useEffect(() => {
    // Auto-create room on mount
    if (!roomCode) {
      createRoom();
    }
  }, []);

  if (!roomCode) {
    return (
      <div className="welcome-screen loading">
        {isCreating ? 'Creating room...' : error || 'Initializing...'}
        {error && <button onClick={createRoom}>Try Again</button>}
      </div>
    );
  }

  const joinUrl = `https://play.pinopoly.com/join/${roomCode}`;

  return (
    <div className="welcome-screen">
      <h1>Pinopoly</h1>

      <div className="join-instructions">
        <div className="qr-section">
          <QRCode value={joinUrl} size={200} />
          <p>Scan to join</p>
        </div>

        <div className="code-section">
          <p>Or go to <strong>play.pinopoly.com</strong></p>
          <div className="room-code-display">{roomCode}</div>
        </div>
      </div>

      <div className="waiting-message">
        Waiting for players to join...
      </div>
    </div>
  );
}
```

---

## PHASE 5: Message Protocol Types

### File: `/packages/shared/src/protocol.ts`

**Complete message protocol definitions:**

```typescript
// ============================================
// CLIENT → SERVER MESSAGES
// ============================================

export interface RegisterClientMessage {
  type: 'register_client';
  roomCode: string;
  clientType: 'display' | 'controller' | 'spectator';
  playerId?: string;
  playerName?: string;
}

export interface PlayerActionMessage {
  type: 'player_action';
  roomCode: string;
  playerId: string;
  action: ActionType;
  payload?: Record<string, any>;
}

export type ActionType =
  | 'roll_dice'
  | 'buy_property'
  | 'auction_property'
  | 'end_turn'
  | 'pay'
  | 'mortgage'
  | 'unmortgage'
  | 'build_house'
  | 'sell_house'
  | 'trade_propose'
  | 'trade_accept'
  | 'trade_reject'
  | 'use_jail_card'
  | 'pay_jail_fine'
  | 'auction_bid'
  | 'declare_bankruptcy';

// ============================================
// SERVER → CLIENT MESSAGES (Display)
// ============================================

export interface DisplayUpdateMessage {
  type: 'display_update';
  version: number;
  timestamp: number;
  payload: DisplayState;
}

export interface DisplayState {
  roomCode: string;
  gamePhase: GamePhase;
  board: {
    spaces: BoardSpace[];
    propertyOwnership: PropertyOwnership[];
  };
  players: PublicPlayerInfo[];
  currentPlayerId: string | null;
  turnPhase: TurnPhase;
  diceResult: [number, number] | null;
  auction: AuctionState | null;
  trade: TradeState | null;
}

// ============================================
// SERVER → CLIENT MESSAGES (Controller)
// ============================================

export interface PlayerUpdateMessage {
  type: 'player_update';
  version: number;
  timestamp: number;
  payload: PlayerState;
}

export interface PlayerState {
  you: PrivatePlayerInfo;
  isYourTurn: boolean;
  availableActions: AvailableAction[];
  gamePhase: GamePhase;
  turnPhase: TurnPhase;
  otherPlayers: PublicPlayerInfo[];
  pendingPayment: PendingPayment | null;
  currentAuction: PlayerAuctionView | null;
  incomingTrade: IncomingTradeView | null;
}

// ============================================
// DATA TYPES
// ============================================

export type GamePhase = 'lobby' | 'playing' | 'paused' | 'ended';

export type TurnPhase =
  | 'pre_roll'
  | 'rolling'
  | 'moving'
  | 'post_roll'
  | 'awaiting_payment'
  | 'in_auction'
  | 'in_trade'
  | 'in_jail'
  | 'bankrupt';

export interface PublicPlayerInfo {
  id: string;
  name: string;
  token: string;
  color: string;
  position: number;
  isInJail: boolean;
  isBankrupt: boolean;
  isBot: boolean;
  isConnected: boolean;
  propertyCount: number;
  // Approximate wealth indicator (not exact amount)
  wealthLevel: 'broke' | 'low' | 'medium' | 'high' | 'rich';
}

export interface PrivatePlayerInfo {
  id: string;
  name: string;
  token: string;
  color: string;
  position: number;
  money: number;  // Exact amount (only you can see)
  properties: OwnedProperty[];
  cards: Card[];  // Your cards (others can't see)
  isInJail: boolean;
  jailTurns: number;
  getOutOfJailCards: number;
  loans: Loan[];
  netWorth: number;
}

export interface AvailableAction {
  type: ActionType;
  label: string;
  description?: string;
  data?: Record<string, any>;
  disabled?: boolean;
  disabledReason?: string;
}

export interface ActionResponse {
  success: boolean;
  newVersion?: number;
  result?: any;
  error?: string;
  errorCode?: ErrorCode;
}

export type ErrorCode =
  | 'NOT_YOUR_TURN'
  | 'INVALID_ACTION'
  | 'INSUFFICIENT_FUNDS'
  | 'PROPERTY_NOT_AVAILABLE'
  | 'ALREADY_OWNED'
  | 'INVALID_TRADE'
  | 'GAME_NOT_FOUND'
  | 'PLAYER_NOT_FOUND'
  | 'SERVER_ERROR';

// ============================================
// EVENT MESSAGES (Broadcast to relevant clients)
// ============================================

export interface DiceRolledEvent {
  type: 'dice_rolled';
  version: number;
  playerId: string;
  playerName: string;
  dice: [number, number];
  total: number;
  isDoubles: boolean;
}

export interface PlayerMovedEvent {
  type: 'player_moved';
  version: number;
  playerId: string;
  from: number;
  to: number;
  path: number[];  // For animation
  passedGo: boolean;
}

export interface PropertyPurchasedEvent {
  type: 'property_purchased';
  version: number;
  playerId: string;
  playerName: string;
  propertyId: number;
  propertyName: string;
  price: number;
}

export interface RentPaidEvent {
  type: 'rent_paid';
  version: number;
  payerId: string;
  payerName: string;
  ownerId: string;
  ownerName: string;
  propertyName: string;
  amount: number;
}

export interface PlayerBankruptEvent {
  type: 'player_bankrupt';
  version: number;
  playerId: string;
  playerName: string;
}

export interface GameEndedEvent {
  type: 'game_ended';
  version: number;
  winnerId: string;
  winnerName: string;
  finalStandings: Array<{
    playerId: string;
    playerName: string;
    netWorth: number;
    position: number;
  }>;
}
```

---

## VALIDATION CHECKLIST

After implementing these changes, verify:

### Server-Side
- [ ] Clients register with type ('display' | 'controller')
- [ ] Each client type joins appropriate rooms
- [ ] State version increments on every change
- [ ] Display clients receive `display_update` events only
- [ ] Controller clients receive `player_update` events only
- [ ] Actions use callback acknowledgment pattern
- [ ] Stale state updates are rejected (version check)
- [ ] Disconnection/reconnection handles both client types

### TV Display
- [ ] Registers as 'display' client type
- [ ] Only subscribes to display events
- [ ] Shows public information only
- [ ] Displays QR code and room code for joining
- [ ] Animations work from display state updates
- [ ] Does not show action buttons (display only)

### Phone Controller
- [ ] Registers as 'controller' client type
- [ ] Only subscribes to player-specific events
- [ ] Shows YOUR money, properties, cards
- [ ] Shows available actions when it's your turn
- [ ] Shows waiting state when it's not your turn
- [ ] Actions wait for server acknowledgment
- [ ] Vibrates/notifies when turn starts

### Message Protocol
- [ ] All messages include version number
- [ ] All messages include timestamp
- [ ] Actions return success/failure response
- [ ] Error responses include error codes
- [ ] State updates are idempotent (same version = no change)

---

## QUICK REFERENCE: Key Files to Modify

```
MUST CHANGE:
├── services/game-server/src/socket/RoomManager.ts   ← Client registry, state builders, targeted emissions
├── services/game-server/src/socket/SocketServer.ts  ← Connection handling, cleanup
├── packages/shared/src/index.ts                     ← Event enums, type definitions
├── apps/tv-display/src/hooks/useSocket.ts           ← Display-specific socket handling
├── apps/tv-display/src/store/gameStore.ts           ← Display state management
├── apps/controller/src/hooks/useSocket.ts           ← Player-specific socket with ACKs
├── apps/controller/src/store/playerStore.ts         ← Player state management
├── apps/controller/src/screens/GameScreen.tsx       ← Action-focused UI
├── apps/controller/src/components/ActionPanel.tsx   ← Action buttons

SHOULD CHANGE:
├── apps/tv-display/src/screens/GameScreen.tsx       ← Simplified display
├── apps/tv-display/src/screens/WelcomeScreen.tsx    ← Room creation + QR
├── apps/controller/src/screens/JoinScreen.tsx       ← Room code entry
├── apps/controller/src/screens/LobbyScreen.tsx      ← Pre-game waiting

NEW FILES TO CREATE:
├── packages/shared/src/protocol.ts                  ← Message protocol types
├── apps/controller/src/components/WaitingOverlay.tsx
├── apps/controller/src/components/MiniBoard.tsx     ← Optional mini board
├── apps/tv-display/src/components/QRCode.tsx        ← QR code generator
```

---

## SUCCESS CRITERIA

The refactor is complete when:

1. **TV creates room** → Shows room code and QR → Players scan/type to join
2. **Phones join** → Enter code → See lobby → Ready up
3. **Game starts** → TV shows board, phones show controls
4. **During play** → Only current player sees action buttons
5. **Actions acknowledged** → UI waits for server confirmation
6. **State versioned** → Out-of-order messages ignored
7. **Disconnect/reconnect** → Players can rejoin, game continues
8. **No desync** → All clients show consistent state

---

END OF PROMPT
