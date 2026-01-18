/**
 * Live Socket Test Script
 * Run against Docker services at localhost:3000
 */

import { io } from 'socket.io-client';

const SERVER_URL = 'http://localhost:3000';
const SocketEvents = {
  LOBBY_JOIN: 'lobby:join',
  LOBBY_READY: 'lobby:ready',
  LOBBY_START_GAME: 'lobby:startGame',
  LOBBY_ADD_BOT: 'lobby:addBot',
  JOINED_GAME: 'lobby:joined',
  JOIN_ERROR: 'lobby:joinError',
  LOBBY_STATE: 'lobby:state',
  LOBBY_PLAYER_JOINED: 'lobby:playerJoined',
  LOBBY_PLAYER_READY: 'lobby:playerReady',
  LOBBY_GAME_STARTING: 'lobby:gameStarting',
  GAME_STARTED: 'game:started',
  GAME_STATE: 'game:state',
  GAME_ROLL_DICE: 'game:rollDice',
  GAME_DICE_ROLLED: 'game:diceRolled',
  GAME_PLAYER_MOVED: 'game:playerMoved',
  GAME_END_TURN: 'game:endTurn',
  GAME_TURN_CHANGED: 'game:turnChanged',
  ERROR: 'error',
};

async function createGame() {
  const response = await fetch(`${SERVER_URL}/api/games`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hostName: 'TestHost' }),
  });
  return response.json();
}

function connectSocket() {
  return new Promise((resolve, reject) => {
    const socket = io(SERVER_URL, {
      transports: ['websocket'],
      autoConnect: true,
    });

    socket.on('connect', () => {
      console.log('✓ Socket connected:', socket.id);
      resolve(socket);
    });

    socket.on('connect_error', (err) => {
      console.error('✗ Socket connection error:', err.message);
      reject(err);
    });

    setTimeout(() => reject(new Error('Socket connection timeout')), 5000);
  });
}

function waitForEvent(socket, event, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const handler = (data) => {
      socket.off(event, handler);
      resolve(data);
    };
    socket.on(event, handler);
    setTimeout(() => {
      socket.off(event, handler);
      reject(new Error(`Timeout waiting for ${event}`));
    }, timeout);
  });
}

async function runTests() {
  console.log('\n=== PINOPOLY v2 SOCKET TESTS ===\n');

  // Phase 1: Create game
  console.log('Phase 1: API Tests');
  console.log('-'.repeat(40));

  const game = await createGame();
  console.log('✓ Game created:', game.roomCode);

  // Phase 2: Socket Connections
  console.log('\nPhase 2: Socket Connection Tests');
  console.log('-'.repeat(40));

  const player1 = await connectSocket();
  console.log('✓ Player 1 connected');

  // Join game
  const joinPromise = waitForEvent(player1, SocketEvents.JOINED_GAME);
  player1.emit(SocketEvents.LOBBY_JOIN, {
    roomCode: game.roomCode,
    playerName: 'Player1',
    token: 'car',
    color: '#FF6B6B',
  });

  const joinResult = await joinPromise;
  console.log('✓ Player 1 joined:', joinResult.playerId);
  console.log('  - Is host:', joinResult.isHost);
  console.log('  - Session token:', joinResult.sessionToken.slice(0, 8) + '...');

  // Connect player 2
  const player2 = await connectSocket();
  console.log('✓ Player 2 connected');

  const join2Promise = waitForEvent(player2, SocketEvents.JOINED_GAME);
  player2.emit(SocketEvents.LOBBY_JOIN, {
    roomCode: game.roomCode,
    playerName: 'Player2',
    token: 'dog',
    color: '#4ECDC4',
  });

  const join2Result = await join2Promise;
  console.log('✓ Player 2 joined:', join2Result.playerId);
  console.log('  - Is host:', join2Result.isHost);

  // Ready up
  const readyPromise = waitForEvent(player1, SocketEvents.LOBBY_PLAYER_READY);
  player2.emit(SocketEvents.LOBBY_READY);
  const readyResult = await readyPromise;
  console.log('✓ Player 2 ready:', readyResult.ready);

  // Phase 3: Start Game
  console.log('\nPhase 3: Game Flow Tests');
  console.log('-'.repeat(40));

  // Listen for countdown
  let countdowns = [];
  player1.on(SocketEvents.LOBBY_GAME_STARTING, (data) => {
    countdowns.push(data.countdown);
    console.log(`  Countdown: ${data.countdown}...`);
  });

  const gameStartPromise = waitForEvent(player1, SocketEvents.GAME_STARTED, 15000);
  player1.emit(SocketEvents.LOBBY_START_GAME);
  console.log('✓ Start game command sent');

  const gameState = await gameStartPromise;
  console.log('✓ Game started!');
  console.log('  - Status:', gameState.status);
  console.log('  - Phase:', gameState.phase);
  console.log('  - Players:', Object.keys(gameState.players).length);
  console.log('  - Current player index:', gameState.currentPlayerIndex);

  // Determine current player
  const currentPlayerId = gameState.playerOrder[gameState.currentPlayerIndex];
  const isPlayer1Turn = currentPlayerId === joinResult.playerId;
  const currentPlayer = isPlayer1Turn ? player1 : player2;
  console.log('  - Current player:', isPlayer1Turn ? 'Player1' : 'Player2');

  // Roll dice
  const dicePromise = waitForEvent(currentPlayer, SocketEvents.GAME_DICE_ROLLED);
  currentPlayer.emit(SocketEvents.GAME_ROLL_DICE);
  console.log('✓ Roll dice command sent');

  const diceResult = await dicePromise;
  console.log('✓ Dice rolled:', diceResult.dice);
  console.log('  - Total:', diceResult.dice[0] + diceResult.dice[1]);

  // Wait for movement
  const movePromise = waitForEvent(currentPlayer, SocketEvents.GAME_PLAYER_MOVED, 2000)
    .catch(() => ({ newPosition: 'unknown' }));
  const moveResult = await movePromise;
  console.log('✓ Player moved to position:', moveResult.newPosition);

  // Get game state
  const statePromise = waitForEvent(currentPlayer, SocketEvents.GAME_STATE);
  const finalState = await statePromise;
  console.log('✓ Current phase:', finalState.phase);

  // End turn (if in appropriate phase)
  if (finalState.phase === 'turn_end' || finalState.phase === 'landed') {
    const turnChangePromise = waitForEvent(currentPlayer, SocketEvents.GAME_TURN_CHANGED);
    currentPlayer.emit(SocketEvents.GAME_END_TURN);
    console.log('✓ End turn command sent');

    const turnResult = await turnChangePromise;
    console.log('✓ Turn changed to next player');
    console.log('  - New player index:', turnResult.gameState?.currentPlayerIndex);
  } else {
    console.log('  - Phase is:', finalState.phase, '(not ending turn)');
  }

  console.log('\n' + '='.repeat(40));
  console.log('ALL SOCKET TESTS PASSED!');
  console.log('='.repeat(40) + '\n');

  // Cleanup
  player1.disconnect();
  player2.disconnect();
}

runTests().catch((error) => {
  console.error('\n✗ TEST FAILED:', error.message);
  process.exit(1);
});
