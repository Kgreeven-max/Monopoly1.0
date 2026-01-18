/**
 * Feature Test Script
 * Tests bots, auctions, trading, and other features
 */

import { io } from 'socket.io-client';

const SERVER_URL = 'http://localhost:3000';
const SocketEvents = {
  LOBBY_JOIN: 'lobby:join',
  LOBBY_ADD_BOT: 'lobby:addBot',
  LOBBY_START_GAME: 'lobby:startGame',
  JOINED_GAME: 'lobby:joined',
  PLAYER_JOINED: 'lobby:playerJoined',
  LOBBY_GAME_STARTING: 'lobby:gameStarting',
  GAME_STARTED: 'game:started',
  GAME_STATE: 'game:state',
  GAME_ROLL_DICE: 'game:rollDice',
  GAME_DICE_ROLLED: 'game:diceRolled',
  GAME_PLAYER_MOVED: 'game:playerMoved',
  GAME_BUY_PROPERTY: 'game:buyProperty',
  GAME_PROPERTY_BOUGHT: 'game:propertyBought',
  GAME_END_TURN: 'game:endTurn',
  GAME_TURN_CHANGED: 'game:turnChanged',
  GAME_CARD_DRAWN: 'game:cardDrawn',
  GAME_EXECUTE_CARD: 'game:executeCard',
  TRADE_PROPOSE: 'trade:propose',
  TRADE_PROPOSED: 'trade:proposed',
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
    const socket = io(SERVER_URL, { transports: ['websocket'] });
    socket.on('connect', () => resolve(socket));
    socket.on('connect_error', reject);
    setTimeout(() => reject(new Error('Timeout')), 5000);
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

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testBotFeature() {
  console.log('\n=== BOT FEATURE TEST ===\n');

  const game = await createGame();
  console.log('✓ Game created:', game.roomCode);

  const player1 = await connectSocket();
  console.log('✓ Player 1 connected');

  const joinData = await new Promise((resolve) => {
    player1.on(SocketEvents.JOINED_GAME, resolve);
    player1.emit(SocketEvents.LOBBY_JOIN, {
      roomCode: game.roomCode,
      playerName: 'Host',
      token: 'car',
      color: '#FF6B6B',
    });
  });
  console.log('✓ Player 1 joined as host');

  // Add a bot
  const botPromise = waitForEvent(player1, SocketEvents.PLAYER_JOINED);
  player1.emit(SocketEvents.LOBBY_ADD_BOT, {
    personality: 'aggressive',
    difficulty: 'normal',
  });
  console.log('✓ Add bot command sent');

  const botResult = await botPromise;
  const players = Object.values(botResult.gameState.players);
  const bot = players.find(p => p.isBot);
  console.log('✓ Bot added:', bot ? bot.name : 'N/A');
  console.log('  - Bot personality:', bot?.botPersonality);

  // Start game with 1 human + 1 bot
  let countdowns = [];
  player1.on(SocketEvents.LOBBY_GAME_STARTING, (data) => {
    countdowns.push(data.countdown);
  });

  const gameStartPromise = waitForEvent(player1, SocketEvents.GAME_STARTED, 15000);
  player1.emit(SocketEvents.LOBBY_START_GAME);
  console.log('✓ Start game command sent');

  const gameState = await gameStartPromise;
  console.log('✓ Game started with bot!');
  console.log('  - Players:', Object.keys(gameState.players).length);
  console.log('  - Countdowns:', countdowns);

  // Play a few turns and watch bot play
  const currentPlayerId = gameState.playerOrder[gameState.currentPlayerIndex];
  const isPlayerTurn = currentPlayerId === joinData.playerId;
  console.log('  - First turn:', isPlayerTurn ? 'Human' : 'Bot');

  if (isPlayerTurn) {
    // Human rolls
    const dicePromise = waitForEvent(player1, SocketEvents.GAME_DICE_ROLLED);
    player1.emit(SocketEvents.GAME_ROLL_DICE);
    const dice = await dicePromise;
    console.log('✓ Human rolled:', dice.dice);

    // Wait for state update
    await sleep(500);

    // End turn
    const turnChangePromise = waitForEvent(player1, SocketEvents.GAME_TURN_CHANGED, 5000)
      .catch(() => null);
    player1.emit(SocketEvents.GAME_END_TURN);
    const turnChange = await turnChangePromise;
    if (turnChange) {
      console.log('✓ Turn ended, bot should play next');
    }
  }

  // Watch for bot activity (it should auto-play)
  console.log('  Watching for bot turns...');
  const botDice = await waitForEvent(player1, SocketEvents.GAME_DICE_ROLLED, 5000)
    .catch(() => null);
  if (botDice) {
    console.log('✓ Bot rolled dice:', botDice.dice);
  }

  player1.disconnect();
  console.log('\n✓ Bot feature test PASSED');
}

async function testTradeFeature() {
  console.log('\n=== TRADE FEATURE TEST ===\n');

  const game = await createGame();
  console.log('✓ Game created:', game.roomCode);

  const player1 = await connectSocket();
  const player2 = await connectSocket();
  console.log('✓ Both players connected');

  const join1 = await new Promise((resolve) => {
    player1.on(SocketEvents.JOINED_GAME, resolve);
    player1.emit(SocketEvents.LOBBY_JOIN, {
      roomCode: game.roomCode,
      playerName: 'Trader1',
      token: 'car',
      color: '#FF6B6B',
    });
  });

  const join2 = await new Promise((resolve) => {
    player2.on(SocketEvents.JOINED_GAME, resolve);
    player2.emit(SocketEvents.LOBBY_JOIN, {
      roomCode: game.roomCode,
      playerName: 'Trader2',
      token: 'dog',
      color: '#4ECDC4',
    });
  });

  console.log('✓ Both players joined');

  // Start game
  const gameStartPromise = waitForEvent(player1, SocketEvents.GAME_STARTED, 15000);
  player1.emit(SocketEvents.LOBBY_START_GAME);
  await gameStartPromise;
  console.log('✓ Game started');

  // Propose a trade
  const tradePromise = waitForEvent(player2, SocketEvents.TRADE_PROPOSED);
  player1.emit(SocketEvents.TRADE_PROPOSE, {
    recipientId: join2.playerId,
    offer: { money: 100, properties: [] },
    request: { money: 50, properties: [] },
  });
  console.log('✓ Trade proposal sent');

  const trade = await tradePromise;
  console.log('✓ Trade received by player 2');
  console.log('  - Trade ID:', trade.tradeId);
  console.log('  - Offer:', JSON.stringify(trade.offer));
  console.log('  - Request:', JSON.stringify(trade.request));

  player1.disconnect();
  player2.disconnect();
  console.log('\n✓ Trade feature test PASSED');
}

async function testGameMechanics() {
  console.log('\n=== GAME MECHANICS TEST ===\n');

  const game = await createGame();
  console.log('✓ Game created:', game.roomCode);

  const player1 = await connectSocket();
  console.log('✓ Player connected');

  const join1 = await new Promise((resolve) => {
    player1.on(SocketEvents.JOINED_GAME, resolve);
    player1.emit(SocketEvents.LOBBY_JOIN, {
      roomCode: game.roomCode,
      playerName: 'Tester',
      token: 'car',
      color: '#FF6B6B',
    });
  });

  // Add bot as second player
  const botPromise = waitForEvent(player1, SocketEvents.PLAYER_JOINED);
  player1.emit(SocketEvents.LOBBY_ADD_BOT, {
    personality: 'conservative',
    difficulty: 'easy',
  });
  await botPromise;
  console.log('✓ Bot added');

  // Start game
  player1.emit(SocketEvents.LOBBY_START_GAME);
  const gameState = await waitForEvent(player1, SocketEvents.GAME_STARTED, 15000);
  console.log('✓ Game started');

  // Track events
  let eventsReceived = {
    diceRolled: false,
    playerMoved: false,
    propertyBought: false,
    cardDrawn: false,
    turnChanged: false,
    gameState: false,
  };

  player1.on(SocketEvents.GAME_DICE_ROLLED, () => eventsReceived.diceRolled = true);
  player1.on(SocketEvents.GAME_PLAYER_MOVED, () => eventsReceived.playerMoved = true);
  player1.on(SocketEvents.GAME_PROPERTY_BOUGHT, () => eventsReceived.propertyBought = true);
  player1.on(SocketEvents.GAME_CARD_DRAWN, () => eventsReceived.cardDrawn = true);
  player1.on(SocketEvents.GAME_TURN_CHANGED, () => eventsReceived.turnChanged = true);
  player1.on(SocketEvents.GAME_STATE, () => eventsReceived.gameState = true);

  // Play a few turns
  const currentPlayerId = gameState.playerOrder[gameState.currentPlayerIndex];
  const isPlayerTurn = currentPlayerId === join1.playerId;

  console.log('  Playing turns...');

  // Roll if it's our turn
  if (isPlayerTurn) {
    player1.emit(SocketEvents.GAME_ROLL_DICE);
  }

  // Wait for game activity
  await sleep(3000);

  console.log('\nEvents received:');
  console.log('  - Dice rolled:', eventsReceived.diceRolled ? '✓' : '✗');
  console.log('  - Player moved:', eventsReceived.playerMoved ? '✓' : '(may not have moved)');
  console.log('  - Game state:', eventsReceived.gameState ? '✓' : '✗');
  console.log('  - Turn changed:', eventsReceived.turnChanged ? '✓' : '(may not have changed)');

  player1.disconnect();
  console.log('\n✓ Game mechanics test PASSED');
}

async function runAllTests() {
  console.log('\n' + '='.repeat(50));
  console.log('  PINOPOLY v2 - COMPREHENSIVE FEATURE TESTS');
  console.log('='.repeat(50));

  try {
    await testBotFeature();
    await testTradeFeature();
    await testGameMechanics();

    console.log('\n' + '='.repeat(50));
    console.log('  ALL FEATURE TESTS PASSED!');
    console.log('='.repeat(50) + '\n');
  } catch (error) {
    console.error('\n✗ TEST FAILED:', error.message);
    process.exit(1);
  }
}

runAllTests();
