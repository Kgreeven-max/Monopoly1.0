from datetime import datetime
import random
import logging

class EventSystem:
    """Manages random events and disasters that affect gameplay"""
    
    def __init__(self, socketio, banker, community_fund):
        self.socketio = socketio
        self.banker = banker
        self.community_fund = community_fund
        self.events = self._define_events()
        self.last_event_lap = 0
        self.event_cooldown = 3  # Minimum laps between events
        self.event_probability = 0.15  # 15% chance per full cycle
        self.logger = logging.getLogger("event_system")
    
    def _define_events(self):
        """Define all possible game events"""
        return {
            # Economic events
            "economic_boom": {
                "title": "Economic Boom",
                "description": "The economy is thriving! All property values increase by 10%.",
                "type": "economic",
                "severity": "positive",
                "action": "property_value_change",
                "value_modifier": 1.1,
                "rent_modifier": 1.1
            },
            "market_crash": {
                "title": "Market Crash",
                "description": "The property market has crashed! All property values decrease by 15%.",
                "type": "economic",
                "severity": "negative",
                "action": "property_value_change",
                "value_modifier": 0.85,
                "rent_modifier": 0.85
            },
            "interest_rate_hike": {
                "title": "Interest Rate Hike",
                "description": "The central bank has increased interest rates! All loan interest rates increase by 3%.",
                "type": "economic",
                "severity": "negative",
                "action": "interest_rate_change",
                "interest_modifier": 0.03
            },
            "interest_rate_cut": {
                "title": "Interest Rate Cut",
                "description": "The central bank has decreased interest rates! All loan interest rates decrease by 2%.",
                "type": "economic",
                "severity": "positive",
                "action": "interest_rate_change",
                "interest_modifier": -0.02
            },
            # Natural disasters
            "hurricane": {
                "title": "Hurricane",
                "description": "A hurricane has damaged properties! All buildings take damage and require repairs.",
                "type": "disaster",
                "severity": "severe",
                "action": "property_damage",
                "damage_percent": 0.2,
                "affected_areas": "all"
            },
            "earthquake": {
                "title": "Earthquake",
                "description": "An earthquake has struck! Buildings in certain areas need extensive repairs.",
                "type": "disaster",
                "severity": "severe",
                "action": "property_damage",
                "damage_percent": 0.3,
                "affected_areas": "random_50_percent"
            },
            "flood": {
                "title": "Flood",
                "description": "A flood has damaged waterfront properties!",
                "type": "disaster",
                "severity": "moderate",
                "action": "property_damage",
                "damage_percent": 0.15,
                "affected_areas": "water_adjacent"
            },
            # Community events
            "community_festival": {
                "title": "Community Festival",
                "description": "A city-wide festival is attracting tourists! Rental income increases for one round.",
                "type": "community",
                "severity": "positive",
                "action": "temporary_rent_boost",
                "rent_modifier": 1.5,
                "duration": 1
            },
            "infrastructure_project": {
                "title": "Infrastructure Project",
                "description": "The city is upgrading infrastructure! Property values increase but taxes are raised.",
                "type": "community",
                "severity": "mixed",
                "action": "infrastructure_upgrade",
                "value_modifier": 1.12,
                "tax_increase": 50
            },
            "tax_reform": {
                "title": "Tax Reform",
                "description": "New tax legislation has been passed! All players pay 10% of their cash to the community fund.",
                "type": "community",
                "severity": "negative",
                "action": "tax_collection",
                "tax_percent": 0.1
            }
        }
    
    def check_for_event(self, game_state):
        """Check if an event should trigger on the current turn"""
        current_lap = game_state.current_lap
        
        # Only trigger events after the first few laps
        if current_lap < 3:
            return None
            
        # Check cooldown period
        if current_lap - self.last_event_lap < self.event_cooldown:
            return None
            
        # Random chance based on probability
        if random.random() > self.event_probability:
            return None
            
        # Select a random event
        event_id = random.choice(list(self.events.keys()))
        event = self.events[event_id]
        
        self.last_event_lap = current_lap
        self.logger.info(f"Event triggered: {event['title']}")
        
        return {
            "id": event_id,
            "data": event,
            "timestamp": datetime.now().isoformat()
        }
    
    def apply_event(self, game_state, event_id):
        """Apply the effects of an event to the game state"""
        if event_id not in self.events:
            self.logger.error(f"Attempted to apply unknown event: {event_id}")
            return False
            
        event = self.events[event_id]
        action = event["action"]
        
        if action == "property_value_change":
            self._apply_property_value_change(game_state, event)
        elif action == "interest_rate_change":
            self._apply_interest_rate_change(game_state, event)
        elif action == "property_damage":
            self._apply_property_damage(game_state, event)
        elif action == "temporary_rent_boost":
            self._apply_temporary_rent_boost(game_state, event)
        elif action == "infrastructure_upgrade":
            self._apply_infrastructure_upgrade(game_state, event)
        elif action == "tax_collection":
            self._apply_tax_collection(game_state, event)
        else:
            self.logger.error(f"Unknown event action: {action}")
            return False
        
        # Broadcast event to all players
        self.socketio.emit('game_event', {
            'event_id': event_id,
            'event_data': event,
            'timestamp': datetime.now().isoformat()
        }, room=game_state.game_id)
        
        return True
    
    def _apply_property_value_change(self, game_state, event):
        """Apply property value and rent changes to all properties"""
        value_mod = event["value_modifier"]
        rent_mod = event["rent_modifier"]
        
        for prop in game_state.properties:
            prop.update_value(prop.value * value_mod)
            prop.update_rent(prop.base_rent * rent_mod)
            
        self.logger.info(f"Applied property value change: {event['title']}")
    
    def _apply_interest_rate_change(self, game_state, event):
        """Apply interest rate changes to all loans"""
        interest_mod = event["interest_modifier"]
        
        for player in game_state.players:
            for loan in player.loans:
                if not loan.is_paid_off:
                    loan.adjust_interest_rate(interest_mod)
        
        self.logger.info(f"Applied interest rate change: {event['title']}")
    
    def _apply_property_damage(self, game_state, event):
        """Apply damage to properties based on the event parameters"""
        damage_percent = event["damage_percent"]
        affected_areas = event["affected_areas"]
        
        affected_properties = []
        if affected_areas == "all":
            affected_properties = game_state.properties
        elif affected_areas == "random_50_percent":
            affected_properties = random.sample(game_state.properties, len(game_state.properties) // 2)
        elif affected_areas == "water_adjacent":
            affected_properties = [p for p in game_state.properties if p.is_water_adjacent]
        
        for prop in affected_properties:
            damage_amount = int(prop.value * damage_percent)
            prop.apply_damage(damage_amount)
            owner = prop.owner
            if owner and owner != "bank":
                owner.send_notification(
                    f"Your property {prop.name} has been damaged and requires {damage_amount} in repairs!"
                )
        
        self.logger.info(f"Applied property damage: {event['title']}")
    
    def _apply_temporary_rent_boost(self, game_state, event):
        """Apply a temporary rent boost for the specified duration"""
        rent_mod = event["rent_modifier"]
        duration = event["duration"]
        
        game_state.add_temporary_effect({
            "type": "rent_modifier",
            "value": rent_mod,
            "remaining_turns": duration
        })
        
        self.logger.info(f"Applied temporary rent boost: {event['title']}")
    
    def _apply_infrastructure_upgrade(self, game_state, event):
        """Apply property value increase and tax increase"""
        value_mod = event["value_modifier"]
        tax_increase = event["tax_increase"]
        
        # Update property values
        for prop in game_state.properties:
            prop.update_value(prop.value * value_mod)
        
        # Apply tax to all players
        for player in game_state.players:
            if player.is_active:
                tax_amount = tax_increase
                player.pay(tax_amount)
                self.community_fund.receive(tax_amount)
                player.send_notification(
                    f"You paid {tax_amount} in taxes for infrastructure improvements."
                )
        
        self.logger.info(f"Applied infrastructure upgrade: {event['title']}")
    
    def _apply_tax_collection(self, game_state, event):
        """Apply a percentage-based tax to all players"""
        tax_percent = event["tax_percent"]
        
        for player in game_state.players:
            if player.is_active:
                tax_amount = int(player.cash * tax_percent)
                player.pay(tax_amount)
                self.community_fund.receive(tax_amount)
                player.send_notification(
                    f"You paid {tax_amount} in taxes ({tax_percent*100}% of your cash)."
                )
        
        self.logger.info(f"Applied tax collection: {event['title']}") 