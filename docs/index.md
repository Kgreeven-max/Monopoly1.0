# Pi-nopoly Documentation

Welcome to the Pi-nopoly documentation. This documentation provides detailed information about the various systems and features of the Pi-nopoly game.

## Core Systems

- [Event System](event_system.md): Documentation for the event system, including economic events, natural disasters, and community events.
- [Property Development](property-development.md): Information about the property development system, including levels, zoning, and regulations.
- [Auction System](auction-system.md): Details about the auction system for properties and foreclosures.
- [Special Spaces](special-spaces.md): Documentation for special board spaces like Community Chest, Chance, and Tax spaces.
- [Financial Instruments](financial-instruments.md): Information about loans, CDs, HELOCs, and the Community Fund.

## Advanced Features

- [Advanced Economics](advanced-economics.md): Documentation for advanced economic features like inflation, market simulation, and the stock market.
- [Game Modes](game-modes.md): Information about different game modes and their rules.
- [Social Features](social-features.md): Details about social features like chat, alliances, and trade negotiations.

## Technical Reference

- [API Reference](api-reference.md): Documentation for the API endpoints.
- [Socket Events](socket-events.md): Information about the socket events used for real-time communication.
- [Database Schema](database-schema.md): Documentation for the database schema.
- [Configuration](configuration.md): Information about configuration options.

## Developer Guide

- [Setup Guide](setup-guide.md): Instructions for setting up the development environment.
- [Contributing](contributing.md): Guidelines for contributing to the project.
- [Testing](testing.md): Information about testing the application.
- [Deployment](deployment.md): Instructions for deploying the application.

## Project Reference

- [Project Overview](../PROJECT_REFERENCE.md): High-level overview of the project.
- [Changelog](../CHANGELOG.md): History of changes to the project.

## Core Systems

The complete design documentation for Pi-nopoly is divided into the following sections:

### Existing Systems (from pinopoly-design-doc.md)
- Event & Disaster System
- Trading System
- Game Statistics and History System
- Game Timer System
- Chat & Social Interaction System
- Spectator Mode
- Notification Center
- Mobile Device Optimization

### Priority Development Systems

1. [**Auction System**](auction-system.md)
   - Standard and foreclosure auctions
   - Bidding mechanics with timer-based resolution
   - Integration with the Community Fund
   - Detailed implementation plan

2. [**AI Players**](ai-players.md)
   - Multiple AI personalities (Conservative, Aggressive, Strategic, Opportunistic)
   - Advanced decision-making framework with weighted factors
   - Market analysis capabilities for property valuation
   - Memory system for learning from past decisions

3. [**Special Spaces**](special-spaces.md)
   - Community Chest and Chance card systems
   - Tax spaces with economic phase-based calculations
   - Special properties like utilities and transportation
   - Integration with the core game engine

4. [**UI Enhancements**](ui-enhancements.md)
   - Event visualization system for game events
   - Enhanced property cards with damage indicators
   - Economic phase visual indicators
   - Real-time game state visualization

5. [**Property Development**](property-development.md)
   - Multi-level development structure
   - Zoning regulations by property group
   - Dynamic development costs
   - Economic impact of development

6. [**Advanced Economics**](advanced-economics.md)
   - Supply and demand system
   - Stock market simulation
   - Advanced interest rates and inflation
   - Market speculation mechanics

7. [**Social Features**](social-features.md)
   - Enhanced chat system
   - Alliance and reputation systems
   - Community governance
   - Social UI enhancements

8. [**Game Modes**](game-modes.md)
   - Classic, Speed, and Co-op modes
   - Specialty modes like Tycoon and Market Crash
   - Custom game configuration
   - Scenario and achievement systems

## Integration Plans

Each system is designed to integrate seamlessly with existing functionality:

### Data Flow Diagram

```
                          ┌─────────────────┐
                          │                 │
                          │  Game State     │
                          │  Management     │
                          │                 │
                          └─────┬─────┬─────┘
                                │     │
                ┌───────────────┘     └───────────────┐
                │                                     │
    ┌───────────▼────────────┐             ┌──────────▼───────────┐
    │                        │             │                      │
    │  Property System       │             │  Player System       │
    │  - Auction System      │◄────┐ ┌────►│  - AI Players        │
    │  - Development System  │     │ │     │  - Social Features   │
    │  - Special Spaces      │     │ │     │  - Reputation        │
    │                        │     │ │     │                      │
    └───────────┬────────────┘     │ │     └──────────┬───────────┘
                │                  │ │                │
                │                  │ │                │
    ┌───────────▼────────────┐     │ │     ┌──────────▼───────────┐
    │                        │     │ │     │                      │
    │  Economic System       │◄────┼─┼────►│  UI System           │
    │  - Stock Market        │     │ │     │  - Visualizations    │
    │  - Interest Rates      │     │ │     │  - Enhanced Cards    │
    │  - Supply & Demand     │     │ │     │  - Animations        │
    │                        │     │ │     │                      │
    └───────────┬────────────┘     │ │     └──────────┬───────────┘
                │                  │ │                │
                └──────────────────┼─┼────────────────┘
                                   │ │
                        ┌──────────▼─▼──────────┐
                        │                       │
                        │  Game Mode System     │
                        │  - Mode Rules         │
                        │  - Scenarios          │
                        │  - Achievements       │
                        │                       │
                        └───────────────────────┘
```

### Implementation Strategy

The systems will be implemented in priority order with the following approach:

1. **Foundation First**: Each system begins with implementing core functionality
2. **Incremental Integration**: Systems are integrated with existing code in phases
3. **Test-Driven Development**: Comprehensive tests validate each component
4. **Progressive Enhancement**: Basic versions launch first with additional features added over time

## Technical Requirements

All systems have been designed with these requirements in mind:

- **Performance**: Optimized for Raspberry Pi hardware
- **Scalability**: Supports up to 8 concurrent players
- **Connectivity**: Works across multiple devices via web interface
- **Persistence**: All game state saved to database for reliability
- **Security**: Proper validation of all user inputs

## Development Timeline

The development of these systems will follow this high-level timeline:

| System | Estimated Time | Dependencies |
|--------|----------------|--------------|
| Auction System | 2 weeks | None |
| AI Players | 3 weeks | None |
| Special Spaces | 2 weeks | None |
| UI Enhancements | 3 weeks | Auction System |
| Property Development | 2 weeks | None |
| Advanced Economics | 3 weeks | Property Development |
| Social Features | 3 weeks | UI Enhancements |
| Game Modes | 2 weeks | All systems |

Total estimated development time: 20 weeks 

## Game Systems

### Core Systems

### Advanced Features

#### Game Modes
The Game Modes system transforms Pi-nopoly from a single gameplay experience into a versatile platform with diverse playstyles. Each game mode features customized rules, objectives, and mechanics to provide fresh challenges while maintaining the core economic simulation.

##### Standard Game Modes
- **Classic Mode**: Traditional Pi-nopoly experience with standard rules
  - Last player standing wins
  - Standard economic cycles and inflation
  - Full property trading and development

- **Speed Mode**: Faster-paced version designed for shorter sessions (30 minutes)
  - Higher starting cash (3000) and Go salary (400)
  - 20-turn or 30-minute time limit
  - Winner determined by highest net worth when time expires
  - Accelerated economic cycles and increased event frequency

- **Co-op Mode**: Players work together against the game system
  - Objective: Develop all properties to at least level 2 before economic collapse
  - Shared Community Fund accessible to all players
  - Allied rent discounts (25% between players)
  - Lose if any player goes bankrupt or time expires

##### Specialty Game Modes
- **Tycoon Mode**: Property development-focused experience
  - Extended development options (5 levels)
  - Development discounts for adjacent properties
  - Property value multipliers for aesthetic improvements
  - First to achieve specified development milestones wins

- **Market Crash Mode**: Economic instability challenge
  - Volatile property values (up to 50% swings)
  - Frequent economic events and extended recession periods
  - Limited bankruptcy protection options
  - Strategic short-selling mechanics

- **Team Battle Mode**: Team-based competitive play
  - 2-4 teams with shared team assets
  - Team-specific bonuses and strategic roles
  - Team property sharing and rent immunity between teammates
  - Highest team net worth wins

##### Custom Game Configuration
The system includes a comprehensive game configuration interface allowing customization of:
- Starting cash and Go salary
- Free parking rules and auction settings
- Turn and time limits
- Economic factors (inflation, disaster impact)
- Win conditions and development options

##### Scenario System
Predefined scenarios with unique challenges:
- Economic Recovery (severe recession start)
- Natural Disaster Aftermath (damaged properties)
- Market Bubble (inflated property values)

#### Achievement System
The Achievement System rewards players for completing specific challenges and milestones:

##### Achievement Categories
- **Mode Mastery**: Complete specific challenges in each game mode
  - Classic Victory: Win a classic mode game
  - Speed Demon: Win a speed mode game in under 20 minutes
  - Team Player: Successfully complete a co-op mode game

- **Strategic Milestones**: Accomplish difficult strategic goals
  - Property Mogul: Own all properties of 3 different colors
  - Monopoly Master: Own 3 complete property groups
  - Improvement King: Have 8 property improvements at once

- **Social Achievements**: Cooperative accomplishments with other players
  - Community Hero: Contribute at least $1000 to the Community Fund
  - Loan Shark: Have 5 loans out to other players
  - Master Investor: Have $3000 invested in CDs

##### Reward System
Achievements unlock special bonuses for future games:
- Trophies (displayed on player profile)
- Cash bonuses at game start
- Special abilities (e.g., community fund interest)
- Access to exclusive game modes

##### Implementation
The system tracks player actions and events to automatically award achievements as they are earned. Players receive immediate notifications when achievements are unlocked, and significant achievements are broadcast to all players.

#### Stock Market
// ... existing code ... 