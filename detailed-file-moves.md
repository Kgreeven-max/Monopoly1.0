# Detailed File Moves for Project Restructuring

## Frontend (client/ → frontend/)

### Pages
- `client/src/pages/BoardPage.jsx` → `frontend/src/pages/BoardPage/index.jsx`
- `client/src/pages/HomePage.jsx` → `frontend/src/pages/HomePage/index.jsx`
- `client/src/pages/AdminPage.jsx` → `frontend/src/pages/AdminPage/index.jsx`
- `client/src/pages/DebugPage.jsx` → `frontend/src/pages/DebugPage/index.jsx`
- `client/src/pages/ConnectPage.jsx` → `frontend/src/pages/ConnectPage/index.jsx`
- `client/src/pages/PlayerPage.jsx` → `frontend/src/pages/PlayerPage/index.jsx`
- `client/src/pages/NotFoundPage.jsx` → `frontend/src/pages/NotFoundPage/index.jsx`
- `client/src/pages/RemotePlayerPage.jsx` → `frontend/src/pages/RemotePlayerPage/index.jsx`

### Game Board Components
- `client/src/components/GameBoard/GameBoard.jsx` → `frontend/src/game-board/components/Board/GameBoard.jsx`
- `client/src/components/GameBoard/PlayerToken.jsx` → `frontend/src/game-board/components/PlayerToken/PlayerToken.jsx`
- `client/src/components/GameBoard/PropertySpace.jsx` → `frontend/src/game-board/components/Spaces/PropertySpace.jsx`
- `client/src/components/GameBoard/SpecialSpace.jsx` → `frontend/src/game-board/components/Spaces/SpecialSpace.jsx`
- `client/src/components/Board/` → `frontend/src/game-board/components/`

### Game Logic Components
- `client/src/components/DiceRoller.jsx` → `frontend/src/game-logic/dice/DiceRoller.jsx`
- `client/src/components/TurnIndicator.jsx` → `frontend/src/game-logic/turns/TurnIndicator.jsx`
- `client/src/components/GameControls.jsx` → `frontend/src/game-logic/turns/GameControls.jsx`

### Economic Components
- `client/src/components/PropertyList.jsx` → `frontend/src/game-logic/economics/PropertyList.jsx`
- `client/src/components/PropertyCard.jsx` → `frontend/src/game-logic/economics/PropertyCard.jsx`
- `client/src/components/FinancialDashboard.jsx` → `frontend/src/game-logic/economics/FinancialDashboard.jsx` 
- `client/src/components/GameStats.jsx` → `frontend/src/game-logic/economics/GameStats.jsx`
- `client/src/components/PropertyDevelopmentModal.jsx` → `frontend/src/game-logic/economics/PropertyDevelopmentModal.jsx`
- `client/src/components/PropertyMortgageModal.jsx` → `frontend/src/game-logic/economics/PropertyMortgageModal.jsx`

### Loan/Financial Components
- `client/src/components/NewLoanModal.jsx` → `frontend/src/game-logic/economics/loans/NewLoanModal.jsx`
- `client/src/components/CDCreationModal.jsx` → `frontend/src/game-logic/economics/loans/CDCreationModal.jsx`
- `client/src/components/HELOCModal.jsx` → `frontend/src/game-logic/economics/loans/HELOCModal.jsx`
- `client/src/components/BankruptcyModal.jsx` → `frontend/src/game-logic/economics/bankruptcy/BankruptcyModal.jsx`

### Market Components
- `client/src/components/MarketFluctuationModal.jsx` → `frontend/src/game-logic/economics/market/MarketFluctuationModal.jsx`
- `client/src/components/MarketCrashDisplay.jsx` → `frontend/src/game-logic/economics/market/MarketCrashDisplay.jsx`
- `client/src/components/AuctionModal.jsx` → `frontend/src/game-logic/economics/trading/AuctionModal.jsx`

### Game State
- `client/src/contexts/GameContext.jsx` → `frontend/src/game-state/contexts/GameContext/index.jsx`
- `client/src/contexts/AuthContext.jsx` → `frontend/src/game-state/contexts/AuthContext/index.jsx`
- `client/src/contexts/SocketContext.jsx` → `frontend/src/game-state/contexts/SocketContext/index.jsx`
- `client/src/contexts/NotificationContext.jsx` → `frontend/src/game-state/contexts/NotificationContext/index.jsx`
- `client/src/services/` → `frontend/src/game-state/services/`

### Shared Components
- `client/src/components/NavBar.jsx` → `frontend/src/components/ui/NavBar.jsx`
- `client/src/components/PlayerList.jsx` → `frontend/src/components/ui/PlayerList.jsx`
- `client/src/components/TeamDisplay.jsx` → `frontend/src/components/ui/TeamDisplay.jsx`
- `client/src/components/PlayerControls/` → `frontend/src/components/ui/PlayerControls/`
- `client/src/components/Chat/` → `frontend/src/components/chat/`
- `client/src/components/NotificationDisplay.jsx` → `frontend/src/components/notifications/NotificationDisplay.jsx`
- `client/src/components/CardDisplay.jsx` → `frontend/src/components/cards/CardDisplay.jsx`
- `client/src/components/GameLog.jsx` → `frontend/src/components/ui/GameLog.jsx`

### Bot-related Components
- `client/src/components/AdminBotManager.jsx` → `frontend/src/pages/AdminPage/AdminBotManager.jsx`
- `client/src/components/BotActionDisplay.jsx` → `frontend/src/components/ui/BotActionDisplay.jsx`
- `client/src/components/BotEventDisplay.jsx` → `frontend/src/components/ui/BotEventDisplay.jsx`

### Game Mode Components
- `client/src/components/GameModeAdmin.jsx` → `frontend/src/pages/AdminPage/GameModeAdmin.jsx`
- `client/src/components/GameModeSelector.jsx` → `frontend/src/pages/HomePage/GameModeSelector.jsx`
- `client/src/components/GameModeSettings.jsx` → `frontend/src/pages/HomePage/GameModeSettings.jsx`

### Styles
- `client/src/styles/` → `frontend/src/styles/`
- All component-specific CSS files should move with their components

### Utils
- `client/src/utils/` → `frontend/src/utils/`

## Backend (src/ → backend/)

### Core Application Files
- `src/app.py` → `backend/app.py`
- `requirements.txt` → `backend/requirements.txt`

### API Routes
- `src/routes/game_routes.py` → `backend/api/routes/game_routes.py`
- `src/routes/player_routes.py` → `backend/api/routes/player_routes.py`
- `src/routes/property_routes.py` → `backend/api/routes/property_routes.py`
- `src/routes/admin_routes.py` → `backend/api/routes/admin_routes.py`
- `src/routes/auth_routes.py` → `backend/api/routes/auth_routes.py`
- `src/routes/board_routes.py` → `backend/api/routes/board_routes.py`
- `src/routes/finance_routes.py` → `backend/api/routes/finance_routes.py`
- `src/routes/crime_routes.py` → `backend/api/routes/crime_routes.py`
- `src/routes/special_space_routes.py` → `backend/api/routes/special_space_routes.py`
- `src/routes/trade_routes.py` → `backend/api/routes/trade_routes.py`
- `src/routes/remote_routes.py` → `backend/api/routes/remote_routes.py`
- `src/routes/game_mode_routes.py` → `backend/api/routes/game_mode_routes.py`
- `src/routes/community_fund_routes.py` → `backend/api/routes/community_fund_routes.py`
- `src/routes/view_routes.py` → `backend/api/routes/view_routes.py`
- `src/routes/social/` → `backend/api/routes/social/`
- `src/routes/player/` → `backend/api/routes/player/`
- `src/routes/admin/` → `backend/api/routes/admin/`

### Socket Handlers
- `src/controllers/socket_controller.py` → `backend/api/socket/socket_controller.py`
- `src/controllers/socket_core.py` → `backend/api/socket/socket_core.py`
- `src/controllers/game_socket_handlers.py` → `backend/api/socket/game_handlers.py`
- `src/controllers/social_socket_handlers.py` → `backend/api/socket/social_handlers.py`
- `src/controllers/admin_socket_handlers.py` → `backend/api/socket/admin_handlers.py`
- `src/controllers/social/socket_handlers.py` → `backend/api/socket/social/handlers.py`

### Game Engine - Economy
- `src/controllers/finance_controller.py` → `backend/game_engine/economy/finance.py`
- `src/controllers/economic_cycle_controller.py` → `backend/game_engine/economy/market.py`
- `src/controllers/auction_controller.py` → `backend/game_engine/economy/auction.py`

### Game Engine - Players
- `src/controllers/player_controller.py` → `backend/game_engine/players/player.py`
- `src/controllers/team_controller.py` → `backend/game_engine/players/team.py`
- `src/controllers/player_action_controller.py` → `backend/game_engine/players/actions.py`
- `src/controllers/crime_controller.py` → `backend/game_engine/players/crime.py`

### Game Engine - Properties
- `src/controllers/property_controller.py` → `backend/game_engine/properties/property.py`
- `src/controllers/special_space_controller.py` → `backend/game_engine/special_spaces/special_space.py`

### Game Engine - Bots
- `src/controllers/bot_controller.py` → `backend/game_engine/bots/bot.py`
- `src/controllers/bot_event_controller.py` → `backend/game_engine/bots/events.py`
- `src/logic/bot_decision_maker.py` → `backend/game_engine/bots/decision_maker.py`
- `src/services/bot_action_handler.py` → `backend/game_engine/bots/action_handler.py`

### Game Engine - Core
- `src/controllers/game_controller.py` → `backend/game_engine/game.py`
- `src/controllers/board_controller.py` → `backend/game_engine/board/board.py`
- `src/controllers/game_mode_controller.py` → `backend/game_engine/game_modes.py`
- `src/controllers/trade_controller.py` → `backend/game_engine/trading/trade.py`
- `src/game_logic/game_logic.py` → `backend/game_engine/rules.py`

### Models
- `src/models/` → `backend/models/`

### Controllers
- `src/controllers/admin_controller.py` → `backend/controllers/admin_controller.py`
- `src/controllers/auth_controller.py` → `backend/controllers/auth_controller.py`
- `src/controllers/connection_controller.py` → `backend/controllers/connection_controller.py`
- `src/controllers/remote_controller.py` → `backend/controllers/remote_controller.py`
- `src/controllers/adaptive_difficulty_controller.py` → `backend/controllers/adaptive_difficulty_controller.py`

### Services
- New services from controller logic to be extracted

### Utils
- `src/utils/` → `backend/utils/`

### Migrations
- `src/migrations/` → `backend/migrations/`

### Templates
- `templates/` → `backend/templates/`

## Configuration
- `config/` → `backend/config/`

## Scripts
- `scripts/` → `scripts/`
- `deployment/` → Combined with scripts

## Documentation
- `docs/` → `docs/`

## Tests
- `tests/` → Split between `tests/frontend/` and `tests/backend/`

## Shared Resources
- Create new `shared/` folder
- Extract common constants from frontend and backend 