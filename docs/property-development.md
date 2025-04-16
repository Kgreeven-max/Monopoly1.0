# Property Development System

## Overview

The Property Development System expands the existing property improvement mechanics to include multiple levels of development with varying costs and returns. This system introduces zoning regulations, advanced improvement types, and economic scaling factors to create a more dynamic property management experience.

## Multi-Level Development Structure

The system defines five distinct development levels for properties:

1. **Undeveloped**
   - Base rent and value
   - No improvements
   - No damage vulnerability

2. **Basic Development**
   - Represented by a house icon
   - 2x rent multiplier
   - 1.5x property value
   - Vulnerable to 50% maximum damage
   - Repair costs are 20% of improvement cost

3. **Intermediate Development**
   - Represented by multiple houses
   - 3.5x rent multiplier
   - 2.0x property value
   - Vulnerable to 60% maximum damage
   - Repair costs are 30% of improvement cost

4. **Advanced Development**
   - Represented by apartments/hotels
   - 5.0x rent multiplier
   - 2.5x property value
   - Vulnerable to 70% maximum damage
   - Repair costs are 40% of improvement cost

5. **Premium Development**
   - Represented by skyscrapers/resorts
   - 7.0x rent multiplier
   - 3.0x property value
   - Vulnerable to 80% maximum damage
   - Repair costs are 50% of improvement cost

## Zoning Regulations

Different property groups have different zoning regulations that limit development options:

| Property Group | Max Level | Special Requirements | Cost Modifier |
|----------------|-----------|----------------------|---------------|
| Brown          | 3         | None                 | 0.8 (20% cheaper) |
| Light Blue     | 3         | None                 | 0.9 (10% cheaper) |
| Pink           | 4         | Community approval for Lvl 3+ | 1.0 |
| Orange         | 4         | Community approval for Lvl 3+ | 1.0 |
| Red            | 4         | Environmental study for Lvl 4 | 1.1 (10% more expensive) |
| Yellow         | 4         | Environmental study for Lvl 4 | 1.1 (10% more expensive) |
| Green          | 4         | Community approval for Lvl 3+<br>Environmental study for Lvl 4 | 1.2 (20% more expensive) |
| Blue           | 4         | Community approval for Lvl 3+<br>Environmental study for Lvl 4 | 1.3 (30% more expensive) |

## Development Costs and Economic Scaling

Development costs scale with both the level of development and current economic conditions:

### Base Development Costs
- Level 1: 50% of property value
- Level 2: 60% of property value
- Level 3: 75% of property value
- Level 4: 100% of property value

### Economic Multipliers
- Recession: 0.85 (15% discount)
- Normal: 1.0
- Growth: 1.1 (10% premium)
- Boom: 1.25 (25% premium)

Final cost is calculated as:
```
development_cost = base_cost × zone_multiplier × economic_multiplier × inflation_factor
```

## Development Requirements

Advanced developments require special approvals:

### Community Approval
- Required for Level 3+ in Pink, Orange, Green, and Blue property groups
- Can be requested at the beginning of a player's turn
- Approval is determined by a community vote
  - Success chance is based on current suspicion level and past behavior
  - Failed approvals can be requested again after a waiting period

### Environmental Study
- Required for Level 4 in Red, Yellow, Green, and Blue property groups
- Costs $200 to commission
- Takes one full game turn to complete
- Study results are permanent unless property is severely damaged

## API Endpoints

The Property Development System provides several API endpoints for checking requirements and retrieving development information:

### `/api/board/property-development/requirements`
Checks if all requirements are met for developing a property to a target level.

**Parameters:**
- `property_id` (int): The ID of the property to check
- `target_level` (int): The development level to check requirements for

**Response:**
```json
{
  "success": true,
  "property": {
    "id": 13,
    "name": "Boardwalk",
    "group": "blue",
    "current_level": 2,
    "max_level": 4
  },
  "requirements": {
    "requirements_met": false,
    "message": "Missing requirements for development",
    "missing_requirements": [
      "Community approval required for level 3+",
      "Environmental study required for level 4"
    ]
  }
}
```

### `/api/board/property-development`
Gets development information for a specific property group, including zoning regulations and economic factors.

**Parameters:**
- `group_name` (string): The name of the property group (e.g., "blue", "orange")

**Response:**
```json
{
  "success": true,
  "group_name": "blue",
  "properties": [...],
  "zoning": {
    "max_level": 4,
    "approval_required": true,
    "study_required": true,
    "cost_modifier": 1.3
  },
  "economic_state": {
    "state": "growth",
    "multiplier": 1.1,
    "inflation_factor": 1.05
  },
  "development_levels": {...}
}
```

### `/api/board/property-development/status`
Gets the current development status and capabilities of a specific property.

**Parameters:**
- `property_id` (int): The ID of the property to get status for

**Response:**
```json
{
  "success": true,
  "property": {
    "id": 13,
    "name": "Boardwalk",
    "group": "blue",
    "position": 39,
    "price": 400,
    "current_price": 800,
    "rent": 50,
    "current_rent": 175,
    "owner": {
      "id": 2,
      "name": "Player 2",
      "community_standing": 65
    },
    "is_mortgaged": false
  },
  "development": {
    "current_level": 2,
    "level_name": "Intermediate Development",
    "max_level": 4,
    "rent_multiplier": 3.5,
    "value_multiplier": 2.0,
    "can_improve": true,
    "improvement_cost": 390,
    "has_community_approval": true,
    "has_environmental_study": false,
    "environmental_study_expires": null
  },
  "damage": {
    "has_damage": true,
    "damage_amount": 120,
    "damage_percentage": 15.0,
    "repair_cost": 36,
    "is_water_adjacent": false,
    "max_damage_factor": 0.6,
    "repair_cost_factor": 0.3
  }
}
```

## Socket Events

The Property Development System uses WebSocket events for real-time property development actions and updates:

### `improve_property` (Client → Server)
Request to improve a property to the next development level.

**Parameters:**
```json
{
  "property_id": 13,
  "player_id": 2,
  "pin": "1234"
}
```

### `property_improved` (Server → Client)
Notification that a property has been improved.

**Data:**
```json
{
  "property_id": 13,
  "property_name": "Boardwalk",
  "player_id": 2,
  "player_name": "Player 2",
  "old_level": 2,
  "new_level": 3,
  "level_name": "Advanced Development",
  "improvement_cost": 390,
  "new_price": 1000,
  "economic_state": "growth"
}
```

### `request_community_approval` (Client → Server)
Request community approval for higher-level development.

**Parameters:**
```json
{
  "property_id": 13,
  "player_id": 2,
  "pin": "1234"
}
```

### `community_approval_result` (Server → Client)
Result of a community approval request.

**Data:**
```json
{
  "property_id": 13,
  "property_name": "Boardwalk",
  "player_id": 2,
  "player_name": "Player 2",
  "approved": true,
  "message": "Community approval granted! Your good standing in the community was a factor.",
  "approval_chance": 75
}
```

### `commission_environmental_study` (Client → Server)
Request to commission an environmental study for highest-level development.

**Parameters:**
```json
{
  "property_id": 13,
  "player_id": 2,
  "pin": "1234"
}
```

### `repair_property` (Client → Server)
Request to repair property damage.

**Parameters:**
```json
{
  "property_id": 13,
  "player_id": 2,
  "pin": "1234",
  "repair_amount": 100
}
```

### `repair_completed` (Server → Client)
Result of a property repair action.

**Data:**
```json
{
  "status": "success",
  "property_id": 13,
  "property_name": "Boardwalk",
  "repair_cost": 30,
  "repaired_amount": 100,
  "remaining_damage": 20,
  "new_rent": 175,
  "development_level": 2,
  "development_name": "Intermediate Development",
  "new_cash": 850,
  "timestamp": "2023-04-08T15:30:45.123Z"
}
```

## Economic Impact

Property development affects the overall game economy:

- Each development level increases inflation slightly (0.2% per level)
- High-level developments can boost nearby property values
- Clustered developments in the same area receive adjacency bonuses
- Development can trigger positive community events

## Implementation Strategy

The development system has been implemented in three phases:

### Phase 1: Core Development Levels (Completed)
- Implemented basic, intermediate, advanced, and premium development levels
- Added development cost calculation
- Updated rent and property value calculations

### Phase 2: Zoning Regulations (Completed)
- Implemented group-specific development limits
- Added community approval and environmental study requirements
- Created API endpoints and socket handlers for development actions

### Phase 3: Economic Integration (Completed)
- Added development impact on inflation
- Implemented development-triggered events
- Enhanced damage and repair system for different development levels 