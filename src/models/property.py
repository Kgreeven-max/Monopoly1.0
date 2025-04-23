from . import db
from datetime import datetime, timedelta
import random
import enum

# Enum for property types
class PropertyType(enum.Enum):
    STREET = 'street'
    RAILROAD = 'railroad'
    UTILITY = 'utility'

class Property(db.Model):
    """Model for game properties"""
    __tablename__ = 'properties'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum(PropertyType), nullable=False)
    position = db.Column(db.Integer, unique=True, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    current_price = db.Column(db.Integer, nullable=True)  # Current price after economic effects
    rent = db.Column(db.Integer)  # Base rent
    current_rent = db.Column(db.Integer, nullable=True)  # Current rent after economic effects
    rent_house_1 = db.Column(db.Integer)
    rent_house_2 = db.Column(db.Integer)
    rent_house_3 = db.Column(db.Integer)
    rent_house_4 = db.Column(db.Integer)
    rent_hotel = db.Column(db.Integer)
    mortgage_value = db.Column(db.Integer, nullable=False)
    house_cost = db.Column(db.Integer)
    hotel_cost = db.Column(db.Integer)
    color_group = db.Column(db.String(50)) # e.g., 'Brown', 'LightBlue', 'Railroad'
    owner_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    is_mortgaged = db.Column(db.Boolean, default=False)
    houses = db.Column(db.Integer, default=0) # 0-4 houses, 5 for hotel
    hotel = db.Column(db.Boolean, default=False)
    
    # Foreign Key to link Property to a Game
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    
    # Add ForeignKey to link to Team model
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    
    # Enhanced development properties
    max_development_level = db.Column(db.Integer, default=4)  # Default max level is 4
    has_community_approval = db.Column(db.Boolean, default=False)  # Community approval for level 3+
    has_environmental_study = db.Column(db.Boolean, default=False)  # Required for level 4 in some zones
    environmental_study_expires = db.Column(db.DateTime, nullable=True)  # Study expiration date
    
    # Market event related fields
    discount_percentage = db.Column(db.Float, nullable=False, default=0)
    discount_amount = db.Column(db.Integer, nullable=False, default=0)
    premium_percentage = db.Column(db.Float, nullable=False, default=0)
    premium_amount = db.Column(db.Integer, nullable=False, default=0)
    
    # Relationship with owner
    owner = db.relationship('Player', back_populates='properties')
    # The 'team' backref is automatically created by the relationship in Team model
    game = db.relationship('Game') # Simple relationship to Game
    
    # Development constants
    DEVELOPMENT_LEVELS = {
        0: {"name": "Undeveloped", "rent_multiplier": 1.0, "value_multiplier": 1.0, "max_damage": 0.0, "repair_cost_factor": 0.0},
        1: {"name": "Basic Development", "rent_multiplier": 2.0, "value_multiplier": 1.5, "max_damage": 0.5, "repair_cost_factor": 0.2},
        2: {"name": "Intermediate Development", "rent_multiplier": 3.5, "value_multiplier": 2.0, "max_damage": 0.6, "repair_cost_factor": 0.3},
        3: {"name": "Advanced Development", "rent_multiplier": 5.0, "value_multiplier": 2.5, "max_damage": 0.7, "repair_cost_factor": 0.4},
        4: {"name": "Premium Development", "rent_multiplier": 7.0, "value_multiplier": 3.0, "max_damage": 0.8, "repair_cost_factor": 0.5}
    }
    
    # Zoning regulations by property group
    ZONING_REGULATIONS = {
        "brown": {"max_level": 3, "approval_required": False, "study_required": False, "cost_modifier": 0.8},
        "light_blue": {"max_level": 3, "approval_required": False, "study_required": False, "cost_modifier": 0.9},
        "pink": {"max_level": 4, "approval_required": True, "study_required": False, "cost_modifier": 1.0},
        "orange": {"max_level": 4, "approval_required": True, "study_required": False, "cost_modifier": 1.0},
        "red": {"max_level": 4, "approval_required": False, "study_required": True, "cost_modifier": 1.1},
        "yellow": {"max_level": 4, "approval_required": False, "study_required": True, "cost_modifier": 1.1},
        "green": {"max_level": 4, "approval_required": True, "study_required": True, "cost_modifier": 1.2},
        "blue": {"max_level": 4, "approval_required": True, "study_required": True, "cost_modifier": 1.3},
        "railroad": {"max_level": 0, "approval_required": False, "study_required": False, "cost_modifier": 0.0},
        "utility": {"max_level": 0, "approval_required": False, "study_required": False, "cost_modifier": 0.0}
    }
    
    # Development base costs as percentage of property value
    DEVELOPMENT_COSTS = {
        1: 0.5,   # 50% of property value for level 1
        2: 0.6,   # 60% of property value for level 2
        3: 0.75,  # 75% of property value for level 3
        4: 1.0    # 100% of property value for level 4
    }
    
    # Economic multipliers for development costs
    ECONOMIC_MULTIPLIERS = {
        "recession": 0.85,   # 15% discount during recession
        "normal": 1.0,       # Standard costs in normal economy
        "growth": 1.1,       # 10% premium during growth
        "boom": 1.25         # 25% premium during boom
    }
    
    def __init__(self, name, position, group_name, price, rent, improvement_cost=0,
                 mortgage_value=0, rent_levels=None):
        self.name = name
        self.position = position
        self.group_name = group_name
        self.price = price
        self.current_price = price
        self.rent = rent
        self.current_rent = rent
        self.mortgage_value = mortgage_value or int(price * 0.5)
        self.is_mortgaged = False
        self.owner_id = None
        self.discount_percentage = 0
        self.discount_amount = 0
        self.premium_percentage = 0
        self.premium_amount = 0
        
        # Set max development level based on property group
        zoning_key = group_name.lower() if group_name else 'default'
        if zoning_key in self.ZONING_REGULATIONS:
            self.max_development_level = self.ZONING_REGULATIONS[zoning_key]["max_level"]
        else:
            self.max_development_level = 4  # Default to max level 4
        
    def __repr__(self):
        return f'<Property {self.name}>'
    
    def to_dict(self):
        """Convert property to dictionary for API responses"""
        current_level = self.DEVELOPMENT_LEVELS.get(self.improvement_level, self.DEVELOPMENT_LEVELS[0])
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'position': self.position,
            'price': self.price,
            'rent': self.rent,
            'rent_house_1': self.rent_house_1,
            'rent_house_2': self.rent_house_2,
            'rent_house_3': self.rent_house_3,
            'rent_house_4': self.rent_house_4,
            'rent_hotel': self.rent_hotel,
            'mortgage_value': self.mortgage_value,
            'house_cost': self.house_cost,
            'hotel_cost': self.hotel_cost,
            'color_group': self.color_group,
            'owner_id': self.owner_id,
            'is_mortgaged': self.is_mortgaged,
            'houses': self.houses,
            'hotel': self.hotel,
            'game_id': self.game_id,
            'improvement_level': self.improvement_level,
            'development_level_name': current_level["name"],
            'improvement_cost': self.improvement_cost,
            'current_improvement_cost': self.current_improvement_cost,
            'max_development_level': self.max_development_level,
            'has_community_approval': self.has_community_approval,
            'has_environmental_study': self.has_environmental_study,
            'environmental_study_expires': self.environmental_study_expires.isoformat() if self.environmental_study_expires else None,
            'discount_percentage': self.discount_percentage,
            'discount_amount': self.discount_amount,
            'premium_percentage': self.premium_percentage,
            'premium_amount': self.premium_amount
        }
    
    def calculate_rent(self, dice_roll=None):
        """Calculate current rent based on improvements, ownership, and type."""
        # No rent if mortgaged or no owner
        if self.is_mortgaged or self.owner is None:
            return 0

        owner = self.owner

        # --- Street Rent Calculation ---
        if self.type == PropertyType.STREET:
            if self.hotel:
                base_rent = self.rent_hotel
            elif self.houses == 4:
                base_rent = self.rent_house_4
            elif self.houses == 3:
                base_rent = self.rent_house_3
            elif self.houses == 2:
                base_rent = self.rent_house_2
            elif self.houses == 1:
                base_rent = self.rent_house_1
            else: # 0 houses
                base_rent = self.rent
                # Check for monopoly (owner owns all properties in the color group)
                all_in_group = Property.query.filter_by(game_id=self.game_id, color_group=self.color_group).all()
                is_monopoly = all(prop.owner_id == owner.id for prop in all_in_group)
                if is_monopoly:
                    base_rent *= 2 # Double base rent for undeveloped monopoly
            return base_rent

        # --- Railroad Rent Calculation ---
        elif self.type == PropertyType.RAILROAD:
            # Count how many railroads the owner owns
            owned_railroads = Property.query.filter(
                Property.game_id == self.game_id,
                Property.type == PropertyType.RAILROAD,
                Property.owner_id == owner.id
            ).count()
            
            if owned_railroads == 1:
                return 25
            elif owned_railroads == 2:
                return 50
            elif owned_railroads == 3:
                return 100
            elif owned_railroads == 4:
                return 200
            else:
                return 0 # Should not happen if owner exists

        # --- Utility Rent Calculation ---
        elif self.type == PropertyType.UTILITY:
            if dice_roll is None:
                # Need dice roll to calculate utility rent, return 0 or base if needed?
                # For admin display, maybe just return base? Let's return 0 for now.
                return 0 
                
            owned_utilities = Property.query.filter(
                Property.game_id == self.game_id,
                Property.type == PropertyType.UTILITY,
                Property.owner_id == owner.id
            ).count()
            
            if owned_utilities == 1:
                return dice_roll * 4
            elif owned_utilities >= 2: # Owns both
                return dice_roll * 10
            else:
                return 0 # Should not happen if owner exists

        return 0 # Default case if type is somehow unknown

    def update_value(self, new_value):
        """Update the property value due to market changes"""
        self.current_price = int(new_value)
        db.session.add(self)
        db.session.commit()
        
    def update_rent(self, new_rent):
        """Update the base rent due to market changes"""
        self.current_rent = int(new_rent)
        db.session.add(self)
        db.session.commit()
        
    def apply_damage(self, damage_amount):
        """Apply damage to a property due to a disaster event"""
        # Calculate the maximum damage this property can sustain based on development level
        dev_level = self.DEVELOPMENT_LEVELS.get(self.improvement_level, self.DEVELOPMENT_LEVELS[0])
        max_damage_factor = dev_level["max_damage"]
        max_damage_amount = int(self.current_price * max_damage_factor)
        
        # Apply damage up to the maximum
        total_damage = min(self.damage_amount + damage_amount, max_damage_amount)
        actual_new_damage = total_damage - self.damage_amount
        
        self.damage_amount = total_damage
        db.session.add(self)
        db.session.commit()
        
        return actual_new_damage
        
    def repair_damage(self, repair_amount=None):
        """Repair property damage, either partially or fully"""
        if self.damage_amount <= 0:
            return {
                "success": False,
                "reason": "Property has no damage to repair",
                "repaired": 0,
                "remaining": 0,
                "cost": 0
            }
            
        # Get development level data
        dev_level = self.DEVELOPMENT_LEVELS.get(self.improvement_level, self.DEVELOPMENT_LEVELS[0])
        repair_cost_factor = dev_level["repair_cost_factor"]
        
        # Calculate full repair amount and cost
        full_repair_amount = self.damage_amount
        full_repair_cost = int(full_repair_amount * repair_cost_factor)
        
        # If repair_amount not specified, do a full repair
        if repair_amount is None or repair_amount >= self.damage_amount:
            repair_amount = self.damage_amount
            repair_cost = full_repair_cost
            self.damage_amount = 0
        else:
            # Partial repair - calculate proportional cost
            repair_cost = int(repair_amount * repair_cost_factor)
            self.damage_amount -= repair_amount
            
        db.session.add(self)
        db.session.commit()
        
        # Calculate new rent after repair
        new_rent = self.calculate_rent()
        
        return {
            "success": True,
            "repaired": repair_amount,
            "remaining": self.damage_amount,
            "cost": repair_cost,
            "full_repair_cost": full_repair_cost,
            "development_level": self.improvement_level,
            "development_name": dev_level["name"],
            "repair_cost_factor": repair_cost_factor,
            "new_rent": new_rent
        }
    
    def calculate_repair_cost(self, repair_amount=None):
        """Calculate the cost to repair property damage"""
        # If repair amount not specified, calculate for full repair
        if repair_amount is None or repair_amount > self.damage_amount:
            repair_amount = self.damage_amount
            
        if repair_amount <= 0:
            return 0
            
        # Get the repair cost factor based on development level
        dev_level = self.DEVELOPMENT_LEVELS.get(self.improvement_level, self.DEVELOPMENT_LEVELS[0])
        repair_cost_factor = dev_level["repair_cost_factor"]
        
        # Calculate the cost of repairs
        # More developed properties cost more to repair proportionally to damage
        repair_cost = int(repair_amount * repair_cost_factor)
        
        return repair_cost
        
    def apply_market_crash(self, percentage):
        """Apply a market crash discount to the property"""
        if percentage <= 0:
            return False
        
        # Calculate discount amount
        self.discount_percentage = percentage
        self.discount_amount = int(self.price * (percentage / 100))
        
        # Apply discount to current price
        self.current_price = self.price - self.discount_amount
        
        # Also update rent proportionally
        discount_factor = 1 - (percentage / 100)
        self.current_rent = int(self.rent * discount_factor)
        
        return True
    
    def apply_economic_boom(self, percentage):
        """Apply an economic boom premium to the property"""
        if percentage <= 0:
            return False
        
        # Calculate premium amount
        self.premium_percentage = percentage
        self.premium_amount = int(self.price * (percentage / 100))
        
        # Apply premium to current price
        self.current_price = self.price + self.premium_amount
        
        # Also update rent proportionally
        premium_factor = 1 + (percentage / 100)
        self.current_rent = int(self.rent * premium_factor)
        
        return True
    
    def restore_market_prices(self):
        """Restore property to base price and rent after market events"""
        # Reset market event fields
        self.discount_percentage = 0
        self.discount_amount = 0
        self.premium_percentage = 0
        self.premium_amount = 0
        
        # Restore base prices
        self.current_price = self.price
        self.current_rent = self.rent
        
        return True
    
    def mortgage(self):
        """Mortgage a property"""
        if self.is_mortgaged or self.improvement_level > 0:
            return False
            
        self.is_mortgaged = True
        return True
    
    def unmortgage(self):
        """Unmortgage a property"""
        if not self.is_mortgaged:
            return False
            
        self.is_mortgaged = False
        return True
    
    def can_improve(self, game_state=None):
        """Check if property can be improved to the next level"""
        # Cannot improve if mortgaged, has lien, or no owner
        if self.is_mortgaged or self.has_lien or not self.owner_id:
            return {"can_improve": False, "reason": "Property is mortgaged, has a lien, or has no owner"}
            
        # Check if already at max level
        if self.improvement_level >= self.max_development_level:
            return {"can_improve": False, "reason": f"Already at maximum development level ({self.max_development_level})"}
            
        # Check group ownership requirement (must own all in group to improve)
        properties_in_group = Property.query.filter_by(group_name=self.group_name).all()
        all_owned = all(prop.owner_id == self.owner_id for prop in properties_in_group)
        
        if not all_owned:
            return {"can_improve": False, "reason": "Must own all properties in the group to improve"}
            
        # Check for community approval requirement
        if self.improvement_level >= 2:  # Going to level 3+
            zone_info = self.ZONING_REGULATIONS.get(self.group_name.lower(), {})
            if zone_info.get("approval_required", False) and not self.has_community_approval:
                return {"can_improve": False, "reason": "Community approval required for level 3+"}
                
        # Check for environmental study requirement
        if self.improvement_level >= 3:  # Going to level 4
            zone_info = self.ZONING_REGULATIONS.get(self.group_name.lower(), {})
            if zone_info.get("study_required", False):
                if not self.has_environmental_study:
                    return {"can_improve": False, "reason": "Environmental study required for level 4"}
                
                # Check if study is expired
                if self.environmental_study_expires and self.environmental_study_expires < datetime.now():
                    return {"can_improve": False, "reason": "Environmental study has expired"}
        
        return {"can_improve": True}
    
    def improve(self, game_state=None):
        """Improve property to the next development level"""
        # Check if improvement is possible
        improvement_check = self.can_improve(game_state)
        if not improvement_check["can_improve"]:
            return {"success": False, "reason": improvement_check["reason"]}
            
        # Get the cost for this improvement level
        improvement_cost = self.calculate_improvement_cost(game_state)
        
        # Increase improvement level
        old_level = self.improvement_level
        self.improvement_level += 1
        new_level = self.improvement_level
        
        # Update property value to reflect improvement
        dev_level = self.DEVELOPMENT_LEVELS.get(self.improvement_level, self.DEVELOPMENT_LEVELS[0])
        value_multiplier = dev_level["value_multiplier"]
        self.current_price = int(self.price * value_multiplier)
        
        db.session.add(self)
        db.session.commit()
        
        return {
            "success": True, 
            "old_level": old_level,
            "new_level": new_level, 
            "cost": improvement_cost,
            "new_value": self.current_price
        }
    
    def calculate_improvement_cost(self, game_state=None):
        """Calculate the cost to improve to the next level"""
        # Check if already at max level
        if self.improvement_level >= self.max_development_level:
            return 0
            
        # Get base cost percentage for next level
        next_level = self.improvement_level + 1
        base_cost_factor = self.DEVELOPMENT_COSTS.get(next_level, 0.5)
        
        # Apply zone cost modifier
        zone_info = self.ZONING_REGULATIONS.get(self.group_name.lower(), {})
        zone_cost_modifier = zone_info.get("cost_modifier", 1.0)
        
        # Apply economic state modifier if game state is provided
        economic_modifier = 1.0
        if game_state:
            economic_state = game_state.inflation_state
            economic_modifier = self.ECONOMIC_MULTIPLIERS.get(economic_state, 1.0)
            
            # Also apply inflation factor
            inflation_factor = game_state.inflation_factor
        else:
            inflation_factor = 1.0
        
        # Calculate final cost
        base_cost = self.price * base_cost_factor
        final_cost = base_cost * zone_cost_modifier * economic_modifier * inflation_factor
        
        return int(final_cost)
    
    def remove_improvement(self):
        """Remove one level of improvement from property"""
        if self.improvement_level <= 0:
            return {"success": False, "reason": "Property has no improvements"}
            
        old_level = self.improvement_level
        self.improvement_level -= 1
        new_level = self.improvement_level
        
        # Update property value to reflect downgrade
        dev_level = self.DEVELOPMENT_LEVELS.get(self.improvement_level, self.DEVELOPMENT_LEVELS[0])
        value_multiplier = dev_level["value_multiplier"]
        self.current_price = int(self.price * value_multiplier)
        
        db.session.add(self)
        db.session.commit()
        
        return {
            "success": True,
            "old_level": old_level,
            "new_level": new_level,
            "new_value": self.current_price
        }
    
    def request_community_approval(self, game_state=None):
        """Request community approval for higher level development"""
        if self.has_community_approval:
            return {"success": False, "reason": "Already has community approval"}
            
        # Check if this property group requires community approval
        zone_info = self.ZONING_REGULATIONS.get(self.group_name.lower(), {})
        if not zone_info.get("approval_required", False):
            return {"success": False, "reason": "Community approval not required for this property group"}
            
        # Calculate approval chance based on player's community standing
        approval_chance = 0.5  # 50% base chance
        
        # Adjust for player's community standing
        player = Player.query.get(self.owner_id)
        if player:
            # Scale from 0-100 to ±0.4 modifier (10-90% chance)
            standing_modifier = (player.community_standing - 50) / 125  # -0.4 to +0.4
            approval_chance += standing_modifier
            
            # Ensure chances are within bounds
            approval_chance = max(0.1, min(0.9, approval_chance))
            
            # Apply economic bonus in growth/boom phases
            if game_state and game_state.inflation_state in ["growth", "boom"]:
                approval_chance += 0.1
            
            # Reduce chances during recession
            if game_state and game_state.inflation_state == "recession":
                approval_chance -= 0.1
        
        # Make the final decision
        if random.random() < approval_chance:
            self.has_community_approval = True
            db.session.add(self)
            db.session.commit()
            
            # Return success with approval chance for transparency
            message = "Community approval granted!"
            if player.community_standing >= 75:
                message += " Your excellent reputation helped secure approval."
            elif player.community_standing >= 60:
                message += " Your good standing in the community was a factor."
                
            return {
                "success": True, 
                "message": message,
                "approval_chance": int(approval_chance * 100)
            }
        else:
            # Return failure with feedback
            message = "Community approval denied. Try again later."
            if player.community_standing < 40:
                message += " Improving your community standing may help."
                
            return {
                "success": False, 
                "reason": message,
                "approval_chance": int(approval_chance * 100)
            }
    
    def commission_environmental_study(self, game_state=None):
        """Commission an environmental study for highest level development"""
        if self.has_environmental_study and self.environmental_study_expires and self.environmental_study_expires > datetime.now():
            return {"success": False, "reason": "Already has a valid environmental study"}
            
        # Check if this property group requires environmental study
        zone_info = self.ZONING_REGULATIONS.get(self.group_name.lower(), {})
        if not zone_info.get("study_required", False):
            return {"success": False, "reason": "Environmental study not required for this property group"}
            
        # Set study expiration (valid for a certain number of game turns)
        # In a real implementation, this would be based on game turns rather than actual time
        duration_days = 30  # Study is valid for 30 real-world days
        self.has_environmental_study = True
        self.environmental_study_expires = datetime.now().replace(hour=23, minute=59, second=59) + timedelta(days=duration_days)
        
        db.session.add(self)
        db.session.commit()
        
        return {
            "success": True, 
            "message": "Environmental study completed successfully!",
            "expires": self.environmental_study_expires.isoformat()
        }
    
    def check_development_requirements(self, target_level):
        """Check if all requirements are met for a specific development level"""
        if target_level <= self.improvement_level:
            return {"requirements_met": True, "message": "Already at or above this level"}
            
        if target_level > self.max_development_level:
            return {
                "requirements_met": False, 
                "message": f"Cannot develop beyond level {self.max_development_level} in this zone"
            }
        
        # Get zoning requirements
        zone_info = self.ZONING_REGULATIONS.get(self.group_name.lower(), {})
        
        missing_requirements = []
        
        # Check community approval for level 3+
        if target_level >= 3 and zone_info.get("approval_required", False) and not self.has_community_approval:
            missing_requirements.append("Community approval required for level 3+")
            
        # Check environmental study for level 4
        if target_level >= 4 and zone_info.get("study_required", False):
            if not self.has_environmental_study:
                missing_requirements.append("Environmental study required for level 4")
            elif self.environmental_study_expires and self.environmental_study_expires < datetime.now():
                missing_requirements.append("Environmental study has expired")
        
        # Check if all properties in group are owned
        properties_in_group = Property.query.filter_by(group_name=self.group_name).all()
        all_owned = all(prop.owner_id == self.owner_id for prop in properties_in_group)
        
        if not all_owned:
            missing_requirements.append("Must own all properties in the group")
        
        # Check for liens or mortgages
        if self.is_mortgaged or self.has_lien:
            missing_requirements.append("Cannot improve mortgaged properties or properties with liens")
        
        if missing_requirements:
            return {
                "requirements_met": False,
                "message": "Missing requirements for development",
                "missing_requirements": missing_requirements
            }
        
        return {"requirements_met": True, "message": "All requirements met for development"} 