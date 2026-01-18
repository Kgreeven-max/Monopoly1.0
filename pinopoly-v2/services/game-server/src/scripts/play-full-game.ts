/**
 * Play Full Game Script
 *
 * Automated script that plays through a complete Pinopoly game with bots
 * until there's a winner.
 *
 * Usage:
 *   npx tsx src/scripts/play-full-game.ts
 *
 * Requires the game server to be running on localhost:3000
 */

import { io, Socket } from 'socket.io-client';
import { SocketEvents, TOKEN_TYPES, BOT_PERSONALITIES, DIFFICULTIES } from '@pinopoly/shared';

const SERVER_URL = process.env.SERVER_URL || 'http://localhost:3000';

interface PlayerState {
  id: string;
  name: string;
  money: number;
  position: number;
  isBot: boolean;
  isBankrupt: boolean;
  botPersonality?: string;
}

interface PropertyState {
  id: number;
  position: number;
  name: string;
  price: number;
  ownerId: string | null;
  houses: number;
  isMortgaged: boolean;
}

interface EconomyState {
  phase: string;
  cyclePosition: number;
  rentMultiplier: number;
  propertyValueMultiplier: number;
}

interface GameState {
  id: string;
  roomCode: string;
  status: 'lobby' | 'playing' | 'paused' | 'finished';
  round: number;
  phase: string;
  currentPlayerIndex: number;
  playerOrder: string[];
  players: Record<string, PlayerState>;
  properties: Record<number, PropertyState>;
  economy: EconomyState;
  lastDiceRoll?: { die1: number; die2: number };
  currentCard?: { cardId: string; deck: string } | null;
  activeTrades?: any[];
}

interface JoinedGameResponse {
  playerId: string;
  playerName: string;
  isHost: boolean;
  sessionToken: string;
  gameState: GameState;
}

class GameRunner {
  private socket: Socket;
  private roomCode: string = '';
  private playerId: string = '';
  private gameState: GameState | null = null;
  private startTime: number = 0;
  private botCount = 0;
  private readonly targetBots = 3;
  private isProcessingTurn = false;
  private turnCheckInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.socket = io(SERVER_URL, {
      transports: ['websocket'],
      autoConnect: false,
    });
    this.setupSocketListeners();
  }

  private setupSocketListeners(): void {
    this.socket.on('connect', () => {
      console.log(`[CONNECT] Connected to server (socket: ${this.socket.id})`);
    });

    this.socket.on('disconnect', (reason) => {
      console.log(`[DISCONNECT] Disconnected: ${reason}`);
      if (this.turnCheckInterval) {
        clearInterval(this.turnCheckInterval);
      }
    });

    this.socket.on(SocketEvents.JOINED_GAME, (data: JoinedGameResponse) => {
      this.playerId = data.playerId;
      this.gameState = data.gameState;
      console.log(`[JOINED] Joined as ${data.playerName} (host: ${data.isHost})`);
      console.log(`[INFO] Room code: ${this.roomCode}`);

      // Add bots after joining
      this.addBots();
    });

    this.socket.on(SocketEvents.JOIN_ERROR, (data: { message: string }) => {
      console.error(`[ERROR] Join failed: ${data.message}`);
      this.cleanup();
    });

    this.socket.on(SocketEvents.PLAYER_JOINED, (data: { gameState: GameState }) => {
      this.gameState = data.gameState;
      const players = Object.values(data.gameState.players);
      const bots = players.filter(p => p.isBot);
      this.botCount = bots.length;

      console.log(`[PLAYER] Player joined. Total players: ${players.length} (${bots.length} bots)`);

      // Start game when we have 3 bots
      if (this.botCount === this.targetBots) {
        console.log('[INFO] All bots added. Starting game in 2 seconds...');
        setTimeout(() => this.startGame(), 2000);
      }
    });

    this.socket.on(SocketEvents.LOBBY_GAME_STARTING, (data: { countdown: number }) => {
      console.log(`[COUNTDOWN] Game starting in ${data.countdown}...`);
    });

    this.socket.on(SocketEvents.GAME_STARTED, (state: GameState) => {
      this.gameState = state;
      this.startTime = Date.now();
      console.log('\n' + '='.repeat(60));
      console.log('GAME STARTED!');
      console.log('='.repeat(60));
      this.printPlayers();

      // Start turn checking to auto-play for human
      this.startTurnChecker();
    });

    this.socket.on(SocketEvents.GAME_STATE, (state: GameState) => {
      const previousPhase = this.gameState?.phase;
      this.gameState = state;

      // Check if game ended
      if (state.status === 'finished') {
        const winner = Object.values(state.players).find(p => !p.isBankrupt);
        if (winner) {
          this.handleGameEnd(winner.id);
        }
        return;
      }

      // Check if it's our turn and we need to take action
      if (state.status === 'playing' && !this.isProcessingTurn) {
        this.checkAndPlayTurn();
      }
    });

    this.socket.on(SocketEvents.GAME_DICE_ROLLED, (data: { playerId: string; dice: number[] }) => {
      const player = this.gameState?.players[data.playerId];
      if (player) {
        console.log(`[DICE] ${player.name} rolled ${data.dice[0]} + ${data.dice[1]} = ${data.dice[0] + data.dice[1]}`);
      }
    });

    this.socket.on(SocketEvents.GAME_PLAYER_MOVED, (data: { playerId: string; to?: number; newPosition?: number; passedGo?: boolean }) => {
      const player = this.gameState?.players[data.playerId];
      const pos = data.to ?? data.newPosition;
      if (player && pos !== undefined) {
        const positionName = this.getPositionName(pos);
        console.log(`[MOVE] ${player.name} moved to ${positionName}`);
        if (data.passedGo) {
          console.log(`[GO] ${player.name} passed GO - collected $200!`);
        }
      }
    });

    this.socket.on(SocketEvents.GAME_PROPERTY_BOUGHT, (data: { playerId: string; propertyId: number }) => {
      const player = this.gameState?.players[data.playerId];
      const property = this.gameState?.properties[data.propertyId];
      if (player && property) {
        console.log(`[BUY] ${player.name} bought ${property.name} for $${property.price}`);
      }
    });

    this.socket.on(SocketEvents.GAME_RENT_PAID, (data: { fromId: string; toId: string; amount: number }) => {
      const from = this.gameState?.players[data.fromId];
      const to = this.gameState?.players[data.toId];
      if (from && to) {
        console.log(`[RENT] ${from.name} paid $${data.amount} rent to ${to.name}`);
      }
    });

    this.socket.on(SocketEvents.GAME_HOUSE_BUILT, (data: { playerId: string; propertyId: number; houses: number }) => {
      const player = this.gameState?.players[data.playerId];
      const property = this.gameState?.properties[data.propertyId];
      if (player && property) {
        const houseText = data.houses === 5 ? 'a hotel' : `${data.houses} house(s)`;
        console.log(`[BUILD] ${player.name} built ${houseText} on ${property.name}`);
      }
    });

    this.socket.on(SocketEvents.GAME_CARD_DRAWN, (data: { cardId: string; deck: string; playerId: string }) => {
      const player = this.gameState?.players[data.playerId];
      if (player) {
        console.log(`[CARD] ${player.name} drew a ${data.deck} card: ${data.cardId}`);
      }
    });

    this.socket.on(SocketEvents.GAME_TURN_CHANGED, (data: { previousPlayerId: string; nextPlayerId: string; round: number; gameState?: GameState }) => {
      if (data.gameState) {
        this.gameState = data.gameState;
      }
      const nextPlayer = this.gameState?.players[data.nextPlayerId];
      if (nextPlayer) {
        console.log(`\n[TURN] Round ${data.round} - ${nextPlayer.name}'s turn`);
        this.printPlayerStatus(data.nextPlayerId);
      }

      // Reset processing flag and check if it's our turn
      this.isProcessingTurn = false;
      setTimeout(() => this.checkAndPlayTurn(), 500);
    });

    // Economy events
    this.socket.on(SocketEvents.ECONOMY_CHANGED, (data: { phase: string; previousPhase: string; cyclePosition: number; rentMultiplier: number; propertyValueMultiplier: number }) => {
      console.log(`\n[ECONOMY] Phase changed: ${data.previousPhase} -> ${data.phase}`);
      console.log(`  Cycle position: ${data.cyclePosition}`);
      console.log(`  Rent multiplier: ${data.rentMultiplier}x`);
      console.log(`  Property value multiplier: ${data.propertyValueMultiplier}x`);
    });

    // Trade events
    this.socket.on(SocketEvents.TRADE_PROPOSED, (data: { id: string; proposerId: string; recipientId: string; offer: any; request: any; isCounter?: boolean }) => {
      const proposer = this.gameState?.players[data.proposerId];
      const recipient = this.gameState?.players[data.recipientId];
      const counterText = data.isCounter ? ' (counter-offer)' : '';
      console.log(`\n[TRADE] ${proposer?.name || data.proposerId} proposed trade to ${recipient?.name || data.recipientId}${counterText}`);

      if (data.offer?.propertyIds?.length > 0) {
        const propNames = data.offer.propertyIds.map((id: number) => this.gameState?.properties[id]?.name || `Property ${id}`);
        console.log(`  Offering: ${propNames.join(', ')}${data.offer.money ? ` + $${data.offer.money}` : ''}`);
      } else if (data.offer?.money) {
        console.log(`  Offering: $${data.offer.money}`);
      }

      if (data.request?.propertyIds?.length > 0) {
        const propNames = data.request.propertyIds.map((id: number) => this.gameState?.properties[id]?.name || `Property ${id}`);
        console.log(`  Requesting: ${propNames.join(', ')}${data.request.money ? ` + $${data.request.money}` : ''}`);
      } else if (data.request?.money) {
        console.log(`  Requesting: $${data.request.money}`);
      }
    });

    this.socket.on(SocketEvents.TRADE_ACCEPTED, (data: { tradeId: string; proposerId: string; recipientId: string }) => {
      const proposer = this.gameState?.players[data.proposerId];
      const recipient = this.gameState?.players[data.recipientId];
      console.log(`[TRADE] ${recipient?.name || data.recipientId} ACCEPTED trade from ${proposer?.name || data.proposerId}`);
    });

    this.socket.on(SocketEvents.TRADE_REJECTED, (data: { tradeId: string; rejectedBy: string }) => {
      const rejecter = this.gameState?.players[data.rejectedBy];
      console.log(`[TRADE] ${rejecter?.name || data.rejectedBy} REJECTED trade`);
    });

    this.socket.on(SocketEvents.GAME_PLAYER_BANKRUPT, (data: { playerId: string; creditorId?: string }) => {
      const player = this.gameState?.players[data.playerId];
      const creditor = data.creditorId ? this.gameState?.players[data.creditorId] : null;
      if (player) {
        console.log('\n' + '-'.repeat(40));
        console.log(`[BANKRUPT] ${player.name} has gone BANKRUPT!`);
        if (creditor) {
          console.log(`[INFO] Assets transferred to ${creditor.name}`);
        }
        console.log('-'.repeat(40));

        const remainingPlayers = Object.values(this.gameState?.players || {}).filter(p => !p.isBankrupt);
        console.log(`[INFO] ${remainingPlayers.length} players remaining`);
      }
    });

    this.socket.on(SocketEvents.GAME_ENDED, (data: { winnerId: string }) => {
      this.handleGameEnd(data.winnerId);
    });

    this.socket.on(SocketEvents.ERROR, (data: { code: string; message: string }) => {
      console.error(`[ERROR] ${data.code}: ${data.message}`);
    });
  }

  private startTurnChecker(): void {
    // Periodically check if it's our turn (backup for missed events)
    this.turnCheckInterval = setInterval(() => {
      if (this.gameState?.status === 'playing' && !this.isProcessingTurn) {
        this.checkAndPlayTurn();
      }
    }, 2000);
  }

  private async checkAndPlayTurn(): Promise<void> {
    if (!this.gameState || this.gameState.status !== 'playing') return;
    if (this.isProcessingTurn) return;

    const currentPlayerId = this.gameState.playerOrder[this.gameState.currentPlayerIndex];

    // Only act if it's our turn (the human player)
    if (currentPlayerId !== this.playerId) return;

    const player = this.gameState.players[this.playerId];
    if (!player || player.isBankrupt) return;

    this.isProcessingTurn = true;

    console.log(`[AUTO] Taking turn for ${player.name} (phase: ${this.gameState.phase})`);

    try {
      await this.sleep(500); // Small delay for realism

      switch (this.gameState.phase) {
        case 'pre_roll':
          console.log('[AUTO] Rolling dice...');
          this.socket.emit(SocketEvents.GAME_ROLL_DICE);
          break;

        case 'jail_decision':
          // Pay fine if we have enough money, otherwise try to roll for doubles
          if (player.money >= 50) {
            console.log('[AUTO] Paying jail fine...');
            this.socket.emit(SocketEvents.GAME_PAY_JAIL_FINE);
          } else {
            console.log('[AUTO] Rolling for doubles to escape jail...');
            this.socket.emit(SocketEvents.GAME_ROLL_FOR_DOUBLES);
          }
          break;

        case 'buy_decision':
          const position = player.position;
          const property = this.gameState.properties[position];
          if (property && !property.ownerId && player.money >= property.price) {
            console.log(`[AUTO] Buying ${property.name}...`);
            this.socket.emit(SocketEvents.GAME_BUY_PROPERTY, { propertyId: position });
          } else {
            console.log('[AUTO] Declining to buy...');
            this.socket.emit(SocketEvents.GAME_DECLINE_PROPERTY, { propertyId: position });
          }
          break;

        case 'card_action':
          if (this.gameState.currentCard) {
            console.log('[AUTO] Executing card...');
            this.socket.emit(SocketEvents.GAME_EXECUTE_CARD);
          }
          break;

        case 'turn_end':
        case 'landed':
          console.log('[AUTO] Ending turn...');
          this.socket.emit(SocketEvents.GAME_END_TURN);
          break;

        case 'bankruptcy':
          console.log('[AUTO] Declaring bankruptcy...');
          this.socket.emit(SocketEvents.GAME_DECLARE_BANKRUPTCY);
          break;

        default:
          // Unknown phase, try to end turn
          console.log(`[AUTO] Unknown phase: ${this.gameState.phase}, attempting to end turn...`);
          this.socket.emit(SocketEvents.GAME_END_TURN);
      }
    } catch (error) {
      console.error('[AUTO] Error during turn:', error);
    }

    // Allow next action after a delay
    setTimeout(() => {
      this.isProcessingTurn = false;
    }, 1000);
  }

  async run(): Promise<void> {
    console.log('\n' + '='.repeat(60));
    console.log('PINOPOLY - AUTOMATED FULL GAME');
    console.log('='.repeat(60));
    console.log(`Server: ${SERVER_URL}`);

    try {
      // Step 1: Create game via API
      console.log('\n[STEP 1] Creating game...');
      await this.createGame();

      // Step 2: Connect socket
      console.log('\n[STEP 2] Connecting to game server...');
      this.socket.connect();

      // Wait for connection
      await this.waitForEvent('connect', 5000);

      // Step 3: Join as host
      console.log('\n[STEP 3] Joining game as host...');
      this.joinGame();

      // The rest happens via event handlers
      // - JOINED_GAME triggers addBots()
      // - PLAYER_JOINED (3 bots) triggers startGame()
      // - GAME_ENDED triggers handleGameEnd()
    } catch (error) {
      console.error('[FATAL]', error);
      this.cleanup();
    }
  }

  private async createGame(): Promise<void> {
    const response = await fetch(`${SERVER_URL}/api/games`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        hostName: 'GameMaster',
        config: {
          maxPlayers: 4,
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create game: ${response.statusText}`);
    }

    const data = await response.json() as { roomCode: string };
    this.roomCode = data.roomCode;
    console.log(`[CREATED] Game created with room code: ${this.roomCode}`);
  }

  private joinGame(): void {
    this.socket.emit(SocketEvents.LOBBY_JOIN, {
      roomCode: this.roomCode,
      playerName: 'GameMaster',
      token: TOKEN_TYPES[0], // 'car'
      color: '#FF6B6B',
    });
  }

  private addBots(): void {
    console.log('\n[STEP 4] Adding 3 bots...');

    const botConfigs = [
      { personality: BOT_PERSONALITIES[1], difficulty: DIFFICULTIES[2] }, // aggressive, hard
      { personality: BOT_PERSONALITIES[0], difficulty: DIFFICULTIES[1] }, // conservative, normal
      { personality: BOT_PERSONALITIES[2], difficulty: DIFFICULTIES[2] }, // strategic, hard
    ];

    // Add bots with small delays between each
    botConfigs.forEach((config, index) => {
      setTimeout(() => {
        console.log(`[BOT] Adding bot ${index + 1}: ${config.personality} (${config.difficulty})`);
        this.socket.emit(SocketEvents.LOBBY_ADD_BOT, config);
      }, index * 500);
    });
  }

  private startGame(): void {
    console.log('\n[STEP 5] Starting game...');
    this.socket.emit(SocketEvents.LOBBY_START_GAME);
  }

  private handleGameEnd(winnerId: string): void {
    if (this.turnCheckInterval) {
      clearInterval(this.turnCheckInterval);
    }

    const winner = this.gameState?.players[winnerId];
    const elapsed = Date.now() - this.startTime;
    const minutes = Math.floor(elapsed / 60000);
    const seconds = Math.floor((elapsed % 60000) / 1000);

    console.log('\n' + '='.repeat(60));
    console.log('GAME OVER!');
    console.log('='.repeat(60));

    if (winner) {
      console.log(`\nWINNER: ${winner.name}`);
      console.log(`Final money: $${winner.money.toLocaleString()}`);
    }

    console.log(`\nGame duration: ${minutes}m ${seconds}s`);
    console.log(`Total rounds: ${this.gameState?.round || 0}`);

    // Print final standings
    console.log('\n--- FINAL STANDINGS ---');
    const players = Object.values(this.gameState?.players || {});
    const sorted = [...players].sort((a, b) => {
      if (a.isBankrupt && !b.isBankrupt) return 1;
      if (!a.isBankrupt && b.isBankrupt) return -1;
      return b.money - a.money;
    });

    sorted.forEach((player, index) => {
      const status = player.isBankrupt ? 'BANKRUPT' : `$${player.money.toLocaleString()}`;
      const medal = index === 0 ? ' [WINNER]' : '';
      console.log(`${index + 1}. ${player.name}: ${status}${medal}`);
    });

    console.log('\n' + '='.repeat(60));
    this.cleanup();
  }

  private printPlayers(): void {
    console.log('\n--- PLAYERS ---');
    Object.values(this.gameState?.players || {}).forEach((player) => {
      const botInfo = player.isBot ? ` (Bot - ${player.botPersonality})` : ' (Human)';
      console.log(`  ${player.name}: $${player.money.toLocaleString()}${botInfo}`);
    });
    console.log('');
  }

  private printPlayerStatus(playerId: string): void {
    const player = this.gameState?.players[playerId];
    if (player) {
      const properties = Object.values(this.gameState?.properties || {}).filter(p => p.ownerId === playerId);
      console.log(`  Money: $${player.money.toLocaleString()} | Properties: ${properties.length}`);
    }
  }

  private getPositionName(position: number): string {
    const names: Record<number, string> = {
      0: 'GO',
      1: 'Mediterranean Avenue',
      2: 'Community Chest',
      3: 'Baltic Avenue',
      4: 'Income Tax',
      5: 'Reading Railroad',
      6: 'Oriental Avenue',
      7: 'Chance',
      8: 'Vermont Avenue',
      9: 'Connecticut Avenue',
      10: 'Jail/Just Visiting',
      11: 'St. Charles Place',
      12: 'Electric Company',
      13: 'States Avenue',
      14: 'Virginia Avenue',
      15: 'Pennsylvania Railroad',
      16: 'St. James Place',
      17: 'Community Chest',
      18: 'Tennessee Avenue',
      19: 'New York Avenue',
      20: 'Free Parking',
      21: 'Kentucky Avenue',
      22: 'Chance',
      23: 'Indiana Avenue',
      24: 'Illinois Avenue',
      25: 'B. & O. Railroad',
      26: 'Atlantic Avenue',
      27: 'Ventnor Avenue',
      28: 'Water Works',
      29: 'Marvin Gardens',
      30: 'Go To Jail',
      31: 'Pacific Avenue',
      32: 'North Carolina Avenue',
      33: 'Community Chest',
      34: 'Pennsylvania Avenue',
      35: 'Short Line',
      36: 'Chance',
      37: 'Park Place',
      38: 'Luxury Tax',
      39: 'Boardwalk',
    };
    return names[position] || `Position ${position}`;
  }

  private waitForEvent(event: string, timeout: number): Promise<void> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error(`Timeout waiting for ${event}`));
      }, timeout);

      this.socket.once(event, () => {
        clearTimeout(timer);
        resolve();
      });
    });
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private cleanup(): void {
    console.log('\n[CLEANUP] Disconnecting...');
    if (this.turnCheckInterval) {
      clearInterval(this.turnCheckInterval);
    }
    this.socket.disconnect();
    process.exit(0);
  }
}

// Run the game
const runner = new GameRunner();
runner.run().catch(console.error);
