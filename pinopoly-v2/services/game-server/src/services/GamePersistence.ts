/**
 * Game Persistence Service (Stub)
 * TODO: Implement full persistence when schema is finalized
 */

import type { GameState } from '@pinopoly/game-engine';

export interface SaveGameOptions {
  gameId: string;
  state: GameState;
  hostId?: string;
}

export interface GameRecord {
  id: string;
  roomCode: string;
  status: string;
  hostId?: string;
  gameConfig: any;
  gameState: any;
  startedAt?: Date;
  endedAt?: Date;
}

/**
 * Save game state (stub - no-op)
 */
export async function saveGameState(options: SaveGameOptions): Promise<void> {
  // Stub implementation - log only
  console.log(`[GamePersistence] Would save game ${options.gameId}`);
}

/**
 * Load game state (stub)
 */
export async function loadGameState(gameId: string): Promise<GameState | null> {
  return null;
}

/**
 * Load game by room code (stub)
 */
export async function loadGameByRoomCode(roomCode: string): Promise<GameState | null> {
  return null;
}

/**
 * Mark game as started (stub)
 */
export async function markGameStarted(gameId: string): Promise<void> {
  console.log(`[GamePersistence] Game ${gameId} started`);
}

/**
 * Mark game as finished (stub)
 */
export async function markGameFinished(
  gameId: string,
  winnerId?: string,
  durationSeconds?: number
): Promise<void> {
  console.log(`[GamePersistence] Game ${gameId} finished`);
}

/**
 * Record game participant (stub)
 */
export async function recordParticipant(
  gameId: string,
  userId: string | null,
  playerName: string,
  token: string
): Promise<void> {
  console.log(`[GamePersistence] Participant ${playerName} joined ${gameId}`);
}

/**
 * Update participant final stats (stub)
 */
export async function updateParticipantStats(
  gameId: string,
  playerId: string,
  finalPosition: number,
  finalNetWorth: number
): Promise<void> {
  console.log(`[GamePersistence] Updated stats for ${playerId}`);
}

/**
 * Log an audit event (stub)
 */
export async function logAuditEvent(
  gameId: string,
  actionType: string,
  actionData: any,
  userId?: string,
  sessionId?: string
): Promise<void> {
  // No-op for now
}

/**
 * Get active games count (stub)
 */
export async function getActiveGamesCount(): Promise<number> {
  return 0;
}

/**
 * Clean up stale games (stub)
 */
export async function cleanupStaleGames(maxAgeMinutes: number = 60): Promise<number> {
  return 0;
}
