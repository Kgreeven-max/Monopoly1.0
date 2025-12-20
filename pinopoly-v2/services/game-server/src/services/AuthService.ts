/**
 * Authentication Service
 * Handles JWT token generation and validation
 */

import jwt from 'jsonwebtoken';
import { config } from '../config';

export interface UserTokenPayload {
  userId: string;
  username: string;
  isGuest?: false;
}

export interface GuestTokenPayload {
  guestId: string;
  guestName: string;
  isGuest: true;
}

export type TokenPayload = UserTokenPayload | GuestTokenPayload;

export type DecodedToken = TokenPayload & {
  iat: number;
  exp: number;
  playerId?: string;
  playerName?: string;
  gameId?: string;
};

/**
 * Generate a JWT token for a user or guest
 */
export function generateToken(payload: TokenPayload): string {
  return jwt.sign(payload, config.jwt.secret, {
    expiresIn: config.jwt.expiresIn as string,
  } as jwt.SignOptions);
}

/**
 * Verify and decode a JWT token
 */
export function verifyToken(token: string): DecodedToken | null {
  try {
    return jwt.verify(token, config.jwt.secret) as DecodedToken;
  } catch {
    return null;
  }
}

/**
 * Check if a token payload is for a guest user
 */
export function isGuestToken(payload: TokenPayload): payload is GuestTokenPayload {
  return 'isGuest' in payload && payload.isGuest === true;
}

/**
 * Check if a token payload is for a registered user
 */
export function isUserToken(payload: TokenPayload): payload is UserTokenPayload {
  return 'userId' in payload && !('isGuest' in payload && payload.isGuest);
}

/**
 * Extract player identifier from token payload
 * Returns either the userId or guestId
 */
export function getPlayerId(payload: TokenPayload): string {
  if (isGuestToken(payload)) {
    return payload.guestId;
  }
  return payload.userId;
}

/**
 * Extract player display name from token payload
 */
export function getPlayerName(payload: TokenPayload): string {
  if (isGuestToken(payload)) {
    return payload.guestName;
  }
  return payload.username;
}

/**
 * Generate a refresh token with longer expiration
 */
export function generateRefreshToken(payload: TokenPayload): string {
  return jwt.sign(payload, config.jwt.secret, {
    expiresIn: '30d',
  });
}

/**
 * Validate token format (basic check before full verification)
 */
export function isValidTokenFormat(token: string): boolean {
  if (!token || typeof token !== 'string') {
    return false;
  }

  const parts = token.split('.');
  return parts.length === 3;
}
