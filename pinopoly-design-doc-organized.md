# Pi-nopoly: Complete Design Document

## SECTION 1: GAME OVERVIEW & ARCHITECTURE

### 1.1 System Overview
Pi-nopoly is a modern economic strategy board game inspired by Monopoly, designed to run on a Raspberry Pi 5 with internet accessibility exclusively via Cloudflare Tunnel. The system integrates complex financial mechanics including inflation, taxes, loans, property investment, and crime in a digital board game experience playable remotely from anywhere in the world.

### 1.2 System Architecture
- **Server**: Raspberry Pi 5 (8GB RAM)
- **Backend**: Python/Flask
- **Database**: SQLite
- **Communication**: WebSockets for real-time updates
- **Internet Access**: Cloudflare Tunnel for all game connectivity
- **Interfaces**: Web-based for all devices
  - Mobile UI for players (responsive web design)
  - Admin dashboard for game control (tablet optimized)
  - TV display for board visualization

### 1.3 Network Configuration
- **Internet-Only Mode**: Cloudflare Tunnel for all connections
  - Secure HTTPS connections
  - No port forwarding required
  - Custom domain support (optional)
  - End-to-end encryption
  - No local network dependency
- **WebSocket Protocol**: For all real-time game updates
- **HTTP/REST API**: For player actions and game management
- **Authentication**: PIN-based player access

### 1.4 Remote Play Features
- **Global Accessibility**: Play from anywhere with internet access
- **Multi-Device Support**: Mobile, tablet, laptop, desktop
- **Low Latency Design**: Optimized for responsive remote play
- **Disconnect Handling**: Auto-reconnection and state preservation
- **Spectator Mode**: Watch games without participating

### 1.5 Project Dependencies
- Flask 2.3+
- Flask-SocketIO 5.3+
- SQLAlchemy 2.0+
- Eventlet 0.33+
- Python-SocketIO 5.10+
- Cloudflared (for Cloudflare Tunnel)

## SECTION 2: GAME RULES & FLOW

### 2.1 Game Setup
1. Players join via web browser with username + PIN
   - Remote players connect via Cloudflare Tunnel URL
   - Support for up to 8 total players (any combination of humans and bots)
2. Admin sets difficulty level (Easy/Normal/Hard)
   - Easy: Start with $3000, lower tax rates
   - Normal: Start with $2000, standard tax rates
   - Hard: Start with $1000, higher tax rates
3. House rules configured by vote or admin:
   - Free Parking Fund: ON/OFF
   - Auction Required: ON/OFF
   - Lap Limit: Infinite/10/20/30
   - AI Players: 0-8 (dynamically adjustable during game)
   - Remote Play Timeout: 30s/60s/90s (for turn actions)

### 2.2 Turn Sequence
1. **Roll Phase**
   - Player rolls dice (2d6)
   - Move token accordingly
   - Three consecutive doubles sends player to jail

2. **Action Phase** (based on landing tile)
   - Property: Buy, auction, or pay rent
   - Tax: Pay income/luxury tax
   - Chance/Community Chest: Draw card and follow instructions
   - Go to Jail: Move directly to jail
   - Jail: Roll doubles, pay fine, or use lawyer
   - Free Parking: Collect community fund (if enabled)
   - GO: Collect $200 and report income

3. **Optional Actions** (can be done anytime during turn)
   - Take out loan/HELOC
   - Create CD investment
   - Initiate trade with other players
   - Improve properties
   - Commit tax evasion (strategic non-reporting)
   - Attempt theft (once per game, strategic)

4. **End Turn Phase**
   - Confirm end of turn
   - Process financial updates
   - Move to next player
   - Auto-end turn if timeout reached (remote play)

### 2.3 Endgame Conditions

#### Default Mode: Infinite Duration
- Game continues until players decide to end
- Winner determined by highest net worth

#### Lap-Limited Mode
- Game ends after predetermined number of laps (10/20/30)
- Final 3 laps have special rules:
  - No new CDs allowed
  - Existing CDs limited to 80% value
  - Final lap forces liquidation of all assets

## SECTION 3: CORE GAME SYSTEMS

### 3.1 Property System

#### Property Structure
- **22 colored properties** (50% of classic Monopoly values)
- **4 railroads**
- **2 utilities**
- **Property Groups**: 8 color-coded neighborhoods

#### Property Mechanics
- **Purchase**: Pay listed price
- **Rent**: Scales with inflation and improvements
- **Improvements**: 
  - Maximum 1 level (no hotels)
  - Cost: 50% of property value
  - Increases rent by 150-200%
- **Ownership Benefits**:
  - Group bonus: +50% rent when owning entire group
  - Neighborhood effect: Improvements increase value of all properties in group
- **Auctions**: Properties not purchased directly are auctioned

### 3.2 Banking System

#### Starting Capital
- Easy: $3000
- Normal: $2000
- Hard: $1000

#### Economic Transactions
- Property purchases
- Rent payments 
- Tax payments
- Loans and CDs
- Improvements
- Fines and penalties
- Trade cash transfers

### 3.3 Financial Instruments

#### Loans
- **Line of credit**: $1000+ (based on difficulty)
- **Interest Rate**: 8-20% per GO lap (adjusts with inflation)
- **Repayment**: Optional partial or full payments
- **Debt Cap**: 200% of net worth
- **Penalties**: Foreclosure after prolonged non-payment

#### CDs (Certificates of Deposit)
- **Investment Options**:
  - 3 laps: 8% return
  - 5 laps: 12% return
  - 7 laps: 18% return
- **Early Withdrawal**:
  - Before 50%: No interest, 10% penalty
  - After 50%: Partial interest, 5% penalty
- **Emergency Liquidation**: 50% of principal (bankruptcy only)

#### HELOCs (Home Equity Line of Credit)
- **Borrow up to 70%** of property value
- **Property lien**: Locks property from trade
- **Interest Rate**: Adjusts with inflation
- **Foreclosure**: After 4 unpaid laps
- **Penalty**: Loss of property

### 3.4 Advanced Inflation Engine

The inflation engine is Pi-nopoly's signature economic system, creating a dynamic economic environment that responds to player actions and game progression.

#### Economic State Assessment
The system continuously tracks the total money in circulation:
- **Recession**: < $5K
- **Stable**: $5K-$10K
- **Inflation**: $10K-$15K
- **High Inflation**: $15K-$20K
- **Overheated**: > $20K

#### Economic Impact Multipliers
Each economic state has different multipliers affecting various game aspects:

| Economic State | Property Values | Rent Amounts | Loan Rates | CD Returns | Tax Rates |
|----------------|----------------|-------------|------------|------------|-----------|
| Recession      | 0.8x           | 0.8x        | -2%        | -1%        | -3%       |
| Stable         | 1.0x           | 1.0x        | Base       | Base       | Base      |
| Inflation      | 1.3x           | 1.3x        | +3%        | +2%        | +3%       |
| High Inflation | 1.6x           | 1.6x        | +6%        | +3%        | +5%       |
| Overheated     | 2.0x           | 2.0x        | +10%       | +5%        | +7%       |

#### Economic Stabilization Mechanisms
To prevent wild economic swings and create a more balanced gameplay experience, Pi-nopoly implements:
- **Dynamic Dampening Factor**: Only 25% of change applies immediately
- **State Transition Cooldown**: Minimum turns before next state change
- **Trend Analysis**: Economic direction prediction based on multiple samples
- **Progressive Taxation**: Higher taxes on wealthier players
- **Wealth Distribution**: Periodic redistribution events from Community Fund

### 3.5 Tax System

#### Income Reporting
At each GO passing:
1. Player receives $200
2. Prompt to report income
   - **Report**: Pay scaled income tax (10-25% based on inflation)
   - **Evade**: Risk audit (no immediate tax)

#### Audit Engine
- **Suspicion Score**: Tracks evasion patterns + visible wealth
- **Audit Trigger**: Random event targeting highest suspicion
- **Audit Results**:
  - **Caught Evading**: Back taxes + penalties (2x rate)
  - **Honest Players**: Possible tax refund from community fund

### 3.6 Crime System

#### Tax Evasion
- **Mechanism**: Under-report income at GO
- **Risk**: Increases Suspicion Score
- **Penalty**: Back taxes + fines if caught

#### Theft
- **Usage**: Once per game per player
- **Success Rate**: 70% chance if far from victim
- **Detection**: Victim can guess thief
- **Penalty**: Return money + fine if identified

#### Jail Mechanics
- **Entry Conditions**: Land on "Go to Jail", 3 doubles, failed theft
- **Escape Options**:
  - Pay $200 fine
  - Roll doubles (1 attempt per turn)
  - Wait 3 turns and pay $100
- **Lawyer Option**: Pay $125 (30% instant release, 30% reduced sentence, 40% fail)

## SECTION 4: COMMUNITY FUND & FREE PARKING

### 4.1 Community Fund System
The Community Fund is Pi-nopoly's central economic redistribution mechanism, collecting money from various game actions and redistributing it according to game rules.

#### Fund Sources
- All tax payments (income and luxury tax)
- All fines and penalties (jail, crime, etc.)
- 10% of auction overbids
- 5% of AI-to-AI trades
- Property tax (bonus tax on excessive ownership)

#### Fund Distribution Methods
- **Free Parking**: When a player lands on Free Parking, they collect part or all of the fund (configurable)
- **Community Chest Cards**: Certain cards draw from the fund (20% of balance)
- **Bank Holiday**: Equal split to all players (periodic event)
- **Audit Refunds**: For honest taxpayers

### 4.2 Free Parking Configuration
In Pi-nopoly, Free Parking behavior is configurable by the admin and directly tied to the Community Fund.

#### Free Parking Options
- **Full Amount**: Player gets the entire Community Fund
- **Half Amount**: Player gets 50% of the Community Fund
- **Fixed Amount**: Player gets a fixed amount (default: $500)
- **Disabled**: Free Parking has no monetary effect

## SECTION 5: BOT/AI PLAYERS SYSTEM

### 5.1 Dynamic Bot Management
Pi-nopoly supports up to 8 total players (human or AI) in any combination, with the ability to dynamically add or remove bot players during gameplay.

#### Player Capacity
- **Maximum Players**: 8 players total (any mix of human/AI)
- **Minimum Players**: 2 players (can be 2 humans, 2 bots, or 1 of each)
- **Dynamic Joining**: Players can join ongoing games
- **Dynamic Bot Addition**: Admin can add bots to reach desired player count
- **Bot Replacement**: Bots can temporarily substitute for disconnected human players

### 5.2 Bot Types & Personalities
Each bot type has a distinct personality and strategy that influences gameplay:

#### Conservative Bot
- **Strategy**: Focuses on safe investments and steady growth
- **Property Purchases**: Only buys properties under 75% of cash reserves
- **Improvements**: Only improves properties when owning complete color group
- **Financial**: Rarely takes loans, prefers secure CDs
- **Tax Behavior**: Always reports accurate income
- **Trading**: Only accepts clearly favorable trades

#### Aggressive Bot
- **Strategy**: Rapid expansion and high-risk investments
- **Property Purchases**: Will spend up to 100% of cash on promising properties
- **Improvements**: Improves properties immediately when affordable
- **Financial**: Frequently leverages loans for expansion
- **Tax Behavior**: Occasionally under-reports income
- **Trading**: Initiates many trade offers, accepts moderate deals

#### Strategic Bot
- **Strategy**: Balanced approach focusing on monopolies
- **Property Purchases**: Prioritizes completing color groups
- **Improvements**: Calculates ROI before improving
- **Financial**: Uses loans strategically to complete sets
- **Tax Behavior**: Reports accurately most of the time
- **Trading**: Offers and accepts trades that complete sets

#### Shark Bot
- **Strategy**: Predatory focus on player loans and foreclosures
- **Property Purchases**: Buys properties to block others' monopolies
- **Improvements**: Focuses on high-traffic properties
- **Financial**: Offers loans to cash-strapped players
- **Tax Behavior**: Moderate tax evasion
- **Trading**: Targets players in financial distress

#### Investor Bot
- **Strategy**: Financial instrument focus over properties
- **Property Purchases**: Buys high-value properties only
- **Improvements**: Improves only highest-ROI properties
- **Financial**: Heavy use of CDs, HELOCs for leverage
- **Tax Behavior**: Complex tax strategies with occasional evasion
- **Trading**: Trades based on sophisticated property valuation

### 5.3 Bot Difficulty Levels
Each bot personality type has three difficulty levels:

#### Difficulty Parameters
- **Easy**: 70% optimal decisions, 20% property valuation error, 2-turn planning horizon
- **Medium**: 85% optimal decisions, 10% property valuation error, 4-turn planning horizon
- **Hard**: 95% optimal decisions, 5% property valuation error, 6-turn planning horizon

### 5.4 Human-like Bot Behaviors
To make bots more human-like and prevent them from being too perfect:

#### Bot Psychology Features
- **Mood System**: Bots have emotional states affecting decisions
- **Recency Bias**: Recent events have greater influence
- **Confirmation Bias**: Tendency to repeat past decisions
- **Risk Aversion**: Variable based on personality and mood
- **Loss Aversion**: Stronger negative reaction to potential losses

### 5.5 Adaptive Difficulty System
To ensure human players remain competitive:

#### Difficulty Adaptation
- **Performance Analysis**: Regular comparison of bot vs human performance
- **Auto-Adjustment**: Bot difficulty decreases if humans fall significantly behind
- **Difficulty Factors**: Adjusted decision accuracy, valuation error, planning horizon
- **Transparency**: Admin notified of automatic adjustments
- **Manual Override**: Admin can manually set difficulty

## SECTION 6: INTERFACE ARCHITECTURE

The Pi-nopoly system implements a multi-device approach with three distinct interface types, each accessed via specific URLs and optimized for its purpose.

### 6.1 Interface Distribution System

#### URL Structure
- **Base Game URL**: `https://your-pinopoly.example.com/` (Cloudflare Tunnel address)
- **Player Interface**: `/play?id=[PLAYER_ID]&pin=[PIN]`
- **Admin Console**: `/admin?key=[ADMIN_KEY]`
- **TV Board Display**: `/board?display=tv&key=[DISPLAY_KEY]`

#### Role Assignment Process
1. **Home Page** (`/`): Landing page where:
   - New players can register with username
   - Existing players can log in with PIN
   - Admin can access console with key
   - TV display can be initialized

2. **Role-Based Redirects**:
   - Players automatically redirected to `/play` after authentication
   - Admin redirected to `/admin` console
   - TV display opens `/board` in fullscreen mode

3. **Authentication Layer**:
   - Player PINs stored in database
   - Admin key configured at setup
   - Display key for TV authorization

4. **Session Management**:
   - Persistent roles stored in browser sessions
   - Automatic reconnection to correct interface
   - Timeout handling for inactive sessions

### 6.2 Player Mobile Interface
- **Device Target**: Smartphones, tablets
- **Responsive Design**: Adapts to any screen size
- **Personal Dashboard Tabs**:
  - **Overview Tab**: Cash, net worth, turn status
  - **Properties Tab**: Owned properties, improvements, liens
  - **Finance Tab**: Loans, CDs, payment schedules
  - **Trade Tab**: Propose and respond to trades
  - **Audit Tab**: Risk meter, tax history
- **Player-Specific Features**:
  - Private financial information
  - Personal notification area
  - Turn action controls
  - Decision prompts (property purchase, income reporting)

### 6.3 Admin Dashboard
- **Device Target**: Tablet or laptop (larger screen)
- **Access Control**: Protected by admin key
- **Administrative Functions**:
  - **Game Controls**: Start, pause, reset, game settings
  - **Player Management**: Add/remove, modify cash
  - **Property Control**: Transfer, modify improvements
  - **Economic Tools**: Trigger inflation changes, audit players
  - **Event Log**: Game history and transactions
- **Monitoring Features**:
  - Real-time player status monitoring
  - Complete financial system overview
  - Trade approval interface
  - System status indicators

### 6.4 TV Board Display
- **Device Target**: Large screen TV or monitor
- **Display Optimization**: 
  - Landscape orientation
  - Large visual elements
  - Read-only interface (no controls)
- **Content Elements**:
  - **Main Board**: Property spaces, player tokens
  - **Economic Display**: Current inflation state
  - **Community Fund**: Current balance
  - **Recent Events**: Scrolling transaction log
  - **Player Stats**: Cash and property summary
- **Special Features**:
  - Automatic cycling between views
  - Animation for player movements
  - Visual indicators for property ownership
  - Economic phase visualization

## SECTION 7: API & COMMUNICATION ARCHITECTURE

### 7.1 Database Schema
The database schema includes tables for:
- Players
- Properties
- Loans/CDs
- Transactions
- Game State
- Trades
- Audit Events
- Economic Phases
- Player Achievements
- Game History

### 7.2 API Endpoints & Multi-Interface Routes

#### Core Web Routes
- Landing page for all users
- Player game interface
- Admin dashboard interface
- TV board display
- New player registration
- Player/admin authentication

#### Game Management API
- Create new game
- Join game with PIN
- Get current game state
- Start/pause/end the game
- List all current players
- Update game configuration

#### Player Actions API
- Roll dice
- Buy property
- End turn
- Report income at GO
- Improve property
- Handle jail options
- Get player's current status

#### Financial System API
- Take out/repay loans
- Create/withdraw CDs
- HELOC management
- Get current interest rates

#### Trading System API
- Propose trades
- Accept/reject trades
- List active trades
- Cancel proposed trades

#### Admin Controls API
- Modify player cash
- Transfer property ownership
- Trigger audits
- Add/remove bot players
- Override game state
- Get system status

#### TV Display API
- Get current board state
- Get player positions
- Get property ownership details
- Get recent game events

### 7.3 WebSocket Events & Interface Coordination

#### Connection Management
- Client connects to WebSocket server
- Client disconnects from server
- Register device role (player/admin/tv)
- Connection alive checks
- Reconnection handling

#### Game Events (All Interfaces)
- Player joined/left game
- Game started/paused/resumed/ended
- Game state updates

#### Player-Specific Events
- Turn notifications
- Dice roll results
- Property purchase decisions
- Income reporting prompts
- Jail options
- Trade proposals
- Audit notices

#### Admin-Specific Events
- Player status updates
- Suspicious activity alerts
- Trade approval requests
- System alerts
- Bot action notifications

#### TV Board-Specific Events
- Board refresh signals
- Player movement animations
- Property ownership changes
- Economic phase transitions
- Action highlights

#### Game Progress Events
- Property purchases
- Rent payments
- Turn endings
- Player bankruptcy
- Card draws

#### Financial Events
- Cash updates
- Property status changes
- Loan/CD creation and updates
- Inflation state changes
- Community fund updates

#### Interface Synchronization
- TV board ready signals
- Admin action notifications
- View switching instructions
- Property focus commands
- System-wide announcements

## SECTION 8: CLOUDFLARE TUNNEL IMPLEMENTATION

### 8.1 Cloudflare Tunnel Architecture
Pi-nopoly uses Cloudflare Tunnel as the **exclusive connectivity method** for all devices and interfaces, eliminating the need for local network configuration.

#### Cloudflare Tunnel Overview
- **Zero Trust Security Model**: No inbound ports needed on the Raspberry Pi
- **Global Network**: Cloudflare's edge network provides low-latency access worldwide
- **Always-on Connectivity**: Persistent outbound connection from Pi to Cloudflare
- **Web Application Firewall**: Built-in protection against common attacks
- **Traffic Encryption**: End-to-end TLS encryption
- **Custom Domain**: Option to use custom domain for the game

### 8.2 Cloudflare Tunnel Setup
1. Create Cloudflare account (free tier is sufficient)
2. Install cloudflared agent on Raspberry Pi
3. Authenticate with Cloudflare
4. Create and configure tunnel for Pi-nopoly
5. Setup DNS routing (custom domain or Cloudflare subdomain)
6. Configure tunnel service for auto-start

### 8.3 Game Server Configuration for Cloudflare-Only Access
- Flask server bound only to localhost (127.0.0.1)
- All traffic routed through Cloudflare Tunnel
- Security headers for HTTPS enforcement
- WebSocket path configuration for Cloudflare compatibility

### 8.4 WebSocket Configuration for Cloudflare
- Custom WebSocket path
- Secure connections
- Reconnection handling
- Connection error management

### 8.5 URL Structure with Cloudflare Domain
All URLs include the Cloudflare domain:
- Player Interface: `https://pinopoly.yourdomain.com/play?id=[PLAYER_ID]&pin=[PIN]`
- Admin Console: `https://pinopoly.yourdomain.com/admin?key=[ADMIN_KEY]`
- TV Board Display: `https://pinopoly.yourdomain.com/board?display=tv&key=[DISPLAY_KEY]`

### 8.6 Performance Optimization for Cloudflare
- WebSocket connection pooling
- Payload size optimization
- Compression for data transfer
- Static asset caching at Cloudflare edge
- Response time monitoring

### 8.7 Security Considerations for Cloudflare-Only Access
- PIN-based player authentication
- Secure admin access key
- Session validation
- Rate limiting for protection
- End-to-end encryption

## SECTION 9: ADDITIONAL GAME MECHANICS

### 9.1 Chance & Community Chest Card System
Pi-nopoly implements a dynamic card system for Chance and Community Chest tiles that scales with the game's economic state.

#### Card Types & Actions
- Movement cards (Advance to GO, properties, etc.)
- Financial cards (collect/pay money)
- Property-related cards (repairs, improvements)
- Get Out of Jail Free cards
- Player interaction cards (collect from/pay each player)

#### Economic Scaling
- Card monetary values adjust based on inflation state
- Higher values during inflation, lower during recession
- Keeps card effects relevant throughout game progression

### 9.2 Auction System
Real-time property auctions for properties that are not purchased directly when landed on.

#### Auction Features
- Timer-based bidding system
- Minimum bid requirements (70% of list price)
- Player pass mechanics
- Automatic auction end conditions
- Community Fund contributions from overbids

### 9.3 Property Improvement System
Players can enhance their properties to increase rent income.

#### Improvement Features
- Purchase properties at list price
- Add improvements to increase rent
- Mortgage properties for cash
- Group ownership bonuses
- Rent calculation based on improvements and economic state

### 9.4 Bankruptcy System
Handles players who cannot meet their financial obligations.

#### Bankruptcy Process
- Asset liquidation
- Property transfers
- CD emergency redemption
- Loan termination
- Game end detection for last player standing

### 9.5 Trophy & Achievement System
Rewards players for accomplishments during gameplay.

#### Achievement Categories
- Property achievements (ownership, improvements)
- Financial achievements (cash, investments)
- Game achievements (jail visits, tax evasion, etc.)
- Progress tracking for long-term goals
- Public recognition for significant accomplishments

### 9.6 Event & Disaster System
Periodic gameplay events that introduce unexpected situations affecting gameplay.

#### Event Types
- Economic events (market crashes, booms, interest rate changes)
- Property events (housing shortages, taxes, infrastructure projects)
- Natural disasters (hurricanes, earthquakes, floods)
- Community events (charity fundraisers, stimulus packages, tax amnesty)

### 9.7 Trading System
Comprehensive player-to-player trading with properties, cash, and items.

#### Trading Features
- Property, cash, and get-out-of-jail card exchanges
- Trade proposal and response system
- Trade validation and execution
- Suspicious trade detection for admin review
- Trade history tracking

### 9.8 Game Statistics and History
Detailed tracking of gameplay for analysis and replay value.

#### Statistics Tracking
- Player performance metrics
- Property ownership distribution
- Economic phase history
- Transaction records
- Game outcome analysis

### 9.9 Game Timer System
Time management for turns and full games.

#### Timer Features
- Turn timers with automatic actions
- Game-length timers for timed sessions
- Warning notifications
- Timeout handling
- Timer customization

### 9.10 Chat & Social Interaction
In-game communication for player interaction.

#### Communication Features
- Text chat for all players
- Private messaging
- Emoji reactions
- System-generated game announcements
- Chat history management

### 9.11 Spectator Mode
Allows non-players to watch the game.

#### Spectator Features
- Read-only game observation
- Real-time game state updates
- Spectator management
- Admin visibility of spectators
- Game state synchronization

### 9.12 Notification Center
Comprehensive player notification system.

#### Notification Types
- Information notifications
- Success/warning/error alerts
- Action requirements
- System-wide announcements
- Read/unread status tracking

### 9.13 Mobile Device Optimization
Tailored experience for different devices.

#### Optimization Features
- Device capability detection
- UI scaling for different screens
- Performance settings
- Data compression
- Touch control optimization

### 9.14 Game Variant System
Different rule sets and game modes beyond standard gameplay.

#### Game Variants
- Standard Pi-nopoly (classic experience)
- Speed Pi-nopoly (faster gameplay)
- Monopolist Mode (property-focused)
- Financial Tycoon (finance-focused)
- Cooperative Mode (team-based)
- Custom Rules (admin-defined)

## SECTION 10: DYNAMIC CONFIGURATION SYSTEM

### 10.1 Admin Game Rules Control Panel
Pi-nopoly implements a comprehensive admin control panel that allows the game administrator to configure all game rules and parameters without requiring code changes or server restarts.

#### Game Rules Configuration Interface
- **Game Setup**: Difficulty, player limit, lap limit, turn timeout
- **Free Parking & Community Fund**: Distribution mode, fund amount
- **Property Rules**: Auction requirement, value multipliers, improvement costs
- **Financial System**: Tax rates, loan rates, debt limits, bankruptcy rules
- **Crime System**: Theft mechanics, jail settings, audit probability
- **Inflation Engine**: Thresholds, transition dampening, enabling/disabling
- **Bot Players**: Difficulty, adaptive settings, turn delay

#### Configuration Management
- Save/load configuration profiles
- Reset to defaults
- Export/import configurations
- Quick templates for different game styles

### 10.2 Server-Side Configuration Management
The server implements a flexible configuration system that stores all game rules in the database and allows them to be modified during gameplay.

#### Configuration Architecture
- Database storage of all game parameters
- API endpoints for retrieving and updating configurations
- Configuration profiles for different game setups
- Change broadcasting to all connected clients

### 10.3 Configuration Change Broadcasting
When configuration changes are made, the system automatically:
1. Validates the new values against allowed ranges
2. Updates the database configuration
3. Broadcasts changes to all clients via WebSockets
4. Applies changes to the runtime game state
5. Logs the configuration change in the event log

## SECTION 11: PRODUCTION DEPLOYMENT

### 11.1 Raspberry Pi Configuration
- **OS**: Raspberry Pi OS Lite (64-bit)
- **Service Setup**: Systemd for auto-start
- **Resource Monitoring**: CPU, memory, network tracking
- **Backup Strategy**: Daily database backups
- **Display Configuration**: HDMI settings for TV board display

### 11.2 Network Configuration
- **Cloudflare Tunnel Setup**: Primary connection method for all devices
- **Firewall Settings**: Restrict to needed ports only
- **QoS Configuration**: Optimize traffic for Cloudflare Tunnel
- **DNS Settings**: Configure custom domain (optional)
- **Connection Security**: TLS encryption for all traffic

### 11.3 Multi-Device Setup
- **Game Start Process**:
  1. Start Pi-nopoly server on Raspberry Pi
  2. Ensure Cloudflare Tunnel is active and connected
  3. Connect TV display to Cloudflare URL with board display parameter
  4. Admin login from tablet/laptop via Cloudflare URL
  5. Players join via mobile devices using the same Cloudflare URL
  
- **Device Assignments**:
  - **Raspberry Pi 5**: Server, no UI needed (headless)
  - **TV/Monitor**: Web browser accessing Cloudflare URL with board parameters
  - **Admin Tablet**: Web browser with admin access via Cloudflare URL
  - **Player Devices**: Individual smartphones/tablets/laptops via Cloudflare URL

### 11.4 Startup Automation
- Auto-launch script for Pi-nopoly server
- Cloudflare Tunnel auto-start
- TV display kiosk mode setup
- Systemd service configuration

### 11.5 Maintenance Procedures
- Update protocol
- Backup and restoration
- Troubleshooting guide
- Performance tuning
- Multi-device diagnostics

## SECTION 12: HIGH AVAILABILITY & FAILURE RECOVERY

### 12.1 Resilient System Architecture
Pi-nopoly implements a comprehensive monitoring and recovery system to ensure uninterrupted gameplay.

#### Component Monitoring
- Flask server health checks
- Database connection monitoring
- Cloudflare tunnel status verification
- WebSocket server availability
- System resource tracking

### 12.2 Automatic Recovery Mechanisms
- Server restart procedures
- Database recovery from backup
- Cloudflare tunnel reconnection
- WebSocket reconnection
- Admin notification of recovery actions

### 12.3 Client-Side Resilience
- Connection resilience implementation
- Reconnection attempt management
- Pending action queueing
- Offline mode notification
- Game state preservation during disconnect

### 12.4 Game State Preservation
- Regular database backups
- In-memory emergency cache
- Transaction logging
- State restoration procedures
- Game continuation after recovery

### 12.5 Cloudflare Tunnel Resilience
- Connection monitoring
- Automatic recovery
- Connectivity health checks
- Failure notification
- Auto-restart scripts

### 12.6 Comprehensive Disaster Recovery Plan
- Hardware failure recovery
- Database restoration
- Game state rebuilding
- Player reconnection handling
- Complete system rebuilding guide

## SECTION 13: DEVELOPMENT ROADMAP

### 13.1 Phase 1: Core Engine (Weeks 1-3)
- Database setup and models
- Basic game loop
- Property and movement mechanics
- Local network testing

### 13.2 Phase 2: Financial Systems (Weeks 4-6)
- Banking system
- Loans and CDs
- Property improvements
- Inflation engine

### 13.3 Phase 3: User Interfaces (Weeks 7-9)
- Player mobile interface
- Admin dashboard
- TV board display
- UI testing and refinement

### 13.4 Phase 4: Advanced Features (Weeks 10-12)
- AI player implementation
- Trade system
- Audit and tax mechanics
- Crime system

### 13.5 Phase 5: Cloudflare Integration (Weeks 13-14)
- Cloudflare Tunnel setup
- Remote play testing
- Security hardening
- Performance optimization

### 13.6 Phase 6: Final Testing & Deployment (Weeks 15-16)
- Multi-player stress testing
- Bug fixes
- Documentation
- Final deployment