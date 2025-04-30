# Pinopoly Project Restructuring Plan

## New Folder Structure

```
pinopoly/
├── README.md                      # Project overview
├── SETUP.md                       # Setup instructions
├── package.json                   # Root package file
├── .env                           # Environment variables
├── .gitignore
│
├── frontend/                      # React frontend
│   ├── public/                    # Static assets
│   ├── package.json               # Frontend dependencies
│   ├── vite.config.js             # Vite configuration
│   └── src/
│       ├── index.jsx              # Entry point
│       ├── App.jsx                # Main App component
│       ├── pages/                 # Top-level views
│       │   ├── BoardPage/         # Main game board page
│       │   ├── HomePage/          # Landing/home page
│       │   ├── AdminPage/         # Admin interface
│       │   ├── DebugPage/         # Debug tools
│       │   ├── ConnectPage/       # Connection page
│       │   └── PlayerPage/        # Player profile/dashboard
│       │
│       ├── game-board/            # Board-specific components
│       │   ├── components/        # Board UI elements
│       │   │   ├── Board/         # Core board rendering
│       │   │   ├── Spaces/        # Board spaces (property, special)
│       │   │   └── PlayerToken/   # Player tokens
│       │   ├── hooks/             # Board-specific hooks
│       │   └── styles/            # Board styles
│       │
│       ├── game-logic/            # Game mechanics
│       │   ├── turns/             # Turn management
│       │   ├── dice/              # Dice roller
│       │   ├── economics/         # Financial mechanics
│       │   │   ├── loans/         # Loan components
│       │   │   ├── market/        # Market fluctuations
│       │   │   ├── bankruptcy/    # Bankruptcy handling
│       │   │   └── trading/       # Trading UI
│       │   └── events/            # Special events
│       │
│       ├── game-state/            # State management
│       │   ├── contexts/          # React contexts
│       │   │   ├── GameContext/   # Game state
│       │   │   ├── AuthContext/   # Authentication
│       │   │   └── SocketContext/ # Socket connections
│       │   └── services/          # API connections
│       │
│       ├── components/            # Shared/reusable components
│       │   ├── ui/                # UI elements
│       │   ├── modals/            # Modal components
│       │   ├── forms/             # Form components
│       │   ├── cards/             # Card displays
│       │   ├── chat/              # Chat features
│       │   └── notifications/     # Notifications
│       │
│       ├── styles/                # Global styles
│       │   ├── index.css          # Main styles
│       │   ├── variables.css      # CSS variables
│       │   └── themes/            # Theme styles
│       │
│       └── utils/                 # Frontend utilities
│           ├── formatters.js      # Data formatting
│           ├── validators.js      # Input validation
│           └── constants.js       # Frontend constants
│
├── backend/                       # Flask backend
│   ├── app.py                     # Main application file
│   ├── requirements.txt           # Python dependencies
│   ├── config/                    # Configuration
│   │   ├── development.json       # Dev environment
│   │   ├── production.json        # Production environment
│   │   └── testing.json           # Test environment
│   │
│   ├── game_engine/               # Game core logic
│   │   ├── board/                 # Board management
│   │   ├── economy/               # Economic system
│   │   │   ├── finance.py         # Financial mechanics
│   │   │   ├── market.py          # Market fluctuations
│   │   │   └── taxation.py        # Tax system
│   │   ├── players/               # Player management
│   │   ├── properties/            # Property system
│   │   ├── special_spaces/        # Special spaces
│   │   ├── events/                # Game events
│   │   └── bots/                  # Bot system
│   │
│   ├── api/                       # API endpoints
│   │   ├── routes/                # Flask routes
│   │   │   ├── game_routes.py     # Game management
│   │   │   ├── player_routes.py   # Player actions
│   │   │   ├── property_routes.py # Property actions
│   │   │   ├── admin_routes.py    # Admin controls
│   │   │   └── auth_routes.py     # Authentication
│   │   └── socket/                # Socket handlers
│   │       ├── game_handlers.py   # Game socket events
│   │       ├── chat_handlers.py   # Chat socket events
│   │       └── socket_core.py     # Socket infrastructure
│   │
│   ├── models/                    # Database models
│   │   ├── game.py                # Game model
│   │   ├── player.py              # Player model
│   │   ├── property.py            # Property model
│   │   ├── transaction.py         # Transaction model
│   │   └── relationships/         # Complex model relationships
│   │
│   ├── controllers/               # Business logic
│   │   ├── game_controller.py     # Game management
│   │   ├── player_controller.py   # Player actions
│   │   ├── property_controller.py # Property management
│   │   └── admin_controller.py    # Admin actions
│   │
│   ├── services/                  # Reusable services
│   │   ├── auth_service.py        # Authentication
│   │   └── event_service.py       # Event handling
│   │
│   ├── utils/                     # Backend utilities
│   │   ├── config_manager.py      # Configuration
│   │   ├── errors.py              # Error handling
│   │   └── validators.py          # Data validation
│   │
│   ├── migrations/                # Database migrations
│   │   └── versions/              # Migration versions
│   │
│   └── templates/                 # HTML templates
│       └── admin/                 # Admin templates
│
├── shared/                        # Shared between front/backend
│   ├── constants/                 # Shared constants
│   │   ├── board_layout.js        # Board configuration
│   │   ├── property_sets.js       # Property set definitions
│   │   └── game_modes.js          # Game mode definitions
│   └── types/                     # Type definitions (if using TS)
│
├── scripts/                       # Utility scripts
│   ├── setup.sh                   # Setup script
│   ├── deploy.sh                  # Deployment script
│   └── test.sh                    # Test script
│
├── docs/                          # Documentation
│   ├── architecture.md            # System architecture
│   ├── game_rules.md              # Game rules
│   └── api.md                     # API documentation
│
└── tests/                         # Tests
    ├── frontend/                  # Frontend tests
    │   └── components/            # Component tests
    └── backend/                   # Backend tests
        ├── unit/                  # Unit tests
        ├── integration/           # Integration tests
        └── api/                   # API tests
```

## Migration Strategy

### Phase 1: Initial Structure Setup
1. Create the new root directory structure
2. Move top-level files to appropriate locations

### Phase 2: Frontend Migration
1. Move client/ to frontend/
2. Reorganize React components by purpose:
   - Move board components to game-board/
   - Move economic components to game-logic/economics/
   - Move contexts to game-state/contexts/

### Phase 3: Backend Migration
1. Move src/ to backend/
2. Reorganize controllers, models by domain:
   - Create game_engine/ with subfolders
   - Move related controllers to appropriate folders

### Phase 4: Shared Resources
1. Create shared/ folder
2. Extract common constants, types, configs

### Phase 5: Testing & Documentation
1. Reorganize tests to match new structure
2. Update imports and paths in all files
3. Update documentation to reflect new structure

## File Moves and Renames

### Frontend Files
- All components in client/src/components/ categorized into:
  - game-board/ (Board, GameBoard, PlayerToken, etc.)
  - game-logic/ (DiceRoller, GameStats, PropertyList, etc.)
  - components/ (reusable UI components)

### Backend Files
- Controllers organized by domain:
  - game_engine/economy/ (finance_controller.py, economic_cycle_controller.py)
  - game_engine/players/ (player_controller.py, team_controller.py)
  - game_engine/properties/ (property_controller.py)
  - game_engine/bots/ (bot_controller.py, bot_event_controller.py)

## Path Updates
After moving files, all import paths will need to be updated to reflect the new structure. 