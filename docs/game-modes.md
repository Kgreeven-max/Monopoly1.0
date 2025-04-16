# Game Modes System

## Overview

The Game Modes System transforms Pi-nopoly from a single gameplay experience into a versatile platform with diverse playstyles. Each game mode features customized rules, objectives, and mechanics to provide fresh challenges and experiences for players, while maintaining the core economic simulation that defines Pi-nopoly.

## Implementation Details

The Game Modes system has been fully implemented with a dedicated database model, API endpoints, and frontend components. 

### Backend Components

- **GameMode Model**: A comprehensive database model that stores all mode-specific settings
- **GameModeController**: Controller handling all game mode operations and initialization
- **API Routes**: RESTful endpoints for mode selection, configuration, and status checking

### Frontend Components

- **GameModeService**: Client service for API communication
- **GameModeSelector**: Component for selecting game modes
- **GameModeSettings**: Component for configuring mode settings
- **GameModeAdmin**: Combined admin interface for game mode management

## Standard Game Modes

### Classic Mode

The traditional Pi-nopoly experience with standard rules:

- **Objective**: Accumulate wealth and drive opponents to bankruptcy
- **Win Condition**: Last player remaining solvent
- **Key Features**:
  - Full property trading and development
  - Economic cycles and inflation
  - Standard event frequency
  - Normal disaster impact

### Speed Mode

A faster-paced version designed for shorter play sessions:

- **Objective**: Same as classic, but accelerated
- **Win Condition**: Player with highest net worth after fixed time/turns
- **Key Features**:
  - Higher starting cash ($3000)
  - Double GO salary ($400)
  - 20-turn or 30-minute limit
  - 60-second turn timer
  - Negative bankruptcy threshold (-$1000)
  - Higher inflation and event frequency

### Co-op Mode

A cooperative experience where players work together against the game system:

- **Objective**: Collectively develop all properties before economic collapse
- **Win Condition**: All properties developed to at least level 2
- **Key Features**:
  - Team-based gameplay
  - Shared income and property development
  - No property auctions
  - Rent immunity between team members
  - Progressive economic challenges

## Specialty Modes

### Tycoon Mode

Development-focused mode emphasizing property improvement:

- **Objective**: Build the most impressive property empire
- **Win Condition**: First to achieve specified development milestones
- **Key Features**:
  - 5 development levels
  - Advanced improvement types
  - Development milestones (bronze, silver, gold)
  - Property aesthetics impact value

### Market Crash Mode

Challenging mode centered around economic instability:

- **Objective**: Survive and thrive during economic turmoil
- **Win Condition**: Highest net worth after market stabilizes
- **Key Features**:
  - Starts in recession (0.7 inflation factor)
  - High market volatility (2.0x)
  - Property value fluctuations
  - Increased event frequency (0.3)
  - Economic cycle acceleration

### Team Battle Mode

Competitive mode pitting teams of players against each other:

- **Objective**: Establish team monopolies and bankrupt opposing teams
- **Win Condition**: First team to bankrupt all opponents or highest team net worth
- **Key Features**:
  - Team-based gameplay (2-4 teams)
  - Team property sharing
  - Team rent immunity
  - Income sharing (10% distributed to team)
  - Team elimination mechanism

## Customization Options

Each game mode provides various configuration options that can be adjusted:

- **Starting Cash**: Initial money provided to players
- **GO Salary**: Amount received when passing GO
- **Free Parking**: Whether fees are collected
- **Auction Settings**: Enabling/disabling property auctions
- **Turn Limits**: Maximum number of turns
- **Time Limits**: Game duration in minutes
- **Turn Timer**: Time per player turn
- **Event Frequency**: Probability of events triggering
- **Disaster Impact**: Severity of negative events
- **Team Settings**: Team-specific configurations

## Technical Implementation

### Database Schema

```sql
CREATE TABLE game_modes (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    mode_type VARCHAR(20) DEFAULT 'classic',
    name VARCHAR(50) NOT NULL,
    
    -- Common settings
    starting_cash INTEGER DEFAULT 1500,
    go_salary INTEGER DEFAULT 200,
    free_parking_collects_fees BOOLEAN DEFAULT FALSE,
    auction_enabled BOOLEAN DEFAULT TRUE,
    max_turns INTEGER NULL,
    max_time_minutes INTEGER NULL,
    bankruptcy_threshold INTEGER DEFAULT 0,
    event_frequency FLOAT DEFAULT 0.15,
    disaster_impact FLOAT DEFAULT 1.0,
    inflation_factor FLOAT DEFAULT 1.0,
    development_levels_enabled BOOLEAN DEFAULT TRUE,
    turn_timer_seconds INTEGER NULL,
    
    -- Mode-specific settings
    _custom_settings TEXT NULL,
    
    -- Team battle settings
    team_based BOOLEAN DEFAULT FALSE,
    team_trading_enabled BOOLEAN DEFAULT FALSE,
    team_property_sharing BOOLEAN DEFAULT FALSE,
    team_rent_immunity BOOLEAN DEFAULT FALSE,
    team_income_sharing FLOAT DEFAULT 0.0,
    
    -- Win condition
    win_condition VARCHAR(30) DEFAULT 'last_standing',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (game_id) REFERENCES game_state(id)
);
```

### API Endpoints

- **GET /api/game-modes/** - List available game modes
- **POST /api/game-modes/select/:game_id** - Select and initialize a game mode
- **GET /api/game-modes/check-win/:game_id** - Check if win condition is met
- **GET /api/game-modes/settings/:game_id** - Get current mode settings
- **POST /api/game-modes/update-settings/:game_id** - Update mode settings
- **GET /api/game-modes/list-active** - List all active game modes

## Achievement System

The Game Modes System includes mode-specific achievements:

### Achievement Categories

1. **Mode Mastery**
   - Complete specific challenges in each game mode
   - Unlock special bonuses for future games

2. **Strategic Milestones**
   - Accomplish difficult strategic goals
   - Track progress across multiple games

3. **Social Achievements**
   - Cooperative accomplishments with other players
   - Community contribution recognition

## Usage Guide

### Starting a Game with a Specific Mode

1. From the admin interface, navigate to Game Mode Management
2. Select the desired game mode
3. Configure any specific settings
4. Start the game

### Changing Mode Settings Mid-game

1. From the admin interface, navigate to Game Mode Management
2. Select the Configure Settings tab
3. Adjust the desired settings
4. Save changes

### Checking Win Conditions

The system automatically checks win conditions at appropriate times:
- End of each turn
- Time limit reached
- Property development events
- Player bankruptcy

When win conditions are met, the game will display the winner and reason. 