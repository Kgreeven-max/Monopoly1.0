/**
 * Pinopoly Game Engine
 *
 * Pure, deterministic game logic with no I/O dependencies.
 * Use this package for:
 * - Server-side game state management
 * - Client-side state prediction
 * - Testing and replay
 */

// =============================================================================
// STATE TYPES
// =============================================================================

export type {
  GameState,
  PlayerState,
  PropertyState,
  EconomyState,
  LoanState,
  CDState,
  HELOCState,
  DiceRoll,
  CardDeck,
  DrawnCard,
  AuctionState,
  TradeState,
  TradeOffer,
  GameConfig,
  GameEvent,
  NetWorth,
  Position,
  GameStatus,
  TurnPhase,
  EconomyPhase,
  ColorGroup,
  PropertyType,
  SpecialSpaceType,
  TokenType,
  BotPersonality,
  Difficulty,
} from './state/types';

// =============================================================================
// ACTION TYPES
// =============================================================================

export { ActionTypes } from './actions/types';

export type {
  GameAction,
  InitializeGameAction,
  StartGameAction,
  PauseGameAction,
  ResumeGameAction,
  EndGameAction,
  AddPlayerAction,
  RemovePlayerAction,
  AddBotAction,
  RollDiceAction,
  EndTurnAction,
  BuyPropertyAction,
  DeclinePropertyAction,
  BuildHouseAction,
  SellHouseAction,
  MortgagePropertyAction,
  UnmortgagePropertyAction,
  PayJailFineAction,
  UseJailCardAction,
  RollForDoublesAction,
  TakeLoanAction,
  RepayLoanAction,
  CreateCDAction,
  WithdrawCDAction,
  OpenHELOCAction,
  ProposeTradeAction,
  AcceptTradeAction,
  RejectTradeAction,
  CounterTradeAction,
  StartAuctionAction,
  PlaceBidAction,
  PassAuctionAction,
  DrawCardAction,
  ExecuteCardAction,
  MovePlayerAction,
  CollectRentAction,
  SendToJailAction,
  BankruptPlayerAction,
  EconomyTickAction,
  AdminAdjustMoneyAction,
  AdminMovePlayerAction,
} from './actions/types';

// =============================================================================
// REDUCER
// =============================================================================

export { gameReducer, createInitialState } from './reducers/gameReducer';
export type { ReducerResult } from './reducers/gameReducer';
export { DEFAULT_CONFIG } from './reducers/initialState';

// =============================================================================
// RNG
// =============================================================================

export { SeededRandom, createRng, generateSeed } from './rng/SeededRandom';

// =============================================================================
// RULES
// =============================================================================

// Movement rules
export {
  BOARD_SIZE,
  GO_POSITION,
  JAIL_POSITION,
  GO_TO_JAIL_POSITION,
  getNextPosition,
  wouldPassGo,
  getSpacesBetween,
  isSpecialSpace,
  isChanceSpace,
  isCommunityChestSpace,
  getNearestRailroad,
  getNearestUtility,
  moveBack,
} from './rules/movement';

// Property rules
export {
  getPropertyByPosition,
  isPropertyOwned,
  getPlayerProperties,
  getGroupProperties,
  hasMonopoly,
  countOwnedRailroads,
  countOwnedUtilities,
  calculateRent,
  canBuildHouse,
  canSellHouse,
  calculatePropertyValue,
  calculateNetWorth,
  getHouseSellValue,
} from './rules/property';

// Card rules
export {
  CARD_DEFINITIONS,
  getCardDefinition,
  calculateRepairsCost,
  executeCardEffect,
  drawCard,
  discardCard,
} from './rules/cards';

export type {
  CardDefinition,
  CardEffectType,
  CardExecutionResult,
} from './rules/cards';
