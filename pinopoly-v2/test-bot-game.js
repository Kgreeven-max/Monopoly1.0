/**
 * Full bot game simulation - tests complete game from start to finish
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
  console.log('🤖 FULL BOT GAME SIMULATION\n');
  console.log('='.repeat(60));

  // Create game via API
  const game = await api('POST', '/games', { hostName: 'BotArena' });
  console.log('✅ Game created:', game.roomCode);

  // Connect display socket to monitor game
  const displaySocket = createSocket();
  displaySocket.connect();

  await new Promise((resolve, reject) => {
    displaySocket.on('connect', () => {
      displaySocket.emit('auth:display', { gameCode: game.roomCode });
    });
    displaySocket.on('auth:success', () => {
      console.log('✅ Display connected');
      resolve();
    });
    setTimeout(() => reject(new Error('Display timeout')), 5000);
  });

  // Connect host socket
  const hostSocket = createSocket();
  hostSocket.connect();

  await new Promise((resolve, reject) => {
    hostSocket.on('connect', () => {
      hostSocket.emit('lobby:join', {
        roomCode: game.roomCode,
        playerName: 'GameMaster',
        token: 'car',
        color: '#FF6B6B',
      });
    });
    hostSocket.on('lobby:joined', () => {
      console.log('✅ Host connected (will spectate)');
      resolve();
    });
    setTimeout(() => reject(new Error('Host join timeout')), 5000);
  });

  // Add 4 bots with different personalities
  console.log('\n🤖 Adding bots...');
  const personalities = ['aggressive', 'conservative', 'strategic', 'opportunistic'];
  for (const personality of personalities) {
    hostSocket.emit('lobby:addBot', { personality, difficulty: 'normal' });
    await sleep(500);
  }
  console.log('✅ 4 bots added');

  // Start game
  console.log('\n🚀 Starting game...');
  await new Promise((resolve, reject) => {
    displaySocket.on('game:started', (state) => {
      console.log('✅ Game started!');
      console.log('   Players:', Object.keys(state.players).length);
      resolve();
    });
    hostSocket.emit('lobby:startGame');
    setTimeout(() => reject(new Error('Start timeout')), 15000);
  });

  // Get host player ID
  let hostPlayerId;
  await new Promise((resolve) => {
    hostSocket.on('game:state', (state) => {
      for (const [id, player] of Object.entries(state.players)) {
        if (player.name === 'GameMaster') {
          hostPlayerId = id;
          break;
        }
      }
      resolve();
    });
    // Trigger a state refresh
    setTimeout(resolve, 1000);
  });

  // Monitor game progress and have host play when it's their turn
  console.log('\n📊 GAME PROGRESS');
  console.log('-'.repeat(60));

  let turnCount = 0;
  let lastRound = 1;
  let gameEnded = false;

  await new Promise((resolve) => {
    const logState = (state) => {
      if (state.round !== lastRound) {
        console.log(`\n📅 ROUND ${state.round}`);
        lastRound = state.round;

        // Show player standings
        const standings = Object.values(state.players)
          .sort((a, b) => b.money - a.money)
          .map((p, i) => `   ${i + 1}. ${p.name}: $${p.money}`);
        console.log('Standings:');
        standings.forEach(s => console.log(s));
      }

      turnCount++;
      const currentId = state.playerOrder[state.currentPlayerIndex];
      const current = state.players[currentId];

      if (turnCount % 5 === 0) {
        console.log(`   [Turn ${turnCount}] ${current.name} at ${current.position}, $${current.money}`);
      }

      // If it's the host's turn, play automatically
      if (currentId === hostPlayerId && !current.isBot) {
        if (state.phase === 'pre_roll') {
          hostSocket.emit('game:rollDice');
        } else if (state.phase === 'buy_decision') {
          // Buy if we can afford it
          const prop = state.properties[current.position];
          if (prop && !prop.ownerId && prop.price && current.money >= prop.price) {
            hostSocket.emit('game:buyProperty', { propertyId: current.position });
          } else {
            hostSocket.emit('game:declineProperty');
          }
        } else if (state.phase === 'turn_end' || state.phase === 'landed') {
          hostSocket.emit('game:endTurn');
        } else if (state.phase === 'card_action') {
          hostSocket.emit('game:executeCard');
        } else if (state.phase === 'jail_decision' || state.phase === 'jail') {
          if (current.money >= 50) {
            hostSocket.emit('game:payJailFine');
          } else {
            hostSocket.emit('game:rollDice');
          }
        }
      }

      // Check for bankruptcies
      const bankrupt = Object.values(state.players).filter(p => p.money < 0);
      if (bankrupt.length > 0) {
        console.log('💀 BANKRUPT:', bankrupt.map(p => p.name).join(', '));
      }

      // Check for game end
      if (state.status === 'finished' || state.status === 'ended') {
        gameEnded = true;
        console.log('\n🏆 GAME ENDED!');

        const winner = Object.values(state.players)
          .sort((a, b) => b.money - a.money)[0];
        console.log(`Winner: ${winner.name} with $${winner.money}`);
        resolve();
      }

      // End after 100 turns or 10 rounds for testing
      if (turnCount >= 100 || state.round >= 10) {
        console.log('\n⏱️ Test limit reached (100 turns or 10 rounds)');
        resolve();
      }
    };

    displaySocket.on('game:state', logState);
    displaySocket.on('game:turnChanged', (data) => {
      if (data.gameState) logState(data.gameState);
    });
    hostSocket.on('game:state', logState);
    hostSocket.on('game:turnChanged', (data) => {
      if (data.gameState) logState(data.gameState);
    });

    // Timeout after 2 minutes
    setTimeout(() => {
      console.log('\n⏱️ Test timeout');
      resolve();
    }, 120000);
  });

  // Final summary
  console.log('\n' + '='.repeat(60));
  console.log('📊 FINAL SUMMARY');
  console.log('='.repeat(60));
  console.log(`Total turns played: ${turnCount}`);
  console.log(`Rounds completed: ${lastRound}`);
  console.log(`Game ended: ${gameEnded ? 'Yes' : 'No (test limit)'}`);

  // Get final state from API
  try {
    const finalGame = await api('GET', `/games/${game.gameId}`);
    console.log(`\nFinal game status: ${finalGame.status}`);
    console.log(`Final round: ${finalGame.round || 'N/A'}`);
  } catch (e) {
    console.log('Could not fetch final game state');
  }

  displaySocket.disconnect();
  hostSocket.disconnect();

  console.log('\n✅ BOT GAME SIMULATION COMPLETE\n');
  process.exit(0);
}

runTest().catch((err) => {
  console.error('\n❌ TEST FAILED:', err.message);
  process.exit(1);
});
