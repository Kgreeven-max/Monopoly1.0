# Financial Instruments System

The Pi-nopoly Financial Instruments system provides players with multiple banking options to enhance gameplay and economic realism. This document details the implementation and features of each financial instrument.

## Overview

The Financial Instruments system consists of several components:

1. **Loans**: Standard borrowing with interest affected by economic conditions
2. **Certificates of Deposit (CDs)**: Investments with guaranteed returns
3. **Home Equity Line of Credit (HELOC)**: Property-backed loans with favorable rates
4. **Community Fund**: Public money pool for game events
5. **Bankruptcy System**: Mechanism for handling player insolvency

## User Interface Components

### Financial Dashboard
The main interface for managing all financial instruments is implemented in `FinancialDashboard.jsx`. This component provides:

- Real-time financial overview (cash, investments, debt, net worth)
- Current interest rates display
- Tab-based navigation between different financial instruments
- Responsive design for all device sizes

```jsx
// Example usage in game interface
<FinancialDashboard
  playerId={currentPlayer.id}
  playerPin={currentPlayer.pin}
  playerCash={currentPlayer.cash}
  onTransactionComplete={handleTransactionComplete}
/>
```

### Loan Management
Loan creation and management is handled through the `NewLoanModal.jsx` component, which provides:

- Dynamic loan amount selection with validation
- Real-time payment calculations
- Interest rate display
- Term and payment schedule information
- Warning messages about payment obligations

```jsx
// Example usage in loan creation
<NewLoanModal
  onClose={handleCloseModal}
  onConfirm={handleLoanConfirmation}
  playerCash={currentPlayer.cash}
  interestRate={currentInterestRate}
  maxLoanAmount={5000}
/>
```

### CD Investment Interface
The CD system is integrated into the Financial Dashboard with dedicated controls for:

- Multiple term options (3, 5, 7 laps)
- Interest rate comparison
- Early withdrawal options
- Current value tracking

### HELOC Management
HELOC features are accessible through the dashboard with:

- Property-based borrowing limits
- Collateral management
- Payment tracking
- Property value integration

## Loan System

Loans allow players to borrow money from the bank to finance property purchases, developments, or other strategic moves.

### Loan Features

- **Standard Terms**: 5-lap duration with compounding interest
- **Dynamic Interest Rates**: Vary based on:
  - Current economic phase (recession, normal, growth, boom)
  - Player's credit history (bankruptcy count)
  - Loan amount (larger loans have slightly higher rates)
- **Partial or Full Repayment**: Players can repay any amount at any time
- **Maximum Borrowing**: Limited to 80% of player's net worth

### Loan Interest Rate Calculation

```python
def _calculate_loan_interest_rate(self, player, amount):
    # Get base rates from economic state
    rates = self.get_interest_rates()["rates"]["loan"]
    
    # Start with standard rate
    rate = rates["standard"]
    
    # Adjust based on bankruptcy history
    if player.bankruptcy_count > 0:
        rate = rates["poor_credit"]
    elif player.cash > 2000:  # Good cash reserves
        rate = rates["good_credit"]
        
    # Adjust for large loans
    if amount > 1000:
        rate += 0.005
        
    return rate
```

## Certificate of Deposit (CD) System

CDs allow players to invest excess cash for guaranteed returns, similar to real-world bank CDs.

### CD Features

- **Multiple Term Options**: 3, 5, or 7 lap durations
- **Increasing Returns**: Longer terms offer higher interest rates
- **Early Withdrawal Penalty**: 10% penalty for withdrawing before maturity
- **Interest Calculation**: Based on initial deposit, term length, and economic conditions

### CD Interest Rate Calculation

```python
def _calculate_cd_interest_rate(self, term_length):
    # Get base rates from economic state
    rates = self.get_interest_rates()["rates"]["cd"]
    
    if term_length == 3:
        return rates["short_term"]
    elif term_length == 7:
        return rates["long_term"]
    else:  # Default to medium term (5 laps)
        return rates["medium_term"]
```

## Home Equity Line of Credit (HELOC) System

HELOCs allow players to borrow against the value of properties they own, providing better rates than standard loans.

### HELOC Features

- **Property Collateral**: Uses property value to determine maximum loan amount
- **Better Interest Rates**: Lower than standard loans due to reduced risk
- **Property Development Bonus**: Developed properties allow for higher borrowing limits
- **Standard Term**: 8-lap duration
- **Multiple HELOCs**: Players can have multiple HELOCs on different properties

### HELOC Calculations

```python
def _calculate_max_heloc_amount(self, property_obj):
    # Base HELOC is 60% of property value
    property_value = property_obj.current_price
    max_heloc = int(property_value * 0.6)
    
    # Add bonus for developed properties
    development_level = property_obj.get_development_level()
    development_bonus = development_level * 0.05  # +5% per level
    
    max_heloc = int(max_heloc * (1 + development_bonus))
    
    return max_heloc
```

## Community Fund System

The Community Fund acts as a public money pool used by game events, Free Parking bonuses, and other community-related mechanics.

### Community Fund Features

- **Fund Sources**:
  - Tax payments (Income Tax and Luxury Tax)
  - Community Chest and Chance card payments
  - Admin contributions
- **Fund Uses**:
  - Free Parking bonuses
  - Community events and improvements
  - Economic stimuli during recessions
- **Administrative Controls**: Game admins can add, withdraw, or clear funds
- **Persistence**: Fund balance persists throughout the game

### Community Fund Implementation

The Community Fund is a non-database model that stores its state in the GameState settings:

```python
class CommunityFund:
    def __init__(self, socketio=None, game_state=None):
        self.socketio = socketio
        self.game_state = game_state or GameState.query.first()
        self._funds = self.game_state.settings.get("community_fund", 0) if self.game_state else 0
    
    def add_funds(self, amount, reason="General contribution"):
        # Add funds and update game state
        self._funds += amount
        
        if self.game_state:
            settings = self.game_state.settings
            settings["community_fund"] = self._funds
            self.game_state.settings = settings
            db.session.add(self.game_state)
            db.session.commit()
            
        # Emit notification event
        if self.socketio:
            self.socketio.emit('community_fund_update', {
                "action": "add",
                "amount": amount,
                "reason": reason,
                "balance": self._funds
            })
            
        return self._funds
```

## Bankruptcy System

The Bankruptcy system handles cases where players cannot pay their debts, providing a mechanism for continuing gameplay without elimination.

### Bankruptcy Features

- **Eligibility Check**: Players can only declare bankruptcy if they cannot pay their debts even after liquidating all assets
- **Debt Forgiveness**: All loans, HELOCs, and other debts are cleared
- **Asset Forfeiture**: All properties are returned to the bank
- **Fresh Start**: Player receives the game's standard starting cash amount
- **Credit Impact**: Player's bankruptcy count increases, affecting future loan interest rates
- **CD Liquidation**: Any active CDs are withdrawn automatically

### Bankruptcy Implementation

```python
def declare_bankruptcy(self, player_id, pin):
    # [Validation code omitted]
    
    # Get player debts and assets
    loans = Loan.get_active_loans_for_player(player_id)
    helocs = Loan.get_active_helocs_for_player(player_id)
    cds = Loan.get_active_cds_for_player(player_id)
    
    # Calculate totals
    loan_total = sum(loan.calculate_current_value() for loan in loans)
    heloc_total = sum(heloc.calculate_current_value() for heloc in helocs)
    total_debt = loan_total + heloc_total
    
    # Verify bankruptcy eligibility
    properties = Property.query.filter_by(owner_id=player_id).all()
    property_value = sum(prop.current_price for prop in properties)
    
    if player.cash + property_value >= total_debt:
        return {"success": False, "error": "You have sufficient assets to pay your debts."}
    
    # Process bankruptcy
    # Clear loans, forfeit properties, reset cash, etc.
    # [Implementation code omitted]
    
    # Update bankruptcy count and emit event
    player.bankruptcy_count += 1
    db.session.add(player)
    db.session.commit()
    
    if self.socketio:
        self.socketio.emit('player_bankruptcy', {
            "player_id": player_id,
            "player_name": player.username,
            "total_debt": total_debt,
            "properties_lost": len(properties)
        })
    
    return {"success": True, "total_debt_forgiven": total_debt}
```

## Economic Impact on Financial Instruments

All financial instruments are affected by the game's economic conditions:

### Economic States and Interest Rate Effects

| Economic State | Loan Rate Modifier | CD Rate Modifier | HELOC Rate Modifier |
|----------------|-------------------:|------------------:|--------------------:|
| Recession      | -2.0%              | -2.0%             | -1.5%               |
| Normal         | +0.0%              | +0.0%             | +0.0%               |
| Growth         | +2.0%              | +1.0%             | +1.5%               |
| Boom           | +5.0%              | +3.0%             | +4.0%               |

## API Endpoints

The Financial Instruments system exposes the following API endpoints:

### Loan Endpoints

- **POST /api/finance/loan/new** - Create a new loan
  - Requires: player_id, pin, amount
- **POST /api/finance/loan/repay** - Repay a loan
  - Requires: player_id, pin, loan_id, amount (optional)

### CD Endpoints

- **POST /api/finance/cd/new** - Create a new CD
  - Requires: player_id, pin, amount, length_laps
- **POST /api/finance/cd/withdraw** - Withdraw a CD
  - Requires: player_id, pin, cd_id

### HELOC Endpoints

- **POST /api/finance/heloc/new** - Create a new HELOC
  - Requires: player_id, pin, property_id, amount

### General Finance Endpoints

- **GET /api/finance/interest-rates** - Get current interest rates
- **GET /api/finance/loans** - Get player's loans, CDs, and HELOCs
  - Requires: player_id, pin
- **POST /api/finance/bankruptcy** - Declare bankruptcy
  - Requires: player_id, pin

### Community Fund Endpoints

- **GET /api/community-fund** - Get Community Fund information
- **POST /api/admin/community-fund/add** - Admin route to add funds
  - Requires: admin_key, amount, reason (optional)
- **POST /api/admin/community-fund/withdraw** - Admin route to withdraw funds
  - Requires: admin_key, amount, reason (optional)
- **POST /api/admin/community-fund/clear** - Admin route to clear all funds
  - Requires: admin_key, reason (optional)

## Socket Events

The Financial Instruments system emits the following socket events:

- **loan_created** - New loan created
- **loan_repaid** - Loan repayment made
- **cd_created** - New CD created
- **cd_withdrawn** - CD withdrawn
- **heloc_created** - New HELOC created
- **player_bankruptcy** - Player declared bankruptcy
- **community_fund_update** - Community Fund balance changed

## Integration with Other Systems

The Financial Instruments system integrates with several other Pi-nopoly systems:

- **Property System**: 
  - HELOCs are directly tied to property ownership and values
  - Property development level affects HELOC borrowing limits
  - Property forfeiture during bankruptcy

- **Event System**: 
  - Economic events affect interest rates for all financial instruments
  - Natural disasters may trigger loans for repairs

- **Special Spaces**: 
  - Tax spaces contribute to the Community Fund
  - Chance and Community Chest cards may interact with loans and the fund

- **Auction System**: 
  - Players can use loans to participate in auctions
  - Foreclosure auctions can occur when loans aren't repaid

- **Player System**: 
  - Players' financial status affects loan eligibility
  - Bankruptcy history tracked in player model

## Database Model

All loans, CDs, and HELOCs use a single `Loan` model with a `loan_type` field to differentiate:

```python
class Loan(db.Model):
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    start_lap = db.Column(db.Integer, nullable=False)
    length_laps = db.Column(db.Integer, nullable=False)
    loan_type = db.Column(db.String(20), nullable=False, default="loan")  # "loan", "cd", "heloc"
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)  # For HELOC
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    original_interest_rate = db.Column(db.Float, nullable=True)
    outstanding_balance = db.Column(db.Integer, nullable=False)
```

## Future Enhancements

Planned enhancements to the Financial Instruments system include:

1. **Variable Interest Rates**: Rates that change dynamically during gameplay
2. **Loan Trading**: Allow players to buy/sell loans from each other
3. **Investment Portfolios**: Advanced investment options beyond CDs
4. **Tax Evasion Mechanics**: Option to under-report income with risk of audit
5. **Crime System Integration**: Financial penalties for theft and other crimes

## Alignment with Game Design Document

This implementation aligns with Section 3.3 of the game design document, which outlines the following financial instruments:

- **Line of credit**: Implemented as loans with dynamic interest rates
- **CDs**: Implemented with 3, 5, and 7 lap options
- **HELOCs**: Implemented with property value-based limits
- **Community Fund**: Implemented for public money management

The current implementation focuses on the core mechanics as specified in the design document with some enhancements for better gameplay. 