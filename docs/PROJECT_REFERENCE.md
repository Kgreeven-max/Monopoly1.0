# Pi-nopoly Project Reference

## Project Overview

Pi-nopoly is a modern digital board game inspired by Monopoly with unique mechanics, designed to run on a Raspberry Pi and be played across multiple devices. The application uses a Flask backend with SocketIO for real-time communication and a web-based frontend.

## Tech Stack

### Backend
- **Framework**: Flask (Python 3.8+)
- **Database**: SQLAlchemy with SQLite or PostgreSQL 
- **Websockets**: Flask-SocketIO for real-time updates
- **Authentication**: JWT-based authentication
- **Deployment**: Runs on Raspberry Pi with Cloudflare Tunnel for remote access

### Frontend
- Web-based client application served from Flask static folder
- Responsive design to work across phones, tablets, and computers

## Project Structure

```
/
├── app.py                 # Main application entry point
├── requirements.txt       # Python dependencies
├── CHANGELOG.md           # Version history
├── README.md              # Project documentation
├── docs/                  # Detailed documentation for each system
│   ├── index.md           # Documentation entry point
│   ├── event_system.md    # Event system documentation
│   ├── property-development.md # Property development system
│   ├── auction-system.md  # Auction system documentation
│   ├── financial-instruments.md # Financial instruments documentation
│   ├── game-modes.md      # Game modes documentation
│   └── social-features.md # Social features documentation
├── src/                   # Source code
│   ├── controllers/       # Business logic
│   │   ├── finance_controller.py # Financial instruments logic
│   │   ├── game_controller.py    # Game state management
│   │   ├── property_controller.py # Property operations
│   │   ├── special_space_controller.py # Special space actions
│   │   ├── socket_controller.py  # Socket event handlers
│   │   ├── bot_controller.py     # AI player management
│   │   ├── bot_event_controller.py # AI event handling
│   │   ├── adaptive_difficulty_controller.py # AI difficulty management
│   │   └── crime_controller.py   # Crime system management
│   ├── models/            # Database models
│   │   ├── finance/       # Financial models
│   │   │   └── loan.py    # Loan, CD, and HELOC model
│   │   ├── community_fund.py # Community fund management
│   │   ├── player.py      # Player model
│   │   ├── bot_player.py  # AI player behaviors and strategies
│   │   ├── bot_events.py  # AI-triggered events
│   │   ├── property.py    # Property model
│   │   ├── crime.py       # Crime system models
│   │   └── special_space.py # Special spaces and cards
│   ├── routes/            # API endpoints
│   │   ├── finance_routes.py   # Financial endpoints
│   │   ├── community_fund_routes.py # Community fund endpoints
│   │   ├── property_routes.py  # Property endpoints
│   │   ├── admin_routes.py     # Admin control endpoints
│   │   ├── crime_routes.py     # Crime system endpoints
│   │   └── special_space_routes.py # Special space endpoints
│   ├── views/             # View templates
│   ├── utils/             # Utility functions
│   └── migrations/        # Database migrations
├── client/                # Frontend code
│   └── dist/              # Built frontend assets
└── public/                # Static assets
```

## Key Features

1. **Dynamic Economic System**:
   - Inflation engine creating realistic economic simulation
   - Economic phases: Recession, Normal, Growth, Boom
   - Property values that fluctuate with economic conditions

2. **Property System**:
   - Multi-level property development (5 levels)
   - Zoning regulations for property groups
   - Damage and repair mechanics
   - Environmental studies and community approval requirements

3. **Auction System**:
   - Standard property auctions when players decline to purchase
   - Foreclosure auctions for properties with unpaid loans
   - Real-time bidding with timer-based resolution

4. **Event System**:
   - Economic events (boom, crash, interest rate changes)
   - Natural disasters (hurricanes, earthquakes, floods)
   - Community events (festivals, infrastructure projects, tax reforms)
   - Temporary effects system

5. **Special Spaces**:
   - Community Chest and Chance card systems with various action types
   - Tax spaces with economic-phase based calculations
   - Go, Jail, Free Parking, and Go To Jail spaces
   - Dynamic card actions (move, pay, collect, jail, repairs, etc.)

6. **Financial Instruments**:
   - Backend Features:
     - Loans with variable interest rates based on economic conditions
     - Certificates of Deposit (CDs) with term-based returns
     - Home Equity Line of Credit (HELOC) for property-backed borrowing
     - Community Fund for public money management
     - Bankruptcy system for handling player insolvency
   - UI Components:
     - `FinancialDashboard`: Main interface for all financial management
       - Real-time financial overview
       - Interest rate monitoring
       - Tab-based instrument management
     - `NewLoanModal`: Loan creation interface
       - Dynamic amount selection
       - Payment calculations
       - Terms and conditions display
     - CD Investment controls
     - HELOC management interface
     - Responsive design for all devices

7. **Complete AI Players System**:
   - Six bot personalities with unique strategies:
     - Conservative Bot: Focuses on safe investments and steady growth
     - Aggressive Bot: Rapid expansion and high-risk investments
     - Strategic Bot: Balanced approach focusing on monopolies
     - Opportunistic Bot: Market timing strategy
     - Shark Bot: Predatory focus on blocking others and targeting distressed players
     - Investor Bot: Financial instrument focus with sophisticated ROI calculations
   - Adaptive difficulty system to maintain competitive balance
   - Bot personalities with unique decision-making strategies
   - Three difficulty levels (easy, medium, hard)

8. **Crime System**:
   - Five crime types with unique mechanics and consequences
   - Dynamic detection system based on game difficulty and player standing
   - Property damage and repair system
   - Police patrol with scheduled checks
   - Criminal record tracking and consequences

9. **Game Modes System**:
   - Multiple game modes with unique rules and win conditions:
     - Classic Mode: Traditional gameplay with standard rules
     - Speed Mode: Faster gameplay with time/turn limits
     - Co-op Mode: Collaborative gameplay to develop properties
     - Tycoon Mode: Development-focused mode with expanded property improvements
     - Market Crash Mode: Economic instability with volatile property values
     - Team Battle Mode: Team-based competitive gameplay
   - Fully customizable game mode settings
   - Mode-specific UI components and interfaces
   - Dynamic win condition checking based on mode

10. **Remote Play**:
   - Multi-device support via Cloudflare Tunnel
   - Player interface for mobile devices
   - Admin interface for game management
   - Board display for TV/monitor

## Core Systems Documentation

### Event System
- Events have a 15% chance to trigger each game cycle
- Types: Economic, Natural Disasters, Community
- Property damage requires repairs to restore value
- Events can create temporary effects with duration

### Property Development System
- 5 development levels from Undeveloped to Premium
- Different property groups have different zoning regulations
- Development costs scale with level, property value, and economic conditions
- Higher developments require community approval or environmental studies

### Auction System
- Standard auctions occur when players decline to purchase properties
- Foreclosure auctions liquidate properties with unpaid loans
- Bidding follows a timer-based system with minimum increments
- Players can pass their turn and are then excluded from further bidding

### Special Spaces System
- **Community Chest & Chance Cards**: Card decks with various actions
- **Tax Spaces**: Income Tax and Luxury Tax with economic-aware calculations
- **Special Locations**: Go, Free Parking, Jail, and Go To Jail
- **Card Actions**: Movement, payments, collections, jail-related, repairs, birthday collections
- **Utility & Railroad Spaces**: Special rent calculations and interactions

### Financial Instruments System
- **Loans**: Standard borrowing with interest rates affected by economic conditions
  - Interest rates vary based on player credit history and economic phase
  - 5-lap standard term with compounding interest
  - Full or partial repayment options
  
- **Certificates of Deposit (CDs)**: Investment option for excess cash
  - Term lengths of 3, 5, or 7 laps with increasing interest rates
  - Early withdrawal penalties (10% of current value)
  - Interest rates based on economic conditions
  
- **Home Equity Line of Credit (HELOC)**: Borrow against property value
  - Better rates than standard loans (collateralized)
  - Maximum value based on property value (60% base with bonuses for developments)
  - 8-lap standard term with property as collateral
  
- **Community Fund**: Public money pool for game events
  - Can be increased by tax collections, cards, and special events
  - Used for Free Parking bonuses and community events
  - Admin controls for fund management
  
- **Bankruptcy System**: Handle player insolvency
  - Triggered when debts exceed combined cash and sellable assets
  - Clears all debt but loses all properties
  - Increases player's bankruptcy count affecting future loans

### AI Players System
- **Bot Types**:
  - **Conservative Bot**: Safe investments, high cash reserves, lower risk tolerance
  - **Aggressive Bot**: Rapid expansion, high-risk investments, willing to spend nearly all cash
  - **Strategic Bot**: Focuses on completing monopolies with strategic property valuation
  - **Opportunistic Bot**: Market timing strategies, buys during recession, sells during boom
  - **Shark Bot**: Predatory strategies, blocks monopolies, targets players in financial distress
  - **Investor Bot**: Focuses on financial instruments, sophisticated ROI calculations, selective property purchases

- **Difficulty Levels**:
  - **Easy**: 70% optimal decisions, 20% property valuation error, 2-turn planning horizon
  - **Medium**: 85% optimal decisions, 10% property valuation error, 4-turn planning horizon
  - **Hard**: 95% optimal decisions, 5% property valuation error, 6-turn planning horizon

- **Adaptive Difficulty System**:
  - Automatically assesses game balance between human and AI players
  - Dynamically adjusts bot difficulty to maintain competitive balance
  - Controlled through admin interface with manual adjustment options
  - Scheduled assessments at configurable intervals

- **Bot Decision-Making Framework**:
  - Property valuation algorithms specific to each bot type
  - Auction bidding strategies with personality-driven behaviors
  - Investment and development decision-making
  - Risk tolerance and planning horizon parameters

### Crime System
- **Crime Types**:
  - **Theft**: Steal money from another player
    - 10-20% of target's cash can be stolen
    - Medium risk of detection
    - Jail time if caught
    
  - **Property Vandalism**: Damage property to reduce its value and rent
    - Reduces property value by 10-30%
    - Damage repairs automatically after 3 turns
    - Medium risk of detection
    - Jail time if caught
    
  - **Rent Evasion**: Avoid paying rent when landing on a property
    - Avoid the entire rent payment
    - Low risk of detection
    - If caught, pay original rent plus 50% penalty
    
  - **Forgery**: Create fake money for immediate cash
    - Gain $100-300 immediately
    - High risk of detection
    - If caught, pay double the amount as fine and go to jail
    
  - **Tax Evasion**: Avoid paying taxes
    - Avoid the entire tax payment
    - Medium-high risk of detection
    - If caught, pay double the original tax amount

- **Detection System**:
  - Base detection rates vary by difficulty level:
    - Easy: 60% chance of being caught
    - Normal: 50% chance of being caught
    - Hard: 40% chance of being caught
  - Player's community standing affects detection (lower standing = higher chance)
  - Police activity level (set by admin or random events) affects detection rates
  - Police patrols can randomly detect recent undetected crimes

- **Consequences**:
  - Criminal record tracking for each player
  - Community standing reduction for detected crimes
  - Jail time for most crimes
  - Financial penalties based on crime type
  - Property damage repair through temporary effects system

- **Admin Controls**:
  - Set police activity level (0.5 to 2.0 multiplier)
  - Pardon players for specific or all crimes
  - View crime statistics and reports
  - Trigger police patrols manually

### Tax System (Partially Implemented)
- Basic income tax implementation
- Luxury tax on high-value properties
- Tax rates affected by economic conditions
- Tax evasion mechanics (via Crime System)

## API Endpoints

The application exposes various API endpoints organized by domain:

- **/api/health** - Health check endpoint
- **/api/game/** - Game management endpoints
- **/api/player/** - Player management endpoints
- **/api/finance/** - Financial transaction endpoints
  - **/api/finance/loan/new** - Create a new loan
  - **/api/finance/loan/repay** - Repay a loan partially or fully
  - **/api/finance/cd/new** - Create a Certificate of Deposit
  - **/api/finance/cd/withdraw** - Withdraw a CD (with potential penalty)
  - **/api/finance/heloc/new** - Create a HELOC on a property
  - **/api/finance/interest-rates** - Get current interest rates
  - **/api/finance/loans** - List player's active loans, CDs, and HELOCs
  - **/api/finance/bankruptcy** - Declare bankruptcy
- **/api/community-fund** - Get Community Fund information
- **/api/admin/community-fund/** - Admin endpoints for Community Fund management
  - **/api/admin/community-fund/add** - Add funds to Community Fund
  - **/api/admin/community-fund/withdraw** - Withdraw funds from Community Fund
  - **/api/admin/community-fund/clear** - Clear all funds from Community Fund
- **/api/crime/** - Crime system endpoints
  - **/api/crime/commit** - Commit a crime
  - **/api/crime/history/{player_id}** - Get player's crime history
  - **/api/crime/types** - Get available crime types
- **/api/admin/crime/** - Admin crime control endpoints
  - **/api/admin/crime/police-activity** - Set police activity level
  - **/api/admin/crime/pardon** - Pardon a player for crimes
  - **/api/admin/crime/statistics** - Get crime statistics
  - **/api/admin/crime/police-patrol** - Trigger a police patrol
- **/api/admin/bots/** - Bot management endpoints
  - **/api/admin/bots** - Get available bot types and difficulty levels
  - **/api/admin/adaptive-difficulty/assessment** - Assess game balance
  - **/api/admin/adaptive-difficulty/adjust** - Manually adjust bot difficulty
  - **/api/admin/adaptive-difficulty/auto-adjust** - Auto-assess and adjust difficulty
- **/api/trade/** - Trading endpoints
- **/api/admin/** - Admin control endpoints
- **/api/board/** - Board and property endpoints
- **/api/board/special-spaces/** - Special spaces endpoints
- **/api/cards/** - Card management endpoints

## Socket Events

Real-time communication is handled through socket events:

- **game_event** - Notifies clients about triggered events
- **property_update** - Updates about property changes
- **auction_started** - Notification of auction beginning
- **auction_bid** - New bid in an auction
- **auction_pass** - Player passes on bidding
- **player_update** - Updates about player status
- **chat_message** - New chat message
- **card_drawn** - Card has been drawn from a deck
- **chance_card_drawn** - Chance card drawn notification
- **community_chest_card_drawn** - Community Chest card drawn notification
- **tax_paid** - Tax payment notification
- **player_sent_to_jail** - Player sent to jail notification
- **free_parking_bonus** - Player received Free Parking bonus
- **loan_created** - New loan created
- **loan_repaid** - Loan repayment made
- **cd_created** - New CD created
- **cd_withdrawn** - CD withdrawn
- **heloc_created** - New HELOC created
- **player_bankruptcy** - Player declared bankruptcy
- **community_fund_update** - Community Fund balance changed
- **bot_created** - New AI player created
- **bot_removed** - AI player removed from game
- **bot_updated** - AI player settings updated
- **bot_difficulty_adjusted** - AI difficulty level adjusted
- **bot_event** - AI player triggered a special event
- **crime_detected** - Crime was detected (broadcast to all)
- **player_notification** - Private notification (e.g., successful crime)
- **property_repaired** - Property damage has been repaired

## Development Status

Current version: 0.9.0

### Implemented Features
- Game Modes System (v0.9.0) - Complete implementation of different game modes
  - Multiple game modes with unique settings and win conditions
  - Game mode selection and configuration from admin interface
  - Win condition tracking based on different modes
  - Mode-specific UI components

- Remote Play (v0.8.0) - Complete implementation of remote play capabilities
  - Cloudflare Tunnel integration for secure remote access
  - QR code sharing for easy connection
  - Remote player connection monitoring
  - Disconnect handling and auto-reconnection

- Crime System (v0.7.0) - Complete implementation of crime mechanics
  - Five crime types with unique mechanics and consequences
  - Police patrol system with scheduled checks
  - Dynamic detection based on game difficulty and player standing
  - Criminal record tracking and consequences
  - Property damage and repair system
  
- AI Players System (v0.6.0) - Complete implementation of all bot types
  - Six bot personalities with unique strategies
  - Adaptive difficulty system
  - Bot-specific decision-making algorithms
  - Three difficulty levels with adjustable parameters
  
- Financial Instruments (v0.5.0) - Loans, CDs, HELOC, and Community Fund
  - Complete loan, CD, and HELOC functionality with database models
  - Interest rates that vary with economic conditions
  - Community Fund implementation for public money management
  - Bankruptcy system for handling player insolvency
  
- Special Spaces System (v0.4.0) - Community Chest, Chance, Tax spaces
- Property Development System (v0.3.0)
- Event System (v0.2.0)
- Auction System (v0.2.0)

### Next Features to Implement (According to Design Doc)
1. **Social Features**
   - Chat system with multiple channels
   - Player alliances and partnerships
   - Reputation system
   - Trade negotiations interface

2. **User Interface Enhancements**
   - Event visualization system
   - Enhanced property cards with damage indicators
   - Economic phase visual indicators
   - Real-time game state visualization

## Development Guidelines

1. **Database Changes:**
   - Run migrations with `flask db migrate -m "Description"`
   - Apply with `flask db upgrade`

2. **Testing Events:**
   - Use admin console to trigger specific events
   - Verify database state after events

3. **Security Considerations:**
   - Keep sensitive logic on server-side
   - Validate all user input
   - Use environment variables for secrets

4. **Performance:**
   - Optimize for Raspberry Pi hardware
   - Limit database queries
   - Use efficient SocketIO communication

## Running the Application

1. **Setup:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configuration:**
   Create a `.env` file with:
   ```
   SECRET_KEY=your-secret-key
   ADMIN_KEY=your-admin-key
   DISPLAY_KEY=your-display-key
   DATABASE_URI=sqlite:///pinopoly.sqlite
   ADAPTIVE_DIFFICULTY_ENABLED=true
   ADAPTIVE_DIFFICULTY_INTERVAL=15
   POLICE_PATROL_ENABLED=true
   POLICE_PATROL_INTERVAL=45
   ```

3. **Database:**
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

4. **Run:**
   ```bash
   python app.py
   ```

5. **Access:**
   - Player Interface: `http://[RaspberryPi_IP]:5000/`
   - Admin Interface: `/admin`
   - Board Display: `/board`

## Cloudflare Tunnel Setup (Planned)

For remote access to the game running on a Raspberry Pi:

1. Install cloudflared
2. Authenticate with Cloudflare
3. Create tunnel and configure routing
4. Start tunnel with `cloudflared tunnel run pinopoly`

*This document will be continuously updated as the project evolves* 