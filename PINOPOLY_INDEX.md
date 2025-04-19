# Pinopoly Project Index

This document provides a comprehensive index of all components in the Pinopoly project, organized by category and showing which components are actively used and which are not currently used. Use this as a reference when making changes to avoid regression issues.

## Table of Contents
- [Core Systems](#core-systems)
- [Controllers](#controllers)
- [Routes](#routes)
- [Models](#models)
- [Socket Events](#socket-events)
- [Migration Scripts](#migration-scripts)
- [User Interfaces](#user-interfaces)
- [API Endpoints](#api-endpoints)
- [Frontend Components](#frontend-components)
- [Setup Scripts](#setup-scripts)
- [Testing & Utility Scripts](#testing--utility-scripts)
- [Documentation](#documentation)
- [Configuration](#configuration)

## Core Systems

| Component | Status | Description | Dependencies |
|-----------|--------|-------------|--------------|
| Game State | ✅ Used | Manages the current state of the game | None |
| Banker | ✅ Used | Handles game currency transfers | Game State |
| Community Fund | ✅ Used | Manages community fund pool | Game State |
| Event System | ✅ Used | Handles game events | Banker, Community Fund |
| Auction System | ✅ Used | Handles property auctions | Banker |
| Socket System | ✅ Used | Manages real-time communication | Flask-SocketIO |
| Game Logic | ✅ Used | Core game rules and mechanics | App |
| Adaptive Difficulty | ⚠️ Partially Used | Adjusts game difficulty | SocketIO |
| Remote Play | ⚠️ Partially Used | Enables remote gameplay | App, Cloudflare Tunnel |
| Crime System | ✅ Used | Handles crime and police activity | Game State, Player Model |
| Property Development | ✅ Used | Manages property improvements | Property Model |
| Game Modes | ⚠️ Partially Used | Different gameplay variations | Game State, Game Controller |
| Social Features | ⚠️ Partially Used | Chat, alliances, and reputation | SocketIO |
| Admin Dashboard | ⚠️ Partially Built | Management interface for game admins with fully implemented Crime, Player, Finance, and Event components | Multiple Systems |
| Economic System | ✅ Used | Handles economic phases, inflation, interest rates, and property values | GameState, SocketIO, Banker |
| Trade System | ✅ Used | Manages trading between players | Trade Controller, SocketIO |
| Financial System | ✅ Used | Manages loans, CDs, and HELOCs | Finance Controller |
| Credit Score System | ✅ Used | Tracks player financial reputation affecting loan rates | Player Model, Finance Controller |

## Controllers

| Controller | Status | Description | Dependencies | Related Features |
|------------|--------|-------------|--------------|------------------|
| GameController | ✅ Used | Manages game state, turn order, and core game mechanics. | Board configuration, Player models | Game setup, turn management, game state updates |
| PlayerController | ✅ Used | Manages player status, actions, and allowed moves. | Game state | Player actions, AI behavior, turn actions |
| PropertyController | ✅ Used | Handles property ownership, auctions, and improvements. | Property models, Player models | Property transactions, auctions, improvements |
| FinanceController | ✅ Used | Manages financial instruments | DB, Banker, Game State |
| SpecialSpaceController | ✅ Used | Handles special spaces (Chance, Community Chest, Tax, Free Parking, Go to Jail) with full implementation of card drawing, jail mechanics, and tax processing | SocketIO, Banker, Community Fund, Game Controller, Board Controller |
| PlayerActionController | ✅ Used | Manages socket event handlers for player actions including property improvements, bankruptcy, jail actions, and card drawings | SocketIO, PropertyController, GameController, SpecialSpaceController | Player actions, socket event communication |
| CardsController | ⚠️ Partially Used | Manages card decks, card drawing and card effects. | Card models | Chance and Community Chest cards |
| TradeController | ✅ Used | Handles player-to-player trades and negotiations. | Player models, Property models | Trading, negotiations |
| DiceController | ⚠️ Partially Used | Manages dice rolls, doubles, and movement logic. | - | Movement, jail mechanics |
| AuctionController | ✅ Used | Handles property auctions when players decline to purchase. Includes timer management, bid validation, and auction completion logic. | Property models, Player models, GameState, SocketIO | Auctions, Property management |
| AIController | ⚠️ Partially Used | Controls AI player decision making. | Game state | AI behavior |
| AdminController | ⚠️ Partially Used | Handles administrative functions and game moderation. | All models | Admin panel, game management |
| EconomicCycleManager | ✅ Used | Manages economic cycles, interest rates, and inflation. | Game state | Financial system, economic simulation |
| RemoteController | ⚠️ Partially Used | Manages remote play | App |
| AuthController | ✅ Used | Manages authentication | None |
| SocialController | ⚠️ Partially Used | Manages social features | SocketIO, App Config |
| ChatController | ⚠️ Partially Used | Manages chat system | SocketIO, App Config |
| AllianceController | ⚠️ Partially Used | Manages alliances | SocketIO, App Config |
| ReputationController | ⚠️ Partially Used | Manages player reputation | SocketIO, App Config |
| SocketController | ✅ Used | Manages socket events | SocketIO, App Config |
| GameModeController | ⚠️ Partially Used | Manages game modes | None |
| AdaptiveDifficultyController | ⚠️ Partially Used | Manages AI difficulty | SocketIO |
| BoardController | ⚠️ Partially Used | Handles board layout, spaces, and configuration. | Space models | Board initialization, property management |
| TeamController | ⚠️ Partially Used | Manages player teams | Game State |
| CrimeController | ✅ Used | Manages crime system including theft, vandalism, forgery, and tax evasion with police patrol and jail handling | SocketIO, Player, Property models | Crime management, police patrols, jail system |
| GameController._internal_end_turn | ✅ Used | Handles the logic for ending a player's turn and transitioning to the next player | GameState, SocketIO | Includes win condition checks and turn transitions |
| SpecialSpaceController.handle_tax_space | ✅ Used | Processes tax payments when a player lands on a tax space | GameState, FinanceController | Handles both income and luxury taxes |
| SpecialSpaceController.handle_free_parking | ✅ Used | Manages the free parking space and jackpot collection | GameState, Banker | Integrates with community fund for jackpot distribution |
| SpecialSpaceController.handle_community_chest_space | ✅ Used | Draws and processes community chest cards | GameState, SocketIO | Implements card effects including collecting money, paying money, etc. |
| SpecialSpaceController.process_community_chest_card | ✅ Used | Socket event handler wrapper for community chest card processing | GameState, SocketIO | Calls handle_community_chest_space and updates expected actions to end turn |
| SpecialSpaceController.handle_chance_space | ✅ Used | Draws and processes chance cards | GameState, SocketIO | Implements card effects including moving player, collecting/paying money, etc. |
| SpecialSpaceController.process_chance_card | ✅ Used | Socket event handler wrapper for chance card processing | GameState, SocketIO | Calls handle_chance_space and updates expected actions to end turn |
| SpecialSpaceController.handle_go_to_jail | ✅ Used | Sends a player to jail and updates their status | GameState, SocketIO | Updates player position and jail state |
| SpecialSpaceController.handle_jail_action | ✅ Used | Processes player attempts to get out of jail | GameState, SocketIO | Handles jail fine payment, card usage, and dice rolling for doubles |
| PropertyController.handle_property_improvement | ✅ Used | Manages adding houses and hotels to properties | GameState, SocketIO | Includes validation for monopoly ownership, even development rules, and bank availability |
| PropertyController.handle_sell_improvement | ✅ Used | Manages selling houses and hotels from properties | GameState, SocketIO | Includes validation for even development rules and proper conversion of hotels to houses |
| EconomicCycleController | ✅ Used | Controls the economic simulation including interest rates, property values, and economic state changes. Now includes market fluctuation space handling | GameState, Property model | Economic simulation, market fluctuations |
| PlayerController.handle_bankruptcy | ✅ Used | Orchestrates player bankruptcy declaration and game state updates | FinanceController, GameState, SocketIO | Handles bankruptcy processing, credit score updates, and UI notifications |

## Routes

| Route Module | Status | Description | Dependencies |
|--------------|--------|-------------|--------------|
| player_routes | ✅ Used | Player-related API routes | PlayerController |
| player_routes.player_declare_bankruptcy | ✅ Used | HTTP API route for player bankruptcy | PlayerController |
| game_routes | ✅ Used | Game-related API routes | GameController |
| finance_routes | ✅ Used | Finance-related API routes | FinanceController |
| player.finance_player_routes | ✅ Used | Player finance API routes | FinanceController |
| community_fund_routes | ✅ Used | Community fund API routes | Community Fund |
| special_space_routes | ✅ Used | Special space API routes | SpecialSpaceController |
| crime_routes | ✅ Used | Crime-related API routes | CrimeController |
| remote_routes | ⚠️ Partially Used | Remote play API routes | RemoteController |
| game_mode_routes | ⚠️ Partially Used | Game mode API routes | GameModeController |
| social/social_routes | ⚠️ Partially Used | Social features API routes | Social controllers |
| auth_routes | ✅ Used | Authentication API routes | AuthController |
| board_routes | ⚠️ Partially Used | Board-related API routes | BoardController |
| trade_routes | ✅ Used | Trading API routes | TradeController |
| admin/game_admin_routes | ⚠️ Partially Used | Game admin API routes | Game-related controllers |
| admin/player_admin_routes | ⚠️ Partially Used | Player admin API routes | PlayerController |
| admin/bot_admin_routes | ⚠️ Partially Used | Bot admin API routes | AIController |
| admin/event_admin_routes | ✅ Used | Event admin API routes with full implementation of event management, scheduling, templates, and impact analysis | EventSystem, AdminController |
| admin/crime_admin_routes | ✅ Used | Crime admin API routes with full management of criminal activity, jail status, crime statistics, and random crime generation | CrimeController, AdminController |
| admin/finance_admin_routes | ✅ Used | Finance admin API routes with comprehensive implementation of settings management, player cash modification, transactions, loans, economic audits, and statistics | FinanceController, AdminController |
| admin/property_admin_routes | ⚠️ Partially Used | Property admin API routes | PropertyController |
| admin/auction_admin_routes | ✅ Used | Auction admin API routes | AuctionController |
| ~~property_routes~~ | ❌ Not Used | Legacy property routes | N/A |
| ~~auction_routes~~ | ❌ Not Used | Legacy auction routes | N/A |
| ~~bot_event_routes~~ | ❌ Not Used | Legacy bot event routes | N/A |

## Models

| Model | Status | Description | Related Controllers |
|-------|--------|-------------|---------------------|
| Player | ✅ Used | Player model | PlayerController, All controllers |
| Property | ✅ Used | Property model | PropertyController |
| GameState | ✅ Used | Game state model | GameController, All controllers |
| Loan | ✅ Used | Loan model | FinanceController |
| Transaction | ✅ Used | Transaction model | FinanceController, Banker |
| Banker | ✅ Used | Banker model | Multiple controllers |
| CommunityFund | ✅ Used | Community fund model | Community Fund routes |
| EventSystem | ✅ Used | Event system model | Event-related controllers |
| EconomicCycleManager | ✅ Used | Economic cycle manager | GameState, FinanceController |
| bots/BotPlayer | ✅ Used | Bot models | AIController |
| bots/ConservativeBot | ⚠️ Partially Used | Conservative bot strategy - Basic decision logic only | AIController |
| bots/AggressiveBot | ⚠️ Partially Used | Aggressive bot strategy - Basic decision logic only | AIController |
| bots/StrategicBot | ⚠️ Partially Used | Strategic bot strategy - Basic decision logic only | AIController |
| bots/OpportunisticBot | ✅ Used | Opportunistic bot strategy | AIController |
| PropertyType | ✅ Used | Property type model | PropertyController |
| Crime | ✅ Used | Crime model with multiple crime types including theft, property vandalism, rent evasion, forgery, and tax evasion | CrimeController |
| GameMode | ⚠️ Partially Used | Game mode model - Not all modes fully implemented | GameModeController |
| Team | ⚠️ Partially Used | Team model - Basic functionality only | TeamController |
| Trade | ✅ Used | Trade model | TradeController |
| TradeItem | ✅ Used | Trade items model | TradeController |
| Auction | ✅ Used | Auction model - Full implementation | AuctionController |
| AuctionSystem | ✅ Used | Auction system model - Full implementation | AuctionController |
| social/Chat | ⚠️ Partially Used | Chat model - Basic messaging only | ChatController |
| social/Alliance | ⚠️ Partially Used | Alliance model - Framework exists but limited functionality | AllianceController |
| social/Reputation | ⚠️ Partially Used | Reputation model - Basic implementation only | ReputationController |
| Economic_phase_change | ⚠️ Partially Used | Economic phase model - Limited phase effects | GameController |
| JailCard | ✅ Used | Jail card model | SpecialSpaceController |

## Socket Events

| Event Type | Direction | Status | Description | Related Controller |
|------------|-----------|--------|-------------|-------------------|
| connect | ⬅️ Client to Server | ✅ Used | Client establishes connection to game server | SocketIO |
| disconnect | ⬅️ Client to Server | ✅ Used | Client disconnects from game server | SocketIO |
| join_game | ⬅️ Client to Server | ✅ Used | Player joins a specific game room | GameController |
| leave_game | ⬅️ Client to Server | ✅ Used | Player leaves a game room | GameController |
| player_update | ➡️ Server to Client | ✅ Used | Broadcast updated player state | PlayerController |
| game_state_update | ➡️ Server to Client | ✅ Used | Broadcast full game state | GameController |
| roll_dice | ⬅️ Client to Server | ✅ Used | Player rolls dice | GameController |
| end_turn | ⬅️ Client to Server | ✅ Used | Player ends their turn | GameController |
| purchase_property | ⬅️ Client to Server | ✅ Used | Player buys property | PropertyController |
| pay_rent | ➡️ Server to Client | ✅ Used | Notify of rent payment | PropertyController |
| auction_start | ➡️ Server to Client | ✅ Used | Property auction begins | AuctionController |
| place_bid | ⬅️ Client to Server | ✅ Used | Place a bid in an auction | AuctionController |
| auction_end | ➡️ Server to Client | ✅ Used | Auction results | AuctionController |
| card_drawn | ➡️ Server to Client | ✅ Used | Player draws Chance/Community Chest card | SpecialSpaceController |
| player_paid_tax | ➡️ Server to Client | ✅ Used | Player pays tax | SpecialSpaceController |
| free_parking | ➡️ Server to Client | ✅ Used | Player lands on Free Parking | SpecialSpaceController |
| player_to_jail | ➡️ Server to Client | ✅ Used | Player is sent to jail | SpecialSpaceController |
| jail_release | ➡️ Server to Client | ✅ Used | Player is released from jail | SpecialSpaceController |
| economic_update | ➡️ Server to Client | ✅ Used | Economic cycle update | EconomicCycleController |
| economic_state | ➡️ Server to Client | ✅ Used | Current economic state | EconomicCycleController |
| market_crash | ➡️ Server to Client | ✅ Used | Market crash event | EconomicCycleController |
| economic_boom | ➡️ Server to Client | ✅ Used | Economic boom event | EconomicCycleController |
| market_fluctuation | ➡️ Server to Client | ✅ Used | Economic impact to player investments | EconomicCycleController |
| handle_market_fluctuation | ⬅️ Client to Server | ✅ Used | Process market fluctuation effects | PlayerActionController, SpecialSpaceController |
| market_fluctuation_result | ➡️ Server to Client | ✅ Used | Direct success response to market fluctuation request | PlayerActionController |
| trade_offer | ⬅️ Client to Server | ✅ Used | Player offers trade | TradeController |
| trade_response | ⬅️ Client to Server | ✅ Used | Player responds to trade | TradeController |
| trade_complete | ➡️ Server to Client | ✅ Used | Trade transaction complete | TradeController |
| start_auction | ⬅️ Client to Server | ✅ Used | Start a property auction | AuctionController |
| pass_auction | ⬅️ Client to Server | ✅ Used | Pass on bidding in an auction | AuctionController |
| get_auctions | ⬅️ Client to Server | ✅ Used | Get list of active auctions | AuctionController |
| get_auction | ⬅️ Client to Server | ✅ Used | Get details for a specific auction | AuctionController |
| get_auction_status | ⬅️ Client to Server | ✅ Used | Get detailed status of an auction including participants | AuctionController |
| auction_status_update | ➡️ Server to Client | ✅ Used | Detailed auction status response | AuctionController |
| admin_cleanup_auctions | ⬅️ Client to Server | ✅ Used | Admin-only: Clean up stale auctions | AuctionController |
| admin_cleanup_result | ➡️ Server to Client | ✅ Used | Result of admin auction cleanup operation | AuctionController |
| start_sequential_auctions | ⬅️ Client to Server | ✅ Used | Admin-only: Start sequential auctions for multiple properties | AuctionController |
| sequential_auctions_started | ➡️ Server to Client | ✅ Used | Confirmation of sequential auctions start | AuctionController |
| sequential_auctions_announcement | ➡️ Server to Client | ✅ Used | Announcement of sequential auction to all players | AuctionController |
| sequential_auction_next | ➡️ Server to Client | ✅ Used | Notification of next auction in sequence | AuctionController |
| sequential_auction_completed | ➡️ Server to Client | ✅ Used | Notification that sequential auction is complete | AuctionController |
| start_emergency_auction | ⬅️ Client to Server | ✅ Used | Player request to start emergency auction | AuctionController |
| emergency_auction_started | ➡️ Server to Client | ✅ Used | Notification that emergency auction has started | AuctionController |
| emergency_auction_started_confirmation | ➡️ Server to Client | ✅ Used | Confirmation to player who started emergency auction | AuctionController |
| cancel_auction | ⬅️ Client to Server | ✅ Used | Admin-only: Cancel an auction | AuctionController |
| mortgage_property | ⬅️ Client to Server | ✅ Used | Player mortgages property | PlayerActionController, PropertyController |
| mortgage_result | ➡️ Server to Client | ✅ Used | Direct success response to mortgage request | PlayerActionController |
| unmortgage_property | ⬅️ Client to Server | ✅ Used | Player unmortgages property | PlayerActionController, PropertyController |
| unmortgage_result | ➡️ Server to Client | ✅ Used | Direct success response to unmortgage request | PlayerActionController |
| improve_property | ⬅️ Client to Server | ✅ Used | Player adds house/hotel | PlayerActionController, PropertyController |
| property_improved | ➡️ Server to Client | ✅ Used | Notification of property improvement | PropertyController |
| sell_improvement | ⬅️ Client to Server | ✅ Used | Player sells house/hotel | PlayerActionController, PropertyController |
| property_improvement_sold | ➡️ Server to Client | ✅ Used | Notification of property improvement sale | PropertyController |
| property_improvement_result | ➡️ Server to Client | ✅ Used | Direct success response to improvement request | PlayerActionController |
| property_improvement_sell_result | ➡️ Server to Client | ✅ Used | Direct success response to sell improvement request | PlayerActionController |
| property_error | ➡️ Server to Client | ✅ Used | Property-related error notification | PropertyController, PlayerActionController |
| pay_jail_fine | ⬅️ Client to Server | ✅ Used | Player pays fine to get out of jail | PlayerActionController |
| jail_fine_paid | ➡️ Server to Client | ✅ Used | Notification of successful jail fine payment | PlayerActionController |
| use_get_out_of_jail_card | ⬅️ Client to Server | ✅ Used | Player uses Get Out of Jail Free card | PlayerActionController |
| jail_card_used | ➡️ Server to Client | ✅ Used | Notification of successful jail card usage | PlayerActionController |
| draw_chance_card | ⬅️ Client to Server | ✅ Used | Player draws a Chance card | PlayerActionController, SpecialSpaceController |
| draw_community_chest_card | ⬅️ Client to Server | ✅ Used | Player draws a Community Chest card | PlayerActionController, SpecialSpaceController |
| ai_player_action | ➡️ Server to Client | ✅ Used | AI player takes action | BotController |
| game_over | ➡️ Server to Client | ✅ Used | Game ends with winner | GameController |
| declare_bankruptcy | ⬅️ Client to Server | ✅ Used | Player declares bankruptcy | PlayerController |
| bankruptcy_result | ➡️ Server to Client | ✅ Used | Bankruptcy declaration result | PlayerController |
| bankruptcy_error | ➡️ Server to Client | ✅ Used | Bankruptcy declaration error | PlayerController |
| player_bankruptcy | ➡️ Server to Client | ✅ Used | Notification that a player has declared bankruptcy | FinanceController |
| propose_trade | ⬅️ Client to Server | ✅ Used | Player offers trade | TradeController |
| respond_to_trade | ⬅️ Client to Server | ✅ Used | Player responds to trade | TradeController |
| cancel_trade | ⬅️ Client to Server | ✅ Used | Player cancels a trade | TradeController |
| get_pending_trades | ⬅️ Client to Server | ✅ Used | Player requests pending trades | TradeController |
| get_trade_history | ⬅️ Client to Server | ✅ Used | Player requests trade history | TradeController |
| trade_action_result | ➡️ Server to Client | ✅ Used | Trade action result notification | TradeController |
| trade_error | ➡️ Server to Client | ✅ Used | Trade error notification | TradeController |
| pending_trades | ➡️ Server to Client | ✅ Used | List of pending trades | TradeController |
| trade_history | ➡️ Server to Client | ✅ Used | Trade history list | TradeController |
| auction_started | ➡️ Server to Client | ✅ Used | Notification of auction start | AuctionController |
| bid_placed | ➡️ Server to Client | ✅ Used | Notification of bid placement | AuctionController |
| auction_ended | ➡️ Server to Client | ✅ Used | Notification of auction completion | AuctionController |
| auction_status | ➡️ Server to Client | ✅ Used | Update on auction status | AuctionController |

## Migration Scripts

| Script | Status | Description | Usage |
|--------|--------|-------------|-------|
| add_free_parking_fund | ✅ Used | Adds free_parking_fund to game_state | Run at app startup |
| property_development_migration | ✅ Used | Property development migration | Run when needed |
| event_system_migration | ⚠️ Partially Used | Event system migration - Limited event types | Run when needed |

## User Interfaces

| Interface Component      | Status     | Description                                                                                                          |
|--------------------------|------------|----------------------------------------------------------------------------------------------------------------------|
| Main Game Board          | ✅ Used    | The primary game interface with property spaces, dice controls, and player information                                |
| Property Card UI         | ✅ Used    | Interface for viewing and managing property details                                                                  |
| Player Dashboard         | ✅ Used    | Player-specific interface showing assets, cash, and game controls                                                    |
| Trade UI                 | ✅ Used    | Interface for negotiating and completing trades between players                                                      |
| Crime System UI          | ✅ Used    | Interface for committing crimes, viewing criminal history and jail status                                            |
| Chat Interface           | ✅ Used    | Real-time communication between players during games                                                                |
| Crime Management UI      | ✅ Used    | Admin interface for configuring the crime system, monitoring criminal activity                                       |
| Player Management UI     | ✅ Used    | Admin interface for player oversight, account management, and financial controls                                     |
| Bot Management UI        | ✅ Used    | Admin interface for bot overview, management, strategy configuration, activity monitoring, and performance analytics |
| Game Modes Management UI | ✅ Used    | Admin interface for creating, editing, and managing game modes with configuration settings and active game monitoring|
| Property Management UI   | ✅ Used    | Admin interface for property configuration, rent adjustments, value management, transfers, and market analysis     |

## API Endpoints

| Endpoint | Status | Description | Controller Method |
|----------|--------|-------------|------------------|
| /api/health | ✅ Used | Health check endpoint | N/A |
| /api/admin/properties | ⚠️ Partially Used | Admin property management - Basic CRUD only | PropertyController |
| /api/admin/bots/test | ⚠️ Partially Used | Test endpoint for bots - Limited functionality | AIController |
| /api/admin/bots/types/test | ⚠️ Partially Used | Test endpoint for bot types - Basic info only | AIController |
| /api/bot-types | ✅ Used | Get bot types | AIController |
| /api/create-bot | ✅ Used | Direct bot creation | AIController.create_bot |
| /api/finance/loan/new | ✅ Used | Create new loan | FinanceController.create_loan |
| /api/finance/loan/repay | ✅ Used | Repay loan | FinanceController.repay_loan |
| /api/finance/cd/new | ✅ Used | Create new CD | FinanceController.create_cd |
| /api/finance/cd/withdraw | ✅ Used | Withdraw CD | FinanceController.withdraw_cd |
| /api/finance/heloc/new | ✅ Used | Create new HELOC | FinanceController.create_heloc |
| /api/finance/interest-rates | ✅ Used | Get interest rates | FinanceController.get_interest_rates |
| /api/finance/loans | ✅ Used | Get player loans | FinanceController.get_player_loans |
| /api/finance/bankruptcy | ✅ Used | Declare bankruptcy | FinanceController.declare_bankruptcy |
| /api/finance/player/:id/loans | ✅ Used | Get player loans | FinanceController.get_player_loans |
| /api/finance/player/:id/cds | ✅ Used | Get player CDs | FinanceController.get_player_cds |
| /api/finance/player/:id/helocs | ✅ Used | Get player HELOCs | FinanceController.get_player_helocs |
| /api/finance/player/:id/financial-summary | ✅ Used | Get financial summary | FinanceController.get_player_financial_summary |
| /api/game/roll | ✅ Used | Roll dice | GameController.handle_roll_dice |
| /api/game/end-turn | ✅ Used | End turn | GameController.end_turn |
| /api/game/start | ✅ Used | Start game | GameController.start_game |
| /api/game/reset | ✅ Used | Reset game | GameController.reset_game |
| /api/player/join | ✅ Used | Join game | PlayerController.join_game |
| /api/player/leave | ✅ Used | Leave game | PlayerController.leave_game |
| /api/property/buy | ✅ Used | Buy property | GameController.handle_property_purchase |
| /api/property/decline | ✅ Used | Decline property | GameController.handle_property_decline |
| /api/property/mortgage | ✅ Used | Mortgage property | GameController.handle_mortgage_property |
| /api/property/unmortgage | ✅ Used | Unmortgage property | GameController.handle_unmortgage_property |
| /api/property/develop | ✅ Used | Develop property | GameController.handle_improve_property |
| /api/property/sell-improvement | ✅ Used | Sell improvement | GameController.handle_sell_improvement |
| /api/special-space/action | ✅ Used | Special space action | GameController.handle_special_space |
| /api/trade/propose | ✅ Used | Propose a trade | TradeController.create_trade_proposal |
| /api/trade/accept | ✅ Used | Accept a trade | TradeController.accept_trade |
| /api/trade/reject | ✅ Used | Reject a trade | TradeController.reject_trade |
| /api/trade/cancel | ✅ Used | Cancel a trade | TradeController.cancel_trade |
| /api/trade/pending/:id | ✅ Used | Get pending trades | TradeController.get_pending_trades |
| /api/trade/history/:id | ✅ Used | Get trade history | TradeController.get_trade_history |
| /api/trade/details/:id | ✅ Used | Get trade details | TradeController._format_trade_for_api |
| /api/admin/reset | ✅ Used | Reset game (admin) | AdminController.reset_game |
| /api/property/:id/details | ✅ Used | Get property details | Property.to_dict |
| /api/property/group/:name | ✅ Used | Get properties by group | Property.query.filter_by |
| /api/admin/auctions/auction/analytics | ✅ Used | Get auction analytics | AuctionController.get_auction_analytics |
| /api/admin/auctions/auction/property-history/:property_id | ✅ Used | Get property auction history | AuctionController.get_property_auction_history |
| /api/admin/auctions/active-auctions/:game_id | ✅ Used | Get active auctions for a game | AuctionController.get_active_auctions |
| /api/admin/auctions/auction/:auction_id | ✅ Used | Get detailed auction information | AuctionController.get_auction |
| /api/admin/auctions/auction-status/:auction_id | ✅ Used | Get detailed auction status with participants | AuctionController.get_auction_status |
| /api/admin/auctions/cancel-auction/:auction_id | ✅ Used | Cancel an active auction | AuctionController.cancel_auction |
| /api/admin/auctions/cleanup-stale-auctions | ✅ Used | Cleanup stale auctions | AuctionController.cleanup_stale_auctions |
| /api/admin/auctions/start-sequential-auctions | ✅ Used | Start sequential auctions for multiple properties | AuctionController.start_sequential_auctions |
| /api/admin/auctions/auction-schedule/:game_id | ✅ Used | Get current auction schedule for a game | AuctionController.get_auction_schedule |
| /api/admin/auctions/process-bot-bid | ✅ Used | Process a bot bid for testing | AuctionController.process_bot_bid |
| /api/admin/auctions/process-multiple-bot-bids | ✅ Used | Process bids from multiple bots at once | AuctionController.process_multiple_bot_bids |
| /api/admin/auctions/batch-end-auctions | ✅ Used | End multiple auctions at once | AuctionController.batch_end_auctions |

## Frontend Components

| Component | Status | Description | Related Features |
|-----------|--------|-------------|-----------------|
| GameBoard | ✅ Used | Main game board | Game display |
| PlayerControls | ✅ Used | Player action buttons | Game control |
| PlayerList | ✅ Used | List of players | Player management |
| PropertyCard | ✅ Used | Property details | Property management |
| PropertyList | ✅ Used | List of properties | Property management |
| DiceRoller | ✅ Used | Dice rolling animation | Game mechanics |
| FinancialDashboard | ✅ Used | Financial information | Finance management |
| BankruptcyModal | ✅ Used | Bankruptcy dialog | Finance management |
| CDCreationModal | ✅ Used | CD creation dialog | Finance management |
| HELOCModal | ✅ Used | HELOC creation dialog | Finance management |
| NewLoanModal | ✅ Used | Loan creation dialog | Finance management |
| AuctionModal | ⚠️ Partially Built | Property auction dialog - Basic bidding only | Auction system |
| PropertyDevelopmentModal | ✅ Used | Property development dialog | Property development |
| PropertyMortgageModal | ✅ Used | Interface for mortgaging and unmortgaging properties | Property management, Finance system |
| TradeModal | ✅ Used | Trade proposal and management | Trade system |
| TradeOfferCard | ✅ Used | Display of trade offers | Trade system |
| GameModeSelector | ⚠️ Partially Built | Game mode selection - Not all modes implemented | Game modes |
| GameModeSettings | ⚠️ Partially Built | Game mode configuration - Basic settings only | Game modes |
| AdminBotManager | ⚠️ Partially Built | Bot management - Basic creation only | Admin controls |
| BotActionDisplay | ⚠️ Partially Built | Bot actions display - Basic info only | Bot system |
| BotEventDisplay | ⚠️ Partially Built | Bot events display - Basic display only | Bot system |
| Chat/* | ⚠️ Partially Built | Chat components - Basic functionality | Social features |
| TurnIndicator | ✅ Used | Current turn display | Game control |
| GameControls | ✅ Used | Game control buttons | Game control |
| NotificationDisplay | ✅ Used | Game notifications | User interface |
| GameStats | ✅ Used | Game statistics | User interface |
| MarketCrashDisplay | ⚠️ Partially Built | Market crash visualization - Basic implementation | Economic system |
| MarketFluctuationModal | ✅ Used | Display economic impacts on player when landing on market fluctuation space | Economic system, Market fluctuation |
| TeamDisplay | ⚠️ Partially Built | Team management UI - Basic functionality | Team system |
| GameModeAdmin | ⚠️ Partially Built | Game mode admin interface - Limited configuration options | Admin dashboard |

## Setup Scripts

| Script | Status | Description | Usage |
|--------|--------|-------------|-------|
| setup_frontend.py | ✅ Used | Enhanced setup script for frontend development environment with Node.js/npm verification, dependency management, environment configuration, and Vite configuration validation | Run once for setup |
| setup_python_backend.py | ✅ Used | Enhanced setup script for backend development environment with Python version check, virtual environment setup, dependency management, and database initialization | Run once for setup |
| make_setup_scripts_executable.py | ✅ Used | Utility script to make setup scripts executable on Unix/Linux systems | Run once after checkout on Unix/Linux |

## Testing & Utility Scripts

| Script | Status | Description | Controller Tested |
|--------|--------|-------------|-------------------|
| test_economic_cycle_controller.py | ✅ Used | Tests for the Economic Cycle Controller | EconomicCycleController |
| test_auction_controller.py | ✅ Used | Tests for the Auction Controller | AuctionController |
| test_special_space_controller.py | ✅ Used | Tests for the Special Space Controller | SpecialSpaceController |
| test_game_controller.py | ✅ Used | Tests for the Game Controller | GameController |
| run_tests.py | ✅ Used | Test runner utility to discover and run all tests | N/A |
| run_coverage.py | ✅ Used | Runs tests with coverage reporting and HTML/XML report generation | N/A |
| make_scripts_executable.py | ✅ Used | Utility to make all scripts executable on Unix/Linux systems | N/A |
| kill_server.py | ✅ Used | Utility to stop the Flask server | N/A |

## Documentation

| Document | Status | Description | Contents |
|----------|--------|-------------|----------|
| README.md | ✅ Used | Project overview | Features, installation, usage |
| CHANGELOG.md | ✅ Used | Version history | Updates by version |
| code-review.md | ✅ Used | Code review checklist | Review status |
| PINOPOLY_INDEX.md | ✅ Used | Project index | Component catalog |
| SETUP_README.md | ✅ Used | Setup instructions | Detailed setup guide for frontend and backend |
| TESTING.md | ✅ Used | Testing guide | Test instructions and best practices |
| docs/game-modes.md | ⚠️ Partially Complete | Game modes documentation - Missing details for some modes | Game mode details |
| docs/remote_play.md | ⚠️ Partially Complete | Remote play documentation - Basic setup only | Setup instructions |
| docs/financial-instruments.md | ✅ Used | Financial system documentation | Finance details |
| docs/auction-system.md | ⚠️ Partially Complete | Auction system documentation - Missing implementation details | Auction details |
| docs/property-development.md | ✅ Used | Property development documentation | Development details |
| docs/social-features.md | ⚠️ Partially Complete | Social features documentation - Many features described but not implemented | Social system details |
| docs/advanced-economics.md | ⚠️ Partially Complete | Economics documentation - Basic system only | Economic details |
| docs/event_system.md | ✅ Used | Event system documentation | Event details |

## Configuration

| Configuration Key | Status | Description | Default Value |
|------------------|--------|-------------|--------------|
| SQLALCHEMY_DATABASE_URI | ✅ Used | Database connection string | 'sqlite:///pinopoly.sqlite' |
| SECRET_KEY | ✅ Used | Flask secret key | 'pinopoly-development-key' |
| ADMIN_KEY | ✅ Used | Admin authentication key | 'pinopoly-admin' |
| DISPLAY_KEY | ✅ Used | Display authentication key | 'pinopoly-display' |
| DEBUG | ✅ Used | Debug mode flag | 'False' |
| REMOTE_PLAY_ENABLED | ✅ Used | Remote play flag | 'False' |
| REMOTE_PLAY_TIMEOUT | ✅ Used | Remote play timeout | 60 |
| ADAPTIVE_DIFFICULTY_ENABLED | ✅ Used | Adaptive difficulty flag | 'true' |
| ADAPTIVE_DIFFICULTY_INTERVAL | ✅ Used | Adaptive difficulty interval | 15 |
| POLICE_PATROL_ENABLED | ✅ Used | Police patrol flag | 'true' |
| POLICE_PATROL_INTERVAL | ✅ Used | Police patrol interval | 45 |
| ECONOMIC_CYCLE_ENABLED | ✅ Used | Enable/disable economic cycle updates | 'true' |
| ECONOMIC_CYCLE_INTERVAL | ✅ Used | Minutes between economic updates | 5 |
| PROPERTY_VALUES_FOLLOW_ECONOMY | ✅ Used | Whether property values update with economy | 'true' |
| PORT | ✅ Used | Server port | 5000 |
| DATABASE_PATH | ✅ Used | SQLite database file path | 'pinopoly.db' |
| FREE_PARKING_FUND | ✅ Used | Free parking fund configuration | 'true' |
| SQLALCHEMY_TRACK_MODIFICATIONS | ✅ Used | Track modifications flag for SQLAlchemy | 'false' |

### Configuration Tools and System

| Component | Status | Description | Usage |
|-----------|--------|-------------|-------|
| config_manager.py | ✅ Used | Core configuration management module with schema validation, type conversion, and environment variable support | Used throughout the application |
| generate_config.py | ✅ Used | CLI tool for generating, validating, and checking configuration files | Run directly from command line |
| flask_config.py | ✅ Used | Utilities for integrating configuration with Flask applications | Used to configure Flask app at startup |
| setup_config.sh | ✅ Used | Bash script for setting up configuration on Unix/Linux/macOS | Run once for initial setup |
| setup_config.ps1 | ✅ Used | PowerShell script for setting up configuration on Windows | Run once for initial setup |
| run_pinopoly.py | ✅ Used | Application startup script with environment and configuration handling | Used to start the application |
| configuration schema | ✅ Used | Comprehensive schema for all configuration options with types, defaults, and validation | Defined in config_manager.py |
| config/base.json | ✅ Used | Base configuration with default values for all environments | Loaded first during startup |
| config/development.json | ✅ Used | Development-specific configuration overrides | Loaded in development environment |
| config/testing.json | ✅ Used | Testing-specific configuration overrides | Loaded in testing environment |
| config/production.json | ✅ Used | Production-specific configuration overrides | Loaded in production environment |
| environment variable overrides | ✅ Used | Support for overriding any configuration via environment variables | Used in all environments |
| docs/configuration.md | ✅ Used | Comprehensive documentation for the configuration system | Reference for developers |
| config/README.md | ✅ Used | Quick reference guide for using configuration tools | Reference for setup |
| test_generate_config.py | ✅ Used | Unit tests for the configuration generator | Validates config generation |
| test_config_manager.py | ✅ Used | Unit tests for the configuration manager | Validates config loading/validation |

### Configuration Workflow

1. Base configuration is loaded from `config/base.json`
2. Environment-specific configuration is loaded from `config/{environment}.json`
3. Environment variables override any existing settings
4. Configuration is validated against the schema
5. Application accesses configuration through the config_manager API

The configuration system provides a robust foundation for managing application settings across different environments, with strong validation, type conversion, and documentation.

## Recent Changes/Fixes

| Feature/Change | Description | Status |
|---------------|-------------|--------|
| Finance Player Routes | Added missing finance_player_routes module | ✅ Fixed |
| Free Parking Fund Migration | Added missing migration script for free_parking_fund | ✅ Fixed |
| Bot Controller create_bot | Added missing create_bot method to BotController | ✅ Fixed |
| Socket Event Handler Update | Updated socket handler to use BotController.create_bot | ✅ Fixed |
| Direct API Bot Creation Update | Updated /api/create-bot to use BotController.create_bot | ✅ Fixed |
| Property Purchase Implementation | Implemented handle_property_purchase in GameController | ✅ Fixed |
| Property Decline Implementation | Implemented handle_property_decline in GameController | ✅ Fixed |
| Property Improvement Implementation | Implemented property improvement functionality in GameController | ✅ Fixed |
| Property Mortgage Implementation | Implemented property mortgage/unmortgage in GameController | ✅ Fixed |
| Special Space Handler Implementation | Implemented special space handler in GameController | ✅ Fixed |
| Trade System Implementation | Implemented trade system in TradeController | ✅ Fixed |
| End Turn Implementation | Implemented _internal_end_turn in GameController | ✅ Fixed |
| Financial System Updates | Updated loan, CD, and bankruptcy functionality in FinanceController | ✅ Fixed |
| Property Improvement Socket Events | Added Socket.IO events for property improvements | ✅ Fixed |
| Property HTTP API Routes | Added HTTP API routes for property actions | ✅ Fixed |
| Credit Score System | Implemented player credit score system | ✅ Fixed |
| Special Spaces Enhancement | Enhanced special spaces with economic integration | ✅ Fixed |
| Tax Space Implementation | Implemented tax space functionality with economic conditions | ✅ Fixed |
| Special Space Handlers | Implemented all special space handlers (Tax, Chance, Community Chest, Free Parking, Go To Jail) with game state updates and events | ✅ Completed |
| Jail Mechanics | Enhanced jail mechanics with options to pay bail, use cards, or roll for doubles | ✅ Completed |
| End Turn Logic | Implemented comprehensive turn transition logic in GameController | ✅ Completed |
| Dice Roll System | Enhanced dice rolling with proper doubles handling and jail logic | ✅ Completed |
| Property Improvement Sale | Implemented handle_sell_improvement method for selling houses and hotels | ✅ Completed |
| Property Development Approval | Added community approval request system for property development | ✅ Completed |
| Environmental Study System | Implemented environmental study commissioning for highest level property development | ✅ Completed |
| Property Development Routes | Added HTTP API routes for property development approval and studies | ✅ Completed |
| Free Parking Implementation | Completed handle_free_parking method with jackpot collection and community fund integration | ✅ Completed |
| Community Chest System | Implemented handle_community_chest_space method with card drawing and effect processing | ✅ Completed |
| Chance Card System | Implemented handle_chance_space method with card drawing and effect processing | ✅ Completed |
| Socket Event Handlers | Added process_chance_card and process_community_chest_card methods to handle socket events | ✅ Completed |
| Bankruptcy System | Implemented comprehensive bankruptcy handling with debt forgiveness, property forfeiture, credit score updates, and game state transitions | ✅ Completed |
| Go to Jail Handler | Implemented handle_go_to_jail method to send players to jail and update game state | ✅ Completed |
| Jail Action System | Implemented handle_jail_action method to process different jail escape options | ✅ Completed |
| Card System Update | Added new card types and effects | ✅ Completed |
| Property Improvement System | Implemented handle_property_improvement and handle_sell_improvement methods with even development rules | ✅ Completed |
| Financial System | Updated loan processing and financial instruments | ⚠️ In Progress |
| Advanced Property Development | Enhanced property development with zoning restrictions, community approval requirements, and environmental impact studies | ✅ Completed |
| Market Fluctuation Space | Implemented market fluctuation space that applies economic effects based on the current economic state, affecting player cash and property values | ✅ Completed |
| PlayerActionController Implementation | Centralized socket event handlers for player actions into a dedicated controller | ✅ Completed |
| Comprehensive Property Improvement System | Implemented both house and hotel improvements with even development rules and property rent updates | ✅ Completed |
| Property Improvement Sale | Improved selling improvements with bank inventory checks and conversion of hotels to houses when possible | ✅ Completed |
| Jail Management Actions | Implemented pay_jail_fine and use_get_out_of_jail_card actions with proper validation | ✅ Completed |
| Bankruptcy Declaration Flow | Refined bankruptcy declaration with proper validation and financial processing | ✅ Completed |
| Market Fluctuation Player Actions | Implemented socket event handler for market fluctuation space with economic impacts | ✅ Completed |
| Property Mortgage Management | Implemented mortgage_property and unmortgage_property socket handlers with validation and user feedback | ✅ Completed |
| Property Mortgage UI | Created PropertyMortgageModal component with mortgage/unmortgage functionality and user-friendly interface | ✅ Completed |
| Trade Socket Events | Implemented comprehensive trade socket events with propose, respond, cancel, history, and pending trade handlers | ✅ Completed |
| Auction System Integration | Enhanced property decline flow with full auction system integration, including automatic auction triggering and improved error handling | ✅ Completed |
| Auction Timer Management | Implemented robust auction timer system with background monitoring to prevent stuck auctions and ensure proper auction closure | ✅ Completed |
| Auction Bid Logic | Implemented _place_bid_logic method in AuctionController with comprehensive validation, bid processing, and notification | ✅ Completed |
| Auction Monitoring | Added get_schedule_auction_check method to automatically monitor and prevent stuck auctions | ✅ Completed |
| Auction Status Retrieval | Added get_auction_status method to provide detailed auction information with participant data | ✅ Completed |
| Batch Auction Management | Implemented batch_end_auctions and cleanup_stale_auctions methods for admin maintenance | ✅ Completed |
| Sequential Auction System | Added start_sequential_auctions and _process_next_sequential_auction methods to handle multiple properties being auctioned in sequence | ✅ Completed |
| Bot Bidding Strategy | Implemented process_bot_bid and _calculate_bot_bid methods to allow AI players to participate in auctions with different strategies | ✅ Completed |
| Emergency Auctions | Added start_emergency_auction method to allow players to quickly auction their properties when they need funds | ✅ Completed |
| Auction Analytics | Implemented comprehensive auction analytics with metrics for auction success rates, price increases, bidder activity, and property statistics | ✅ Completed |
| Property Auction History | Added API endpoint to retrieve full auction history for specific properties | ✅ Completed |
| Auction Admin Routes | Implemented admin routes for auction management, including analytics, active auctions, property history, and auction status endpoints | ✅ Completed |
| Admin Routes Registration | Improved admin routes registration with centralized registration function and consistent URL prefixes | ✅ Completed |
| Auction Schedule Management | Added API endpoints for managing auction scheduling, including sequential auctions, auction cancellation, and bot bidding | ✅ Completed |
| Auction Admin Dashboard | Extended auction management with tools for batch operations, stale auction cleanup, and auction monitoring | ✅ Completed |
| Multiple Bot Bidding | Added API endpoint to simulate multiple bots bidding on an auction at once with different strategies | ✅ Completed |
| admin/finance_admin_routes.py | Implemented comprehensive finance admin routes with settings management, player cash modification, transactions, loans, economic audits, and statistics | ✅ Completed |
| admin/event_admin_routes.py | Implemented comprehensive event admin routes with event management, scheduling, templates, and impact analysis | ✅ Completed |

## TODOs and Known Issues

| Item                             | Status              | Notes                                                              |
|----------------------------------|---------------------|-------------------------------------------------------------------|
| Implement Auction System         | ⚠️ Planned         | Feature for auctioning unsold properties when players pass         |
| Optimize Database Queries        | ⚠️ In Progress     | Performance improvements needed for large game sessions           |
| Fix Trade System Race Condition  | 🔄 Under Review     | Occasional issue with trade completion timing                     |
| Complete Admin Dashboard         | ✅ Completed        | Admin interfaces for Crime, Player, Bot, Property, and Finance management fully implemented |
| Enhance Mobile Responsiveness    | ⚠️ Planned         | Improvements needed for smaller screen sizes                      |
| Add Game Session Recovery        | ⚠️ Planned         | Mechanism to recover from crashes or disconnections               |
| Fix Chat Notification Bug        | 🔄 Under Review     | Notifications sometimes don't appear for new messages             |

---

## Legend
- ✅ Used: Component is actively used in the application
- ⚠️ Partially Used/Built: Component is partially implemented or used
- ❌ Not Used: Component is referenced but not currently used
- ❓ Unknown: Status is unclear

Last updated: May 19, 2025 

### Game Mechanics
- **Economic Cycle Manager** [Partially Implemented]: Handles inflation, economic states, and market fluctuations.
- **Turn Management** [Implemented]: Manages player turns, actions, and state transitions.
- **Dice** [Implemented]: Manages the random generation of dice rolls.
- **Auction System** [Implemented]: Handles property auctions when players decline to purchase properties or during foreclosures.
  - Includes methods for starting auctions, placing bids, ending auctions, and transferring properties.
  - Implemented full auction lifecycle with property transfer, payment processing, and timer management.
  - Socket.IO events for real-time auction updates. 

## Special Spaces

| Space Type | Status | Description | Controller Method |
|------------|--------|-------------|------------------|
| Go | ✅ Used | Collect salary when passing or landing | `SpecialSpaceController.handle_go_space` |
| Jail | ✅ Used | Detain players, support Get Out of Jail cards | `SpecialSpaceController.handle_jail`, `SpecialSpaceController.handle_get_out_of_jail` |
| Free Parking | ✅ Used | Option to collect accumulated funds | `SpecialSpaceController.handle_free_parking` |
| Go To Jail | ✅ Used | Send player directly to jail | `SpecialSpaceController.handle_go_to_jail` |
| Chance | ✅ Used | Draw cards with random effects | `SpecialSpaceController.handle_chance_space` |
| Community Chest | ✅ Used | Draw cards with random effects | `SpecialSpaceController.handle_community_chest_space` |
| Tax Spaces | ✅ Used | Pay taxes based on income or luxury | `SpecialSpaceController.handle_tax_space` |
| Market Fluctuation | ✅ Used | Apply economic effects based on current state | `SpecialSpaceController.handle_market_fluctuation_space` | 