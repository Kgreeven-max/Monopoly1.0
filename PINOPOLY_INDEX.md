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
| Community Fund | ⚠️ Partially Used | Manages community fund pool | Game State |
| Event System | ⚠️ Partially Used | Handles game events | Banker, Community Fund |
| Auction System | ⚠️ Partially Used | Handles property auctions | Banker |
| Socket System | ✅ Used | Manages real-time communication | Flask-SocketIO |
| Game Logic | ⚠️ Partially Used | Core game rules and mechanics | App |
| Adaptive Difficulty | ⚠️ Partially Used | Adjusts game difficulty | SocketIO |
| Remote Play | ⚠️ Partially Used | Enables remote gameplay | App, Cloudflare Tunnel |
| Crime System | ⚠️ Partially Used | Handles crime and police activity | Game State, Player Model |
| Property Development | ⚠️ Partially Used | Manages property improvements | Property Model |
| Game Modes | ⚠️ Partially Used | Different gameplay variations | Game State, Game Controller |
| Social Features | ⚠️ Partially Used | Chat, alliances, and reputation | SocketIO |
| Admin Dashboard | ⚠️ Partially Built | Management interface for game admins | Multiple Systems |
| Economic System | ⚠️ Partially Used | Handles economic phases and market conditions | Game State |

## Controllers

| Controller | Status | Description | Dependencies |
|------------|--------|-------------|--------------|
| GameController | ✅ Used | Manages game flow | Game Logic, Game State |
| PlayerController | ✅ Used | Manages player actions | DB |
| PropertyController | ⚠️ Partially Used | Manages properties | DB, Banker, Event System, SocketIO |
| AuctionController | ⚠️ Partially Used | Manages property auctions | DB, Banker, Event System, SocketIO |
| BotController | ⚠️ Partially Used | Manages AI players | Game Logic, Game Controller, Property Controller, Auction Controller, Banker, Special Space Controller |
| FinanceController | ⚠️ Partially Used | Manages financial instruments | DB, Banker, Game State |
| CrimeController | ⚠️ Partially Used | Manages crime system | SocketIO |
| SpecialSpaceController | ⚠️ Partially Used | Manages special board spaces | SocketIO, Banker, Community Fund |
| RemoteController | ⚠️ Partially Used | Manages remote play | App |
| AuthController | ✅ Used | Manages authentication | None |
| SocialController | ⚠️ Partially Used | Manages social features | SocketIO, App Config |
| ChatController | ⚠️ Partially Used | Manages chat system | SocketIO, App Config |
| AllianceController | ⚠️ Partially Used | Manages alliances | SocketIO, App Config |
| ReputationController | ⚠️ Partially Used | Manages player reputation | SocketIO, App Config |
| SocketController | ✅ Used | Manages socket events | SocketIO, App Config |
| GameModeController | ⚠️ Partially Used | Manages game modes | None |
| AdaptiveDifficultyController | ⚠️ Partially Used | Manages AI difficulty | SocketIO |
| BoardController | ⚠️ Partially Used | Manages game board | None |
| TeamController | ⚠️ Partially Used | Manages player teams | Game State |
| AdminController | ⚠️ Partially Used | Manages admin functions | Game State, Player Controller |

## Routes

| Route Module | Status | Description | Dependencies |
|--------------|--------|-------------|--------------|
| player_routes | ✅ Used | Player-related API routes | PlayerController |
| game_routes | ✅ Used | Game-related API routes | GameController |
| finance_routes | ⚠️ Partially Used | Finance-related API routes | FinanceController |
| player.finance_player_routes | ⚠️ Partially Used | Player finance API routes | FinanceController |
| community_fund_routes | ⚠️ Partially Used | Community fund API routes | Community Fund |
| special_space_routes | ⚠️ Partially Used | Special space API routes | SpecialSpaceController |
| crime_routes | ⚠️ Partially Used | Crime-related API routes | CrimeController |
| remote_routes | ⚠️ Partially Used | Remote play API routes | RemoteController |
| game_mode_routes | ⚠️ Partially Used | Game mode API routes | GameModeController |
| social/social_routes | ⚠️ Partially Used | Social features API routes | Social controllers |
| auth_routes | ✅ Used | Authentication API routes | AuthController |
| board_routes | ⚠️ Partially Used | Board-related API routes | BoardController |
| trade_routes | ⚠️ Partially Used | Trading API routes | Trade controllers |
| admin/game_admin_routes | ⚠️ Partially Used | Game admin API routes | Game-related controllers |
| admin/player_admin_routes | ⚠️ Partially Used | Player admin API routes | PlayerController |
| admin/bot_admin_routes | ⚠️ Partially Used | Bot admin API routes | BotController |
| admin/event_admin_routes | ⚠️ Partially Used | Event admin API routes | EventSystem |
| admin/crime_admin_routes | ⚠️ Partially Used | Crime admin API routes | CrimeController |
| admin/finance_admin_routes | ⚠️ Partially Used | Finance admin API routes | FinanceController |
| admin/property_admin_routes | ⚠️ Partially Used | Property admin API routes | PropertyController |
| ~~property_routes~~ | ❌ Not Used | Legacy property routes | N/A |
| ~~auction_routes~~ | ❌ Not Used | Legacy auction routes | N/A |
| ~~bot_event_routes~~ | ❌ Not Used | Legacy bot event routes | N/A |

## Models

| Model | Status | Description | Related Controllers |
|-------|--------|-------------|---------------------|
| Player | ✅ Used | Player model | PlayerController, All controllers |
| Property | ✅ Used | Property model | PropertyController |
| GameState | ✅ Used | Game state model | GameController, All controllers |
| Loan | ⚠️ Partially Used | Loan model - Basic functionality implemented | FinanceController |
| Transaction | ✅ Used | Transaction model | FinanceController, Banker |
| Banker | ⚠️ Partially Used | Banker model - Missing advanced features | Multiple controllers |
| CommunityFund | ⚠️ Partially Used | Community fund model - Basic implementation only | Community Fund routes |
| EventSystem | ⚠️ Partially Used | Event system model - Limited event types | Event-related controllers |
| bots/BotPlayer | ✅ Used | Bot models | BotController |
| bots/ConservativeBot | ⚠️ Partially Used | Conservative bot strategy - Basic decision logic only | BotController |
| bots/AggressiveBot | ⚠️ Partially Used | Aggressive bot strategy - Basic decision logic only | BotController |
| bots/StrategicBot | ⚠️ Partially Used | Strategic bot strategy - Basic decision logic only | BotController |
| bots/OpportunisticBot | ✅ Used | Opportunistic bot strategy | BotController |
| PropertyType | ✅ Used | Property type model | PropertyController |
| Crime | ⚠️ Partially Used | Crime model - Limited crime types implemented | CrimeController |
| GameMode | ⚠️ Partially Used | Game mode model - Not all modes fully implemented | GameModeController |
| Team | ⚠️ Partially Used | Team model - Basic functionality only | TeamController |
| Trade | ⚠️ Partially Used | Trade model - Limited trade types | TradeController |
| Auction | ⚠️ Partially Used | Auction model - Missing advanced features | AuctionController |
| AuctionSystem | ⚠️ Partially Used | Auction system model - Basic functionality only | AuctionController |
| social/Chat | ⚠️ Partially Used | Chat model - Basic messaging only | ChatController |
| social/Alliance | ⚠️ Partially Used | Alliance model - Framework exists but limited functionality | AllianceController |
| social/Reputation | ⚠️ Partially Used | Reputation model - Basic implementation only | ReputationController |
| Economic_phase_change | ⚠️ Partially Used | Economic phase model - Limited phase effects | GameController |
| JailCard | ⚠️ Partially Used | Jail card model - Basic functionality only | SpecialSpaceController |

## Socket Events

| Event | Status | Description | Related Controllers |
|-------|--------|-------------|---------------------|
| get_all_players | ✅ Used | Retrieves all players | PlayerController |
| remove_bot | ✅ Used | Removes a bot player | BotController |
| reset_all_players | ✅ Used | Resets all players | PlayerController |
| finance_update | ✅ Used | Broadcasts financial updates | FinanceController |
| create_bot | ✅ Used | Creates a new bot player | BotController |
| bot_created | ✅ Used | Broadcasts bot creation | BotController |
| bot_removed | ✅ Used | Broadcasts bot removal | BotController |
| all_players_reset | ✅ Used | Broadcasts player reset | PlayerController |
| loan_created | ⚠️ Partially Used | Broadcasts loan creation - Basic implementation | FinanceController |
| loan_repaid | ⚠️ Partially Used | Broadcasts loan repayment - Basic implementation | FinanceController |
| cd_created | ⚠️ Partially Used | Broadcasts CD creation - Basic implementation | FinanceController |
| cd_withdrawn | ⚠️ Partially Used | Broadcasts CD withdrawal - Basic implementation | FinanceController |
| heloc_created | ⚠️ Partially Used | Broadcasts HELOC creation - Basic implementation | FinanceController |
| player_bankruptcy | ⚠️ Partially Used | Broadcasts player bankruptcy - Limited options | FinanceController |
| property_purchased | ✅ Used | Broadcasts property purchase | PropertyController |
| property_developed | ⚠️ Partially Used | Broadcasts property development - Limited functionality | PropertyController |
| dice_rolled | ✅ Used | Broadcasts dice roll | GameController |
| player_moved | ✅ Used | Broadcasts player movement | GameController |
| turn_started | ✅ Used | Broadcasts turn start | GameController |
| turn_ended | ✅ Used | Broadcasts turn end | GameController |
| chat_message | ⚠️ Partially Used | Broadcasts chat messages - Basic functionality only | ChatController |
| player_joined | ✅ Used | Broadcasts player joining | PlayerController |
| player_left | ✅ Used | Broadcasts player leaving | PlayerController |
| economic_phase_change | ⚠️ Partially Used | Broadcasts economic phase changes - Limited effects | GameController |
| team_formed | ⚠️ Partially Used | Broadcasts team formation - Basic functionality | TeamController |
| alliance_created | ⚠️ Partially Used | Broadcasts alliance creation - Framework only | AllianceController |

## Migration Scripts

| Script | Status | Description | Usage |
|--------|--------|-------------|-------|
| add_free_parking_fund | ✅ Used | Adds free_parking_fund to game_state | Run at app startup |
| property_development_migration | ⚠️ Partially Used | Property development migration - Basic structure only | Run when needed |
| event_system_migration | ⚠️ Partially Used | Event system migration - Limited event types | Run when needed |

## User Interfaces

| UI Component | Status | Description | Related Routes |
|--------------|--------|-------------|---------------|
| /admin | ⚠️ Partially Built | Admin panel UI - Core functionality works but many advanced features incomplete | Admin routes |
| /board | ⚠️ Partially Built | Game board UI - Basic visualization but missing advanced features | Game routes |
| /connect | ⚠️ Partially Built | Connection info for remote play - Basic functionality works | Remote routes |
| /admin_game_modes | ⚠️ Partially Built | Game modes admin UI - Basic settings only | Game mode routes |
| /admin_remote_play | ⚠️ Partially Built | Remote play admin UI - Core functionality only | Remote routes |

## API Endpoints

| Endpoint | Status | Description | Controller Method |
|----------|--------|-------------|------------------|
| /api/health | ✅ Used | Health check endpoint | N/A |
| /api/admin/properties | ⚠️ Partially Used | Admin property management - Basic CRUD only | PropertyController |
| /api/admin/bots/test | ⚠️ Partially Used | Test endpoint for bots - Limited functionality | BotController |
| /api/admin/bots/types/test | ⚠️ Partially Used | Test endpoint for bot types - Basic info only | BotController |
| /api/bot-types | ✅ Used | Get bot types | BotController |
| /api/create-bot | ✅ Used | Direct bot creation | BotController.create_bot |
| /api/finance/loan/new | ⚠️ Partially Used | Create new loan - Basic loan types only | FinanceController.create_loan |
| /api/finance/loan/repay | ⚠️ Partially Used | Repay loan - Limited repayment options | FinanceController.repay_loan |
| /api/finance/cd/new | ⚠️ Partially Used | Create new CD - Basic implementation | FinanceController.create_cd |
| /api/finance/cd/withdraw | ⚠️ Partially Used | Withdraw CD - Basic implementation | FinanceController.withdraw_cd |
| /api/finance/heloc/new | ⚠️ Partially Used | Create new HELOC - Limited valuation logic | FinanceController.create_heloc |
| /api/finance/interest-rates | ⚠️ Partially Used | Get interest rates - Limited rate dynamics | FinanceController.get_interest_rates |
| /api/finance/loans | ⚠️ Partially Used | Get player loans - Basic implementation | FinanceController.get_player_loans |
| /api/finance/bankruptcy | ⚠️ Partially Used | Declare bankruptcy - Limited options | FinanceController.declare_bankruptcy |
| /api/finance/player/:id/loans | ⚠️ Partially Used | Get player loans - Basic implementation | FinanceController.get_player_loans |
| /api/finance/player/:id/cds | ⚠️ Partially Used | Get player CDs - Basic implementation | FinanceController.get_player_cds |
| /api/finance/player/:id/helocs | ⚠️ Partially Used | Get player HELOCs - Basic implementation | FinanceController.get_player_helocs |
| /api/finance/player/:id/financial-summary | ⚠️ Partially Used | Get financial summary - Limited metrics | FinanceController.get_player_financial_summary |
| /api/game/roll | ✅ Used | Roll dice | GameController.roll_dice |
| /api/game/end-turn | ✅ Used | End turn | GameController.end_turn |
| /api/game/start | ✅ Used | Start game | GameController.start_game |
| /api/game/reset | ✅ Used | Reset game | GameController.reset_game |
| /api/player/join | ✅ Used | Join game | PlayerController.join_game |
| /api/player/leave | ✅ Used | Leave game | PlayerController.leave_game |
| /api/property/buy | ✅ Used | Buy property | PropertyController.buy_property |
| /api/property/mortgage | ✅ Used | Mortgage property | PropertyController.mortgage_property |
| /api/property/develop | ⚠️ Partially Used | Develop property - Limited development options | PropertyController.develop_property |
| /api/admin/reset | ✅ Used | Reset game (admin) | AdminController.reset_game |

## Frontend Components

| Component | Status | Description | Related Features |
|-----------|--------|-------------|-----------------|
| GameBoard | ⚠️ Partially Built | Main game board - Basic visualization only | Game display |
| PlayerControls | ⚠️ Partially Built | Player action buttons - Limited action set | Game control |
| PlayerList | ✅ Used | List of players | Player management |
| PropertyCard | ⚠️ Partially Built | Property details - Basic info only | Property management |
| PropertyList | ⚠️ Partially Built | List of properties - Missing advanced sorting/filtering | Property management |
| DiceRoller | ✅ Used | Dice rolling animation | Game mechanics |
| FinancialDashboard | ⚠️ Partially Built | Financial information - Limited metrics | Finance management |
| BankruptcyModal | ⚠️ Partially Built | Bankruptcy dialog - Basic options only | Finance management |
| CDCreationModal | ⚠️ Partially Built | CD creation dialog - Limited term options | Finance management |
| HELOCModal | ⚠️ Partially Built | HELOC creation dialog - Basic implementation | Finance management |
| NewLoanModal | ⚠️ Partially Built | Loan creation dialog - Limited loan types | Finance management |
| AuctionModal | ⚠️ Partially Built | Property auction dialog - Basic bidding only | Auction system |
| PropertyDevelopmentModal | ⚠️ Partially Built | Property development dialog - Limited options | Property development |
| GameModeSelector | ⚠️ Partially Built | Game mode selection - Not all modes implemented | Game modes |
| GameModeSettings | ⚠️ Partially Built | Game mode configuration - Basic settings only | Game modes |
| AdminBotManager | ⚠️ Partially Built | Bot management - Basic creation only | Admin controls |
| BotActionDisplay | ⚠️ Partially Built | Bot actions display - Basic info only | Bot system |
| BotEventDisplay | ⚠️ Partially Built | Bot events display - Basic display only | Bot system |
| Chat/* | ⚠️ Partially Built | Chat components - Basic functionality | Social features |
| TurnIndicator | ✅ Used | Current turn display | Game control |
| GameControls | ⚠️ Partially Built | Game control buttons - Limited control set | Game control |
| NotificationDisplay | ⚠️ Partially Built | Game notifications - Basic notifications only | User interface |
| GameStats | ⚠️ Partially Built | Game statistics - Limited stats displayed | User interface |
| MarketCrashDisplay | ⚠️ Partially Built | Market crash visualization - Basic implementation | Economic system |
| TeamDisplay | ⚠️ Partially Built | Team management UI - Basic functionality | Team system |
| GameModeAdmin | ⚠️ Partially Built | Game mode admin interface - Limited configuration options | Admin dashboard |

## Setup Scripts

| Script | Status | Description | Usage |
|--------|--------|-------------|-------|
| setup_frontend.py | ✅ Used | Sets up frontend development environment | Run once for setup |
| setup_python_backend.py | ✅ Used | Sets up backend development environment | Run once for setup |

## Testing & Utility Scripts

| Script | Status | Description | Usage |
|--------|--------|-------------|-------|
| kill_server.py | ✅ Used | Kills server processes on port 5000 | Run as needed |
| test_db.py | ✅ Used | Tests database queries | Run for debugging |
| test_reset.py | ✅ Used | Tests game reset functionality | Run for testing |

## Documentation

| Document | Status | Description | Contents |
|----------|--------|-------------|----------|
| README.md | ✅ Used | Project overview | Features, installation, usage |
| CHANGELOG.md | ✅ Used | Version history | Updates by version |
| code-review.md | ✅ Used | Code review checklist | Review status |
| PINOPOLY_INDEX.md | ✅ Used | Project index | Component catalog |
| docs/game-modes.md | ⚠️ Partially Complete | Game modes documentation - Missing details for some modes | Game mode details |
| docs/remote_play.md | ⚠️ Partially Complete | Remote play documentation - Basic setup only | Setup instructions |
| docs/financial-instruments.md | ⚠️ Partially Complete | Financial system documentation - Missing advanced features | Finance details |
| docs/auction-system.md | ⚠️ Partially Complete | Auction system documentation - Missing implementation details | Auction details |
| docs/property-development.md | ⚠️ Partially Complete | Property development documentation - Basic system only | Development details |
| docs/social-features.md | ⚠️ Partially Complete | Social features documentation - Many features described but not implemented | Social system details |
| docs/advanced-economics.md | ⚠️ Partially Complete | Economics documentation - Basic system only | Economic details |
| docs/event_system.md | ⚠️ Partially Complete | Event system documentation - Limited event types | Event details |

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
| PORT | ✅ Used | Server port | 5000 |
| DATABASE_PATH | ✅ Used | SQLite database file path | 'pinopoly.db' |

## Recent Changes/Fixes

| Change | Date | Description | Status |
|--------|------|-------------|--------|
| Finance Player Routes | 2025-04-17 | Added missing finance_player_routes module | ✅ Fixed |
| Free Parking Fund Migration | 2025-04-17 | Added missing migration script for free_parking_fund | ✅ Fixed |
| Bot Controller create_bot | 2025-04-17 | Added missing create_bot method to BotController | ✅ Fixed |
| Socket Event Handler Update | 2025-04-17 | Updated socket handler to use BotController.create_bot | ✅ Fixed |
| Direct API Bot Creation Update | 2025-04-17 | Updated /api/create-bot to use BotController.create_bot | ✅ Fixed |

## TODOs and Known Issues

| Issue | Priority | Description | Affected Components |
|-------|----------|-------------|---------------------|
| Property Routes Missing | Medium | Property routes file is referenced but not found | app.py imports |
| Auction Routes Missing | Medium | Auction routes file is referenced but not found | app.py imports |
| Bot Event Routes Missing | Low | Bot event routes file is referenced but not found | app.py imports |
| Cloudflared Missing | Low | Remote play requires cloudflared which isn't installed | RemoteController |
| GameState settings access | Medium | Some code assumes GameState.settings exists | Various controllers |
| Code Review Items | Medium | Several items from code-review.md not yet addressed | Multiple components |
| Social Features Incomplete | Low | Social features partially implemented | Social controllers |
| Admin Dashboard Incomplete | High | Many admin features are partially implemented or missing | Admin UI, Controllers, Routes |
| Advanced Bot Types | Medium | Advanced bot types not fully implemented | BotController, Bot models |
| Property Development System | Medium | Property development system partially implemented | PropertyController, Property model |
| Game Modes Implementation | Medium | Some game modes not fully implemented | GameModeController |
| Economic System Limited | Medium | Economic phases have limited effects | Economic phase change model |
| Crime System Incomplete | Medium | Not all crime types fully implemented | CrimeController, Crime model |
| Financial Instruments Limited | Medium | Advanced financial features not fully implemented | FinanceController |
| Documentation-Implementation Mismatch | High | Documentation describes features not yet fully implemented | Multiple components |
| Team System Incomplete | Low | Team mechanics not fully developed | TeamController, Team model |
| Property Valuation Logic Incomplete | Medium | Advanced property valuation not implemented | PropertyController |

---

## Legend
- ✅ Used: Component is actively used in the application
- ⚠️ Partially Used/Built: Component is partially implemented or used
- ❌ Not Used: Component is referenced but not currently used
- ❓ Unknown: Status is unclear

Last updated: April 17, 2025 