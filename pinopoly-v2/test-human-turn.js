/**
 * Test human player turn handling
 */

const { io } = require('socket.io-client');

const SERVER_URL = 'http://localhost:3000';
const API_URL = `${SERVER_URL}/api`;

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

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

function createSocket() {
  return io(SERVER_URL, {
    transports: ['websocket'],
    autoConnect: false,
  });
}

async function runTest() {
  console.log('🎮 HUMAN PLAYER TURN TEST\n');
  console.log('='.repeat(50));

  // Create game
  const game = await api('POST', '/games', { hostName: 'Test' });
  console.log('✅ Game created:', game.roomCode);

  // Connect as player
  const socket = createSocket();
  socket.connect();

  let playerId;
  let currentState;

  await new Promise((resolve, reject) => {
    socket.on('connect', () => {
      console.log('✅ Socket connected');
      socket.emit('lobby:join', {
        roomCode: game.roomCode,
        playerName: 'HumanPlayer',
        token: 'car',
        color: '#FF6B6B',
      });
    });

    socket.on('lobby:joined', (data) => {
      console.log('✅ Joined as:', data.playerName);
      playerId = data.playerId;
      resolve();
    });

    socket.on('lobby:joinError', (error) => {
      reject(new Error(error.message));
    });

    setTimeout(() => reject(new Error('Join timeout')), 5000);
  });

  // Add just 1 bot to keep it simple
  await new Promise((resolve) => {
    socket.on('lobby:playerJoined', (data) => {
      if (data.player && data.player.isBot) {
        console.log('✅ Bot added:', data.player.name);
        resolve();
      }
    });
    socket.emit('lobby:addBot', { personality: 'conservative', difficulty: 'normal' });
    setTimeout(resolve, 2000);
  });

  // Start game
  console.log('\n🚀 Starting game...');

  await new Promise((resolve, reject) => {
    socket.on('game:started', (state) => {
      console.log('✅ Game started');
      console.log('   Phase:', state.phase);
      console.log('   Current player index:', state.currentPlayerIndex);
      console.log('   Player order:', state.playerOrder);
      currentState = state;

      // Check if it's our turn
      const currentPlayerId = state.playerOrder[state.currentPlayerIndex];
      if (currentPlayerId === playerId) {
        console.log('   ⭐ IT IS OUR TURN!');
      } else {
        console.log('   👤 Bot\'s turn first');
      }
      resolve();
    });

    socket.emit('lobby:startGame');
    setTimeout(() => reject(new Error('Start timeout')), 10000);
  });

  // Wait for our turn and roll
  console.log('\n🎲 Waiting for our turn...');

  await new Promise((resolve) => {
    let turnCount = 0;
    const maxTurns = 10;

    const handleState = (state) => {
      currentState = state;
      const currentPlayerId = state.playerOrder[state.currentPlayerIndex];
      const currentPlayer = state.players[currentPlayerId];

      turnCount++;
      console.log(`\nTurn ${turnCount}: ${currentPlayer.name} (phase: ${state.phase})`);
      console.log(`   Position: ${currentPlayer.position}, Money: $${currentPlayer.money}`);

      if (currentPlayerId === playerId) {
        console.log('   ⭐ OUR TURN!');

        if (state.phase === 'pre_roll') {
          console.log('   🎲 Rolling dice...');
          socket.emit('game:rollDice');
        } else if (state.phase === 'buy_decision') {
          console.log('   💰 Declining to buy (for test)...');
          socket.emit('game:declineProperty');
        } else if (state.phase === 'turn_end' || state.phase === 'landed') {
          console.log('   ➡️ Ending turn...');
          socket.emit('game:endTurn');
        } else if (state.phase === 'card_action') {
          console.log('   🃏 Executing card...');
          socket.emit('game:executeCard');
        }
      }

      if (turnCount >= maxTurns) {
        resolve();
      }
    };

    socket.on('game:state', handleState);
    socket.on('game:turnChanged', (data) => {
      if (data.gameState) handleState(data.gameState);
    });
    socket.on('game:diceRolled', (data) => {
      console.log('   Dice result:', data.dice, '(total:', data.dice[0] + data.dice[1], ')');
    });
    socket.on('game:playerMoved', (data) => {
      console.log('   Moved to position:', data.newPosition);
    });

    // Initial check
    if (currentState) {
      handleState(currentState);
    }

    setTimeout(resolve, 60000); // Max 1 minute
  });

  console.log('\n' + '='.repeat(50));
  console.log('✅ TEST COMPLETE');
  console.log('='.repeat(50));

  socket.disconnect();
  process.exit(0);
}

runTest().catch((err) => {
  console.error('\n❌ TEST FAILED:', err.message);
  process.exit(1);
});
