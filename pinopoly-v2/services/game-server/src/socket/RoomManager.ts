/**
 * Room Manager - Handles game rooms and state
 */

import { Server } from 'socket.io';
import { PrismaClient } from '@prisma/client';
import {
  GameState,
  GameConfig,
  gameReducer,
  createInitialState,
  generateSeed,
  ActionTypes,
  TokenType,
  BotPersonality,
  Difficulty,
} from '@pinopoly/game-engine';
import { SocketEvents, generateRoomCode, uuid } from '@pinopoly/shared';
import { AuthenticatedSocket } from './SocketServer';
import { config } from '../config';

interface GameRoom {
  id: string;
  code: string;
  state: GameState;
  hostSocketId: string | null;
  displaySockets: Set<string>;
  playerSockets: Map<string, string>; // playerId -> socketId
}

export class RoomManager {
  private rooms: Map<string, GameRoom> = new Map();
  private socketToRoom: Map<string, string> = new Map();

  constructor(
    private io: Server,
    private prisma: PrismaClient
  ) {
    this.setupSocketHandlers();
  }

  private setupSocketHandlers(): void {
    this.io.on('connection', (socket: AuthenticatedSocket) => {
      // Lobby events
      socket.on(SocketEvents.LOBBY_JOIN, (data) => this.handleJoin(socket, data));
      socket.on(SocketEvents.LOBBY_READY, () => this.handleReady(socket));
      socket.on(SocketEvents.LOBBY_UNREADY, () => this.handleUnready(socket));
      socket.on(SocketEvents.LOBBY_ADD_BOT, (data) => this.handleAddBot(socket, data));
      socket.on(SocketEvents.LOBBY_REMOVE_BOT, (data) => this.handleRemoveBot(socket, data));
      socket.on(SocketEvents.LOBBY_START_GAME, () => this.handleStartGame(socket));

      // Game events
      socket.on(SocketEvents.GAME_ROLL_DICE, () => this.handleRollDice(socket));
      socket.on(SocketEvents.GAME_END_TURN, () => this.handleEndTurn(socket));
      socket.on(SocketEvents.GAME_BUY_PROPERTY, (data) => this.handleBuyProperty(socket, data));
      socket.on(SocketEvents.GAME_DECLINE_PROPERTY, (data) => this.handleDeclineProperty(socket, data));
      socket.on(SocketEvents.GAME_BUILD_HOUSE, (data) => this.handleBuildHouse(socket, data));
      socket.on(SocketEvents.GAME_MORTGAGE, (data) => this.handleMortgage(socket, data));
      socket.on(SocketEvents.GAME_UNMORTGAGE, (data) => this.handleUnmortgage(socket, data));

      // Jail events
      socket.on(SocketEvents.GAME_PAY_JAIL_FINE, () => this.handlePayJailFine(socket));
      socket.on(SocketEvents.GAME_USE_JAIL_CARD, () => this.handleUseJailCard(socket));

      // Card events
      socket.on(SocketEvents.GAME_EXECUTE_CARD, () => this.handleExecuteCard(socket));

      // Auction events
      socket.on(SocketEvents.AUCTION_BID, (data) => this.handleAuctionBid(socket, data));
      socket.on(SocketEvents.AUCTION_PASS, (data) => this.handleAuctionPass(socket, data));

      // Disconnect
      socket.on('disconnect', () => this.handleDisconnect(socket));
    });
  }

  // ===========================================================================
  // PUBLIC METHODS
  // ===========================================================================

  async createGame(hostSocketId: string, gameConfig: Partial<GameConfig>): Promise<GameRoom> {
    // Check max games
    if (this.rooms.size >= config.game.maxConcurrentGames) {
      throw new Error('Maximum concurrent games reached');
    }

    const roomCode = this.generateUniqueRoomCode();
    const gameId = uuid();
    const seed = generateSeed();

    // Create initial state
    const state = createInitialState(gameId, roomCode, gameConfig, seed);

    // Create room
    const room: GameRoom = {
      id: gameId,
      code: roomCode,
      state,
      hostSocketId,
      displaySockets: new Set(),
      playerSockets: new Map(),
    };

    this.rooms.set(roomCode, room);

    // Save to database
    await this.prisma.game.create({
      data: {
        id: gameId,
        roomCode,
        status: 'lobby',
        gameConfig: gameConfig as any,
      },
    });

    return room;
  }

  getRoom(roomCode: string): GameRoom | undefined {
    return this.rooms.get(roomCode);
  }

  getRoomByPlayerId(playerId: string): GameRoom | undefined {
    for (const room of this.rooms.values()) {
      if (room.state.players[playerId]) {
        return room;
      }
    }
    return undefined;
  }

  // ===========================================================================
  // LOBBY HANDLERS
  // ===========================================================================

  private async handleJoin(socket: AuthenticatedSocket, data: {
    roomCode: string;
    playerName: string;
    token: TokenType;
    color: string;
  }): Promise<void> {
    try {
      const { roomCode, playerName, token, color } = data;
      const room = this.rooms.get(roomCode);

      if (!room) {
        socket.emit(SocketEvents.JOIN_ERROR, { message: 'Game not found' });
        socket.emit(SocketEvents.ERROR, { code: 'ROOM_NOT_FOUND', message: 'Game not found' });
        return;
      }

      if (room.state.status !== 'lobby') {
        socket.emit(SocketEvents.JOIN_ERROR, { message: 'Game already started' });
        socket.emit(SocketEvents.ERROR, { code: 'GAME_STARTED', message: 'Game already started' });
        return;
      }

      const playerCount = Object.keys(room.state.players).length;
      if (playerCount >= room.state.config.maxPlayers) {
        socket.emit(SocketEvents.JOIN_ERROR, { message: 'Game is full' });
        socket.emit(SocketEvents.ERROR, { code: 'GAME_FULL', message: 'Game is full' });
        return;
      }

      // Add player
      const playerId = uuid();
      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.ADD_PLAYER,
        payload: {
          playerId,
          name: playerName,
          token,
          color,
          socketId: socket.id,
        },
      });

      room.state = newState;
      room.playerSockets.set(playerId, socket.id);
      this.socketToRoom.set(socket.id, roomCode);

      // First player to join becomes the host
      if (room.hostSocketId === 'host-placeholder' || !room.hostSocketId) {
        room.hostSocketId = socket.id;
        console.log(`Player ${playerName} became host of game ${roomCode}`);
      }

      // Set socket context
      socket.playerId = playerId;
      socket.gameId = room.id;
      socket.role = 'player';

      // Join socket room
      socket.join(roomCode);

      // Notify all about new player
      this.io.to(roomCode).emit(SocketEvents.LOBBY_PLAYER_JOINED, {
        player: newState.players[playerId],
        gameState: newState,
      });

      // Send joined confirmation to new player (controller expects this)
      const isHost = room.hostSocketId === socket.id;
      socket.emit(SocketEvents.JOINED_GAME, {
        playerId,
        playerName,
        token,
        isHost,
        gameState: newState,
      });

      // Also send lobby state for displays
      socket.emit(SocketEvents.LOBBY_STATE, this.getLobbyState(room));

      // Save participant to database
      await this.prisma.gameParticipant.create({
        data: {
          gameId: room.id,
          playerName,
          token,
          color,
          isBot: false,
        },
      });
    } catch (error) {
      console.error('Join error:', error);
      socket.emit(SocketEvents.JOIN_ERROR, { message: 'Failed to join game' });
      socket.emit(SocketEvents.ERROR, { code: 'JOIN_ERROR', message: 'Failed to join game' });
    }
  }

  private handleReady(socket: AuthenticatedSocket): void {
    const roomCode = this.socketToRoom.get(socket.id);
    if (!roomCode || !socket.playerId) return;

    const room = this.rooms.get(roomCode);
    if (!room) return;

    // Mark player as ready (would need to add ready state to PlayerState)
    this.io.to(roomCode).emit(SocketEvents.LOBBY_PLAYER_READY, {
      playerId: socket.playerId,
      ready: true,
    });
  }

  private handleUnready(socket: AuthenticatedSocket): void {
    const roomCode = this.socketToRoom.get(socket.id);
    if (!roomCode || !socket.playerId) return;

    this.io.to(roomCode).emit(SocketEvents.LOBBY_PLAYER_READY, {
      playerId: socket.playerId,
      ready: false,
    });
  }

  private async handleAddBot(socket: AuthenticatedSocket, data: {
    personality: BotPersonality;
    difficulty: Difficulty;
  }): Promise<void> {
    console.log('handleAddBot called with:', data);
    const roomCode = this.socketToRoom.get(socket.id);
    if (!roomCode) {
      console.log('handleAddBot: No room code for socket', socket.id);
      return;
    }

    const room = this.rooms.get(roomCode);
    if (!room) {
      console.log('handleAddBot: Room not found:', roomCode);
      return;
    }
    if (room.hostSocketId !== socket.id) {
      console.log('handleAddBot: Not host. hostSocketId:', room.hostSocketId, 'socket.id:', socket.id);
      return;
    }
    console.log('handleAddBot: Adding bot to room', roomCode);

    const botId = uuid();
    const botNumber = Object.values(room.state.players).filter(p => p.isBot).length + 1;
    const tokens: TokenType[] = ['dog', 'cat', 'ship', 'thimble', 'boot', 'wheelbarrow'];
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'];

    const [newState, events] = gameReducer(room.state, {
      type: ActionTypes.ADD_BOT,
      payload: {
        botId,
        name: `Bot ${botNumber}`,
        token: tokens[botNumber % tokens.length],
        color: colors[botNumber % colors.length],
        personality: data.personality,
        difficulty: data.difficulty,
      },
    });

    room.state = newState;

    this.io.to(roomCode).emit(SocketEvents.LOBBY_PLAYER_JOINED, {
      player: newState.players[botId],
    });
  }

  private handleRemoveBot(socket: AuthenticatedSocket, data: { botId: string }): void {
    const roomCode = this.socketToRoom.get(socket.id);
    if (!roomCode) return;

    const room = this.rooms.get(roomCode);
    if (!room || room.hostSocketId !== socket.id) return;

    const [newState, events] = gameReducer(room.state, {
      type: ActionTypes.REMOVE_PLAYER,
      payload: { playerId: data.botId },
    });

    room.state = newState;

    this.io.to(roomCode).emit(SocketEvents.LOBBY_PLAYER_LEFT, {
      playerId: data.botId,
    });
  }

  private async handleStartGame(socket: AuthenticatedSocket): Promise<void> {
    console.log('handleStartGame called');
    const roomCode = this.socketToRoom.get(socket.id);
    if (!roomCode) {
      console.log('handleStartGame: No room code for socket', socket.id);
      return;
    }

    const room = this.rooms.get(roomCode);
    if (!room) {
      console.log('handleStartGame: Room not found:', roomCode);
      return;
    }
    if (room.hostSocketId !== socket.id) {
      console.log('handleStartGame: Not host. hostSocketId:', room.hostSocketId, 'socket.id:', socket.id);
      return;
    }
    console.log('handleStartGame: Starting game', roomCode, 'with', Object.keys(room.state.players).length, 'players');

    try {
      // Countdown
      for (let i = 3; i > 0; i--) {
        this.io.to(roomCode).emit(SocketEvents.LOBBY_GAME_STARTING, { countdown: i });
        await this.sleep(1000);
      }

      // Start game
      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.START_GAME,
        payload: { initiatorId: socket.playerId! },
      });

      room.state = newState;

      // Update database
      await this.prisma.game.update({
        where: { id: room.id },
        data: {
          status: 'playing',
          startedAt: new Date(),
        },
      });

      // Broadcast game started event (controller expects this)
      this.io.to(roomCode).emit(SocketEvents.GAME_STARTED, newState);

      // Broadcast game state
      this.io.to(roomCode).emit(SocketEvents.GAME_STATE, newState);

      // Check if first player is a bot
      this.checkBotTurn(room);
    } catch (error) {
      console.error('Start game error:', error);
      socket.emit(SocketEvents.ERROR, { code: 'START_ERROR', message: 'Failed to start game' });
    }
  }

  // ===========================================================================
  // GAME HANDLERS
  // ===========================================================================

  private handleRollDice(socket: AuthenticatedSocket): void {
    const room = this.getRoomBySocket(socket);
    if (!room || !this.isCurrentPlayer(room, socket.playerId)) return;

    try {
      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.ROLL_DICE,
        payload: { playerId: socket.playerId! },
      });

      room.state = newState;

      // Emit dice roll event
      const diceEvent = events.find(e => e.type === 'DICE_ROLLED');
      if (diceEvent) {
        const diceData = diceEvent.payload.dice as { die1: number; die2: number };
        this.io.to(room.code).emit(SocketEvents.GAME_DICE_ROLLED, {
          playerId: socket.playerId,
          dice: [diceData.die1, diceData.die2],
        });
      }

      // Emit move event
      const moveEvent = events.find(e => e.type === 'PLAYER_MOVED');
      if (moveEvent) {
        this.io.to(room.code).emit(SocketEvents.GAME_PLAYER_MOVED, moveEvent.payload);
      }

      // Emit full state
      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);
    } catch (error) {
      console.error('Roll dice error:', error);
      socket.emit(SocketEvents.ERROR, { code: 'ACTION_ERROR', message: String(error) });
    }
  }

  private handleEndTurn(socket: AuthenticatedSocket): void {
    const room = this.getRoomBySocket(socket);
    if (!room || !this.isCurrentPlayer(room, socket.playerId)) return;

    try {
      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.END_TURN,
        payload: { playerId: socket.playerId! },
      });

      room.state = newState;

      // Emit turn change
      const turnEvent = events.find(e => e.type === 'TURN_CHANGED');
      if (turnEvent) {
        this.io.to(room.code).emit(SocketEvents.GAME_TURN_CHANGED, turnEvent.payload);
      }

      // Emit full state
      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);

      // Check if next player is bot
      this.checkBotTurn(room);
    } catch (error) {
      console.error('End turn error:', error);
      socket.emit(SocketEvents.ERROR, { code: 'ACTION_ERROR', message: String(error) });
    }
  }

  private handleBuyProperty(socket: AuthenticatedSocket, data: { propertyId: number }): void {
    const room = this.getRoomBySocket(socket);
    if (!room || !this.isCurrentPlayer(room, socket.playerId)) return;

    try {
      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.BUY_PROPERTY,
        payload: { playerId: socket.playerId!, propertyId: data.propertyId },
      });

      room.state = newState;

      this.io.to(room.code).emit(SocketEvents.GAME_PROPERTY_BOUGHT, {
        playerId: socket.playerId,
        propertyId: data.propertyId,
      });

      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);
    } catch (error) {
      console.error('Buy property error:', error);
      socket.emit(SocketEvents.ERROR, { code: 'ACTION_ERROR', message: String(error) });
    }
  }

  private handleDeclineProperty(socket: AuthenticatedSocket, data: { propertyId: number }): void {
    const room = this.getRoomBySocket(socket);
    if (!room || !this.isCurrentPlayer(room, socket.playerId)) return;

    try {
      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.DECLINE_PROPERTY,
        payload: { playerId: socket.playerId!, propertyId: data.propertyId },
      });

      room.state = newState;
      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);

      // Check for auction
      if (newState.activeAuction) {
        this.io.to(room.code).emit(SocketEvents.AUCTION_STARTED, newState.activeAuction);
      }
    } catch (error) {
      socket.emit(SocketEvents.ERROR, { code: 'ACTION_ERROR', message: String(error) });
    }
  }

  private handleBuildHouse(socket: AuthenticatedSocket, data: { propertyId: number }): void {
    const room = this.getRoomBySocket(socket);
    if (!room) return;

    try {
      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.BUILD_HOUSE,
        payload: { playerId: socket.playerId!, propertyId: data.propertyId },
      });

      room.state = newState;

      this.io.to(room.code).emit(SocketEvents.GAME_HOUSE_BUILT, {
        playerId: socket.playerId,
        propertyId: data.propertyId,
        houses: newState.properties[data.propertyId].houses,
      });

      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);
    } catch (error) {
      socket.emit(SocketEvents.ERROR, { code: 'ACTION_ERROR', message: String(error) });
    }
  }

  private handleMortgage(socket: AuthenticatedSocket, data: { propertyId: number }): void {
    const room = this.getRoomBySocket(socket);
    if (!room) return;

    try {
      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.MORTGAGE_PROPERTY,
        payload: { playerId: socket.playerId!, propertyId: data.propertyId },
      });

      room.state = newState;
      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);
    } catch (error) {
      socket.emit(SocketEvents.ERROR, { code: 'ACTION_ERROR', message: String(error) });
    }
  }

  private handleUnmortgage(socket: AuthenticatedSocket, data: { propertyId: number }): void {
    const room = this.getRoomBySocket(socket);
    if (!room) return;

    try {
      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.UNMORTGAGE_PROPERTY,
        payload: { playerId: socket.playerId!, propertyId: data.propertyId },
      });

      room.state = newState;
      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);
    } catch (error) {
      socket.emit(SocketEvents.ERROR, { code: 'ACTION_ERROR', message: String(error) });
    }
  }

  private handlePayJailFine(socket: AuthenticatedSocket): void {
    const room = this.getRoomBySocket(socket);
    if (!room || !this.isCurrentPlayer(room, socket.playerId)) return;

    try {
      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.PAY_JAIL_FINE,
        payload: { playerId: socket.playerId! },
      });

      room.state = newState;
      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);
    } catch (error) {
      socket.emit(SocketEvents.ERROR, { code: 'ACTION_ERROR', message: String(error) });
    }
  }

  private handleUseJailCard(socket: AuthenticatedSocket): void {
    const room = this.getRoomBySocket(socket);
    if (!room || !this.isCurrentPlayer(room, socket.playerId)) return;

    try {
      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.USE_JAIL_CARD,
        payload: { playerId: socket.playerId! },
      });

      room.state = newState;
      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);
    } catch (error) {
      socket.emit(SocketEvents.ERROR, { code: 'ACTION_ERROR', message: String(error) });
    }
  }

  private handleExecuteCard(socket: AuthenticatedSocket): void {
    const room = this.getRoomBySocket(socket);
    if (!room || !this.isCurrentPlayer(room, socket.playerId)) return;

    try {
      if (!room.state.currentCard) {
        socket.emit(SocketEvents.ERROR, { code: 'ACTION_ERROR', message: 'No card to execute' });
        return;
      }

      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.EXECUTE_CARD,
        payload: {
          playerId: socket.playerId!,
          cardId: room.state.currentCard.cardId,
        },
      });

      room.state = newState;

      // Emit card drawn event with details
      const cardEvent = events.find(e => e.type === 'CARD_DRAWN');
      if (cardEvent) {
        this.io.to(room.code).emit(SocketEvents.GAME_CARD_DRAWN, cardEvent.payload);
      }

      // Emit move event if player moved
      const moveEvent = events.find(e => e.type === 'PLAYER_MOVED');
      if (moveEvent) {
        this.io.to(room.code).emit(SocketEvents.GAME_PLAYER_MOVED, moveEvent.payload);
      }

      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);

      // Check if next player is a bot
      if (newState.phase === 'turn_end' || newState.phase === 'pre_roll') {
        // Allow turn to continue if needed
      }
    } catch (error) {
      console.error('Execute card error:', error);
      socket.emit(SocketEvents.ERROR, { code: 'ACTION_ERROR', message: String(error) });
    }
  }

  private handleAuctionBid(socket: AuthenticatedSocket, data: { auctionId: string; amount: number }): void {
    const room = this.getRoomBySocket(socket);
    if (!room || !room.state.activeAuction) return;

    try {
      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.PLACE_BID,
        payload: {
          playerId: socket.playerId!,
          auctionId: data.auctionId,
          amount: data.amount,
        },
      });

      room.state = newState;

      this.io.to(room.code).emit(SocketEvents.AUCTION_BID_PLACED, {
        playerId: socket.playerId,
        amount: data.amount,
      });

      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);
    } catch (error) {
      socket.emit(SocketEvents.ERROR, { code: 'ACTION_ERROR', message: String(error) });
    }
  }

  private handleAuctionPass(socket: AuthenticatedSocket, data: { auctionId: string }): void {
    const room = this.getRoomBySocket(socket);
    if (!room || !room.state.activeAuction) return;

    try {
      const [newState, events] = gameReducer(room.state, {
        type: ActionTypes.PASS_AUCTION,
        payload: {
          playerId: socket.playerId!,
          auctionId: data.auctionId,
        },
      });

      room.state = newState;

      // Check if auction ended
      if (!newState.activeAuction) {
        const auctionEvent = events.find(e => e.type === 'AUCTION_ENDED');
        if (auctionEvent) {
          this.io.to(room.code).emit(SocketEvents.AUCTION_ENDED, auctionEvent.payload);
        }
      }

      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);
    } catch (error) {
      socket.emit(SocketEvents.ERROR, { code: 'ACTION_ERROR', message: String(error) });
    }
  }

  private handleDisconnect(socket: AuthenticatedSocket): void {
    const roomCode = this.socketToRoom.get(socket.id);
    if (!roomCode) return;

    const room = this.rooms.get(roomCode);
    if (!room) return;

    // Remove from maps
    this.socketToRoom.delete(socket.id);
    if (socket.playerId) {
      room.playerSockets.delete(socket.playerId);
    }

    // Notify room
    if (socket.playerId) {
      this.io.to(roomCode).emit('player:disconnected', {
        playerId: socket.playerId,
      });
    }

    // If room is empty and in lobby, delete it
    if (room.playerSockets.size === 0 && room.state.status === 'lobby') {
      this.rooms.delete(roomCode);
    }
  }

  // ===========================================================================
  // HELPER METHODS
  // ===========================================================================

  private getRoomBySocket(socket: AuthenticatedSocket): GameRoom | undefined {
    const roomCode = this.socketToRoom.get(socket.id);
    if (!roomCode) return undefined;
    return this.rooms.get(roomCode);
  }

  private isCurrentPlayer(room: GameRoom, playerId: string | undefined): boolean {
    if (!playerId) return false;
    const currentPlayerId = room.state.playerOrder[room.state.currentPlayerIndex];
    return currentPlayerId === playerId;
  }

  private getLobbyState(room: GameRoom) {
    return {
      roomCode: room.code,
      players: Object.values(room.state.players),
      config: room.state.config,
      hostId: room.hostSocketId,
    };
  }

  private generateUniqueRoomCode(): string {
    let code: string;
    do {
      code = generateRoomCode();
    } while (this.rooms.has(code));
    return code;
  }

  private async checkBotTurn(room: GameRoom): Promise<void> {
    const currentPlayerId = room.state.playerOrder[room.state.currentPlayerIndex];
    const currentPlayer = room.state.players[currentPlayerId];

    if (currentPlayer?.isBot) {
      // Add delay for realism
      await this.sleep(config.game.botThinkDelayMs);

      // TODO: Queue bot action to worker
      // For now, simple auto-play
      this.executeBotTurn(room, currentPlayerId);
    }
  }

  private async executeBotTurn(room: GameRoom, botId: string): Promise<void> {
    // Simple bot logic - just roll and end turn
    console.log('Bot', botId, 'taking turn');
    try {
      // Roll dice
      let [newState, events] = gameReducer(room.state, {
        type: ActionTypes.ROLL_DICE,
        payload: { playerId: botId },
      });
      room.state = newState;

      // Emit dice roll event
      const diceEvent = events.find(e => e.type === 'DICE_ROLLED');
      if (diceEvent) {
        const diceData = diceEvent.payload.dice as { die1: number; die2: number };
        this.io.to(room.code).emit(SocketEvents.GAME_DICE_ROLLED, {
          playerId: botId,
          dice: [diceData.die1, diceData.die2],
        });
        console.log('Bot rolled:', diceData.die1, '+', diceData.die2);
      }

      // Emit move event
      const moveEvent = events.find(e => e.type === 'PLAYER_MOVED');
      if (moveEvent) {
        this.io.to(room.code).emit(SocketEvents.GAME_PLAYER_MOVED, moveEvent.payload);
      }

      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);

      await this.sleep(1000);

      // Handle buy decision if applicable
      if (newState.phase === 'buy_decision') {
        const currentPosition = newState.players[botId].position;
        const property = newState.properties[currentPosition];

        if (property && !property.ownerId) {
          // Simple logic: buy if can afford
          if (newState.players[botId].money >= property.price) {
            [newState, events] = gameReducer(newState, {
              type: ActionTypes.BUY_PROPERTY,
              payload: { playerId: botId, propertyId: currentPosition },
            });
            room.state = newState;
            this.io.to(room.code).emit(SocketEvents.GAME_PROPERTY_BOUGHT, {
              playerId: botId,
              propertyId: currentPosition,
            });
            console.log('Bot bought property:', currentPosition);
          } else {
            [newState, events] = gameReducer(newState, {
              type: ActionTypes.DECLINE_PROPERTY,
              payload: { playerId: botId, propertyId: currentPosition },
            });
            room.state = newState;
          }
          this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);
          await this.sleep(500);
        }
      }

      // Handle card action (Chance/Community Chest)
      if (newState.phase === 'card_action' && newState.currentCard) {
        console.log('Bot executing card:', newState.currentCard.cardId);

        // Emit the card drawn event
        this.io.to(room.code).emit(SocketEvents.GAME_CARD_DRAWN, {
          cardId: newState.currentCard.cardId,
          deck: newState.currentCard.deck,
          playerId: botId,
        });

        await this.sleep(1500); // Let players see the card

        // Execute the card
        [newState, events] = gameReducer(newState, {
          type: ActionTypes.EXECUTE_CARD,
          payload: {
            playerId: botId,
            cardId: newState.currentCard.cardId,
          },
        });
        room.state = newState;

        // Emit any movement events
        const moveEvent = events.find(e => e.type === 'PLAYER_MOVED');
        if (moveEvent) {
          this.io.to(room.code).emit(SocketEvents.GAME_PLAYER_MOVED, moveEvent.payload);
        }

        this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);
        await this.sleep(500);

        // If the card caused us to land on a new space, handle it
        if (newState.phase === 'buy_decision') {
          const currentPosition = newState.players[botId].position;
          const property = newState.properties[currentPosition];

          if (property && !property.ownerId) {
            if (newState.players[botId].money >= property.price) {
              [newState, events] = gameReducer(newState, {
                type: ActionTypes.BUY_PROPERTY,
                payload: { playerId: botId, propertyId: currentPosition },
              });
              room.state = newState;
              this.io.to(room.code).emit(SocketEvents.GAME_PROPERTY_BOUGHT, {
                playerId: botId,
                propertyId: currentPosition,
              });
              console.log('Bot bought property after card:', currentPosition);
            } else {
              [newState, events] = gameReducer(newState, {
                type: ActionTypes.DECLINE_PROPERTY,
                payload: { playerId: botId, propertyId: currentPosition },
              });
              room.state = newState;
            }
            this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);
            await this.sleep(500);
          }
        }
      }

      // End turn
      if (newState.phase === 'turn_end' || newState.phase === 'landed') {
        [newState, events] = gameReducer(newState, {
          type: ActionTypes.END_TURN,
          payload: { playerId: botId },
        });
        room.state = newState;

        // Emit turn change event
        const turnEvent = events.find(e => e.type === 'TURN_CHANGED');
        if (turnEvent) {
          this.io.to(room.code).emit(SocketEvents.GAME_TURN_CHANGED, turnEvent.payload);
        }

        this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);
        console.log('Bot ended turn, next player index:', newState.currentPlayerIndex);

        // Check if next player is also a bot
        this.checkBotTurn(room);
      }
    } catch (error) {
      console.error('Bot turn error:', error);
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Handle a bot decision from the bot worker
   */
  handleBotDecision(gameId: string, decision: any): void {
    const room = Array.from(this.rooms.values()).find(r => r.id === gameId);
    if (!room || !room.state) {
      console.warn(`Bot decision for unknown game: ${gameId}`);
      return;
    }

    try {
      const [newState, events] = gameReducer(room.state, decision.action);
      room.state = newState;
      this.io.to(room.code).emit(SocketEvents.GAME_STATE, newState);

      // Check if next player is also a bot
      this.checkBotTurn(room);
    } catch (error) {
      console.error('Error applying bot decision:', error);
    }
  }
}
