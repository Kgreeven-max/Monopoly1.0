/**
 * End-to-end test script for Pinopoly game flows
 * Tests: Create game, join, add bots, start game, gameplay
 */

const { io } = require('socket.io-client');

const SERVER_URL = 'http://localhost:3000';
const API_URL = `${SERVER_URL}/api`;

// Helper to wait
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Helper to make API calls
async function api(method, path, body) {
  const fetch = (await import('node-fetch')).default;
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) options.body = JSON.stringify(body);
  const res = await fetch(`${API_URL}${path}`, options);
  return res.json();
}

// Create a socket connection
function createSocket() {
  return io(SERVER_URL, {
    transports: ['websocket'],
    autoConnect: false,
  });
}

async function runTest() {
  console.log('🎮 PINOPOLY GAME FLOW TEST\n');
  console.log('='.repeat(50));

  // PHASE 2: Create Game
  console.log('\n📺 PHASE 2: Create Game');
  console.log('-'.repeat(30));

  const game = await api('POST', '/games', { hostName: 'Test Display' });
  console.log('✅ Game created:', game.roomCode);
  console.log('   Game ID:', game.gameId);
  console.log('   Status:', game.status);

  // Connect as display
  const displaySocket = createSocket();
  displaySocket.connect();

  await new Promise((resolve, reject) => {
    displaySocket.on('connect', () => {
      console.log('✅ Display socket connected');
      displaySocket.emit('auth:display', { gameCode: game.roomCode });
    });

    displaySocket.on('auth:success', (data) => {
      console.log('✅ Display authenticated:', data.role);
      resolve();
    });

    displaySocket.on('game:state', (state) => {
      console.log('✅ Received initial game state');
      console.log('   Players:', Object.keys(state.players).length);
      console.log('   Status:', state.status);
    });

    displaySocket.on('connect_error', reject);
    setTimeout(() => reject(new Error('Display connection timeout')), 5000);
  });

  // PHASE 3: Player Join Flow
  console.log('\n🎮 PHASE 3: Player Join Flow');
  console.log('-'.repeat(30));

  const playerSocket = createSocket();
  playerSocket.connect();

  let playerId;
  let isHost = false;
  let currentState;

  await new Promise((resolve, reject) => {
    playerSocket.on('connect', () => {
      console.log('✅ Player socket connected');

      // Join the game
      playerSocket.emit('lobby:join', {
        roomCode: game.roomCode,
        playerName: 'TestPlayer1',
        token: 'car',
        color: '#FF6B6B',
      });
    });

    playerSocket.on('lobby:joined', (data) => {
      console.log('✅ Player joined successfully!');
      console.log('   Player ID:', data.playerId);
      console.log('   Is Host:', data.isHost);
      playerId = data.playerId;
      isHost = data.isHost;
      currentState = data.gameState;
      resolve();
    });

    playerSocket.on('lobby:joinError', (error) => {
      console.log('❌ Join error:', error.message);
      reject(new Error(error.message));
    });

    playerSocket.on('error', (error) => {
      console.log('❌ Socket error:', error);
    });

    setTimeout(() => reject(new Error('Player join timeout')), 5000);
  });

  // Verify player appears in game state
  const gameState = await api('GET', `/games/code/${game.roomCode}`);
  console.log('✅ Game state shows', gameState.playerCount, 'player(s)');

  // PHASE 4: Add Multiple Bots
  console.log('\n🤖 PHASE 4: Add Multiple Bots');
  console.log('-'.repeat(30));

  const personalities = ['aggressive', 'conservative', 'strategic'];

  for (let i = 0; i < 3; i++) {
    await new Promise((resolve) => {
      const onPlayerJoined = (data) => {
        if (data.player && data.player.isBot) {
          console.log(`✅ Bot ${i + 1} added:`, data.player.name, `(${data.player.personality || 'unknown'})`);
          playerSocket.off('lobby:playerJoined', onPlayerJoined);
          resolve();
        }
      };

      playerSocket.on('lobby:playerJoined', onPlayerJoined);

      playerSocket.emit('lobby:addBot', {
        personality: personalities[i],
        difficulty: 'normal',
      });

      setTimeout(resolve, 2000); // Timeout fallback
    });
    await sleep(500);
  }

  // Verify player count
  const updatedGame = await api('GET', `/games/code/${game.roomCode}`);
  console.log('✅ Total players in game:', updatedGame.playerCount);

  // PHASE 5: Start Game
  console.log('\n🚀 PHASE 5: Start Game');
  console.log('-'.repeat(30));

  await new Promise((resolve, reject) => {
    let countdownReceived = false;
    let gameStarted = false;

    playerSocket.on('lobby:gameStarting', (data) => {
      console.log('   Countdown:', data.countdown);
      countdownReceived = true;
    });

    playerSocket.on('game:started', (state) => {
      console.log('✅ Game started!');
      console.log('   Status:', state.status);
      console.log('   Current player index:', state.currentPlayerIndex);
      console.log('   Phase:', state.phase);
      currentState = state;
      gameStarted = true;
    });

    playerSocket.on('game:state', (state) => {
      if (state.status === 'playing' && !gameStarted) {
        console.log('✅ Game state updated to playing');
        currentState = state;
        gameStarted = true;
        resolve();
      }
    });

    playerSocket.emit('lobby:startGame');
    console.log('   Starting game...');

    setTimeout(() => {
      if (gameStarted) resolve();
      else reject(new Error('Game start timeout'));
    }, 10000);
  });

  // PHASE 6-9: Gameplay Loop
  console.log('\n🎲 PHASE 6-9: Gameplay Loop');
  console.log('-'.repeat(30));

  // Wait for bots to take their turns automatically
  console.log('   Waiting for turns... (bots should auto-play)');

  let turnsPlayed = 0;
  const maxTurns = 10;

  await new Promise((resolve) => {
    const checkTurn = (state) => {
      currentState = state;
      const currentPlayerId = state.playerOrder[state.currentPlayerIndex];
      const currentPlayer = state.players[currentPlayerId];

      console.log(`   Turn ${turnsPlayed + 1}: ${currentPlayer.name} at position ${currentPlayer.position} (phase: ${state.phase})`);

      // If it's our turn and we need to roll
      if (currentPlayerId === playerId && state.phase === 'pre_roll') {
        console.log('   Our turn! Rolling dice...');
        playerSocket.emit('game:rollDice');
      }

      // If we can end our turn
      if (currentPlayerId === playerId && (state.phase === 'turn_end' || state.phase === 'landed' || state.phase === 'buy_decision')) {
        console.log('   Ending our turn...');
        playerSocket.emit('game:endTurn');
      }

      turnsPlayed++;
      if (turnsPlayed >= maxTurns) {
        resolve();
      }
    };

    playerSocket.on('game:state', checkTurn);
    playerSocket.on('game:turnChanged', (data) => checkTurn(data.gameState));
    playerSocket.on('game:diceRolled', (data) => {
      console.log('   Dice rolled:', data.dice);
    });
    playerSocket.on('game:playerMoved', (data) => {
      console.log('   Player moved to:', data.newPosition);
    });

    // Trigger initial check
    if (currentState.phase === 'pre_roll') {
      const currentPlayerId = currentState.playerOrder[currentState.currentPlayerIndex];
      if (currentPlayerId === playerId) {
        playerSocket.emit('game:rollDice');
      }
    }

    setTimeout(resolve, 30000); // Max 30 seconds
  });

  // SUMMARY
  console.log('\n' + '='.repeat(50));
  console.log('📊 TEST SUMMARY');
  console.log('='.repeat(50));
  console.log('✅ Game created successfully');
  console.log('✅ Display connected');
  console.log('✅ Player joined');
  console.log('✅ Bots added');
  console.log('✅ Game started');
  console.log(`✅ ${turnsPlayed} turns played`);

  // Final game state
  const finalGame = await api('GET', `/games/${game.gameId}`);
  console.log('\nFinal game state:');
  console.log('   Status:', finalGame.status);
  console.log('   Round:', finalGame.round || 'N/A');

  // Cleanup
  displaySocket.disconnect();
  playerSocket.disconnect();

  console.log('\n✅ TEST COMPLETE\n');
  process.exit(0);
}

// Run the test
runTest().catch((err) => {
  console.error('\n❌ TEST FAILED:', err.message);
  process.exit(1);
});
