# Advanced Economics System

## Overview

The Advanced Economics System transforms Pi-nopoly's financial mechanics with sophisticated market dynamics, supply and demand modeling, and realistic economic cycles. These systems create a dynamic gameplay environment where property values, development opportunities, and financial strategies must adapt to evolving economic conditions.

## Supply and Demand System

The supply and demand system dynamically affects property values based on player actions and game events:

### Property Value Factors

1. **Base Value Calculation**
   - Each property has a base list price that scales with inflation
   - Position on board (later properties have higher base values)
   - Group membership (higher value groups have higher base multipliers)

2. **Supply Factors**
   - Number of properties available for purchase
   - Development density in an area
   - Property damage reductions
   - Foreclosure events

3. **Demand Factors**
   - Player interest (measured by landing frequency)
   - Group completion potential
   - Development level of surrounding properties
   - Special event bonuses/penalties

### Value Adjustment Algorithm

Property values are adjusted each game lap using the following algorithm:

```python
def adjust_property_values():
    """Adjust all property values based on supply and demand"""
    properties = Property.query.all()
    game_state = GameState.query.first()
    
    # Global economic factors
    inflation_factor = game_state.inflation_factor
    economic_state = game_state.inflation_state
    economic_multipliers = {
        "recession": 0.9,
        "normal": 1.0,
        "growth": 1.1,
        "boom": 1.2
    }
    economic_multiplier = economic_multipliers.get(economic_state, 1.0)
    
    # Calculate supply and demand factors
    supply_factors = calculate_supply_factors()
    demand_factors = calculate_demand_factors()
    
    # Adjust each property
    for prop in properties:
        # Get property-specific factors
        property_supply = supply_factors.get(prop.id, 1.0)
        property_demand = demand_factors.get(prop.id, 1.0)
        
        # Calculate market pressure
        market_pressure = property_demand / property_supply
        
        # Apply bounded adjustment (-15% to +15% per lap)
        adjustment_factor = max(0.85, min(1.15, market_pressure))
        
        # Apply final adjustment with economic factors
        prop.current_price = int(prop.base_price * inflation_factor * 
                               economic_multiplier * adjustment_factor)
        
        # Adjust rent proportionally
        prop.current_rent = int(prop.base_rent * inflation_factor * 
                              economic_multiplier * adjustment_factor)
    
    db.session.commit()
```

## Stock Market Simulation

The stock market adds an alternative investment option for players:

### Stock System Mechanics

1. **Company Representation**
   - 10 virtual companies with shares available for purchase
   - Each company has industry alignment with property groups
   - Initial stock prices range from $50 to $200

2. **Price Fluctuation Model**
   - Base fluctuation using random walk with momentum
   - Influenced by economic phase (more volatile in boom/recession)
   - Industry-specific events affect related stocks
   - Player trading volume affects price movement

3. **Trading Mechanics**
   - Players can buy and sell shares during their turn
   - Transaction fees (1-3% commission)
   - Limit on shares available at any time
   - Insider trading penalties for suspicious patterns

### Stock Market Integration

```python
class StockMarket:
    """Manages the in-game stock market"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.companies = self._initialize_companies()
        self.available_shares = {}  # company_id -> available shares
        self.price_history = {}  # company_id -> list of historical prices
        self.last_update = datetime.now()
        self.update_frequency = 2  # Updates every 2 game turns
    
    def _initialize_companies(self):
        """Initialize stock market companies"""
        companies = [
            {
                "id": "utility_corp",
                "name": "Utility Corporation",
                "industry": "utilities",
                "base_price": 100,
                "volatility": 0.08,
                "related_groups": ["utility"],
                "shares_total": 1000
            },
            {
                "id": "transport_inc",
                "name": "Transport Inc.",
                "industry": "transportation",
                "base_price": 120,
                "volatility": 0.06,
                "related_groups": ["railroad"],
                "shares_total": 1000
            },
            {
                "id": "luxury_brands",
                "name": "Luxury Brands",
                "industry": "luxury",
                "base_price": 200,
                "volatility": 0.12,
                "related_groups": ["blue", "green"],
                "shares_total": 800
            },
            # Additional companies...
        ]
        
        # Set up initial state
        result = {}
        for company in companies:
            company_id = company["id"]
            result[company_id] = company
            
            # Initialize available shares
            self.available_shares[company_id] = company["shares_total"] // 2  # 50% available initially
            
            # Initialize price history
            self.price_history[company_id] = [company["base_price"]]
        
        return result
    
    def update_stock_prices(self):
        """Update stock prices based on market factors"""
        game_state = GameState.query.first()
        economic_state = game_state.inflation_state
        
        # Define economic volatility multipliers
        volatility_multipliers = {
            "recession": 1.5,  # Higher volatility in recession
            "normal": 1.0,
            "growth": 1.2,
            "boom": 1.8   # Highest volatility in boom
        }
        
        volatility_multiplier = volatility_multipliers.get(economic_state, 1.0)
        
        # Update each company's stock price
        price_updates = []
        
        for company_id, company in self.companies.items():
            # Get previous price
            prev_price = self.price_history[company_id][-1]
            
            # Calculate base volatility
            base_volatility = company["volatility"] * volatility_multiplier
            
            # Generate random movement with bias based on economic state
            economic_bias = {
                "recession": -0.02,  # Slight downward bias
                "normal": 0.0,
                "growth": 0.01,   # Slight upward bias
                "boom": 0.03      # Stronger upward bias
            }.get(economic_state, 0.0)
            
            # Calculate price movement
            import random
            movement = random.normalvariate(economic_bias, base_volatility)
            
            # Apply movement with constraints
            new_price = prev_price * (1 + movement)
            new_price = max(10, min(1000, new_price))  # Price bounds
            
            # Update price history
            self.price_history[company_id].append(new_price)
            
            # Trim history if too long
            if len(self.price_history[company_id]) > 50:
                self.price_history[company_id] = self.price_history[company_id][-50:]
            
            # Record update
            price_updates.append({
                "company_id": company_id,
                "company_name": company["name"],
                "previous_price": prev_price,
                "new_price": new_price,
                "change_percent": ((new_price - prev_price) / prev_price) * 100
            })
        
        # Broadcast updates
        self.socketio.emit('stock_market_update', {
            "updates": price_updates,
            "timestamp": datetime.now().isoformat(),
            "economic_state": economic_state
        })
        
        return price_updates
```

## Advanced Interest Rates and Inflation Mechanics

The enhanced financial system features realistic interest rate dynamics:

### Interest Rate Model

1. **Base Rate Determination**
   - Central bank rate affected by economic phase
   - Responds to inflation with counter-cyclical adjustments
   - Gradual changes with announcement events

2. **Loan-Specific Rates**
   - Base rate plus risk premium
   - Risk premium determined by borrower's financial condition
   - Loan size and duration affect rate
   - Collateralized loans (HELOC) receive preferential rates

3. **Investment Returns**
   - Certificate of Deposit (CD) returns tied to base rate
   - Risk-free but with liquidity constraints
   - Early withdrawal penalties

### Inflation System

```python
class EconomicCycleManager:
    """Manages the economic cycle, interest rates, and inflation"""
    
    def __init__(self, socketio, banker):
        self.socketio = socketio
        self.banker = banker
        self.base_interest_rate = 0.05  # 5% starting base rate
        self.inflation_target = 0.03    # 3% target inflation
        self.inflation_rate = 0.03      # Current inflation rate
        self.cycle_position = 0.0       # 0.0 to 1.0 position in cycle
        self.cycle_direction = 0.01     # Cycle movement per update
        self.last_update = datetime.now()
    
    def update_economic_cycle(self):
        """Update the economic cycle position and related factors"""
        # Move cycle position
        self.cycle_position += self.cycle_direction
        
        # Check for cycle boundaries and reverse if needed
        if self.cycle_position >= 1.0:
            self.cycle_position = 1.0
            self.cycle_direction = -0.01  # Start moving backward
        elif self.cycle_position <= 0.0:
            self.cycle_position = 0.0
            self.cycle_direction = 0.01   # Start moving forward
        
        # Determine economic state based on cycle position
        if self.cycle_position < 0.25:
            economic_state = "recession"
        elif self.cycle_position < 0.5:
            economic_state = "normal"
        elif self.cycle_position < 0.75:
            economic_state = "growth"
        else:
            economic_state = "boom"
        
        # Update inflation rate based on cycle position
        # Higher inflation in boom, lower in recession
        cycle_inflation_effect = (self.cycle_position - 0.5) * 0.04
        self.inflation_rate = self.inflation_target + cycle_inflation_effect
        
        # Adjust base interest rate to counter inflation
        # Increase rates when inflation is above target
        inflation_gap = self.inflation_rate - self.inflation_target
        if abs(inflation_gap) > 0.01:  # Only adjust if gap is significant
            rate_adjustment = inflation_gap * 1.5  # 1.5x response factor
            self.base_interest_rate += rate_adjustment * 0.1  # Gradual adjustment
        
        # Apply bounds to interest rate
        self.base_interest_rate = max(0.01, min(0.15, self.base_interest_rate))
        
        # Update game state
        game_state = GameState.query.first()
        game_state.inflation_state = economic_state
        game_state.inflation_rate = self.inflation_rate
        game_state.base_interest_rate = self.base_interest_rate
        db.session.commit()
        
        # Update all loans with new base rate
        self.banker.update_loan_rates(self.base_interest_rate)
        
        # Broadcast update
        self.socketio.emit('economic_update', {
            "economic_state": economic_state,
            "cycle_position": self.cycle_position,
            "inflation_rate": self.inflation_rate,
            "base_interest_rate": self.base_interest_rate
        })
        
        return {
            "economic_state": economic_state,
            "inflation_rate": self.inflation_rate,
            "base_interest_rate": self.base_interest_rate
        }
```

## Market Speculation Mechanics

The system introduces opportunities for market speculation:

### Speculation Features

1. **Property Flipping**
   - Buy low, sell high strategy
   - Short-term ownership bonuses/penalties
   - Renovation for quick value increases

2. **Market Timing Tools**
   - Economic indicators predict upcoming changes
   - Risk/reward tradeoffs for various strategies
   - Insider information cards from Chance/Community Chest

3. **Futures Contracts**
   - Bet on future property values
   - Lock in prices now for later purchases
   - Risk management for development plans

## Implementation Timeline

The Advanced Economics System will be implemented in four phases:

### Phase 1: Supply and Demand System
- Property value adjustment algorithm
- Market pressure calculations
- UI for displaying property value trends

### Phase 2: Interest Rate and Inflation
- Dynamic interest rate model
- Inflation effects on gameplay
- Economic phase transitions

### Phase 3: Stock Market
- Company creation and share system
- Price fluctuation mechanics
- Trading interface

### Phase 4: Market Speculation
- Property flipping mechanics
- Economic indicator tools
- Futures contracts 