# Implementation Steps for Project Reorganization

## Preparation

1. **Backup your project**
   ```bash
   # Create a backup of the entire project
   cp -r "Monopoly1.0" "Monopoly1.0_backup_$(date +%Y%m%d)"
   ```

2. **Create the new directory structure**
   ```bash
   # Create main directories
   mkdir -p frontend/src/{pages,game-board,game-logic,game-state,components,styles,utils}
   mkdir -p frontend/src/game-board/components/{Board,Spaces,PlayerToken}
   mkdir -p frontend/src/game-board/{hooks,styles}
   mkdir -p frontend/src/game-logic/{turns,dice,economics,events}
   mkdir -p frontend/src/game-logic/economics/{loans,market,bankruptcy,trading}
   mkdir -p frontend/src/game-state/{contexts,services}
   mkdir -p frontend/src/components/{ui,modals,forms,cards,chat,notifications}
   
   mkdir -p backend/{api,game_engine,models,controllers,services,utils,migrations,templates}
   mkdir -p backend/api/{routes,socket}
   mkdir -p backend/game_engine/{board,economy,players,properties,special_spaces,events,bots,trading}
   
   mkdir -p shared/{constants,types}
   mkdir -p scripts
   mkdir -p tests/{frontend,backend}
   ```

## Phase 1: Frontend Migration

1. **Move frontend base files**
   ```bash
   cp -r client/package.json client/vite.config.js client/index.html frontend/
   cp -r client/src/{index.jsx,App.jsx} frontend/src/
   ```

2. **Migrate page components**
   ```bash
   mkdir -p frontend/src/pages/{BoardPage,HomePage,AdminPage,DebugPage,ConnectPage,PlayerPage,NotFoundPage,RemotePlayerPage}
   
   # Move each page to its own directory
   for page in BoardPage HomePage AdminPage DebugPage ConnectPage PlayerPage NotFoundPage RemotePlayerPage; do
     cp client/src/pages/${page}.jsx frontend/src/pages/${page}/index.jsx
     # If there are associated CSS files, move them too
     if [ -f client/src/styles/${page}.css ]; then
       cp client/src/styles/${page}.css frontend/src/pages/${page}/styles.css
     fi
   done
   ```

3. **Migrate game board components**
   ```bash
   # Copy GameBoard components
   cp client/src/components/GameBoard/GameBoard.jsx frontend/src/game-board/components/Board/
   cp client/src/components/GameBoard/PlayerToken.jsx frontend/src/game-board/components/PlayerToken/
   cp client/src/components/GameBoard/PropertySpace.jsx frontend/src/game-board/components/Spaces/
   cp client/src/components/GameBoard/SpecialSpace.jsx frontend/src/game-board/components/Spaces/
   
   # Copy Board components if they exist
   if [ -d client/src/components/Board ]; then
     cp -r client/src/components/Board/* frontend/src/game-board/components/
   fi
   
   # Copy CSS files
   cp client/src/components/GameBoard/*.css frontend/src/game-board/styles/
   ```

4. **Migrate game logic components**
   ```bash
   # Dice roller
   cp client/src/components/DiceRoller.jsx frontend/src/game-logic/dice/
   cp client/src/components/DiceRoller.css frontend/src/game-logic/dice/
   
   # Turn related components
   cp client/src/components/TurnIndicator.jsx frontend/src/game-logic/turns/
   cp client/src/components/TurnIndicator.css frontend/src/game-logic/turns/
   cp client/src/components/GameControls.jsx frontend/src/game-logic/turns/
   cp client/src/components/GameControls.css frontend/src/game-logic/turns/
   ```

5. **Migrate economic components**
   ```bash
   # Property management
   cp client/src/components/PropertyList.jsx frontend/src/game-logic/economics/
   cp client/src/components/PropertyList.css frontend/src/game-logic/economics/
   cp client/src/components/PropertyCard.jsx frontend/src/game-logic/economics/
   cp client/src/components/PropertyCard.css frontend/src/game-logic/economics/
   cp client/src/components/PropertyDevelopmentModal.jsx frontend/src/game-logic/economics/
   cp client/src/components/PropertyDevelopmentModal.css frontend/src/game-logic/economics/
   cp client/src/components/PropertyMortgageModal.jsx frontend/src/game-logic/economics/
   cp client/src/components/PropertyMortgageModal.css frontend/src/game-logic/economics/
   
   # Financial components
   cp client/src/components/FinancialDashboard.jsx frontend/src/game-logic/economics/
   cp client/src/components/FinancialDashboard.css frontend/src/game-logic/economics/
   cp client/src/components/GameStats.jsx frontend/src/game-logic/economics/
   cp client/src/components/GameStats.css frontend/src/game-logic/economics/
   
   # Loans
   cp client/src/components/NewLoanModal.jsx frontend/src/game-logic/economics/loans/
   cp client/src/components/NewLoanModal.css frontend/src/game-logic/economics/loans/
   cp client/src/components/CDCreationModal.jsx frontend/src/game-logic/economics/loans/
   cp client/src/components/CDCreationModal.css frontend/src/game-logic/economics/loans/
   cp client/src/components/HELOCModal.jsx frontend/src/game-logic/economics/loans/
   cp client/src/components/HELOCModal.css frontend/src/game-logic/economics/loans/
   
   # Bankruptcy
   cp client/src/components/BankruptcyModal.jsx frontend/src/game-logic/economics/bankruptcy/
   cp client/src/components/BankruptcyModal.css frontend/src/game-logic/economics/bankruptcy/
   
   # Market
   cp client/src/components/MarketFluctuationModal.jsx frontend/src/game-logic/economics/market/
   cp client/src/components/MarketFluctuationModal.css frontend/src/game-logic/economics/market/
   cp client/src/components/MarketCrashDisplay.jsx frontend/src/game-logic/economics/market/
   cp client/src/components/MarketCrashDisplay.css frontend/src/game-logic/economics/market/
   
   # Trading
   cp client/src/components/AuctionModal.jsx frontend/src/game-logic/economics/trading/
   cp client/src/components/AuctionModal.css frontend/src/game-logic/economics/trading/
   ```

6. **Migrate contexts and services**
   ```bash
   mkdir -p frontend/src/game-state/contexts/{GameContext,AuthContext,SocketContext,NotificationContext}
   
   # Move contexts
   cp client/src/contexts/GameContext.jsx frontend/src/game-state/contexts/GameContext/index.jsx
   cp client/src/contexts/AuthContext.jsx frontend/src/game-state/contexts/AuthContext/index.jsx
   cp client/src/contexts/SocketContext.jsx frontend/src/game-state/contexts/SocketContext/index.jsx
   cp client/src/contexts/NotificationContext.jsx frontend/src/game-state/contexts/NotificationContext/index.jsx
   
   # Move services
   cp -r client/src/services/* frontend/src/game-state/services/
   ```

7. **Migrate shared components**
   ```bash
   # UI components
   cp client/src/components/NavBar.jsx frontend/src/components/ui/
   cp client/src/components/PlayerList.jsx frontend/src/components/ui/
   cp client/src/components/PlayerList.css frontend/src/components/ui/
   cp client/src/components/TeamDisplay.jsx frontend/src/components/ui/
   cp client/src/components/TeamDisplay.css frontend/src/components/ui/
   cp client/src/components/GameLog.jsx frontend/src/components/ui/
   cp -r client/src/components/PlayerControls/* frontend/src/components/ui/PlayerControls/
   
   # Chat components
   cp -r client/src/components/Chat/* frontend/src/components/chat/
   
   # Notifications
   cp client/src/components/NotificationDisplay.jsx frontend/src/components/notifications/
   cp client/src/components/NotificationDisplay.css frontend/src/components/notifications/
   
   # Cards
   cp client/src/components/CardDisplay.jsx frontend/src/components/cards/
   
   # Bot-related components
   cp client/src/components/BotActionDisplay.jsx frontend/src/components/ui/
   cp client/src/components/BotActionDisplay.css frontend/src/components/ui/
   cp client/src/components/BotEventDisplay.jsx frontend/src/components/ui/
   cp client/src/components/BotEventDisplay.css frontend/src/components/ui/
   ```

8. **Migrate admin components**
   ```bash
   cp client/src/components/AdminBotManager.jsx frontend/src/pages/AdminPage/
   cp client/src/components/AdminBotManager.css frontend/src/pages/AdminPage/
   cp client/src/components/GameModeAdmin.jsx frontend/src/pages/AdminPage/
   
   # Game mode components for HomePage
   cp client/src/components/GameModeSelector.jsx frontend/src/pages/HomePage/
   cp client/src/components/GameModeSettings.jsx frontend/src/pages/HomePage/
   ```

9. **Migrate remaining styles and utils**
   ```bash
   cp -r client/src/styles/* frontend/src/styles/
   cp -r client/src/utils/* frontend/src/utils/
   ```

10. **Update imports in frontend files**
    This step needs to be done manually for each file, updating import paths to match the new structure.

## Phase 2: Backend Migration

1. **Move backend base files**
   ```bash
   cp src/app.py backend/
   cp requirements.txt backend/
   ```

2. **Migrate API routes**
   ```bash
   # Move route files
   for route in game player property admin auth board finance crime special_space trade remote game_mode community_fund view; do
     cp src/routes/${route}_routes.py backend/api/routes/
   done
   
   # Move specialized route directories
   cp -r src/routes/social backend/api/routes/
   cp -r src/routes/player backend/api/routes/
   cp -r src/routes/admin backend/api/routes/
   ```

3. **Migrate socket handlers**
   ```bash
   cp src/controllers/socket_controller.py backend/api/socket/
   cp src/controllers/socket_core.py backend/api/socket/
   cp src/controllers/game_socket_handlers.py backend/api/socket/game_handlers.py
   cp src/controllers/social_socket_handlers.py backend/api/socket/social_handlers.py
   cp src/controllers/admin_socket_handlers.py backend/api/socket/admin_handlers.py
   cp -r src/controllers/social/socket_handlers.py backend/api/socket/social/handlers.py
   ```

4. **Migrate game engine - economy**
   ```bash
   cp src/controllers/finance_controller.py backend/game_engine/economy/finance.py
   cp src/controllers/economic_cycle_controller.py backend/game_engine/economy/market.py
   cp src/controllers/auction_controller.py backend/game_engine/economy/auction.py
   ```

5. **Migrate game engine - players**
   ```bash
   cp src/controllers/player_controller.py backend/game_engine/players/player.py
   cp src/controllers/team_controller.py backend/game_engine/players/team.py
   cp src/controllers/player_action_controller.py backend/game_engine/players/actions.py
   cp src/controllers/crime_controller.py backend/game_engine/players/crime.py
   ```

6. **Migrate game engine - properties**
   ```bash
   cp src/controllers/property_controller.py backend/game_engine/properties/property.py
   cp src/controllers/special_space_controller.py backend/game_engine/special_spaces/special_space.py
   ```

7. **Migrate game engine - bots**
   ```bash
   cp src/controllers/bot_controller.py backend/game_engine/bots/bot.py
   cp src/controllers/bot_event_controller.py backend/game_engine/bots/events.py
   cp src/logic/bot_decision_maker.py backend/game_engine/bots/decision_maker.py
   cp src/services/bot_action_handler.py backend/game_engine/bots/action_handler.py
   ```

8. **Migrate game engine - core**
   ```bash
   cp src/controllers/game_controller.py backend/game_engine/game.py
   cp src/controllers/board_controller.py backend/game_engine/board/board.py
   cp src/controllers/game_mode_controller.py backend/game_engine/game_modes.py
   cp src/controllers/trade_controller.py backend/game_engine/trading/trade.py
   cp src/game_logic/game_logic.py backend/game_engine/rules.py
   ```

9. **Migrate models and remaining controllers**
   ```bash
   cp -r src/models/* backend/models/
   
   # Remaining controllers
   cp src/controllers/admin_controller.py backend/controllers/
   cp src/controllers/auth_controller.py backend/controllers/
   cp src/controllers/connection_controller.py backend/controllers/
   cp src/controllers/remote_controller.py backend/controllers/
   cp src/controllers/adaptive_difficulty_controller.py backend/controllers/
   ```

10. **Migrate utils, migrations, and templates**
    ```bash
    cp -r src/utils/* backend/utils/
    cp -r src/migrations/* backend/migrations/
    cp -r templates/* backend/templates/
    ```

11. **Move configuration files**
    ```bash
    cp -r config/* backend/config/
    ```

12. **Update imports in backend files**
    This step needs to be done manually for each file, updating import paths to match the new structure.

## Phase 3: Shared Resources

1. **Move or create shared constants**
   ```bash
   # Extract common constants from frontend and backend
   # This may require manual identification of shared constants
   # Create new shared files in shared/constants/
   ```

## Phase 4: Scripts and Documentation

1. **Organize scripts**
   ```bash
   cp -r scripts/* scripts/
   cp -r deployment/* scripts/
   ```

2. **Organize tests**
   ```bash
   # Split tests between frontend and backend
   mkdir -p tests/frontend tests/backend
   
   # Copy frontend-related tests
   # Copy backend-related tests
   ```

3. **Update documentation**
   ```bash
   # Update documentation to reflect new structure
   cp -r docs/* docs/
   ```

4. **Create new package.json at root**
   Create a new root package.json with scripts to run both frontend and backend.

## Phase 5: Cleanup and Verification

1. **Verify all imports are working**
   Update any broken imports and ensure the application can build.

2. **Run tests**
   Ensure all tests pass with the new structure.

3. **Start application**
   Verify the application starts and functions correctly.

4. **Remove duplicate files**
   Once everything is verified working, remove any duplicate or unnecessary files. 