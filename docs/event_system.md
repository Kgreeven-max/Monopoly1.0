# Event System Documentation

The Pi-nopoly Event System adds unpredictable events to gameplay, creating a more dynamic and realistic economic simulation. Events can impact properties, player finances, and the overall game economy.

## Event Types

### Economic Events
Events that affect the general economy, property values, and interest rates.

| Event | Description | Effect |
|-------|-------------|--------|
| **Economic Boom** | Strong economic growth | Property values +10%, rent +10% |
| **Market Crash** | Economic downturn | Property values -15%, rent -15% |
| **Interest Rate Hike** | Central bank raises rates | All loan interest rates +3% |
| **Interest Rate Cut** | Central bank lowers rates | All loan interest rates -2% |

### Natural Disasters
Events that damage properties and require repairs.

| Event | Description | Effect |
|-------|-------------|--------|
| **Hurricane** | Massive storm | All properties damaged by 20% of value |
| **Earthquake** | Seismic activity | Random 50% of properties damaged by 30% of value |
| **Flood** | Water damage | Waterfront properties damaged by 15% of value |

### Community Events
Events that affect players collectively or through community infrastructure.

| Event | Description | Effect |
|-------|-------------|--------|
| **Community Festival** | City celebration | Rental income +50% for one round |
| **Infrastructure Project** | City upgrades | Property values +12%, all players pay 50 in taxes |
| **Tax Reform** | New tax legislation | All players pay 10% of cash to community fund |

## How Events Work

### Event Triggering
- Events have a 15% chance to trigger at the end of each full game cycle
- Events won't trigger during the first 3 laps of the game
- A minimum of 3 laps must pass between events (cooldown period)

### Property Damage
When properties are damaged:
1. Damage amount is calculated as a percentage of the property value
2. Rent income is reduced proportionally to damage
3. Players must repair properties to restore full rent value
4. Repairs cost the full damage amount to complete

### Event Processing
1. The `EventSystem.check_for_event()` method is called at the end of a turn
2. If an event triggers, it's applied through the `apply_event()` method
3. Event effects are applied to the game state, properties, and/or players
4. All players are notified about the event and its effects

## Temporary Effects

Some events create temporary effects that last for a specific number of turns. These are stored in the game state and processed each turn.

Example of a temporary effect:
```json
{
  "type": "rent_modifier",
  "value": 1.5,
  "remaining_turns": 1
}
```

## Event System API

### Classes

#### EventSystem
```python
class EventSystem:
    def __init__(self, socketio, banker, community_fund)
    def check_for_event(self, game_state)  # Returns event or None
    def apply_event(self, game_state, event_id)  # Applies event effects
```

#### Property (Event-related methods)
```python
class Property:
    def update_value(self, new_value)  # Update property value
    def update_rent(self, new_rent)  # Update rent value
    def apply_damage(self, damage_amount)  # Apply damage to property
    def repair_damage(self, repair_amount=None)  # Repair property
```

#### GameState (Event-related methods)
```python
class GameState:
    def add_temporary_effect(self, effect)  # Add a temporary effect
    def process_turn_end(self)  # Process/update temporary effects
```

## Socket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `game_event` | Server → Client | Notifies clients about triggered events |
| `property_update` | Server → Client | Updates clients about property changes |
| `repair_property` | Client → Server | Request to repair damaged property |
| `repair_completed` | Server → Client | Confirmation of property repair |

## Implementing New Events

To add a new event to the system:

1. Add the event definition to the `_define_events()` method in `EventSystem`
2. Implement or reuse an appropriate action handler (`_apply_*` method)
3. Test the event through the admin interface

## Testing Events

Events can be manually triggered through the admin interface for testing:

1. Navigate to the admin panel
2. Select "Event Manager" 
3. Choose an event from the dropdown
4. Click "Trigger Event" to apply it to the game 