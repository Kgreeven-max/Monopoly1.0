# Pinopoly V2 Comprehensive Testing & Fixing Plan

## Overview
This plan covers testing and fixing EVERY user flow, button, and interaction in the Pinopoly v2 game system. The goal is to make everything production-ready with no placeholders, partial builds, or broken features.

## System Components
- **TV Display** (`apps/tv-display`) - Port 3001 - Main board display
- **Controller** (`apps/controller`) - Port 3002 - Phone/player interface
- **Game Server** (`services/game-server`) - Port 3000 - Backend + WebSocket
- **Admin Console** (`apps/admin-console`) - Port 3003 - Admin dashboard

---

## PHASE 1: Infrastructure Verification

### 1.1 Verify All Services Running
- [ ] Ensure Docker containers are healthy
- [ ] Verify game-server responds on port 3000
- [ ] Verify tv-display serves on port 3001
- [ ] Verify controller serves on port 3002
- [ ] Verify admin-console serves on port 3003

### 1.2 Database & Persistence
- [ ] Verify Prisma schema is migrated
- [ ] Verify database connections work
- [ ] Test game state persistence

---

## PHASE 2: TV Display App Testing

### 2.1 Welcome Screen
**File**: `apps/tv-display/src/screens/WelcomeScreen.tsx`

Tests:
- [ ] "Create New Game" button triggers API call
- [ ] API returns valid room code (6 characters)
- [ ] Socket connects after game creation
- [ ] Error handling for failed game creation
- [ ] Room code input field accepts exactly 6 characters
- [ ] "Join" button connects to existing game

### 2.2 Lobby Screen
**File**: `apps/tv-display/src/screens/LobbyScreen.tsx`

Tests:
- [ ] Room code displayed prominently
- [ ] QR code generates correctly with room URL
- [ ] Player list updates when players join
- [ ] Player cards show name, token, color
- [ ] Host indicator shown on first player
- [ ] Bot players show robot indicator
- [ ] Player count updates in real-time
- [ ] "Start Game" button visible when 2+ players

### 2.3 Game Screen
**File**: `apps/tv-display/src/screens/GameScreen.tsx`

Tests:
- [ ] Board renders all 40 spaces correctly
- [ ] Player tokens appear at correct positions
- [ ] Dice animation plays on roll
- [ ] Player tokens animate when moving
- [ ] Property ownership colors show correctly
- [ ] House/hotel indicators display
- [ ] Event log scrolls with new events
- [ ] Turn indicator highlights current player
- [ ] Player panel shows all players with money

### 2.4 Results Screen
**File**: `apps/tv-display/src/screens/ResultsScreen.tsx`

Tests:
- [ ] Winner displayed with trophy
- [ ] Final standings sorted by net worth
- [ ] Stats display correctly
- [ ] "Play Again" returns to welcome

---

## PHASE 3: Controller (Phone) App Testing

### 3.1 Join Screen - Step 1: Room Code
**File**: `apps/controller/src/screens/JoinScreen.tsx`

Tests:
- [ ] Room code input accepts 6 characters
- [ ] Input auto-capitalizes
- [ ] "Next" button enabled only at 6 chars
- [ ] Error shown for invalid room code
- [ ] Validates room exists on server

### 3.2 Join Screen - Step 2: Name Entry
Tests:
- [ ] Name input field works
- [ ] Name persisted from previous sessions
- [ ] "Next" button enabled with valid name
- [ ] Character limit enforced

### 3.3 Join Screen - Step 3: Token Selection
**File**: `apps/controller/src/components/TokenPicker.tsx`

Tests:
- [ ] All 8 tokens displayed
- [ ] Token selection highlights choice
- [ ] Color assignment works
- [ ] "Join Game" emits LOBBY_JOIN event
- [ ] Player receives JOINED_GAME confirmation
- [ ] Error if token already taken

### 3.4 Lobby Screen
**File**: `apps/controller/src/screens/LobbyScreen.tsx`

Tests:
- [ ] Own player card highlighted
- [ ] Other players visible
- [ ] Bot players shown with indicator
- [ ] "Ready" button toggles ready state
- [ ] Host sees "Start Game" button
- [ ] Host sees "Add Bot" button
- [ ] Non-host doesn't see host controls
- [ ] Start game works with 2+ players

### 3.5 Game Screen - Pre-Roll Phase
**File**: `apps/controller/src/screens/GameScreen.tsx`
**File**: `apps/controller/src/components/ActionPanel.tsx`

Tests:
- [ ] Status bar shows money, position
- [ ] "Your Turn" indicator when active
- [ ] ROLL button large and prominent
- [ ] ROLL button disabled when not your turn
- [ ] Dice roll emits GAME_ROLL_DICE event

### 3.6 Game Screen - Buy Decision Phase
Tests:
- [ ] Property card shows when landing on unowned
- [ ] Property shows name, price, rent table
- [ ] "Buy" button subtracts money
- [ ] "Auction" button starts auction
- [ ] Can't buy if insufficient funds

### 3.7 Game Screen - Rent Payment
Tests:
- [ ] Rent automatically deducted
- [ ] Notification shows rent amount
- [ ] Money updates in real-time

### 3.8 Game Screen - Building
Tests:
- [ ] Build option shows when owning monopoly
- [ ] House count displays correctly
- [ ] Can't build more than 4 houses
- [ ] Hotel upgrade works
- [ ] Building costs correct amount

### 3.9 Game Screen - Jail
Tests:
- [ ] Jail indicator shows when in jail
- [ ] "Pay $50" option available
- [ ] "Use Get Out of Jail Free" if owned
- [ ] "Roll for doubles" option
- [ ] Released after 3 turns
- [ ] Forced to pay on 3rd turn

### 3.10 Game Screen - End Turn
Tests:
- [ ] "End Turn" button visible after actions
- [ ] Turn advances to next player
- [ ] Bot turns execute automatically

---

## PHASE 4: Server-Side Logic Testing

### 4.1 Game Creation
**File**: `services/game-server/src/api/routes/games.ts`
**File**: `services/game-server/src/socket/RoomManager.ts`

Tests:
- [ ] POST /api/games creates game
- [ ] Room code is unique
- [ ] Initial state correct
- [ ] Game added to RoomManager

### 4.2 Player Joining
**File**: `services/game-server/src/socket/RoomManager.ts:handleJoin()`

Tests:
- [ ] LOBBY_JOIN creates player
- [ ] First player becomes host
- [ ] Token assignment works
- [ ] Color assignment works
- [ ] Duplicate prevention
- [ ] LOBBY_PLAYER_JOINED broadcast

### 4.3 Game Start
**File**: `services/game-server/src/socket/RoomManager.ts:handleStartGame()`

Tests:
- [ ] Only host can start
- [ ] Minimum 2 players required
- [ ] Turn order shuffled
- [ ] Game status changes to 'playing'
- [ ] First player gets turn

### 4.4 Dice Roll
**File**: `services/game-server/src/socket/RoomManager.ts:handleRollDice()`

Tests:
- [ ] Only current player can roll
- [ ] Dice values 1-6 each
- [ ] Doubles detected
- [ ] Movement calculated correctly
- [ ] Events emitted in order

### 4.5 Property Purchase
**File**: `services/game-server/src/socket/RoomManager.ts:handleBuyProperty()`

Tests:
- [ ] Owner set correctly
- [ ] Money deducted
- [ ] Can't buy owned property
- [ ] Can't buy with insufficient funds

### 4.6 Rent Collection
Tests:
- [ ] Rent calculated correctly
- [ ] Monopoly doubles rent
- [ ] Houses increase rent
- [ ] Mortgaged properties no rent

### 4.7 Bot AI
**File**: `services/game-server/src/socket/RoomManager.ts:checkBotTurn()`

Tests:
- [ ] Bots take turns automatically
- [ ] Delay before bot actions
- [ ] Bot personalities affect decisions
- [ ] Bots can buy properties
- [ ] Bots end turns properly

### 4.8 Bankruptcy
Tests:
- [ ] Detected when can't pay
- [ ] Properties transferred
- [ ] Player marked bankrupt
- [ ] Removed from turn order
- [ ] Game ends with 1 player left

---

## PHASE 5: Game Engine Logic Testing

### 5.1 Property Rules
**File**: `packages/game-engine/src/rules/property.ts`

Tests:
- [ ] Rent calculation formulas correct
- [ ] Monopoly detection works
- [ ] Building rules enforced
- [ ] Mortgage values correct

### 5.2 Movement Rules
**File**: `packages/game-engine/src/rules/movement.ts`

Tests:
- [ ] Pass GO detection
- [ ] GO TO JAIL space
- [ ] Community Chest spaces
- [ ] Chance spaces

### 5.3 Card Effects
**File**: `packages/game-engine/src/rules/cards.ts`

Tests:
- [ ] All card types work
- [ ] Money transfers correct
- [ ] Movement cards work
- [ ] Get out of jail cards

---

## PHASE 6: Socket Event Flow Testing

### 6.1 Event Propagation
Tests:
- [ ] Events reach all clients in room
- [ ] Events in correct order
- [ ] No dropped events
- [ ] Reconnection handling

### 6.2 State Synchronization
Tests:
- [ ] All clients have same state
- [ ] State updates atomic
- [ ] No race conditions

---

## PHASE 7: Admin Console Testing

### 7.1 Authentication
**File**: `apps/admin-console/src/screens/LoginScreen.tsx`

Tests:
- [ ] Login with valid token works
- [ ] Invalid token rejected
- [ ] Session persists

### 7.2 Dashboard
**File**: `apps/admin-console/src/screens/DashboardScreen.tsx`

Tests:
- [ ] Stats display correctly
- [ ] Games list populated
- [ ] Game details viewable
- [ ] Admin actions work

---

## PHASE 8: Integration Testing

### 8.1 Full Game Flow
Test complete game from start to finish:
1. [ ] TV creates game
2. [ ] 2 players join via controllers
3. [ ] 1 bot added
4. [ ] Host starts game
5. [ ] Complete 5 rounds of turns
6. [ ] Properties purchased
7. [ ] Rent collected
8. [ ] One player bankrupted
9. [ ] Game ends
10. [ ] Results shown correctly

### 8.2 Edge Cases
- [ ] Player disconnect/reconnect
- [ ] All bots game
- [ ] Maximum players (8)
- [ ] Auction scenarios
- [ ] Trade scenarios

---

## PHASE 9: Bug Fixes Required

Based on the conversation history and codebase analysis:

### Known Issues to Fix:

1. **Controller Join Flow Broken**
   - Players can't join games
   - Need to verify LOBBY_JOIN handler
   - Check socket connection in controller

2. **Socket Event Naming Mismatch**
   - Verify shared package events match server
   - Check all emits use correct event names

3. **Bot Turn Execution**
   - Verify bot turns trigger properly
   - Check async timing

4. **State Synchronization**
   - Ensure GAME_STATE emitted after every action
   - All clients receive updates

---

## Execution Order

### Day 1: Foundation
1. Verify infrastructure running
2. Fix TV Display create/join flow
3. Fix Controller join flow
4. Test lobby functionality

### Day 2: Gameplay
5. Test dice rolling
6. Test property purchase
7. Test rent collection
8. Test turn advancement

### Day 3: Advanced Features
9. Test bot AI
10. Test jail mechanics
11. Test building houses
12. Test bankruptcy

### Day 4: Polish
13. Test auctions
14. Test trading
15. Test admin console
16. Full integration test

---

## Success Criteria

- All user flows work without errors
- No console errors in browser
- No server crashes
- All socket events properly handled
- State synchronized across all clients
- Bots play autonomously
- Game completes from start to finish
- Production-ready code quality
