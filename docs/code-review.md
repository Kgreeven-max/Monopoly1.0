# Code Review Checklist

This document tracks files reviewed against the coding standards and requirements.

## Models

### Core
- [x] `player.py`
- [x] `game_state.py`
- [x] `property.py`
- [ ] `card.py`
- [ ] `dice.py`
- [ ] `board.py`
- [ ] `banker.py`
- [ ] `community_fund.py`
- [x] `event_system.py` # Reviewed: Needs refactor (Logic placement - Service, Coupling, State persistence, Magic numbers)
- [ ] `loan.py`
- [ ] `auction.py` # Model needed for persistence
- [x] `auction_system.py` # Reviewed: Needs major refactor (Persistence P1, logic placement, size, coupling, concurrency)
- [x] `crime.py` # Reviewed: Needs refactor (size, commits, logic placement)
- [x] `bot_player.py` # Reviewed: Needs major refactor (size, responsibility, game logic, commits, coupling)
- [x] `special_space.py` # Reviewed: Needs refactor (size, mixed responsibilities, logic placement - CardDeck/TaxSpace, coupling, commits)
- [x] `bot_events.py` # Reviewed: Needs major refactor (size, logic placement, coupling - circular dep!, commits)
- [x] `economic_phase_change.py` # Reviewed: OK
- [x] `jail_card.py` # Reviewed: OK

### Social
- [x] `reputation.py`
- [x] `alliance.py`
- [x] `chat.py`

### Finance
- [x] `finance/*` # Reviewed: loan.py needs commits removed & GameState decoupling.

### Utility/Other
- [ ] `base_model.py`
- [ ] `db.py`
- [x] `__init__.py` # Reviewed: Needs refactor (Remove global singletons, use DI, fix circular deps)

## Controllers

- [ ] `game_controller.py`
- [x] `admin_controller.py`
- [x] `board_controller.py`
- [x] `special_space_controller.py`
- [x] `socket_controller.py` # Reviewed: Authentication in social handlers
- [ ] `auction_controller.py`
- [ ] `property_controller.py`
- [ ] `bot_controller.py`
- [ ] `bot_event_controller.py`
- [ ] `trade_controller.py` (If created)
- [ ] `social/social_controller.py` 
- [ ] `social/socket_handlers.py`

## Routes

- [x] `admin_routes.py` (Refactored to use AdminController)
- [x] `board_routes.py` (Refactored to use BoardController)
- [x] `special_space_routes.py` (Partially refactored for cards -> SpecialSpaceController)
- [ ] `game_routes.py`
- [ ] `trade_routes.py`
- [ ] `player_routes.py`
- [ ] `property_routes.py`
- [ ] `remote_play_routes.py`

## Services / Utilities

- [ ] `auth.py`
- [ ] `decorators.py`
- [ ] `utils.py`

## Client Code (Key Areas)

- [ ] `client/src/services/apiService.js`
- [ ] `client/src/services/socketService.js`
- [ ] `client/src/contexts/AuthContext.js`
- [ ] `client/src/components/GameBoard/GameBoard.js`
- [ ] `client/src/components/PlayerDashboard/PlayerDashboard.js`
- [ ] `client/src/hooks/useSocket.js`

## Documentation / Config

- [ ] `README.md`
- [ ] `docs/architecture.md`
- [ ] `docs/technical.md`
- [ ] `tasks/tasks.md`
- [ ] `shared-component-notes.md`
- [ ] `.cursorrules`