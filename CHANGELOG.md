# Pi-nopoly Changelog

## Version 0.9.0 - Game Modes Update (2023-04-09)

### Added
- Complete Game Modes System:
  - Classic Mode: Traditional gameplay with standard rules
  - Speed Mode: Faster gameplay with time/turn limits
  - Co-op Mode: Collaborative gameplay to develop properties
  - Tycoon Mode: Development-focused mode with expanded property improvements
  - Market Crash Mode: Economic instability with volatile property values
  - Team Battle Mode: Team-based competitive gameplay
- Game mode configuration options:
  - Customizable starting cash
  - Turn and time limits
  - Mode-specific win conditions
  - Property value dynamics
  - Team-based features
- Win condition checking for different game modes
- Game mode selection in admin interface
- Mode-specific settings management
- Lap-based effects for different game modes

### Changed
- Enhanced GameState model with mode and settings fields
- Updated process_turn_end to handle mode-specific turn limits
- Added turn_number tracking to GameState model
- Added process_game_mode_lap_effects for mode-specific lap updates
- Improved to_dict method to include game mode information

## Version 0.8.0 - Remote Play Update (2023-04-08)

### Added
- Complete Remote Play System:
  - Cloudflare Tunnel integration for secure remote access
  - Dynamic tunnel creation, management, and configuration
  - QR code sharing for easy connection
  - Remote player connection monitoring and management
  - Disconnection handling with auto-reconnection
  - Turn timeout system for remote players
  - Ping functionality to check player connection quality
  - Player connection status tracking
  - Admin controls for:
    - Creating and managing tunnels
    - Monitoring connected players
    - Pinging remote players
    - Removing disconnected players
    - Setting timeout durations
  - Connect page with connection instructions

### Changed
- Enhanced socket controller with robust connection tracking
- Improved authentication system for remote players
- Added remote play configuration options
- Updated health check endpoint to include remote play status

## Version 0.7.0 - Crime System Update (2023-04-22)

### Added
- Complete Crime System:
  - Five crime types implementation:
    - Theft - Steal money from other players
    - Property Vandalism - Damage properties to reduce value and rent
    - Rent Evasion - Avoid paying rent when landing on properties
    - Forgery - Create fake money
    - Tax Evasion - Avoid paying taxes
  - Dynamic crime detection system based on:
    - Game difficulty
    - Player's community standing
    - Police activity level
  - Consequences system:
    - Jail time for most crimes
    - Financial penalties
    - Damage to community standing
    - Criminal record tracking
  - Property damage and repair mechanics
  - Criminal record tracking for players
- Police patrol system with scheduled checks
- Admin controls for:
  - Setting police activity levels
  - Pardoning players for crimes
  - Viewing crime statistics
- New API endpoints for crime-related actions
- Extended player model with criminal record tracking

### Changed
- Enhanced game state model to include police activity
- Updated jail mechanics to handle crime-related sentences
- Improved community standing impacts from criminal activity
- Expanded temporary effects system to handle property repairs

## Version 0.6.0 - AI Players System Update (2023-04-15)

### Added
- Complete AI Players System:
  - Conservative Bot implementation - Focuses on safe investments and steady growth
  - Aggressive Bot implementation - Rapid expansion and high-risk investments
  - Strategic Bot implementation - Balanced approach focusing on monopolies
  - Shark Bot implementation - Predatory focus on blocking others and targeting distressed players
  - Investor Bot implementation - Financial instrument focus with sophisticated ROI calculations
  - Enhanced Opportunistic Bot with market timing strategy
- Adaptive Difficulty System:
  - Automatic assessment of game balance between human and bot players
  - Dynamic difficulty adjustment to maintain competitive balance
  - Three difficulty levels (easy, medium, hard) with adjustable parameters
  - Admin controls for manual difficulty adjustments
  - Scheduled automatic assessments
- Bot Personality Features:
  - Unique decision-making strategies for each bot type
  - Specialized property valuation algorithms
  - Distinctive auction bidding behaviors
  - Type-specific pre-roll and post-roll actions

### Changed
- Enhanced bot controller to support all bot types
- Improved bot decision-making framework with more realistic behaviors
- Updated admin interface to expose new bot management features
- Extended property evaluation algorithms to incorporate bot-specific strategies

## Version 0.5.0 - Financial Instruments Update (2023-04-08)

### Added
- Complete financial instruments system:
  - Loans with variable interest rates based on economic conditions
  - Certificates of Deposit (CDs) with configurable terms (3, 5, 7 laps)
  - Home Equity Line of Credit (HELOC) for property-backed borrowing
  - Community Fund for public money management
  - Bankruptcy system for handling player insolvency
- New API endpoints for financial instrument management
- New socket events for real-time financial updates
- Admin controls for Community Fund management
- Extended documentation in `docs/financial-instruments.md`

### Changed
- Updated project reference documentation
- Improved economic simulation to affect financial instrument rates
- Enhanced player model to track bankruptcy history

## Version 0.4.0 - Special Spaces Update (2023-04-01)

### Added
- Special spaces implementation:
  - Community Chest and Chance card systems
  - Tax spaces with economic-phase based calculations
  - Go, Jail, Free Parking, and Go To Jail mechanics
  - Special space API endpoints
  - Card drawing and action execution
- Different card action types:
  - Movement actions (go to specific space, advance, etc.)
  - Payment actions (pay to bank, collect from bank, etc.)
  - Jail-related actions (go to jail, get out of jail free)
  - Property-related actions (repairs, improvements)
  - Player interaction (birthday collections)

### Changed
- Updated game controller to handle special space landings
- Enhanced socket events for special space interactions
- Improved game state tracking for special space effects

## Version 0.3.0 - Property Development Update (2023-03-15)

### Added
- Property development system with 5 development levels
- Zoning regulations for property groups
- Damage and repair mechanics
- Environmental studies and community approval requirements
- Development-based rent calculations
- Property improvements and degradation

### Changed
- Updated property model to include development level
- Enhanced property controller for development operations
- Improved UI for property management

## Version 0.2.0 - Game Mechanics Update (2023-03-01)

### Added
- Event system with economic, natural disaster, and community events
- Auction system for properties and foreclosures
- Basic AI player (Opportunistic Bot only) with market timing strategy
- Basic economic simulation with recession, normal, growth, and boom phases

### Changed
- Enhanced game flow and turn management
- Improved property acquisition mechanics
- Updated socket controller for real-time events

## Version 0.1.0 - Initial Release (2023-02-15)

### Added
- Basic game functionality
- Player management (join, leave, move)
- Property system (purchase, mortgage)
- Turn-based gameplay
- Simple UI for game interaction

## Next Features (According to Design Doc)

1. **Game Modes**
   - Classic Mode: Traditional gameplay
   - Speed Mode: Faster gameplay with time/turn limits
   - Co-op Mode: Collaborative gameplay

2. **User Interface Enhancements**
   - Event visualization system
   - Enhanced property cards with damage indicators
   - Economic phase visual indicators
   - Real-time game state visualization 

3. **Social Features**
   - Chat system with multiple channels
   - Player alliances and partnerships
   - Reputation system
   - Trade negotiations interface 