### 14.7 Event & Disaster System

Pi-nopoly implements a dynamic event system that periodically introduces unexpected situations affecting gameplay.

```python
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
                "rate_modifier": 0.03
            },
            "interest_rate_cut": {
                "title": "Interest Rate Cut",
                "description": "The central bank has cut interest rates! All loan interest rates decrease by 2%.",
                "type": "economic",
                "severity": "positive",
                "action": "interest_rate_change",
                "rate_modifier": -0.02
            },
            
            # Property events
            "housing_shortage": {
                "title": "Housing Shortage",
                "description": "A housing shortage has hit the city! All improved properties generate 20% more rent.",
                "type": "property",
                "severity": "positive_owners",
                "action": "improved_property_rent_change",
                "rent_modifier": 1.2
            },
            "property_tax": {
                "title": "Property Tax Assessment",
                "description": "The city has imposed a new property tax! All property owners pay 10% of their property value.",
                "type": "property",
                "severity": "negative",
                "action": "property_tax",
                "tax_rate": 0.1
            },
            "renovation_grants": {
                "title": "Renovation Grants",
                "description": "The government is offering renovation grants! Property improvements cost 30% less.",
                "type": "property",
                "severity": "positive",
                "action": "improvement_cost_change",
                "cost_modifier": 0.7
            },
            "infrastructure_project": {
                "title": "Infrastructure Project",
                "description": "A new infrastructure project has begun! Properties in one random group increase in value by 25%.",
                "type": "property",
                "severity": "mixed",
                "action": "group_value_change",
                "value_modifier": 1.25
            },
            
            # Natural disasters
            "hurricane": {
                "title": "Hurricane Warning",
                "description": "A hurricane has hit the city! All improved properties must pay for repairs.",
                "type": "disaster",
                "severity": "negative",
                "action": "property_repair_cost",
                "cost_per_improvement": 50
            },
            "earthquake": {
                "title": "Earthquake",
                "description": "An earthquake has damaged properties! Random properties lose improvements.",
                "type": "disaster",
                "severity": "negative",
                "action": "random_improvement_loss",
                "affected_count": 3
            },
            "flood": {
                "title": "Flood",
                "description": "A flood has damaged low-value properties! Brown and light blue properties lose value.",
                "type": "disaster",
                "severity": "negative",
                "action": "specific_group_damage",
                "affected_groups": ["brown", "light_blue"],
                "value_modifier": 0.8
            },
            
            # Community events
            "charity_fundraiser": {
                "title": "Charity Fundraiser",
                "description": "A charity event is being held! All players donate $50 to the Community Fund.",
                "type": "community",
                "severity": "mixed",
                "action": "all_player_payment",
                "amount": 50,
                "destination": "community_fund"
            },
            "stimulus_package": {
                "title": "Government Stimulus",
                "description": "The government has issued a stimulus package! Each player receives $100.",
                "type": "community",
                "severity": "positive",
                "action": "all_player_payment",
                "amount": -100,  # Negative means players receive
                "destination": "players"
            },
            "tax_amnesty": {
                "title": "Tax Amnesty",
                "description": "The government has declared a tax amnesty! All suspicion scores are reduced by half.",
                "type": "community",
                "severity": "positive",
                "action": "suspicion_modifier",
                "modifier": 0.5
            },
            "bank_holiday": {
                "title": "Bank Holiday",
                "description": "It's a bank holiday! The Community Fund is distributed equally to all players.",
                "type": "community",
                "severity": "positive",
                "action": "distribute_community_fund",
                "percentage": 0.7  # 70% of fund is distributed
            }
        }
    
    def check_for_event(self):
        """Check if an event should trigger"""
        # Get game state
        game_state = GameState.query.first()
        current_lap = game_state.current_lap
        
        # Check cooldown
        if current_lap - self.last_event_lap < self.event_cooldown:
            return None
        
        # Check probability
        import random
        if random.random() > self.event_probability:
            return None
        
        # Select random event
        event_id = random.choice(list(self.events.keys()))
        event = self.events[event_id]
        
        # Process event
        result = self._process_event(event_id, event)
        
        # Update last event lap
        self.last_event_lap = current_lap
        
        return result
    
    def trigger_specific_event(self, event_id):
        """Admin function to trigger a specific event"""
        if event_id not in self.events:
            return {
                "success": False,
                "error": f"Event not found: {event_id}"
            }
        
        event = self.events[event_id]
        return self._process_event(event_id, event)
    
    def _process_event(self, event_id, event):
        """Process a game event"""
        action = event.get("action")
        
        # Process based on action type
        if action == "property_value_change":
            result = self._handle_property_value_change(event)
        elif action == "interest_rate_change":
            result = self._handle_interest_rate_change(event)
        elif action == "improved_property_rent_change":
            result = self._handle_improved_property_rent_change(event)
        elif action == "property_tax":
            result = self._handle_property_tax(event)
        elif action == "improvement_cost_change":
            result = self._handle_improvement_cost_change(event)
        elif action == "group_value_change":
            result = self._handle_group_value_change(event)
        elif action == "property_repair_cost":
            result = self._handle_property_repair_cost(event)
        elif action == "random_improvement_loss":
            result = self._handle_random_improvement_loss(event)
        elif action == "specific_group_damage":
            result = self._handle_specific_group_damage(event)
        elif action == "all_player_payment":
            result = self._handle_all_player_payment(event)
        elif action == "suspicion_modifier":
            result = self._handle_suspicion_modifier(event)
        elif action == "distribute_community_fund":
            result = self._handle_distribute_community_fund(event)
        else:
            result = {
                "success": False,
                "error": f"Unknown action: {action}"
            }
        
        # Broadcast event
        if result.get("success", False):
            self.socketio.emit('game_event', {
                "event_id": event_id,
                "title": event.get("title"),
                "description": event.get("description"),
                "type": event.get("type"),
                "severity": event.get("severity"),
                "effects": result.get("effects", {})
            })
        
        return {
            "success": result.get("success", False),
            "event_id": event_id,
            "event": event,
            "result": result
        }
    
    def _handle_property_value_change(self, event):
        """Handle changing all property values"""
        value_modifier = event.get("value_modifier", 1.0)
        rent_modifier = event.get("rent_modifier", 1.0)
        
        # Update all properties
        properties = Property.query.all()
        for prop in properties:
            prop.current_price = int(prop.current_price * value_modifier)
            prop.current_rent = int(prop.current_rent * rent_modifier)
        
        db.session.commit()
        
        return {
            "success": True,
            "effects": {
                "value_modifier": value_modifier,
                "rent_modifier": rent_modifier,
                "affected_properties": len(properties)
            }
        }
    
    def _handle_interest_rate_change(self, event):
        """Handle changing all loan interest rates"""
        rate_modifier = event.get("rate_modifier", 0.0)
        
        # Update all active loans (except CDs)
        loans = Loan.query.filter_by(is_active=True, is_cd=False).all()
        for loan in loans:
            loan.interest_rate = max(0.01, loan.interest_rate + rate_modifier)
        
        db.session.commit()
        
        return {
            "success": True,
            "effects": {
                "rate_modifier": rate_modifier,
                "affected_loans": len(loans)
            }
        }
    
    # ... Other event handlers would be implemented similarly ...
```

### 14.8 Trading System

Pi-nopoly implements a comprehensive trading system allowing players to exchange properties, cash, and get-out-of-jail cards.

```python
class TradingSystem:
    """Manages player-to-player trades"""
    
    def __init__(self, socketio, banker):
        self.socketio = socketio
        self.banker = banker
        self.active_trades = {}  # trade_id -> trade_data
        self.next_trade_id = 1
    
    def propose_trade(self, proposer_id, receiver_id, trade_data):
        """Propose a new trade between players"""
        # Verify players
        proposer = Player.query.get(proposer_id)
        receiver = Player.query.get(receiver_id)
        
        if not proposer or not receiver:
            return {
                "success": False,
                "error": "Player not found"
            }
        
        if not proposer.in_game or not receiver.in_game:
            return {
                "success": False,
                "error": "Player not in game"
            }
        
        # Validate trade contents
        validation = self._validate_trade(proposer_id, receiver_id, trade_data)
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"]
            }
        
        # Generate trade ID
        trade_id = str(self.next_trade_id)
        self.next_trade_id += 1
        
        # Create trade object
        trade = {
            "id": trade_id,
            "proposer_id": proposer_id,
            "receiver_id": receiver_id,
            "proposer_cash": trade_data.get("proposer_cash", 0),
            "receiver_cash": trade_data.get("receiver_cash", 0),
            "proposer_properties": trade_data.get("proposer_properties", []),
            "receiver_properties": trade_data.get("receiver_properties", []),
            "proposer_jail_cards": trade_data.get("proposer_jail_cards", []),
            "receiver_jail_cards": trade_data.get("receiver_jail_cards", []),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        
        # Store trade
        self.active_trades[trade_id] = trade
        
        # Record in database
        db_trade = Trade(
            proposer_id=proposer_id,
            receiver_id=receiver_id,
            proposer_cash=trade["proposer_cash"],
            receiver_cash=trade["receiver_cash"],
            status="pending",
            details=json.dumps(trade)
        )
        db.session.add(db_trade)
        db.session.commit()
        
        # Add trade items
        for prop_id in trade["proposer_properties"]:
            item = TradeItem(
                trade_id=db_trade.id,
                property_id=prop_id,
                is_from_proposer=True
            )
            db.session.add(item)
        
        for prop_id in trade["receiver_properties"]:
            item = TradeItem(
                trade_id=db_trade.id,
                property_id=prop_id,
                is_from_proposer=False
            )
            db.session.add(item)
        
        db.session.commit()
        
        # Notify receiver
        self.socketio.emit('trade_proposed', {
            "trade_id": trade_id,
            "proposer_id": proposer_id,
            "proposer_name": proposer.username,
            "receiver_id": receiver_id,
            "receiver_name": receiver.username,
            "trade_data": trade
        }, room=f"player_{receiver_id}")
        
        # Notify proposer
        self.socketio.emit('trade_sent', {
            "trade_id": trade_id,
            "proposer_id": proposer_id,
            "proposer_name": proposer.username,
            "receiver_id": receiver_id,
            "receiver_name": receiver.username,
            "trade_data": trade
        }, room=f"player_{proposer_id}")
        
        # Check if this is a suspicious trade (for admin approval)
        if self._is_suspicious_trade(trade):
            # Flag for admin review
            db_trade.status = "flagged"
            db.session.commit()
            
            # Notify admin
            self.socketio.emit('suspicious_trade', {
                "trade_id": trade_id,
                "proposer_id": proposer_id,
                "proposer_name": proposer.username,
                "receiver_id": receiver_id,
                "receiver_name": receiver.username,
                "trade_data": trade,
                "reason": "Potentially unbalanced trade"
            }, room="admin")
        
        return {
            "success": True,
            "trade_id": trade_id,
            "trade": trade,
            "flagged": db_trade.status == "flagged"
        }
    
    def respond_to_trade(self, trade_id, player_id, accept):
        """Accept or reject a proposed trade"""
        # Verify trade exists
        if trade_id not in self.active_trades:
            db_trade = Trade.query.get(trade_id)
            if db_trade:
                # Restore from database
                self.active_trades[trade_id] = json.loads(db_trade.details)
            else:
                return {
                    "success": False,
                    "error": "Trade not found"
                }
        
        trade = self.active_trades[trade_id]
        
        # Check if player is the receiver
        if trade["receiver_id"] != player_id:
            return {
                "success": False,
                "error": "Only the receiver can respond to this trade"
            }
        
        # Check if trade is pending
        if trade["status"] != "pending":
            return {
                "success": False,
                "error": f"Trade cannot be responded to (status: {trade['status']})"
            }
        
        # Check if trade is flagged (needs admin approval)
        db_trade = Trade.query.get(trade_id)
        if db_trade.status == "flagged":
            return {
                "success": False,
                "error": "This trade requires admin approval"
            }
        
        # Check if trade has expired
        expires_at = datetime.fromisoformat(trade["expires_at"])
        if datetime.now() > expires_at:
            # Trade expired
            trade["status"] = "expired"
            db_trade.status = "expired"
            db.session.commit()
            
            # Clean up
            del self.active_trades[trade_id]
            
            return {
                "success": False,
                "error": "Trade has expired"
            }
        
        if accept:
            # Verify trade is still valid
            validation = self._validate_trade(
                trade["proposer_id"], 
                trade["receiver_id"], 
                {
                    "proposer_cash": trade["proposer_cash"],
                    "receiver_cash": trade["receiver_cash"],
                    "proposer_properties": trade["proposer_properties"],
                    "receiver_properties": trade["receiver_properties"],
                    "proposer_jail_cards": trade["proposer_jail_cards"],
                    "receiver_jail_cards": trade["receiver_jail_cards"]
                }
            )
            
            if not validation["valid"]:
                # Trade no longer valid
                trade["status"] = "invalid"
                db_trade.status = "invalid"
                db.session.commit()
                
                # Clean up
                del self.active_trades[trade_id]
                
                return {
                    "success": False,
                    "error": validation["error"]
                }
            
            # Execute the trade
            result = self._execute_trade(trade)
            
            if result["success"]:
                # Update status
                trade["status"] = "completed"
                trade["updated_at"] = datetime.now().isoformat()
                db_trade.status = "completed"
                db.session.commit()
                
                # Notify both players
                self.socketio.emit('trade_completed', {
                    "trade_id": trade_id,
                    "trade_data": trade,
                    "result": result
                }, rooms=[f"player_{trade['proposer_id']}", f"player_{trade['receiver_id']}"])
                
                # Notify all players (for board updates)
                self.socketio.emit('trade_completed_public', {
                    "trade_id": trade_id,
                    "proposer_id": trade["proposer_id"],
                    "receiver_id": trade["receiver_id"],
                    "property_changes": result.get("property_changes", [])
                })
                
                # Clean up
                del self.active_trades[trade_id]
                
                return {
                    "success": True,
                    "trade_id": trade_id,
                    "status": "completed",
                    "result": result
                }
            else:
                # Trade execution failed
                trade["status"] = "failed"
                trade["updated_at"] = datetime.now().isoformat()
                db_trade.status = "failed"
                db.session.commit()
                
                # Clean up
                del self.active_trades[trade_id]
                
                return {
                    "success": False,
                    "error": result.get("error", "Trade execution failed"),
                    "trade_id": trade_id
                }
        else:
            # Reject the trade
            trade["status"] = "rejected"
            trade["updated_at"] = datetime.now().isoformat()
            db_trade.status = "rejected"
            db.session.commit()
            
            # Notify proposer
            self.socketio.emit('trade_rejected', {
                "trade_id": trade_id,
                "trade_data": trade
            }, room=f"player_{trade['proposer_id']}")
            
            # Clean up
            del self.active_trades[trade_id]
            
            return {
                "success": True,
                "trade_id": trade_id,
                "status": "rejected"
            }
    
    def admin_approve_trade(self, trade_id):
        """Admin approves a flagged trade"""
        # Verify trade exists
        db_trade = Trade.query.get(trade_id)
        if not db_trade or db_trade.status != "flagged":
            return {
                "success": False,
                "error": "Flagged trade not found"
            }
        
        # Update status
        db_trade.status = "pending"
        db.session.commit()
        
        # Update in-memory trade if exists
        if trade_id in self.active_trades:
            self.active_trades[trade_id]["status"] = "pending"
        else:
            # Restore from database
            self.active_trades[trade_id] = json.loads(db_trade.details)
        
        # Notify players
        self.socketio.emit('trade_approved_by_admin', {
            "trade_id": trade_id,
            "message": "Trade has been approved by admin and is now pending acceptance"
        }, rooms=[f"player_{db_trade.proposer_id}", f"player_{db_trade.receiver_id}"])
        
        return {
            "success": True,
            "trade_id": trade_id,
            "status": "pending"
        }
    
    def _validate_trade(self, proposer_id, receiver_id, trade_data):
        """Validate if a trade is possible"""
        # Get players
        proposer = Player.query.get(proposer_id)
        receiver = Player.query.get(receiver_id)
        
        if not proposer or not receiver:
            return {"valid": False, "error": "Player not found"}
        
        # Check cash amounts
        proposer_cash = trade_data.get("proposer_cash", 0)
        receiver_cash = trade_data.get("receiver_cash", 0)
        
        if proposer_cash < 0 or receiver_cash < 0:
            return {"valid": False, "error": "Cash amounts cannot be negative"}
        
        if proposer_cash > proposer.cash:
            return {"valid": False, "error": "Proposer doesn't have enough cash"}
        
        if receiver_cash > receiver.cash:
            return {"valid": False, "error": "Receiver doesn't have enough cash"}
        
        # Check properties
        proposer_properties = trade_data.get("proposer_properties", [])
        receiver_properties = trade_data.get("receiver_properties", [])
        
        # Verify proposer owns all properties they're offering
        for prop_id in proposer_properties:
            prop = Property.query.get(prop_id)
            if not prop:
                return {"valid": False, "error": f"Property {prop_id} not found"}
            
            if prop.owner_id != proposer_id:
                return {"valid": False, "error": f"Proposer doesn't own property {prop.name}"}
            
            if prop.has_lien:
                return {"valid": False, "error": f"Property {prop.name} has a lien and cannot be traded"}
        
        # Verify receiver owns all properties they're offering
        for prop_id in receiver_properties:
            prop = Property.query.get(prop_id)
            if not prop:
                return {"valid": False, "error": f"Property {prop_id} not found"}
            
            if prop.owner_id != receiver_id:
                return {"valid": False, "error": f"Receiver doesn't own property {prop.name}"}
            
            if prop.has_lien:
                return {"valid": False, "error": f"Property {prop.name} has a lien and cannot be traded"}
        
        # Check jail cards
        proposer_jail_cards = trade_data.get("proposer_jail_cards", [])
        receiver_jail_cards = trade_data.get("receiver_jail_cards", [])
        
        # Verify proposer owns all jail cards they're offering
        for card_id in proposer_jail_cards:
            card = JailCard.query.get(card_id)
            if not card:
                return {"valid": False, "error": f"Jail card {card_id} not found"}
            
            if card.player_id != proposer_id or card.used:
                return {"valid": False, "error": "Proposer doesn't own this jail card"}
        
        # Verify receiver owns all jail cards they're offering
        for card_id in receiver_jail_cards:
            card = JailCard.query.get(card_id)
            if not card:
                return {"valid": False, "error": f"Jail card {card_id} not found"}
            
            if card.player_id != receiver_id or card.used:
                return {"valid": False, "error": "Receiver doesn't own this jail card"}
        
        return {"valid": True}
    
    def _is_suspicious_trade(self, trade):
        """Check if a trade seems suspicious and should be flagged for admin review"""
        # Calculate value of what proposer is giving
        proposer_giving_value = trade["proposer_cash"]
        
        for prop_id in trade["proposer_properties"]:
            prop = Property.query.get(prop_id)
            if prop:
                proposer_giving_value += prop.current_price
        
        # Calculate value of what receiver is giving
        receiver_giving_value = trade["receiver_cash"]
        
        for prop_id in trade["receiver_properties"]:
            prop = Property.query.get(prop_id)
            if prop:
                receiver_giving_value += prop.current_price
        
        # Check for significantly unbalanced trades
        if proposer_giving_value > 0 and receiver_giving_value > 0:
            ratio = max(proposer_giving_value, receiver_giving_value) / min(proposer_giving_value, receiver_giving_value)
            
            # Flag if one side is giving 3x more value than the other
            if ratio > 3.0:
                return True
        
        # Flag if one side is giving something for nothing
        if (proposer_giving_value > 0 and receiver_giving_value == 0) or \
           (receiver_giving_value > 0 and proposer_giving_value == 0):
            return True
        
        # Flag if both players are bots (potential collusion)
        proposer = Player.query.get(trade["proposer_id"])
        receiver = Player.query.get(trade["receiver_id"])
        
        if proposer and receiver and proposer.bot_type and receiver.bot_type:
            return True
        
        return False
    
    def _execute_trade(self, trade):
        """Execute an accepted trade"""
        try:
            # Get players
            proposer = Player.query.get(trade["proposer_id"])
            receiver = Player.query.get(trade["receiver_id"])
            
            if not proposer or not receiver:
                return {"success": False, "error": "Player not found"}
            
            # Exchange cash
            proposer.cash -= trade["proposer_cash"]
            proposer.cash += trade["receiver_cash"]
            
            receiver.cash -= trade["receiver_cash"]
            receiver.cash += trade["proposer_cash"]
            
            # Track property changes for response
            property_changes = []
            
            # Transfer proposer's properties to receiver
            for prop_id in trade["proposer_properties"]:
                prop = Property.query.get(prop_id)
                if prop and prop.owner_id == proposer.id:
                    prop.owner_id = receiver.id
                    property_changes.append({
                        "property_id": prop.id,
                        "property_name": prop.name,
                        "from_player_id": proposer.id,
                        "to_player_id": receiver.id
                    })
            
            # Transfer receiver's properties to proposer
            for prop_id in trade["receiver_properties"]:
                prop = Property.query.get(prop_id)
                if prop and prop.owner_id == receiver.id:
                    prop.owner_id = proposer.id
                    property_changes.append({
                        "property_id": prop.id,
                        "property_name": prop.name,
                        "from_player_id": receiver.id,
                        "to_player_id": proposer.id
                    })
            
            # Transfer proposer's jail cards to receiver
            for card_id in trade["proposer_jail_cards"]:
                card = JailCard.query.get(card_id)
                if card and card.player_id == proposer.id and not card.used:
                    card.player_id = receiver.id
            
            # Transfer receiver's jail cards to proposer
            for card_id in trade["receiver_jail_cards"]:
                card = JailCard.query.get(card_id)
                if card and card.player_id == receiver.id and not card.used:
                    card.player_id = proposer.id
            
            # Create transaction record
            cash_transaction = None
            if trade["proposer_cash"] > 0 or trade["receiver_cash"] > 0:
                net_amount = trade["proposer_cash"] - trade["receiver_cash"]
                
                if net_amount != 0:
                    from_player_id = proposer.id if net_amount > 0 else receiver.id
                    to_player_id = receiver.id if net_amount > 0 else proposer.id
                    
                    cash_transaction = Transaction(
                        from_player_id=from_player_id,
                        to_player_id=to_player_id,
                        amount=abs(net_amount),
                        transaction_type="trade_cash",
                        description=f"Cash exchange in trade {trade['id']}"
                    )
                    db.session.add(cash_transaction)
            
            # Create property transaction records
            for change in property_changes:
                property_transaction = Transaction(
                    from_player_id=change["from_player_id"],
                    to_player_id=change["to_player_id"],
                    amount=0,  # No cash directly involved
                    transaction_type="trade_property",
                    property_id=change["property_id"],
                    description=f"Property {change['property_name']} exchanged in trade {trade['id']}"
                )
                db.session.add(property_transaction)
            
            db.session.commit()
            
            return {
                "success": True,
                "cash_exchange": {
                    "proposer_gave": trade["proposer_cash"],
                    "receiver_gave": trade["receiver_cash"],
                    "net_amount": trade["proposer_cash"] - trade["receiver_cash"]
                },
                "property_changes": property_changes,
                "jail_card_changes": {
                    "proposer_gave": len(trade["proposer_jail_cards"]),
                    "receiver_gave": len(trade["receiver_jail_cards"])
                }
            }
        except Exception as e:
            # Roll back transaction on error
            db.session.rollback()
            return {"success": False, "error": str(e)}
```

### 14.9 Game Statistics and History System

Pi-nopoly implements a comprehensive statistics and history tracking system to enhance the replay value and provide insights into gameplay patterns.

```python
class StatisticsManager:
    """Manages game statistics and history"""
    
    def __init__(self, socketio):
        self.socketio = socketio
    
    def record_game_end(self, winner_id=None, reason="normal"):
        """Record the end of a game with statistics"""
        # Get game state
        game_state = GameState.query.first()
        
        # Calculate game duration in minutes
        start_time = game_state.start_time
        end_time = datetime.now()
        duration_minutes = (end_time - start_time).total_seconds() / 60
        
        # Collect player stats
        player_stats = []
        players = Player.query.filter_by(in_game=True).all()
        bankrupt_players = Player.query.filter_by(in_game=False).all()
        
        # Include both active and bankrupt players
        all_players = players + bankrupt_players
        
        for player in all_players:
            # Calculate property value
            property_value = 0
            property_count = 0
            properties = Property.query.filter_by(owner_id=player.id).all()
            
            for prop in properties:
                property_value += prop.current_price
                property_count += 1
            
            # Calculate net worth
            net_worth = player.cash + property_value
            
            # Get loan information
            loans_data = self._get_player_loan_data(player.id)
            
            # Get transaction history
            transaction_count, money_paid, money_received = self._get_transaction_stats(player.id)
            
            # Create player stat record
            player_stat = {
                "player_id": player.id,
                "username": player.username,
                "is_bot": player.bot_type is not None,
                "bot_type": player.bot_type,
                "is_winner": player.id == winner_id,
                "final_cash": player.cash,
                "property_value": property_value,
                "property_count": property_count,
                "net_worth": net_worth,
                "loans": loans_data,
                "transaction_count": transaction_count,
                "money_paid": money_paid,
                "money_received": money_received,
                "is_bankrupt": not player.in_game
            }
            
            player_stats.append(player_stat)
        
        # Sort by net worth (highest first)
        player_stats.sort(key=lambda x: x["net_worth"], reverse=True)
        
        # Calculate property ownership distribution
        property_distribution = self._get_property_distribution()
        
        # Calculate economic phases history
        economic_history = self._get_economic_history()
        
        # Create game history record
        game_history = GameHistory(
            winner_id=winner_id,
            end_reason=reason,
            duration_minutes=int(duration_minutes),
            total_laps=game_state.current_lap,
            player_count=len(all_players),
            bot_count=sum(1 for p in all_players if p.bot_type),
            final_inflation_state=game_state.inflation_state,
            player_stats=json.dumps(player_stats),
            property_stats=json.dumps(property_distribution),
            economic_stats=json.dumps(economic_history)
        )
        
        db.session.add(game_history)
        db.session.commit()
        
        # Broadcast game statistics to all players
        self.socketio.emit('game_statistics', {
            "game_id": game_history.id,
            "duration_minutes": int(duration_minutes),
            "total_laps": game_state.current_lap,
            "winner_id": winner_id,
            "winner_name": Player.query.get(winner_id).username if winner_id else None,
            "player_stats": player_stats,
            "property_distribution": property_distribution,
            "economic_history": economic_history
        })
        
        return {
            "success": True,
            "game_id": game_history.id,
            "player_stats": player_stats
        }
    
    def _get_player_loan_data(self, player_id):
        """Get loan statistics for a player"""
        loans = Loan.query.filter_by(player_id=player_id).all()
        
        active_loans = [l for l in loans if not l.is_cd and l.is_active]
        active_cds = [l for l in loans if l.is_cd and l.is_active]
        
        total_debt = sum(l.amount for l in active_loans)
        total_investments = sum(l.amount for l in active_cds)
        
        return {
            "active_loans": len(active_loans),
            "active_cds": len(active_cds),
            "total_loans_taken": len([l for l in loans if not l.is_cd]),
            "total_cds_created": len([l for l in loans if l.is_cd]),
            "total_debt": total_debt,
            "total_investments": total_investments
        }
    
    def _get_transaction_stats(self, player_id):
        """Get transaction statistics for a player"""
        # Outgoing money
        outgoing = Transaction.query.filter_by(from_player_id=player_id).all()
        money_paid = sum(t.amount for t in outgoing)
        
        # Incoming money
        incoming = Transaction.query.filter_by(to_player_id=player_id).all()
        money_received = sum(t.amount for t in incoming)
        
        # Total transactions
        transaction_count = len(outgoing) + len(incoming)
        
        return transaction_count, money_paid, money_received
    
    def _get_property_distribution(self):
        """Get property ownership distribution stats"""
        distribution = {}
        
        # Count properties by group and owner
        groups = db.session.query(Property.group_name).distinct().all()
        for group in groups:
            group_name = group[0]
            distribution[group_name] = {
                "properties": [],
                "owners": {}
            }
            
            properties = Property.query.filter_by(group_name=group_name).all()
            for prop in properties:
                owner_id = prop.owner_id
                owner_name = "Bank"
                if owner_id:
                    owner = Player.query.get(owner_id)
                    owner_name = owner.username if owner else "Unknown"
                
                # Add to properties list
                distribution[group_name]["properties"].append({
                    "id": prop.id,
                    "name": prop.name,
                    "owner_id": owner_id,
                    "owner_name": owner_name,
                    "price": prop.current_price,
                    "improvement_level": prop.improvement_level
                })
                
                # Count in owners dictionary
                if owner_id:
                    if owner_id not in distribution[group_name]["owners"]:
                        distribution[group_name]["owners"][owner_id] = 0
                    distribution[group_name]["owners"][owner_id] += 1
        
        return distribution
    
    def _get_economic_history(self):
        """Get economic phase history"""
        # Query phase change log from database
        phase_changes = EconomicPhaseChange.query.order_by(EconomicPhaseChange.lap_number).all()
        
        history = []
        for change in phase_changes:
            history.append({
                "lap": change.lap_number,
                "old_state": change.old_state,
                "new_state": change.new_state,
                "inflation_factor": change.inflation_factor,
                "total_cash": change.total_cash
            })
        
        return history
    
    def get_player_history(self, player_id):
        """Get gameplay history for a specific player"""
        # Find all games this player participated in
        games = GameHistory.query.filter(
            GameHistory.player_stats.like(f'%"player_id": {player_id}%')
        ).order_by(GameHistory.created_at.desc()).all()
        
        player_history = []
        for game in games:
            player_stats = json.loads(game.player_stats)
            player_data = next((p for p in player_stats if p["player_id"] == player_id), None)
            
            if player_data:
                player_history.append({
                    "game_id": game.id,
                    "date": game.created_at.isoformat(),
                    "duration_minutes": game.duration_minutes,
                    "total_laps": game.total_laps,
                    "player_count": game.player_count,
                    "is_winner": player_data["is_winner"],
                    "final_net_worth": player_data["net_worth"],
                    "final_cash": player_data["final_cash"],
                    "property_count": player_data["property_count"],
                    "rank": player_stats.index(player_data) + 1
                })
        
        # Calculate aggregate statistics
        games_played = len(player_history)
        games_won = sum(1 for g in player_history if g["is_winner"])
        win_rate = games_won / max(1, games_played)
        average_rank = sum(g["rank"] for g in player_history) / max(1, games_played)
        average_net_worth = sum(g["final_net_worth"] for g in player_history) / max(1, games_played)
        
        return {
            "player_id": player_id,
            "games_played": games_played,
            "games_won": games_won,
            "win_rate": win_rate,
            "average_rank": average_rank,
            "average_net_worth": average_net_worth,
            "game_history": player_history
        }
```

### 14.10 Game Timer System

Pi-nopoly implements a flexible timer system to keep games moving and allow for timed games.

```python
class GameTimerSystem:
    """Manages various game timers and turn limits"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.turn_timers = {}  # player_id -> timer_data
        self.game_timer = None  # For whole game countdown
    
    def start_turn_timer(self, player_id, seconds):
        """Start a timer for a player's turn"""
        # Cancel any existing timer for this player
        self.cancel_turn_timer(player_id)
        
        # Create new timer
        timer_data = {
            "player_id": player_id,
            "start_time": datetime.now(),
            "duration": seconds,
            "remaining": seconds,
            "timer_thread": None,
            "warning_sent": False
        }
        
        # Start timer thread
        timer_thread = threading.Thread(
            target=self._turn_timer_tick,
            args=(player_id,)
        )
        timer_thread.daemon = True
        timer_thread.start()
        
        timer_data["timer_thread"] = timer_thread
        self.turn_timers[player_id] = timer_data
        
        # Notify player
        self.socketio.emit('turn_timer_started', {
            "player_id": player_id,
            "seconds": seconds
        }, room=f"player_{player_id}")
        
        return {
            "success": True,
            "player_id": player_id,
            "seconds": seconds
        }
    
    def _turn_timer_tick(self, player_id):
        """Background thread for turn timer"""
        while player_id in self.turn_timers:
            timer_data = self.turn_timers[player_id]
            elapsed = (datetime.now() - timer_data["start_time"]).total_seconds()
            remaining = max(0, timer_data["duration"] - elapsed)
            timer_data["remaining"] = remaining
            
            # Send warning at 10 seconds
            if remaining <= 10 and not timer_data["warning_sent"]:
                self.socketio.emit('turn_timer_warning', {
                    "player_id": player_id,
                    "seconds_remaining": int(remaining)
                }, room=f"player_{player_id}")
                timer_data["warning_sent"] = True
            
            # Check if timer expired
            if remaining <= 0:
                self._handle_turn_timeout(player_id)
                break
            
            # Update every second
            if int(remaining) % 5 == 0 or remaining <= 10:
                self.socketio.emit('turn_timer_update', {
                    "player_id": player_id,
                    "seconds_remaining": int(remaining)
                }, room=f"player_{player_id}")
            
            time.sleep(1)
    
    def _handle_turn_timeout(self, player_id):
        """Handle a player's turn timing out"""
        # Remove timer
        if player_id in self.turn_timers:
            del self.turn_timers[player_id]
        
        # Get game state
        game_state = GameState.query.first()
        
        # Check if it's still this player's turn
        if game_state.current_player_id != player_id:
            return  # No longer their turn
        
        # Force end turn
        self.socketio.emit('turn_timeout', {
            "player_id": player_id,
            "message": "Your turn timed out and will be ended automatically"
        }, room=f"player_{player_id}")
        
        # Notify all players
        self.socketio.emit('player_turn_timeout', {
            "player_id": player_id
        })
        
        # End the turn (this would call your turn engine's end_turn method)
        from game_logic.turn import end_turn
        end_turn(player_id, force=True)
    
    def cancel_turn_timer(self, player_id):
        """Cancel a player's turn timer"""
        if player_id in self.turn_timers:
            # No need to stop thread, it will exit when checking for player_id
            del self.turn_timers[player_id]
            return True
        return False
    
    def get_remaining_time(self, player_id):
        """Get remaining time for a player's turn"""
        if player_id in self.turn_timers:
            return int(self.turn_timers[player_id]["remaining"])
        return None
    
    def start_game_timer(self, minutes):
        """Start a timer for the whole game"""
        # Cancel any existing game timer
        self.cancel_game_timer()
        
        # Convert to seconds
        seconds = minutes * 60
        
        # Create game timer
        self.game_timer = {
            "start_time": datetime.now(),
            "duration": seconds,
            "remaining": seconds,
            "timer_thread": None,
            "warnings_sent": set()
        }
        
        # Start timer thread
        timer_thread = threading.Thread(
            target=self._game_timer_tick
        )
        timer_thread.daemon = True
        timer_thread.start()
        
        self.game_timer["timer_thread"] = timer_thread
        
        # Notify all players
        self.socketio.emit('game_timer_started', {
            "minutes": minutes,
            "seconds": seconds
        })
        
        return {
            "success": True,
            "minutes": minutes,
            "seconds": seconds
        }
    
    def _game_timer_tick(self):
        """Background thread for game timer"""
        if not self.game_timer:
            return
        
        while self.game_timer:
            elapsed = (datetime.now() - self.game_timer["start_time"]).total_seconds()
            remaining = max(0, self.game_timer["duration"] - elapsed)
            self.game_timer["remaining"] = remaining
            
            # Convert to minutes for warnings
            remaining_minutes = int(remaining / 60)
            
            # Send warnings at specific times
            warning_times = [60, 30, 15, 10, 5, 2, 1]  # Minutes
            for warning_time in warning_times:
                if remaining_minutes == warning_time and warning_time not in self.game_timer["warnings_sent"]:
                    self.socketio.emit('game_timer_warning', {
                        "minutes_remaining": warning_time
                    })
                    self.game_timer["warnings_sent"].add(warning_time)
            
            # Check if timer expired
            if remaining <= 0:
                self._handle_game_timeout()
                break
            
            # Update every minute
            if int(remaining) % 60 == 0:
                self.socketio.emit('game_timer_update', {
                    "minutes_remaining": remaining_minutes,
                    "seconds_remaining": int(remaining)
                })
            
            time.sleep(1)
    
    def _handle_game_timeout(self):
        """Handle the game timer expiring"""
        # Clear game timer
        self.game_timer = None
        
        # Notify all players
        self.socketio.emit('game_timer_expired', {
            "message": "Game time has expired"
        })
        
        # End the game (this would call your game engine's end_game method)
        from game_logic.game import end_game
        end_game(reason="time_limit")
    
    def cancel_game_timer(self):
        """Cancel the game timer"""
        if self.game_timer:
            # No need to stop thread, it will exit when checking game_timer
            self.game_timer = None
            return True
        return False
    
    def get_game_remaining_time(self):
        """Get remaining time for the game timer"""
        if self.game_timer:
            return {
                "seconds": int(self.game_timer["remaining"]),
                "minutes": int(self.game_timer["remaining"] / 60)
            }
        return None
```

### 14.11 Chat & Social Interaction System

Pi-nopoly implements a built-in communication system to enable player interaction during gameplay.

```python
class ChatSystem:
    """Manages in-game chat and player communication"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.chat_history = {}  # game_id -> list of messages
        self.max_history = 100  # Maximum messages to retain per game
        self.emoji_reactions = ["👍", "👎", "😂", "😮", "😢", "🎉", "💰", "🏠", "🎲", "🚓"]
    
    def send_message(self, player_id, message_text, is_private=False, recipient_id=None):
        """Send a chat message"""
        # Validate player
        player = Player.query.get(player_id)
        if not player:
            return {
                "success": False,
                "error": "Player not found"
            }
        
        # Check message length
        if not message_text or len(message_text) > 500:
            return {
                "success": False,
                "error": "Invalid message length"
            }
        
        # Create message object
        message = {
            "id": str(uuid.uuid4()),
            "player_id": player_id,
            "player_name": player.username,
            "text": message_text,
            "timestamp": datetime.now().isoformat(),
            "is_private": is_private,
            "recipient_id": recipient_id,
            "reactions": {}
        }
        
        # Add to history
        game_state = GameState.query.first()
        game_id = game_state.id
        
        if game_id not in self.chat_history:
            self.chat_history[game_id] = []
        
        self.chat_history[game_id].append(message)
        
        # Trim history if needed
        if len(self.chat_history[game_id]) > self.max_history:
            self.chat_history[game_id] = self.chat_history[game_id][-self.max_history:]
        
        # Broadcast message
        if is_private and recipient_id:
            # Private message
            recipient = Player.query.get(recipient_id)
            if recipient:
                self.socketio.emit('chat_message', message, rooms=[
                    f"player_{player_id}",  # Sender
                    f"player_{recipient_id}"  # Recipient
                ])
                
                # Also send to admin
                self.socketio.emit('chat_message', message, room="admin")
        else:
            # Public message
            self.socketio.emit('chat_message', message)
        
        return {
            "success": True,
            "message_id": message["id"]
        }
    
    def add_reaction(self, player_id, message_id, emoji):
        """Add an emoji reaction to a message"""
        # Validate player
        player = Player.query.get(player_id)
        if not player:
            return {
                "success": False,
                "error": "Player not found"
            }
        
        # Validate emoji
        if emoji not in self.emoji_reactions:
            return {
                "success": False,
                "error": "Invalid emoji"
            }
        
        # Find message
        game_state = GameState.query.first()
        game_id = game_state.id
        
        if game_id not in self.chat_history:
            return {
                "success": False,
                "error": "No chat history"
            }
        
        message = None
        for msg in self.chat_history[game_id]:
            if msg["id"] == message_id:
                message = msg
                break
        
        if not message:
            return {
                "success": False,
                "error": "Message not found"
            }
        
        # Add or update reaction
        if emoji not in message["reactions"]:
            message["reactions"][emoji] = []
        
        # Check if player already reacted with this emoji
        if player_id in message["reactions"][emoji]:
            # Remove reaction (toggle)
            message["reactions"][emoji].remove(player_id)
            if not message["reactions"][emoji]:
                del message["reactions"][emoji]
        else:
            # Add reaction
            message["reactions"][emoji].append(player_id)
        
        # Broadcast reaction update
        self.socketio.emit('chat_reaction', {
            "message_id": message_id,
            "reactions": message["reactions"]
        })
        
        return {
            "success": True,
            "message_id": message_id,
            "reactions": message["reactions"]
        }
    
    def get_chat_history(self, player_id, limit=50):
        """Get recent chat history"""
        # Validate player
        player = Player.query.get(player_id)
        if not player:
            return {
                "success": False,
                "error": "Player not found"
            }
        
        # Get history
        game_state = GameState.query.first()
        game_id = game_state.id
        
        if game_id not in self.chat_history:
            return {
                "success": True,
                "messages": []
            }
        
        # Filter private messages
        messages = []
        for msg in self.chat_history[game_id]:
            if not msg["is_private"] or msg["player_id"] == player_id or msg["recipient_id"] == player_id:
                messages.append(msg)
        
        # Return most recent messages up to limit
        return {
            "success": True,
            "messages": messages[-limit:]
        }
    
    def send_trade_message(self, trade_id, proposer_id, receiver_id):
        """Send an automated message about a trade proposal"""
        # Get players
        proposer = Player.query.get(proposer_id)
        receiver = Player.query.get(receiver_id)
        
        if not proposer or not receiver:
            return
        
        # Create message text
        message_text = f"📝 Trade Proposal: {proposer.username} has sent a trade offer to {receiver.username}."
        
        # Create system message
        message = {
            "id": str(uuid.uuid4()),
            "player_id": None,  # System message
            "player_name": "System",
            "text": message_text,
            "timestamp": datetime.now().isoformat(),
            "is_private": False,
            "recipient_id": None,
            "reactions": {},
            "is_system": True,
            "trade_id": trade_id
        }
        
        # Add to history
        game_state = GameState.query.first()
        game_id = game_state.id
        
        if game_id not in self.chat_history:
            self.chat_history[game_id] = []
        
        self.chat_history[game_id].append(message)
        
        # Broadcast message
        self.socketio.emit('chat_message', message)
    
    def send_system_message(self, message_text, is_private=False, recipient_id=None):
        """Send a system message"""
        # Create system message
        message = {
            "id": str(uuid.uuid4()),
            "player_id": None,  # System message
            "player_name": "System",
            "text": message_text,
            "timestamp": datetime.now().isoformat(),
            "is_private": is_private,
            "recipient_id": recipient_id,
            "reactions": {},
            "is_system": True
        }
        
        # Add to history
        game_state = GameState.query.first()
        game_id = game_state.id
        
        if game_id not in self.chat_history:
            self.chat_history[game_id] = []
        
        self.chat_history[game_id].append(message)
        
        # Broadcast message
        if is_private and recipient_id:
            # Private system message
            self.socketio.emit('chat_message', message, room=f"player_{recipient_id}")
        else:
            # Public system message
            self.socketio.emit('chat_message', message)
```

### 14.12 Spectator Mode

Pi-nopoly implements a spectator mode to allow non-players to watch the game.

```python
class SpectatorSystem:
    """Manages spectators who are watching the game"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.spectators = {}  # spectator_id -> spectator_data
        self.next_spectator_id = 1
    
    def add_spectator(self, username=None, connection_id=None):
        """Add a new spectator to the game"""
        spectator_id = str(self.next_spectator_id)
        self.next_spectator_id += 1
        
        # Generate username if needed
        if not username:
            username = f"Spectator {spectator_id}"
        
        # Create spectator data
        spectator = {
            "id": spectator_id,
            "username": username,
            "connection_id": connection_id,
            "joined_at": datetime.now().isoformat()
        }
        
        # Store spectator
        self.spectators[spectator_id] = spectator
        
        # Add to spectator room
        if connection_id:
            self.socketio.server.enter_room(connection_id, "spectators")
        
        # Notify admin
        self.socketio.emit('spectator_joined', {
            "spectator_id": spectator_id,
            "username": username,
            "spectator_count": len(self.spectators)
        }, room="admin")
        
        # Send game state to new spectator
        self._send_game_state(spectator_id)
        
        return {
            "success": True,
            "spectator_id": spectator_id,
            "username": username
        }
    
    def remove_spectator(self, spectator_id):
        """Remove a spectator from the game"""
        if spectator_id not in self.spectators:
            return {
                "success": False,
                "error": "Spectator not found"
            }
        
        spectator = self.spectators[spectator_id]
        
        # Remove from spectator room
        if spectator["connection_id"]:
            self.socketio.server.leave_room(spectator["connection_id"], "spectators")
        
        # Remove from storage
        del self.spectators[spectator_id]
        
        # Notify admin
        self.socketio.emit('spectator_left', {
            "spectator_id": spectator_id,
            "username": spectator["username"],
            "spectator_count": len(self.spectators)
        }, room="admin")
        
        return {
            "success": True,
            "spectator_id": spectator_id
        }
    
    def get_spectators(self):
        """Get list of current spectators"""
        return {
            "success": True,
            "spectator_count": len(self.spectators),
            "spectators": list(self.spectators.values())
        }
    
    def send_message_to_spectators(self, message):
        """Send a message to all spectators"""
        self.socketio.emit('spectator_message', {
            "message": message,
            "timestamp": datetime.now().isoformat()
        }, room="spectators")
        
        return {
            "success": True,
            "spectator_count": len(self.spectators)
        }
    
    def _send_game_state(self, spectator_id):
        """Send current game state to a spectator"""
        if spectator_id not in self.spectators:
            return
        
        spectator = self.spectators[spectator_id]
        
        # Get game state
        game_state = GameState.query.first()
        
        # Get player data
        players = Player.query.filter_by(in_game=True).all()
        player_data = []
        
        for player in players:
            # Calculate net worth
            net_worth = player.cash
            properties = Property.query.filter_by(owner_id=player.id).all()
            property_value = sum(p.current_price for p in properties)
            net_worth += property_value
            
            player_data.append({
                "id": player.id,
                "username": player.username,
                "position": player.position,
                "cash": player.cash,
                "net_worth": net_worth,
                "is_bot": player.bot_type is not None,
                "bot_type": player.bot_type,
                "jail_status": player.jail_status,
                "property_count": len(properties)
            })
        
        # Get property data
        properties = Property.query.all()
        property_data = []
        
        for prop in properties:
            owner = Player.query.get(prop.owner_id) if prop.owner_id else None
            
            property_data.append({
                "id": prop.id,
                "name": prop.name,
                "position": prop.position,
                "group": prop.group_name,
                "price": prop.current_price,
                "rent": prop.current_rent,
                "owner_id": prop.owner_id,
                "owner_name": owner.username if owner else None,
                "improvement_level": prop.improvement_level,
                "has_lien": prop.has_lien
            })
        
        # Prepare game state data
        state_data = {
            "current_player_id": game_state.current_player_id,
            "current_lap": game_state.current_lap,
            "inflation_state": game_state.inflation_state,
            "inflation_factor": game_state.inflation_factor,
            "community_fund": game_state.community_fund,
            "players": player_data,
            "properties": property_data
        }
        
        # Send to spectator
        self.socketio.emit('game_state_update', state_data, room=f"spectator_{spectator_id}")
```

### 14.13 Notification Center

Pi-nopoly implements a comprehensive notification system to keep players informed of game events.

```python
class NotificationCenter:
    """Manages in-game notifications for players"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.notifications = {}  # player_id -> list of notifications
        self.max_notifications = 50  # Maximum notifications to retain per player
    
    def send_notification(self, player_id, message, type="info", data=None, broadcast=False):
        """Send a notification to a player"""
        # Generate notification ID
        notification_id = str(uuid.uuid4())
        
        # Create notification object
        notification = {
            "id": notification_id,
            "player_id": player_id,
            "message": message,
            "type": type,  # "info", "success", "warning", "error", "action"
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "read": False
        }
        
        # Store notification
        if player_id not in self.notifications:
            self.notifications[player_id] = []
        
        self.notifications[player_id].append(notification)
        
        # Trim notifications if needed
        if len(self.notifications[player_id]) > self.max_notifications:
            self.notifications[player_id] = self.notifications[player_id][-self.max_notifications:]
        
        # Send to player
        self.socketio.emit('notification', notification, room=f"player_{player_id}")
        
        # Broadcast to all if requested (typically for major game events)
        if broadcast:
            # Get player name
            player = Player.query.get(player_id)
            player_name = player.username if player else "Unknown"
            
            # Create broadcast notification
            broadcast_notification = notification.copy()
            broadcast_notification["player_name"] = player_name
            
            # Send to all except the target player
            for pid in self.notifications.keys():
                if pid != player_id:
                    self.socketio.emit('broadcast_notification', broadcast_notification, room=f"player_{pid}")
        
        return {
            "success": True,
            "notification_id": notification_id
        }
    
    def mark_as_read(self, player_id, notification_id):
        """Mark a notification as read"""
        if player_id not in self.notifications:
            return {
                "success": False,
                "error": "No notifications for player"
            }
        
        # Find notification
        for notification in self.notifications[player_id]:
            if notification["id"] == notification_id:
                notification["read"] = True
                return {
                    "success": True,
                    "notification_id": notification_id
                }
        
        return {
            "success": False,
            "error": "Notification not found"
        }
    
    def mark_all_as_read(self, player_id):
        """Mark all notifications for a player as read"""
        if player_id not in self.notifications:
            return {
                "success": False,
                "error": "No notifications for player"
            }
        
        # Mark all as read
        for notification in self.notifications[player_id]:
            notification["read"] = True
        
        return {
            "success": True,
            "count": len(self.notifications[player_id])
        }
    
    def get_notifications(self, player_id, unread_only=False, limit=20):
        """Get notifications for a player"""
        if player_id not in self.notifications:
            return {
                "success": True,
                "notifications": []
            }
        
        # Filter if needed
        notifications = self.notifications[player_id]
        if unread_only:
            notifications = [n for n in notifications if not n["read"]]
        
        # Sort by timestamp (newest first)
        sorted_notifications = sorted(
            notifications,
            key=lambda n: n["timestamp"],
            reverse=True
        )
        
        # Limit results
        limited_notifications = sorted_notifications[:limit]
        
        return {
            "success": True,
            "notifications": limited_notifications,
            "total": len(notifications),
            "unread_count": len([n for n in notifications if not n["read"]])
        }
    
    def clear_notifications(self, player_id):
        """Clear all notifications for a player"""
        if player_id in self.notifications:
            self.notifications[player_id] = []
        
        return {
            "success": True
        }
    
    def send_action_notification(self, player_id, message, action_type, action_data=None, timeout=None):
        """Send a notification that requires player action"""
        data = {
            "action_type": action_type,
            "action_data": action_data,
            "timeout": timeout
        }
        
        return self.send_notification(player_id, message, type="action", data=data)
    
    def send_system_notification(self, message, type="info", broadcast=True):
        """Send a notification to all players"""
        # Get all players
        players = Player.query.filter_by(in_game=True).all()
        
        # Create system notification
        notification = {
            "id": str(uuid.uuid4()),
            "player_id": None,  # System notification
            "message": message,
            "type": type,
            "timestamp": datetime.now().isoformat(),
            "is_system": True
        }
        
        # Send to all players
        for player in players:
            # Store notification
            if player.id not in self.notifications:
                self.notifications[player.id] = []
            
            player_notification = notification.copy()
            player_notification["player_id"] = player.id
            
            self.notifications[player.id].append(player_notification)
            
            # Trim notifications if needed
            if len(self.notifications[player.id]) > self.max_notifications:
                self.notifications[player.id] = self.notifications[player.id][-self.max_notifications:]
            
            # Send to player
            self.socketio.emit('notification', player_notification, room=f"player_{player.id}")
        
        # Also send to spectators and admin
        self.socketio.emit('system_notification', notification, rooms=["spectators", "admin"])
        
        return {
            "success": True,
            "notification_id": notification["id"]
        }
```

### 14.14 Mobile Device Optimization

Pi-nopoly implements specific optimizations for mobile devices to ensure smooth gameplay across all platforms.

```python
class MobileOptimizationManager:
    """Manages mobile-specific optimizations for Pi-nopoly"""
    
    def __init__(self):
        self.user_agents = {}  # client_id -> user agent info
        self.device_settings = {}  # client_id -> device-specific settings
    
    def register_device(self, client_id, user_agent):
        """Register a device and determine its capabilities"""
        # Parse user agent to determine device type
        is_mobile = 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent
        is_tablet = 'iPad' in user_agent or 'Tablet' in user_agent
        is_desktop = not (is_mobile or is_tablet)
        
        # Determine screen class from user agent (very simplified)
        screen_class = 'large'
        if is_mobile:
            screen_class = 'small'
        elif is_tablet:
            screen_class = 'medium'
        
        # Store device info
        self.user_agents[client_id] = {
            "user_agent": user_agent,
            "is_mobile": is_mobile,
            "is_tablet": is_tablet,
            "is_desktop": is_desktop,
            "screen_class": screen_class
        }
        
        # Create device-specific settings
        self.device_settings[client_id] = self._generate_device_settings(
            is_mobile, is_tablet, is_desktop, screen_class
        )
        
        return {
            "success": True,
            "device_info": self.user_agents[client_id],
            "device_settings": self.device_settings[client_id]
        }
    
    def _generate_device_settings(self, is_mobile, is_tablet, is_desktop, screen_class):
        """Generate device-specific settings based on device type"""
        # Default settings
        settings = {
            "ui_scale": 1.0,
            "animation_enabled": True,
            "animation_speed": 1.0,
            "data_compression": False,
            "image_quality": "high",
            "auto_refresh": True,
            "refresh_interval": 5000,  # 5 seconds
            "batch_updates": False,
            "touch_controls": is_mobile or is_tablet,
            "dice_animation": True,
            "sound_enabled": True,
            "notification_style": "popup",
            "show_tooltips": True,
            "interface_density": "normal"
        }
        
        # Adjust settings based on device type
        if is_mobile:
            settings.update({
                "ui_scale": 1.2,  # Slightly larger UI elements
                "animation_speed": 0.8,  # Slightly faster animations
                "data_compression": True,  # Reduce data usage
                "image_quality": "medium",  # Lower quality images
                "auto_refresh": False,  # Manual refresh to save data
                "batch_updates": True,  # Batch updates to reduce overhead
                "interface_density": "compact"  # More compact UI
            })
        elif is_tablet:
            settings.update({
                "ui_scale": 1.1,
                "data_compression": screen_class == "medium",  # Compress for smaller tablets
                "interface_density": "balanced"
            })
        
        return settings
    
    def get_device_settings(self, client_id):
        """Get device settings for a client"""
        if client_id not in self.device_settings:
            # Return default settings
            return self._generate_device_settings(False, False, True, 'large')
        
        return self.device_settings[client_id]
    
    def update_device_settings(self, client_id, settings):
        """Update device settings for a client"""
        if client_id not in self.device_settings:
            return {
                "success": False,
                "error": "Device not registered"
            }
        
        # Update settings
        self.device_settings[client_id].update(settings)
        
        return {
            "success": True,
            "device_settings": self.device_settings[client_id]
        }
    
    def optimize_payload(self, data, client_id):
        """Optimize a data payload for the specific device"""
        settings = self.get_device_settings(client_id)
        
        # Make a copy to avoid modifying original data
        optimized = copy.deepcopy(data)
        
        # Apply optimizations based on settings
        if settings["data_compression"]:
            # Remove unnecessary fields
            if "description" in optimized:
                optimized["desc"] = optimized["description"][:100] + "..." if len(optimized["description"]) > 100 else optimized["description"]
                del optimized["description"]
            
            # Simplify nested structures
            if "properties" in optimized and isinstance(optimized["properties"], list) and len(optimized["properties"]) > 10:
                # Only include essential property data for list views
                simplified_properties = []
                for prop in optimized["properties"]:
                    simplified_properties.append({
                        "id": prop["id"],
                        "name": prop["name"],
                        "owner_id": prop.get("owner_id"),
                        "price": prop.get("price")
                    })
                optimized["properties"] = simplified_properties
        
        # Adjust image quality
        if "image_urls" in optimized and settings["image_quality"] != "high":
            quality_suffix = "medium" if settings["image_quality"] == "medium" else "low"
            for i, url in enumerate(optimized["image_urls"]):
                optimized["image_urls"][i] = url.replace(".png", f"_{quality_suffix}.png")
        
        return optimized
```

These additional game mechanics complete the Pi-nopoly experience with:

1. **Chat & Social Interaction System** - In-game communication with emoji reactions
2. **Spectator Mode** - Non-player observation of games in progress
3. **Notification Center** - Comprehensive player notification system
4. **Mobile Device Optimization** - Tailored experience for different devices

With these additions, Pi-nopoly now provides a fully-featured modern gaming experience with all the social and quality-of-life features players expect from contemporary digital games.    def _start_auction_timer(self, auction_id):
        """Start a timer for the auction"""
        def auction_tick():
            # Check if auction still exists
            if auction_id not in self.active_auctions:
                return
            
            auction = self.active_auctions[auction_id]
            
            # Decrement timer
            auction["current_timer"] -= 1
            
            # Broadcast timer update
            if auction["current_timer"] % 5 == 0 or auction["current_timer"] <= 10:
                self.socketio.emit('auction_timer', {
                    "auction_id": auction_id,
                    "seconds_remaining": auction["current_timer"]
                })
            
            # Check if timer expired
            if auction["current_timer"] <= 0:
                self._end_auction(auction_id)
            else:
                # Schedule next tick
                threading.Timer(1.0, auction_tick).start()
        
        # Start first tick
        threading.Timer(1.0, auction_tick).start()
    
    def place_bid(self, auction_id, player_id, bid_amount):
        """Place a bid in an auction"""
        # Check if auction exists and is active
        if auction_id not in self.active_auctions:
            return {
                "success": False,
                "error": "Auction not found"
            }
        
        auction = self.active_auctions[auction_id]
        if auction["status"] != "active":
            return {
                "success": False,
                "error": "Auction is not active"
            }
        
        # Check if player is eligible
        if player_id not in auction["eligible_players"] or player_id in auction["players_passed"]:
            return {
                "success": False,
                "error": "Player not eligible to bid"
            }
        
        # Check if bid is high enough
        if bid_amount <= auction["current_bid"]:
            return {
                "success": False,
                "error": "Bid must be higher than current bid"
            }
        
        if bid_amount < auction["minimum_bid"] and auction["current_bid"] < auction["minimum_bid"]:
            return {
                "success": False,
                "error": f"First bid must be at least {auction['minimum_bid']}"
            }
        
        # Check if player has enough cash
        player = Player.query.get(player_id)
        if not player or player.cash < bid_amount:
            return {
                "success": False,
                "error": "Not enough cash to place bid"
            }
        
        # Update auction
        auction["current_bid"] = bid_amount
        auction["current_bidder"] = player_id
        
        # Record bid
        bid = {
            "player_id": player_id,
            "amount": bid_amount,
            "time": datetime.now().isoformat()
        }
        auction["bids"].append(bid)
        
        # Reset timer to 10 seconds after a new bid
        auction["current_timer"] = 10
        
        # Broadcast update
        self.socketio.emit('auction_bid', {
            "auction_id": auction_id,
            "property_id": auction["property_id"],
            "property_name": auction["property_name"],
            "player_id": player_id,
            "player_name": player.username,
            "bid_amount": bid_amount,
            "seconds_remaining": auction["current_timer"]
        })
        
        return {
            "success": True,
            "bid": bid
        }
    
    def pass_auction(self, auction_id, player_id):
        """Player passes on bidding in an auction"""
        # Check if auction exists and is active
        if auction_id not in self.active_auctions:
            return {
                "success": False,
                "error": "Auction not found"
            }
        
        auction = self.active_auctions[auction_id]
        if auction["status"] != "active":
            return {
                "success": False,
                "error": "Auction is not active"
            }
        
        # Check if player is eligible
        if player_id not in auction["eligible_players"] or player_id in auction["players_passed"]:
            return {
                "success": False,
                "error": "Player not eligible to pass"
            }
        
        # Add player to passed list
        auction["players_passed"].append(player_id)
        
        # Broadcast update
        player = Player.query.get(player_id)
        self.socketio.emit('auction_pass', {
            "auction_id": auction_id,
            "player_id": player_id,
            "player_name": player.username if player else "Unknown"
        })
        
        # Check if all players have passed
        active_bidders = [p for p in auction["eligible_players"] if p not in auction["players_passed"]]
        
        if len(active_bidders) == 0:
            # No one is bidding, end the auction
            self._end_auction(auction_id)
        elif len(active_bidders) == 1 and auction["current_bidder"] in active_bidders:
            # Only the current winning bidder is left
            self._end_auction(auction_id)
        
        return {
            "success": True
        }
    
    def _end_auction(self, auction_id):
        """End an auction and process the result"""
        if auction_id not in self.active_auctions:
            return
        
        auction = self.active_auctions[auction_id]
        auction["status"] = "completed"
        auction["end_time"] = datetime.now().isoformat()
        
        # Get property
        property_obj = Property.query.get(auction["property_id"])
        if not property_obj:
            # Something went wrong - property doesn't exist
            self.socketio.emit('auction_ended', {
                "auction_id": auction_id,
                "status": "error",
                "error": "Property not found"
            })
            del self.active_auctions[auction_id]
            return
        
        # Check if there was a winning bid
        if auction["current_bidder"] is not None:
            # Get winning player
            winner = Player.query.get(auction["current_bidder"])
            if not winner:
                # Winner doesn't exist
                self.socketio.emit('auction_ended', {
                    "auction_id": auction_id,
                    "status": "error",
                    "error": "Winning bidder not found"
                })
                del self.active_auctions[auction_id]
                return
            
            # Check if winner still has enough cash
            if winner.cash < auction["current_bid"]:
                # Winner can't afford it anymore
                self.socketio.emit('auction_ended', {
                    "auction_id": auction_id,
                    "status": "error",
                    "error": "Winning bidder cannot afford the bid",
                    "property_id": property_obj.id,
                    "property_name": property_obj.name
                })
                del self.active_auctions[auction_id]
                return
            
            # Process purchase
            winning_bid = auction["current_bid"]
            list_price = property_obj.current_price
            
            # Calculate overbid amount (for community fund)
            overbid = max(0, winning_bid - list_price)
            community_fund_amount = int(overbid * 0.1)  # 10% of overbid
            
            # Process payment
            winner.cash -= winning_bid
            property_obj.owner_id = winner.id
            db.session.commit()
            
            # Add overbid to community fund if applicable
            if community_fund_amount > 0:
                community_fund = CommunityFund.get_instance()
                community_fund.add(
                    community_fund_amount, 
                    "auction_overbid", 
                    winner.id, 
                    f"10% of overbid for {property_obj.name}"
                )
            
            # Broadcast result
            self.socketio.emit('auction_ended', {
                "auction_id": auction_id,
                "status": "sold",
                "property_id": property_obj.id,
                "property_name": property_obj.name,
                "winner_id": winner.id,
                "winner_name": winner.username,
                "winning_bid": winning_bid,
                "list_price": list_price,
                "overbid": overbid,
                "community_fund_amount": community_fund_amount
            })
        else:
            # No winning bid
            self.socketio.emit('auction_ended', {
                "auction_id": auction_id,
                "status": "no_sale",
                "property_id": property_obj.id,
                "property_name": property_obj.name
            })
        
        # Remove auction from active list
        del self.active_auctions[auction_id]
```

### 14.3 Property Improvement System

Pi-nopoly implements a property improvement system that allows players to enhance their properties to increase rent.

```python
class PropertyManager:
    """Manages property ownership and improvements"""
    
    def __init__(self, socketio, banker):
        self.socketio = socketio
        self.banker = banker
    
    def buy_property(self, player_id, property_id):
        """Purchase a property at list price"""
        # Verify property and player
        property_obj = Property.query.get(property_id)
        player = Player.query.get(player_id)
        
        if not property_obj:
            return {
                "success": False,
                "error": "Property not found"
            }
        
        if not player:
            return {
                "success": False,
                "error": "Player not found"
            }
        
        # Check if property is available
        if property_obj.owner_id is not None:
            return {
                "success": False,
                "error": "Property already owned"
            }
        
        # Check if player has enough cash
        price = property_obj.current_price
        if player.cash < price:
            return {
                "success": False,
                "error": "Not enough cash"
            }
        
        # Process purchase
        player.cash -= price
        property_obj.owner_id = player.id
        db.session.commit()
        
        # Record transaction
        transaction = Transaction(
            from_player_id=player.id,
            to_player_id=None,  # Bank
            amount=price,
            transaction_type="property_purchase",
            property_id=property_id,
            description=f"Purchase of {property_obj.name}"
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Broadcast property update
        self.socketio.emit('property_purchased', {
            "property_id": property_obj.id,
            "property_name": property_obj.name,
            "player_id": player.id,
            "player_name": player.username,
            "price": price
        })
        
        return {
            "success": True,
            "property": {
                "id": property_obj.id,
                "name": property_obj.name,
                "price": price
            },
            "player": {
                "id": player.id,
                "name": player.username,
                "cash": player.cash
            }
        }
    
    def improve_property(self, player_id, property_id):
        """Add an improvement to a property"""
        # Verify property and player
        property_obj = Property.query.get(property_id)
        player = Player.query.get(player_id)
        
        if not property_obj:
            return {
                "success": False,
                "error": "Property not found"
            }
        
        if not player:
            return {
                "success": False,
                "error": "Player not found"
            }
        
        # Check ownership
        if property_obj.owner_id != player.id:
            return {
                "success": False,
                "error": "Player does not own this property"
            }
        
        # Check if property can be improved
        if property_obj.has_lien:
            return {
                "success": False,
                "error": "Cannot improve property with a lien"
            }
        
        # Check if property is already at max improvement
        max_improvement = 1  # Only one level of improvement
        if property_obj.improvement_level >= max_improvement:
            return {
                "success": False,
                "error": "Property already at maximum improvement level"
            }
        
        # Check if player owns all properties in the group
        group_properties = Property.query.filter_by(group_name=property_obj.group_name).all()
        for prop in group_properties:
            if prop.owner_id != player.id:
                return {
                    "success": False,
                    "error": "Must own all properties in group to improve"
                }
        
        # Calculate improvement cost
        improvement_cost_factor = 0.5  # 50% of property value
        improvement_cost = int(property_obj.current_price * improvement_cost_factor)
        
        # Check if player has enough cash
        if player.cash < improvement_cost:
            return {
                "success": False,
                "error": "Not enough cash for improvement"
            }
        
        # Process improvement
        player.cash -= improvement_cost
        property_obj.improvement_level += 1
        db.session.commit()
        
        # Calculate new rent
        new_rent = self._calculate_rent(property_obj)
        
        # Record transaction
        transaction = Transaction(
            from_player_id=player.id,
            to_player_id=None,  # Bank
            amount=improvement_cost,
            transaction_type="property_improvement",
            property_id=property_id,
            description=f"Improvement of {property_obj.name}"
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Broadcast property update
        self.socketio.emit('property_improved', {
            "property_id": property_obj.id,
            "property_name": property_obj.name,
            "player_id": player.id,
            "player_name": player.username,
            "improvement_level": property_obj.improvement_level,
            "improvement_cost": improvement_cost,
            "new_rent": new_rent
        })
        
        return {
            "success": True,
            "property": {
                "id": property_obj.id,
                "name": property_obj.name,
                "improvement_level": property_obj.improvement_level,
                "new_rent": new_rent
            },
            "cost": improvement_cost,
            "player_cash": player.cash
        }
    
    def _calculate_rent(self, property_obj):
        """Calculate rent for a property based on improvements and ownership"""
        # Base rent
        base_rent = property_obj.current_rent
        rent = base_rent
        
        # Check for group bonus (owning all properties in group)
        if property_obj.owner_id:
            group_properties = Property.query.filter_by(group_name=property_obj.group_name).all()
            all_owned = all(prop.owner_id == property_obj.owner_id for prop in group_properties)
            
            if all_owned:
                # 50% bonus for owning all in group
                rent *= 1.5
        
        # Apply improvement multiplier
        improvement_multipliers = [1.0, 2.0]  # No improvement, with improvement
        if property_obj.improvement_level >= 0 and property_obj.improvement_level < len(improvement_multipliers):
            rent *= improvement_multipliers[property_obj.improvement_level]
        
        # Apply inflation factor
        game_state = GameState.query.first()
        rent *= game_state.inflation_factor
        
        return int(rent)
    
    def mortgage_property(self, player_id, property_id):
        """Mortgage a property to get cash"""
        # Verify property and player
        property_obj = Property.query.get(property_id)
        player = Player.query.get(player_id)
        
        if not property_obj:
            return {
                "success": False,
                "error": "Property not found"
            }
        
        if not player:
            return {
                "success": False,
                "error": "Player not found"
            }
        
        # Check ownership
        if property_obj.owner_id != player.id:
            return {
                "success": False,
                "error": "Player does not own this property"
            }
        
        # Check if property already has a lien
        if property_obj.has_lien:
            return {
                "success": False,
                "error": "Property already has a lien"
            }
        
        # Check if property has improvements
        if property_obj.improvement_level > 0:
            return {
                "success": False,
                "error": "Must remove improvements before mortgaging"
            }
        
        # Calculate mortgage value
        mortgage_value = int(property_obj.current_price * 0.5)  # 50% of current price
        
        # Process mortgage
        player.cash += mortgage_value
        property_obj.has_lien = True
        property_obj.lien_amount = mortgage_value
        
        # Get current game state for lap tracking
        game_state = GameState.query.first()
        property_obj.lien_start_lap = game_state.current_lap
        
        db.session.commit()
        
        # Record transaction
        transaction = Transaction(
            from_player_id=None,  # Bank
            to_player_id=player.id,
            amount=mortgage_value,
            transaction_type="property_mortgage",
            property_id=property_id,
            description=f"Mortgage of {property_obj.name}"
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Broadcast property update
        self.socketio.emit('property_mortgaged', {
            "property_id": property_obj.id,
            "property_name": property_obj.name,
            "player_id": player.id,
            "player_name": player.username,
            "mortgage_value": mortgage_value
        })
        
        return {
            "success": True,
            "property": {
                "id": property_obj.id,
                "name": property_obj.name,
                "mortgage_value": mortgage_value
            },
            "player_cash": player.cash
        }
    
    def unmortgage_property(self, player_id, property_id):
        """Pay off a mortgage to remove lien"""
        # Verify property and player
        property_obj = Property.query.get(property_id)
        player = Player.query.get(player_id)
        
        if not property_obj:
            return {
                "success": False,
                "error": "Property not found"
            }
        
        if not player:
            return {
                "success": False,
                "error": "Player not found"
            }
        
        # Check ownership
        if property_obj.owner_id != player.id:
            return {
                "success": False,
                "error": "Player does not own this property"
            }
        
        # Check if property has a lien
        if not property_obj.has_lien:
            return {
                "success": False,
                "error": "Property does not have a lien"
            }
        
        # Calculate unmortgage cost (original mortgage + 10% interest)
        unmortgage_cost = int(property_obj.lien_amount * 1.1)
        
        # Check if player has enough cash
        if player.cash < unmortgage_cost:
            return {
                "success": False,
                "error": "Not enough cash to unmortgage"
            }
        
        # Process unmortgage
        player.cash -= unmortgage_cost
        property_obj.has_lien = False
        property_obj.lien_amount = 0
        property_obj.lien_start_lap = 0
        db.session.commit()
        
        # Record transaction
        transaction = Transaction(
            from_player_id=player.id,
            to_player_id=None,  # Bank
            amount=unmortgage_cost,
            transaction_type="property_unmortgage",
            property_id=property_id,
            description=f"Unmortgage of {property_obj.name}"
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Broadcast property update
        self.socketio.emit('property_unmortgaged', {
            "property_id": property_obj.id,
            "property_name": property_obj.name,
            "player_id": player.id,
            "player_name": player.username,
            "unmortgage_cost": unmortgage_cost
        })
        
        return {
            "success": True,
            "property": {
                "id": property_obj.id,
                "name": property_obj.name,
                "unmortgage_cost": unmortgage_cost
            },
            "player_cash": player.cash
        }
```

### 14.4 Bankruptcy System

Pi-nopoly implements a bankruptcy system that handles players who cannot meet their financial obligations.

```python
class BankruptcyManager:
    """Handles player bankruptcy process"""
    
    def __init__(self, socketio, banker):
        self.socketio = socketio
        self.banker = banker
    
    def process_bankruptcy(self, player_id, creditor_id=None):
        """Process bankruptcy for a player"""
        # Verify player
        player = Player.query.get(player_id)
        
        if not player:
            return {
                "success": False,
                "error": "Player not found"
            }
        
        # Check if player is actually bankrupt
        # In a real implementation, this would be more complex
        if player.cash > 0:
            return {
                "success": False,
                "error": "Player is not bankrupt"
            }
        
        # Get all player assets
        properties = Property.query.filter_by(owner_id=player_id).all()
        loans = Loan.query.filter_by(player_id=player_id, is_cd=True, is_active=True).all()
        
        # Get total liquidation value
        liquidation_value = 0
        
        # Add CD values (at 50% liquidation value)
        cd_value = sum(loan.amount * 0.5 for loan in loans)
        liquidation_value += cd_value
        
        # Handle properties
        for prop in properties:
            # If property has a lien, no value can be recovered
            if not prop.has_lien:
                prop_value = prop.current_price * 0.5
                if prop.improvement_level > 0:
                    prop_value += prop.current_price * 0.25 * prop.improvement_level
                liquidation_value += prop_value
        
        # Check if we're bankrupt to a specific creditor or the bank
        if creditor_id:
            creditor = Player.query.get(creditor_id)
            if creditor:
                # Transfer liquidated assets to creditor
                creditor.cash += liquidation_value
                
                # Record transaction
                transaction = Transaction(
                    from_player_id=player_id,
                    to_player_id=creditor_id,
                    amount=liquidation_value,
                    transaction_type="bankruptcy_liquidation",
                    description=f"Bankruptcy liquidation to {creditor.username}"
                )
                db.session.add(transaction)
        
        # Process property transfers
        for prop in properties:
            if creditor_id:
                # Transfer to creditor
                prop.owner_id = creditor_id
            else:
                # Return to bank
                prop.owner_id = None
            
            # Remove improvements and liens
            prop.improvement_level = 0
            prop.has_lien = False
            prop.lien_amount = 0
            prop.lien_start_lap = 0
        
        # Close all loans and CDs
        for loan in Loan.query.filter_by(player_id=player_id, is_active=True).all():
            loan.is_active = False
        
        # Mark player as out of the game
        player.in_game = False
        player.cash = 0
        db.session.commit()
        
        # Broadcast bankruptcy
        self.socketio.emit('player_bankrupt', {
            "player_id": player.id,
            "player_name": player.username,
            "creditor_id": creditor_id,
            "creditor_name": creditor.username if creditor else "Bank",
            "liquidation_value": liquidation_value
        })
        
        # Check for game end condition
        active_players = Player.query.filter_by(in_game=True).count()
        if active_players <= 1:
            # Only one player left, they win
            self._trigger_game_end()
        
        return {
            "success": True,
            "player": {
                "id": player.id,
                "name": player.username
            },
            "liquidation_value": liquidation_value,
            "creditor_id": creditor_id,
            "game_ended": active_players <= 1
        }
    
    def _trigger_game_end(self):
        """End game due to bankruptcy"""
        # Get the remaining player, if any
        remaining_player = Player.query.filter_by(in_game=True).first()
        
        if remaining_player:
            # One player remaining = winner
            self.socketio.emit('game_ended', {
                "reason": "bankruptcy",
                "winner_id": remaining_player.id,
                "winner_name": remaining_player.username
            })
        else:
            # No players remaining - unusual case
            self.socketio.emit('game_ended', {
                "reason": "bankruptcy",
                "no_winners": True
            })
        
        # Update game state
        game_state = GameState.query.first()
        game_state.status = "ended"
        db.session.commit()
```

### 14.5 Trophy & Achievement System

Pi-nopoly implements a trophy and achievement system to reward players for accomplishments during gameplay.

```python
class AchievementSystem:
    """Manages player achievements and trophies"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.achievement_definitions = {
            # Property achievements
            "property_mogul": {
                "title": "Property Mogul",
                "description": "Own 10 properties at the same time",
                "icon": "building",
                "type": "property",
                "threshold": 10
            },
            "monopoly_master": {
                "title": "Monopoly Master",
                "description": "Own 3 complete property groups",
                "icon": "crown",
                "type": "property_group",
                "threshold": 3
            },
            "improvement_king": {
                "title": "Improvement King",
                "description": "Have 8 property improvements at once",
                "icon": "hammer",
                "type": "improvements",
                "threshold": 8
            },
            
            # Financial achievements
            "millionaire": {
                "title": "Millionaire",
                "description": "Have $5000 in cash",
                "icon": "money-bag",
                "type": "cash",
                "threshold": 5000
            },
            "loan_shark": {
                "title": "Loan Shark",
                "description": "Have 5 loans out to other players",
                "icon": "shark",
                "type": "loans_given",
                "threshold": 5
            },
            "cd_investor": {
                "title": "Master Investor",
                "description": "Have $3000 invested in CDs",
                "icon": "chart",
                "type": "cd_investment",
                "threshold": 3000
            },
            
            # Game achievements
            "jail_bird": {
                "title": "Jail Bird",
                "description": "Go to jail 5 times in one game",
                "icon": "bars",
                "type": "jail_visits",
                "threshold": 5
            },
            "tax_evader": {
                "title": "Tax Evader",
                "description": "Successfully evade taxes 3 times",
                "icon": "mask",
                "type": "tax_evasions",
                "threshold": 3
            },
            "master_thief": {
                "title": "Master Thief",
                "description": "Successfully steal from another player",
                "icon": "thief",
                "type": "theft_success",
                "threshold": 1
            },
            "auction_winner": {
                "title": "Auction Winner",
                "description": "Win 3 property auctions",
                "icon": "gavel",
                "type": "auction_wins",
                "threshold": 3
            }
        }
    
    def check_achievements(self, player_id, event_type, event_data):
        """Check if player has earned any achievements from an event"""
        # Get player and their achievements
        player = Player.query.get(player_id)
        if not player:
            return
        
        # Get or create player achievements record
        player_achievements = PlayerAchievement.query.filter_by(player_id=player_id).first()
        if not player_achievements:
            player_achievements = PlayerAchievement(player_id=player_id)
            db.session.add(player_achievements)
            db.session.commit()
        
        # Parse achievement data
        achievements_data = json.loads(player_achievements.achievements_data)
        
        # Get unlocked achievements
        unlocked = achievements_data.get("unlocked", [])
        
        # Get progress data
        progress = achievements_data.get("progress", {})
        
        # Update progress based on event
        earned_achievements = []
        
        if event_type == "property_purchase":
            # Count properties owned
            property_count = Property.query.filter_by(owner_id=player_id).count()
            progress["property_count"] = property_count
            
            # Check property groups owned
            group_counts = {}
            properties = Property.query.filter_by(owner_id=player_id).all()
            for prop in properties:
                group_counts[prop.group_name] = group_counts.get(prop.group_name, 0) + 1
            
            # Count complete groups
            complete_groups = 0
            for group, count in group_counts.items():
                total_in_group = Property.query.filter_by(group_name=group).count()
                if count == total_in_group:
                    complete_groups += 1
            
            progress["complete_groups"] = complete_groups
            
            # Check for achievements
            if property_count >= 10 and "property_mogul" not in unlocked:
                earned_achievements.append("property_mogul")
            
            if complete_groups >= 3 and "monopoly_master" not in unlocked:
                earned_achievements.append("monopoly_master")
        
        elif event_type == "property_improve":
            # Count total improvements
            improvement_count = db.session.query(func.sum(Property.improvement_level))\
                .filter(Property.owner_id == player_id).scalar() or 0
            progress["improvement_count"] = improvement_count
            
            # Check for achievements
            if improvement_count >= 8 and "improvement_king" not in unlocked:
                earned_achievements.append("improvement_king")
        
        elif event_type == "cash_update":
            # Check cash amount
            cash_amount = player.cash
            progress["cash_amount"] = cash_amount
            
            # Check for achievements
            if cash_amount >= 5000 and "millionaire" not in unlocked:
                earned_achievements.append("millionaire")
        
        elif event_type == "cd_create":
            # Total CD investments
            cd_total = db.session.query(func.sum(Loan.amount))\
                .filter(Loan.player_id == player_id, Loan.is_cd == True, Loan.is_active == True).scalar() or 0
            progress["cd_investment"] = cd_total
            
            # Check for achievements
            if cd_total >= 3000 and "cd_investor" not in unlocked:
                earned_achievements.append("cd_investor")
        
        elif event_type == "jail_enter":
            # Increment jail counter
            jail_visits = progress.get("jail_visits", 0) + 1
            progress["jail_visits"] = jail_visits
            
            # Check for achievements
            if jail_visits >= 5 and "jail_bird" not in unlocked:
                earned_achievements.append("jail_bird")
        
        elif event_type == "tax_evasion":
            # Increment successful tax evasions
            if event_data.get("success", False):
                tax_evasions = progress.get("tax_evasions", 0) + 1
                progress["tax_evasions"] = tax_evasions
                
                # Check for achievements
                if tax_evasions >= 3 and "tax_evader" not in unlocked:
                    earned_achievements.append("tax_evader")
        
        elif event_type == "theft":
            # Check successful theft
            if event_data.get("success", False):
                theft_success = progress.get("theft_success", 0) + 1
                progress["theft_success"] = theft_success
                
                # Check for achievements
                if theft_success >= 1 and "master_thief" not in unlocked:
                    earned_achievements.append("master_thief")
        
        elif event_type == "auction_win":
            # Increment auction wins
            auction_wins = progress.get("auction_wins", 0) + 1
            progress["auction_wins"] = auction_wins
            
            # Check for achievements
            if auction_wins >= 3 and "auction_winner" not in unlocked:
                earned_achievements.append("auction_winner")
        
        # Add any earned achievements to unlocked list
        for achievement_id in earned_achievements:
            unlocked.append(achievement_id)
        
        # Update player achievements
        achievements_data["unlocked"] = unlocked
        achievements_data["progress"] = progress
        player_achievements.achievements_data = json.dumps(achievements_data)
        db.session.commit()
        
        # Notify about new achievements
        for achievement_id in earned_achievements:
            achievement_def = self.achievement_definitions.get(achievement_id)
            if achievement_def:
                self.socketio.emit('achievement_unlocked', {
                    'player_id': player_id,
                    'player_name': player.username,
                    'achievement_id': achievement_id,
                    'title': achievement_def['title'],
                    'description': achievement_def['description'],
                    'icon': achievement_def['icon']
                })
                
                # Public broadcast of significant achievements
                self.socketio.emit('public_achievement', {
                    'player_id': player_id,
                    'player_name': player.username,
                    'achievement_id': achievement_id,
                    'title': achievement_def['title']
                }, broadcast=True)
        
        return earned_achievements
    
    def get_player_achievements(self, player_id):
        """Get all achievements for a player"""
        # Get player achievements record
        player_achievements = PlayerAchievement.query.filter_by(player_id=player_id).first()
        
        if not player_achievements:
            # No achievements yet
            return {
                'unlocked': [],
                'progress': {},
                'available': self.achievement_definitions
            }
        
        # Parse achievement data
        achievements_data = json.loads(player_achievements.achievements_data)
        
        # Get unlocked achievements with full details
        unlocked = []
        for achievement_id in achievements_data.get("unlocked", []):
            if achievement_id in self.achievement_definitions:
                achievement = self.achievement_definitions[achievement_id].copy()
                achievement['id'] = achievement_id
                unlocked.append(achievement)
        
        # Get progress data
        progress = achievements_data.get("progress", {})
        
        # Add threshold information to progress
        progress_with_thresholds = {}
        for key, value in progress.items():
            # Find relevant achievement
            for achievement_id, achievement in self.achievement_definitions.items():
                if achievement.get('type') == key:
                    progress_with_thresholds[key] = {
                        'current': value,
                        'threshold': achievement.get('threshold', 0),
                        'percent': min(100, int(value / achievement.get('threshold', 1) * 100))
                    }
                    break
            
            # If no matching achievement, just use the raw value
            if key not in progress_with_thresholds:
                progress_with_thresholds[key] = {'current': value}
        
        return {
            'unlocked': unlocked,
            'progress': progress_with_thresholds,
            'available': self.achievement_definitions
        }
```

### 14.6 Special Tile Actions

Pi-nopoly implements special actions for non-property tiles to enhance gameplay.

```python
class TileActionManager:
    """Handles special tile actions like Go, Jail, Free Parking, etc."""
    
    def __init__(self, socketio, banker, community_fund, card_manager):
        self.socketio = socketio
        self.banker = banker
        self.community_fund = community_fund
        self.card_manager = card_manager
        self.tile_definitions = self._create_tile_definitions()
    
    def _create_tile_definitions(self):
        """Create definitions for all special tiles"""
        return {
            0: {  # GO
                "name": "GO",
                "type": "go",
                "action": "collect_pass_go",
                "amount": 200
            },
            2: {  # Community Chest
                "name": "Community Chest",
                "type": "community_chest",
                "action": "draw_card"
            },
            4: {  # Income Tax
                "name": "Income Tax",
                "type": "tax",
                "action": "pay_income_tax"
            },
            7: {  # Chance
                "name": "Chance",
                "type": "chance",
                "action": "draw_card"
            },
            10: {  # Jail / Just Visiting
                "name": "Jail / Just Visiting",
                "type": "jail",
                "action": "jail_visit"
            },
            17: {  # Community Chest
                "name": "Community Chest",
                "type": "community_chest",
                "action": "draw_card"
            },
            20: {  # Free Parking
                "name": "Free Parking",
                "type": "free_parking",
                "action": "free_parking"
            },
            22: {  # Chance
                "name": "Chance",
                "type": "chance",
                "action": "draw_card"
            },
            30: {  # Go to Jail
                "name": "Go to Jail",
                "type": "go_to_jail",
                "action": "send_to_jail"
            },
            33: {  # Community Chest
                "name": "Community Chest",
                "type": "community_chest",
                "action": "draw_card"
            },
            36: {  # Chance
                "name": "Chance",
                "type": "chance",
                "action": "draw_card"
            },
            38: {  # Luxury Tax
                "name": "Luxury Tax",
                "type": "tax",
                "action": "pay_luxury_tax",
                "amount": 100
            }
        }
    
    def process_tile_action(self, player_id, tile_position):
        """Process action for landing on a special tile"""
        # Check if tile is a special tile
        if tile_position not in self.tile_definitions:
            return {
                "success": False,
                "error": "Not a special tile"
            }
        
        # Get tile definition
        tile = self.tile_definitions[tile_position]
        
        # Get player
        player = Player.query.get(player_id)
        if not player:
            return {
                "success": False,
                "error": "Player not found"
            }
        
        # Process action based on tile type
        action = tile["action"]
        
        if action == "collect_pass_go":
            return self._handle_go(player)
        elif action == "draw_card":
            if tile["type"] == "chance":
                return self._handle_chance(player)
            else:  # community chest
                return self._handle_community_chest(player)
        elif action == "pay_income_tax":
            return self._handle_income_tax(player)
        elif action == "pay_luxury_tax":
            return self._handle_luxury_tax(player, tile["amount"])
        elif action == "jail_visit":
            return self._handle_jail_visit(player)
        elif action == "send_to_jail":
            return self._handle_go_to_jail(player)
        elif action == "free_parking":
            return self._handle_free_parking(player)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
    
    def _handle_go(self, player):
        """Handle landing directly on GO"""
        # Extra bonus for landing directly on GO (not just passing)
        bonus_amount = 200  # Same as passing GO
        
        # Add to player's cash
        player.cash += bonus_amount
        db.session.commit()
        
        # Record transaction
        transaction = Transaction(
            from_player_id=None,  # Bank
            to_player_id=player.id,
            amount=bonus_amount,
            transaction_type="go_bonus",
            description="Bonus for landing on GO"
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Broadcast update
        self.socketio.emit('go_bonus', {
            "player_id": player.id,
            "player_name": player.username,
            "amount": bonus_amount
        })
        
        return {
            "success": True,
            "action": "go_bonus",
            "amount": bonus_amount
        }
    
    def _handle_chance(self, player):
        """Handle landing on Chance tile"""
        # Draw a chance card
        card_result = self.card_manager.draw_chance_card(player.id)
        
        # Broadcast card drawn
        self.socketio.emit('chance_card', {
            "player_id": player.id,
            "player_name": player.username,
            "card": card_result.get("card", {}),
            "result": card_result.get("result", {})
        })
        
        return {
            "success": True,
            "action": "chance_card",
            "card_result": card_result
        }
    
    def _handle_community_chest(self, player):
        """Handle landing on Community Chest tile"""
        # Draw a community chest card
        card_result = self.card_manager.draw_community_chest_card(player.id)
        
        # Broadcast card drawn
        self.socketio.emit('community_chest_card', {
            "player_id": player.id,
            "player_name": player.username,
            "card": card_result.get("card", {}),
            "result": card_result.get("result", {})
        })
        
        return {
            "success": True,
            "action": "community_chest_card",
            "card_result": card_result
        }
    
    def _handle_income_tax(self, player):
        """Handle landing on Income Tax tile"""
        # Calculate tax (10% of net worth or $200, whichever is less)
        net_worth = self._calculate_net_worth(player.id)
        percentage_tax = int(net_worth * 0.1)
        fixed_tax = 200
        
        tax_amount = min(percentage_tax, fixed_tax)
        
        # Check if player has enough cash
        if player.cash < tax_amount:
            # Player can't afford it - handle bankruptcy or liquidation
            return {
                "success": False,
                "error": "Not enough cash for income tax",
                "required": tax_amount,
                "available": player.cash
            }
        
        # Pay tax
        player.cash -= tax_amount
        db.session.commit()
        
        # Add to community fund
        self.community_fund.add(
            tax_amount, 
            "income_tax", 
            player.id, 
            "Income Tax payment"
        )
        
        # Record transaction
        transaction = Transaction(
            from_player_id=player.id,
            to_player_id=None,  # Bank/Community Fund
            amount=tax_amount,
            transaction_type="income_tax",
            description="Income Tax payment"
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Broadcast update
        self.socketio.emit('tax_paid', {
            "player_id": player.id,
            "player_name": player.username,
            "tax_type": "income_tax",
            "amount": tax_amount,
            "net_worth": net_worth
        })
        
        return {
            "success": True,
            "action": "income_tax",
            "amount": tax_amount,
            "net_worth": net_worth
        }
    
    def _handle_luxury_tax(self, player, amount):
        """Handle landing on Luxury Tax tile"""
        # Check if player has enough cash
        if player.cash < amount:
            # Player can't afford it - handle bankruptcy or liquidation
            return {
                "success": False,
                "error": "Not enough cash for luxury tax",
                "required": amount,
                "available": player.cash
            }
        
        # Pay tax
        player.cash -= amount
        db.session.commit()
        
        # Add to community fund
        self.community_fund.add(
            amount, 
            "luxury_tax", 
            player.id, 
            "Luxury Tax payment"
        )
        
        # Record transaction
        transaction = Transaction(
            from_player_id=player.id,
            to_player_id=None,  # Bank/Community Fund
            amount=amount,
            transaction_type="luxury_tax",
            description="Luxury Tax payment"
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Broadcast update
        self.socketio.emit('tax_paid', {
            "player_id": player.id,
            "player_name": player.username,
            "tax_type": "luxury_tax",
            "amount": amount
        })
        
        return {
            "success": True,
            "action": "luxury_tax",
            "amount": amount
        }
    
    def _handle_jail_visit(self, player):
        """Handle landing on Jail (just visiting)"""
        # No action needed, just visiting
        return {
            "success": True,
            "action": "jail_visit",
            "message": "Just visiting jail"
        }
    
    def _handle_go_to_jail(self, player):
        """Handle landing on Go To Jail tile"""
        # Send player to jail
        player.position = 10  # Jail position
        player.jail_status = 1  # First turn in jail
        db.session.commit()
        
        # Broadcast jail entry
        self.socketio.emit('player_jailed', {
            "player_id": player.id,
            "player_name": player.username,
            "reason": "Landed on Go To Jail"
        })
        
        return {
            "success": True,
            "action": "go_to_jail",
            "new_position": 10
        }
    
    def _handle_free_parking(self, player):
        """Handle landing on Free Parking tile"""
        # Check community fund configuration
        return self.community_fund.handle_free_parking(player.id)
    
    def _calculate_net_worth(self, player_id):
        """Calculate a player's total net worth"""
        player = Player.query.get(player_id)
        if not player:
            return 0
        
        # Start with cash
        net_worth = player.cash
        
        # Add property values
        properties = Property.query.filter_by(owner_id=player_id).all()
        for prop in properties:
            if not prop.has_lien:  # Mortgaged properties don't count
                net_worth += prop.current_price
                # Add improvement value
                if prop.improvement_level > 0:
                    net_worth += prop.current_price * 0.5 * prop.improvement_level
        
        # Add CD values
        cds = Loan.query.filter_by(player_id=player_id, is_cd=True, is_active=True).all()
        for cd in cds:
            net_worth += cd.amount
        
        # Subtract loans
        loans = Loan.query.filter_by(player_id=player_id, is_cd=False, is_active=True).all()
        for loan in loans:
            net_worth -= loan.amount
        
        return net_worth
```

These additional game mechanics complete the Pi-nopoly experience with:

1. **Chance & Community Chest Card System** - Dynamic cards with economic scaling
2. **Auction System** - Real-time property auctions with bidding
3. **Property Improvement System** - Enhance properties to increase rent
4. **Bankruptcy System** - Handles player insolvency and asset liquidation
5. **Trophy & Achievement System** - Rewards for gameplay accomplishments
6. **Special Tile Actions** - Unique mechanics for non-property spaces

These systems work together to create a rich, engaging gameplay experience that goes well beyond traditional board games while maintaining the core economic strategy elements.## SECTION 14: ADDITIONAL GAME MECHANICS

### 14.1 Chance & Community Chest Card System

Pi-nopoly implements a dynamic card system for Chance and Community Chest tiles that scales with the game's economic state.

#### Card Manager Implementation

```python
class CardManager:
    """Manages Chance and Community Chest cards"""
    
    def __init__(self, socketio, community_fund):
        self.socketio = socketio
        self.community_fund = community_fund
        self.chance_cards = []
        self.community_chest_cards = []
        self.chance_discard = []
        self.community_chest_discard = []
        self._initialize_cards()
    
    def _initialize_cards(self):
        """Initialize standard card decks"""
        # Chance cards
        self.chance_cards = [
            {
                "id": "chance_advance_go",
                "title": "Advance to GO",
                "description": "Collect $200",
                "action_type": "move",
                "position": 0,
                "collect_go": True
            },
            {
                "id": "chance_advance_boardwalk",
                "title": "Advance to Boardwalk",
                "description": "If you pass GO, collect $200",
                "action_type": "move",
                "position": 39,
                "collect_go": True
            },
            {
                "id": "chance_advance_illinois",
                "title": "Advance to Illinois Ave",
                "description": "If you pass GO, collect $200",
                "action_type": "move",
                "position": 24,
                "collect_go": True
            },
            {
                "id": "chance_advance_st_charles",
                "title": "Advance to St. Charles Place",
                "description": "If you pass GO, collect $200",
                "action_type": "move",
                "position": 11,
                "collect_go": True
            },
            {
                "id": "chance_advance_nearest_utility",
                "title": "Advance to nearest Utility",
                "description": "If unowned, you may buy it. If owned, pay owner 10 times the amount shown on dice.",
                "action_type": "nearest",
                "tile_type": "utility",
                "rent_multiplier": 10
            },
            {
                "id": "chance_advance_nearest_railroad",
                "title": "Advance to nearest Railroad",
                "description": "If unowned, you may buy it. If owned, pay owner twice the normal rent.",
                "action_type": "nearest",
                "tile_type": "railroad",
                "rent_multiplier": 2
            },
            {
                "id": "chance_bank_dividend",
                "title": "Bank pays you dividend",
                "description": "Collect $50",
                "action_type": "collect",
                "amount": 50,
                "scales_with_inflation": True
            },
            {
                "id": "chance_get_out_of_jail",
                "title": "Get Out of Jail Free",
                "description": "This card may be kept until needed or traded",
                "action_type": "get_out_of_jail",
                "keepable": True
            },
            {
                "id": "chance_go_back",
                "title": "Go back 3 spaces",
                "description": "",
                "action_type": "move_relative",
                "spaces": -3
            },
            {
                "id": "chance_go_to_jail",
                "title": "Go to Jail",
                "description": "Go directly to Jail. Do not pass GO, do not collect $200",
                "action_type": "jail",
                "collect_go": False
            },
            {
                "id": "chance_property_repairs",
                "title": "Make general repairs",
                "description": "For each house pay $25, for each hotel pay $100",
                "action_type": "property_charge",
                "per_improvement": 25,
                "scales_with_inflation": True
            },
            {
                "id": "chance_speeding_fine",
                "title": "Speeding fine",
                "description": "Pay $15",
                "action_type": "pay",
                "amount": 15,
                "scales_with_inflation": True,
                "community_fund": True
            },
            {
                "id": "chance_trip_railroad",
                "title": "Take a trip to Reading Railroad",
                "description": "If you pass GO, collect $200",
                "action_type": "move",
                "position": 5,
                "collect_go": True
            },
            {
                "id": "chance_chairman",
                "title": "You have been elected Chairman of the Board",
                "description": "Pay each player $50",
                "action_type": "pay_each_player",
                "amount": 50,
                "scales_with_inflation": True
            },
            {
                "id": "chance_building_loan",
                "title": "Your building loan matures",
                "description": "Collect $150",
                "action_type": "collect",
                "amount": 150,
                "scales_with_inflation": True
            }
        ]
        
        # Community Chest cards
        self.community_chest_cards = [
            {
                "id": "cc_advance_go",
                "title": "Advance to GO",
                "description": "Collect $200",
                "action_type": "move",
                "position": 0,
                "collect_go": True
            },
            {
                "id": "cc_bank_error",
                "title": "Bank error in your favor",
                "description": "Collect $200",
                "action_type": "collect",
                "amount": 200,
                "scales_with_inflation": True
            },
            {
                "id": "cc_doctors_fee",
                "title": "Doctor's fee",
                "description": "Pay $50",
                "action_type": "pay",
                "amount": 50,
                "scales_with_inflation": True,
                "community_fund": True
            },
            {
                "id": "cc_stock_sale",
                "title": "From sale of stock",
                "description": "Collect $50",
                "action_type": "collect",
                "amount": 50,
                "scales_with_inflation": True
            },
            {
                "id": "cc_get_out_of_jail",
                "title": "Get Out of Jail Free",
                "description": "This card may be kept until needed or traded",
                "action_type": "get_out_of_jail",
                "keepable": True
            },
            {
                "id": "cc_go_to_jail",
                "title": "Go to Jail",
                "description": "Go directly to Jail. Do not pass GO, do not collect $200",
                "action_type": "jail",
                "collect_go": False
            },
            {
                "id": "cc_holiday_fund",
                "title": "Holiday fund matures",
                "description": "Collect $100",
                "action_type": "collect",
                "amount": 100,
                "scales_with_inflation": True
            },
            {
                "id": "cc_income_tax_refund",
                "title": "Income tax refund",
                "description": "Collect $20",
                "action_type": "collect",
                "amount": 20,
                "scales_with_inflation": True,
                "from_community_fund": True
            },
            {
                "id": "cc_birthday",
                "title": "It is your birthday",
                "description": "Collect $10 from each player",
                "action_type": "collect_from_each_player",
                "amount": 10,
                "scales_with_inflation": True
            },
            {
                "id": "cc_life_insurance",
                "title": "Life insurance matures",
                "description": "Collect $100",
                "action_type": "collect",
                "amount": 100,
                "scales_with_inflation": True
            },
            {
                "id": "cc_hospital",
                "title": "Hospital fees",
                "description": "Pay $50",
                "action_type": "pay",
                "amount": 50,
                "scales_with_inflation": True,
                "community_fund": True
            },
            {
                "id": "cc_school_fees",
                "title": "School fees",
                "description": "Pay $50",
                "action_type": "pay",
                "amount": 50,
                "scales_with_inflation": True,
                "community_fund": True
            },
            {
                "id": "cc_consultancy_fee",
                "title": "Receive consultancy fee",
                "description": "Collect $25",
                "action_type": "collect",
                "amount": 25,
                "scales_with_inflation": True
            },
            {
                "id": "cc_street_repairs",
                "title": "Street repairs",
                "description": "Pay $40 per house and $115 per hotel",
                "action_type": "property_charge",
                "per_improvement": 40,
                "per_hotel": 115,
                "scales_with_inflation": True,
                "community_fund": True
            },
            {
                "id": "cc_beauty_contest",
                "title": "You won second prize in a beauty contest",
                "description": "Collect $10",
                "action_type": "collect",
                "amount": 10,
                "scales_with_inflation": True
            },
            {
                "id": "cc_inheritance",
                "title": "You inherit",
                "description": "Collect $100",
                "action_type": "collect",
                "amount": 100,
                "scales_with_inflation": True
            }
        ]
        
        # Shuffle decks
        random.shuffle(self.chance_cards)
        random.shuffle(self.community_chest_cards)
    
    def draw_chance_card(self, player_id):
        """Draw a card from the Chance deck"""
        # If deck is empty, shuffle discard pile and reuse
        if not self.chance_cards:
            self.chance_cards = self.chance_discard
            self.chance_discard = []
            random.shuffle(self.chance_cards)
        
        # No cards available
        if not self.chance_cards:
            return {
                "success": False,
                "error": "No Chance cards available"
            }
        
        # Draw a card
        card = self.chance_cards.pop(0)
        
        # Apply inflation scaling if needed
        card = self._apply_economic_scaling(card)
        
        # Process the card
        result = self._process_card(card, player_id)
        
        # Add to discard pile if not keepable
        if not card.get('keepable', False) or not result.get('kept', False):
            self.chance_discard.append(card)
        
        return {
            "success": True,
            "card": card,
            "result": result
        }
    
    def draw_community_chest_card(self, player_id):
        """Draw a card from the Community Chest deck"""
        # If deck is empty, shuffle discard pile and reuse
        if not self.community_chest_cards:
            self.community_chest_cards = self.community_chest_discard
            self.community_chest_discard = []
            random.shuffle(self.community_chest_cards)
        
        # No cards available
        if not self.community_chest_cards:
            return {
                "success": False,
                "error": "No Community Chest cards available"
            }
        
        # Draw a card
        card = self.community_chest_cards.pop(0)
        
        # Apply inflation scaling if needed
        card = self._apply_economic_scaling(card)
        
        # Process the card
        result = self._process_card(card, player_id)
        
        # Add to discard pile if not keepable
        if not card.get('keepable', False) or not result.get('kept', False):
            self.community_chest_discard.append(card)
        
        return {
            "success": True,
            "card": card,
            "result": result
        }
    
    def _apply_economic_scaling(self, card):
        """Apply economic scaling to card amounts based on inflation"""
        # Make a copy to avoid modifying the original
        card = card.copy()
        
        # Check if card needs scaling
        if not card.get('scales_with_inflation', False):
            return card
        
        # Get current inflation state and factor
        game_state = GameState.query.first()
        inflation_factor = game_state.inflation_factor
        
        # Scale amounts
        if 'amount' in card:
            card['original_amount'] = card['amount']
            card['amount'] = int(card['amount'] * inflation_factor)
        
        if 'per_improvement' in card:
            card['original_per_improvement'] = card['per_improvement']
            card['per_improvement'] = int(card['per_improvement'] * inflation_factor)
        
        if 'per_hotel' in card:
            card['original_per_hotel'] = card['per_hotel']
            card['per_hotel'] = int(card['per_hotel'] * inflation_factor)
        
        return card
    
    def _process_card(self, card, player_id):
        """Process a card's action for the given player"""
        player = Player.query.get(player_id)
        if not player:
            return {"error": "Player not found"}
        
        action_type = card.get('action_type')
        
        # Process based on action type
        if action_type == 'move':
            return self._process_move_action(card, player)
        elif action_type == 'move_relative':
            return self._process_move_relative_action(card, player)
        elif action_type == 'nearest':
            return self._process_nearest_action(card, player)
        elif action_type == 'collect':
            return self._process_collect_action(card, player)
        elif action_type == 'pay':
            return self._process_pay_action(card, player)
        elif action_type == 'jail':
            return self._process_jail_action(card, player)
        elif action_type == 'get_out_of_jail':
            return self._process_get_out_of_jail_action(card, player)
        elif action_type == 'property_charge':
            return self._process_property_charge_action(card, player)
        elif action_type == 'collect_from_each_player':
            return self._process_collect_from_each_action(card, player)
        elif action_type == 'pay_each_player':
            return self._process_pay_each_action(card, player)
        else:
            return {"error": f"Unknown action type: {action_type}"}
    
    def _process_move_action(self, card, player):
        """Process a 'move' action"""
        old_position = player.position
        new_position = card.get('position', 0)
        
        # Check if passing GO
        passing_go = (new_position < old_position) and card.get('collect_go', True)
        
        # Update player position
        player.position = new_position
        db.session.commit()
        
        # Handle passing GO
        if passing_go:
            # Player will get $200 from the move
            banking_system.deposit(player.id, 200)
        
        return {
            "action": "move",
            "old_position": old_position,
            "new_position": new_position,
            "passing_go": passing_go
        }
    
    def _process_move_relative_action(self, card, player):
        """Process a 'move_relative' action"""
        old_position = player.position
        spaces = card.get('spaces', 0)
        
        # Calculate new position
        board_size = 40
        new_position = (old_position + spaces) % board_size
        
        # Check if passing GO (only for forward movement)
        passing_go = (spaces > 0) and (old_position + spaces >= board_size) and card.get('collect_go', True)
        
        # Update player position
        player.position = new_position
        db.session.commit()
        
        # Handle passing GO
        if passing_go:
            # Player will get $200 from the move
            banking_system.deposit(player.id, 200)
        
        return {
            "action": "move_relative",
            "old_position": old_position,
            "new_position": new_position,
            "spaces": spaces,
            "passing_go": passing_go
        }
    
    def _process_nearest_action(self, card, player):
        """Process a 'nearest' action to find nearest utility or railroad"""
        old_position = player.position
        tile_type = card.get('tile_type')
        
        # Find positions of all tiles of specified type
        if tile_type == 'utility':
            type_positions = [12, 28]  # Electric Company, Water Works
        elif tile_type == 'railroad':
            type_positions = [5, 15, 25, 35]  # Reading, Pennsylvania, B&O, Short Line
        else:
            return {"error": f"Unknown tile type: {tile_type}"}
        
        # Find the next position of this type
        new_position = None
        for pos in type_positions:
            if pos > old_position:
                new_position = pos
                break
        
        # If we didn't find a position ahead, wrap around to the first one
        if new_position is None:
            new_position = type_positions[0]
        
        # Check if passing GO
        passing_go = (new_position < old_position) and card.get('collect_go', True)
        
        # Update player position
        player.position = new_position
        db.session.commit()
        
        # Handle passing GO
        if passing_go:
            # Player will get $200 from the move
            banking_system.deposit(player.id, 200)
        
        # Get property at new position
        property_obj = Property.query.filter_by(position=new_position).first()
        
        # Set rent multiplier if property is owned
        rent_multiplier = None
        if property_obj and property_obj.owner_id is not None and property_obj.owner_id != player.id:
            rent_multiplier = card.get('rent_multiplier', 1)
        
        return {
            "action": "nearest",
            "tile_type": tile_type,
            "old_position": old_position,
            "new_position": new_position,
            "passing_go": passing_go,
            "rent_multiplier": rent_multiplier,
            "property_id": property_obj.id if property_obj else None
        }
    
    def _process_collect_action(self, card, player):
        """Process a 'collect' action"""
        amount = card.get('amount', 0)
        
        # Check if collecting from community fund
        if card.get('from_community_fund', False):
            # Try to draw from community fund
            result = self.community_fund.withdraw(
                amount, 
                player.id, 
                f"Community Chest card: {card.get('title')}"
            )
            
            if not result:
                # If fund doesn't have enough, take what's available
                game_state = GameState.query.first()
                available = game_state.community_fund
                if available > 0:
                    self.community_fund.withdraw(
                        available, 
                        player.id, 
                        f"Community Chest card: {card.get('title')} (partial)"
                    )
                    return {
                        "action": "collect",
                        "from_community_fund": True,
                        "requested_amount": amount,
                        "actual_amount": available,
                        "partial": True
                    }
                else:
                    return {
                        "action": "collect",
                        "from_community_fund": True,
                        "requested_amount": amount,
                        "actual_amount": 0,
                        "failed": True
                    }
        else:
            # Collect from bank
            banking_system.deposit(player.id, amount)
        
        return {
            "action": "collect",
            "amount": amount,
            "from_community_fund": card.get('from_community_fund', False)
        }
    
    def _process_pay_action(self, card, player):
        """Process a 'pay' action"""
        amount = card.get('amount', 0)
        
        # Check if player has enough cash
        if player.cash < amount:
            # Player can't afford it - handle bankruptcy or debt
            # This is simplified; real implementation would be more complex
            actually_paid = player.cash
            player.cash = 0
            db.session.commit()
            
            # Add to community fund if specified
            if card.get('community_fund', False):
                self.community_fund.add(
                    actually_paid, 
                    "card_payment", 
                    player.id, 
                    f"Card payment (partial): {card.get('title')}"
                )
            
            return {
                "action": "pay",
                "requested_amount": amount,
                "actual_amount": actually_paid,
                "to_community_fund": card.get('community_fund', False),
                "partial": True
            }
        else:
            # Pay the full amount
            player.cash -= amount
            db.session.commit()
            
            # Add to community fund if specified
            if card.get('community_fund', False):
                self.community_fund.add(
                    amount, 
                    "card_payment", 
                    player.id, 
                    f"Card payment: {card.get('title')}"
                )
            
            return {
                "action": "pay",
                "amount": amount,
                "to_community_fund": card.get('community_fund', False)
            }
    
    def _process_jail_action(self, card, player):
        """Process a 'jail' action"""
        # Send player to jail
        player.position = 10  # Jail position
        player.jail_status = 1  # First turn in jail
        db.session.commit()
        
        return {
            "action": "jail",
            "new_position": 10
        }
    
    def _process_get_out_of_jail_action(self, card, player):
        """Process a 'get_out_of_jail' action"""
        # Check if player wants to keep the card
        # This would typically be handled by asking the player
        # For now, always keep it
        keep_card = True
        
        if keep_card:
            # Give player a get out of jail card
            jail_card = JailCard(
                player_id=player.id,
                card_type=card.get('id', 'unknown'),
                used=False
            )
            db.session.add(jail_card)
            db.session.commit()
            
            return {
                "action": "get_out_of_jail",
                "kept": True,
                "jail_card_id": jail_card.id
            }
        else:
            return {
                "action": "get_out_of_jail",
                "kept": False
            }
    
    def _process_property_charge_action(self, card, player):
        """Process a 'property_charge' action for houses/hotels"""
        # Get all properties owned by player
        properties = Property.query.filter_by(owner_id=player.id).all()
        
        # Count improvements
        total_improvements = sum(p.improvement_level for p in properties)
        
        # Calculate charge
        per_improvement = card.get('per_improvement', 0)
        total_charge = total_improvements * per_improvement
        
        # Check if player has enough cash
        if player.cash < total_charge:
            # Player can't afford it - handle bankruptcy or debt
            actually_paid = player.cash
            player.cash = 0
            db.session.commit()
            
            # Add to community fund if specified
            if card.get('community_fund', False):
                self.community_fund.add(
                    actually_paid, 
                    "property_charge", 
                    player.id, 
                    f"Property charge (partial): {card.get('title')}"
                )
            
            return {
                "action": "property_charge",
                "improvements": total_improvements,
                "per_improvement": per_improvement,
                "requested_amount": total_charge,
                "actual_amount": actually_paid,
                "to_community_fund": card.get('community_fund', False),
                "partial": True
            }
        else:
            # Pay the full amount
            player.cash -= total_charge
            db.session.commit()
            
            # Add to community fund if specified
            if card.get('community_fund', False):
                self.community_fund.add(
                    total_charge, 
                    "property_charge", 
                    player.id, 
                    f"Property charge: {card.get('title')}"
                )
            
            return {
                "action": "property_charge",
                "improvements": total_improvements,
                "per_improvement": per_improvement,
                "amount": total_charge,
                "to_community_fund": card.get('community_fund', False)
            }
    
    def _process_collect_from_each_action(self, card, player):
        """Process a 'collect_from_each_player' action"""
        amount = card.get('amount', 0)
        
        # Get all other active players
        other_players = Player.query.filter(
            Player.id != player.id, 
            Player.in_game == True
        ).all()
        
        total_collected = 0
        collections = []
        
        # Collect from each player
        for other in other_players:
            # Determine how much this player can pay
            pay_amount = min(amount, other.cash)
            
            # Transfer the money
            if pay_amount > 0:
                other.cash -= pay_amount
                total_collected += pay_amount
                
                collections.append({
                    "player_id": other.id,
                    "amount": pay_amount
                })
        
        # Add to player's cash
        player.cash += total_collected
        db.session.commit()
        
        return {
            "action": "collect_from_each_player",
            "amount_per_player": amount,
            "players_count": len(other_players),
            "total_collected": total_collected,
            "collections": collections
        }
    
    def _process_pay_each_action(self, card, player):
        """Process a 'pay_each_player' action"""
        amount = card.get('amount', 0)
        
        # Get all other active players
        other_players = Player.query.filter(
            Player.id != player.id, 
            Player.in_game == True
        ).all()
        
        # Calculate total amount needed
        total_needed = amount * len(other_players)
        
        # Check if player has enough cash
        if player.cash < total_needed:
            # Player can't afford to pay everyone fully
            available = player.cash
            player.cash = 0
            
            # Distribute available cash proportionally
            payments = []
            if available > 0 and other_players:
                amount_per_player = available // len(other_players)
                remainder = available % len(other_players)
                
                for i, other in enumerate(other_players):
                    # Distribute remainder one unit at a time
                    payment = amount_per_player + (1 if i < remainder else 0)
                    other.cash += payment
                    
                    payments.append({
                        "player_id": other.id,
                        "amount": payment
                    })
            
            db.session.commit()
            
            return {
                "action": "pay_each_player",
                "requested_amount_per_player": amount,
                "players_count": len(other_players),
                "total_requested": total_needed,
                "total_paid": available,
                "payments": payments,
                "partial": True
            }
        else:
            # Pay each player the full amount
            player.cash -= total_needed
            
            payments = []
            for other in other_players:
                other.cash += amount
                
                payments.append({
                    "player_id": other.id,
                    "amount": amount
                })
            
            db.session.commit()
            
            return {
                "action": "pay_each_player",
                "amount_per_player": amount,
                "players_count": len(other_players),
                "total_paid": total_needed,
                "payments": payments
            }
        }
```

### 14.2 Auction System

Pi-nopoly implements a real-time auction system for properties that are not purchased directly when landed on.

```python
class AuctionSystem:
    """Manages property auctions in Pi-nopoly"""
    
    def __init__(self, socketio, banker):
        self.socketio = socketio
        self.banker = banker
        self.active_auctions = {}  # auction_id -> auction_data
        self.next_auction_id = 1
    
    def start_auction(self, property_id):
        """Start a new auction for a property"""
        # Check if property exists and is available
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {
                "success": False,
                "error": "Property not found"
            }
        
        if property_obj.owner_id is not None:
            return {
                "success": False,
                "error": "Property already has an owner"
            }
        
        # Generate auction ID
        auction_id = str(self.next_auction_id)
        self.next_auction_id += 1
        
        # Get active players
        players = Player.query.filter_by(in_game=True).all()
        player_ids = [p.id for p in players]
        
        # Create auction object
        minimum_bid = int(property_obj.current_price * 0.7)  # Start at 70% of list price
        auction = {
            "id": auction_id,
            "property_id": property_id,
            "property_name": property_obj.name,
            "minimum_bid": minimum_bid,
            "start_price": property_obj.current_price,
            "current_bid": minimum_bid - 1,  # So first valid bid is minimum
            "current_bidder": None,
            "eligible_players": player_ids,
            "players_passed": [],
            "bids": [],
            "status": "active",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "timer": 30,  # 30 second initial timer
            "current_timer": 30
        }
        
        # Store auction
        self.active_auctions[auction_id] = auction
        
        # Notify all players
        self.socketio.emit('auction_started', {
            "auction_id": auction_id,
            "property_id": property_id,
            "property_name": property_obj.name,
            "minimum_bid": minimum_bid,
            "start_price": property_obj.current_price,
            "timer": auction["timer"]
        })
        
        # Start auction timer
        self._start_auction_timer(auction_id)
        
        return {
            "success": True,
            "auction_id": auction_id,
            "auction": auction
        }## SECTION 11: DYNAMIC CONFIGURATION SYSTEM

### 11.1 Admin Game Rules Control Panel

Pi-nopoly implements a comprehensive admin control panel that allows the game administrator to configure all game rules and parameters without requiring code changes or server restarts.

#### Game Rules Configuration Interface

```javascript
// Admin Control Panel - Game Rules Configuration
function renderGameRulesConfig() {
    const configSection = document.getElementById('game-rules-config');
    
    const html = `
        <div class="config-panel">
            <h3>Game Rules Configuration</h3>
            
            <div class="config-group">
                <h4>Game Setup</h4>
                
                <div class="config-row">
                    <label for="difficulty">Game Difficulty</label>
                    <select id="difficulty" name="difficulty">
                        <option value="easy" ${gameConfig.difficulty === 'easy' ? 'selected' : ''}>Easy ($3000 starting cash)</option>
                        <option value="normal" ${gameConfig.difficulty === 'normal' ? 'selected' : ''}>Normal ($2000 starting cash)</option>
                        <option value="hard" ${gameConfig.difficulty === 'hard' ? 'selected' : ''}>Hard ($1000 starting cash)</option>
                    </select>
                </div>
                
                <div class="config-row">
                    <label for="max_players">Maximum Players</label>
                    <select id="max_players" name="max_players">
                        <option value="2" ${gameConfig.max_players === 2 ? 'selected' : ''}>2 Players</option>
                        <option value="3" ${gameConfig.max_players === 3 ? 'selected' : ''}>3 Players</option>
                        <option value="4" ${gameConfig.max_players === 4 ? 'selected' : ''}>4 Players</option>
                        <option value="5" ${gameConfig.max_players === 5 ? 'selected' : ''}>5 Players</option>
                        <option value="6" ${gameConfig.max_players === 6 ? 'selected' : ''}>6 Players</option>
                        <option value="7" ${gameConfig.max_players === 7 ? 'selected' : ''}>7 Players</option>
                        <option value="8" ${gameConfig.max_players === 8 ? 'selected' : ''}>8 Players</option>
                    </select>
                </div>
                
                <div class="config-row">
                    <label for="lap_limit">Game Length</label>
                    <select id="lap_limit" name="lap_limit">
                        <option value="0" ${gameConfig.lap_limit === 0 ? 'selected' : ''}>Infinite (No Limit)</option>
                        <option value="10" ${gameConfig.lap_limit === 10 ? 'selected' : ''}>10 Laps</option>
                        <option value="20" ${gameConfig.lap_limit === 20 ? 'selected' : ''}>20 Laps</option>
                        <option value="30" ${gameConfig.lap_limit === 30 ? 'selected' : ''}>30 Laps</option>
                        <option value="40" ${gameConfig.lap_limit === 40 ? 'selected' : ''}>40 Laps</option>
                    </select>
                </div>
                
                <div class="config-row">
                    <label for="turn_timeout">Turn Timeout</label>
                    <select id="turn_timeout" name="turn_timeout">
                        <option value="30" ${gameConfig.turn_timeout === 30 ? 'selected' : ''}>30 Seconds</option>
                        <option value="60" ${gameConfig.turn_timeout === 60 ? 'selected' : ''}>60 Seconds</option>
                        <option value="90" ${gameConfig.turn_timeout === 90 ? 'selected' : ''}>90 Seconds</option>
                        <option value="120" ${gameConfig.turn_timeout === 120 ? 'selected' : ''}>2 Minutes</option>
                        <option value="300" ${gameConfig.turn_timeout === 300 ? 'selected' : ''}>5 Minutes</option>
                        <option value="0" ${gameConfig.turn_timeout === 0 ? 'selected' : ''}>No Timeout</option>
                    </select>
                </div>
            </div>
            
            <div class="config-group">
                <h4>Free Parking & Community Fund</h4>
                
                <div class="config-row">
                    <label for="community_fund_mode">Community Fund Mode</label>
                    <select id="community_fund_mode" name="community_fund_mode">
                        <option value="free_parking_full" ${gameConfig.community_fund_mode === 'free_parking_full' ? 'selected' : ''}>Full Amount to Free Parking</option>
                        <option value="free_parking_half" ${gameConfig.community_fund_mode === 'free_parking_half' ? 'selected' : ''}>Half Amount to Free Parking</option>
                        <option value="free_parking_fixed" ${gameConfig.community_fund_mode === 'free_parking_fixed' ? 'selected' : ''}>Fixed $500 from Free Parking</option>
                        <option value="free_parking_disabled" ${gameConfig.community_fund_mode === 'free_parking_disabled' ? 'selected' : ''}>Free Parking Disabled</option>
                        <option value="bank_holiday" ${gameConfig.community_fund_mode === 'bank_holiday' ? 'selected' : ''}>Bank Holiday Distribution</option>
                    </select>
                </div>
                
                <div class="config-row">
                    <button id="modify-fund" class="secondary-btn">Modify Fund Amount</button>
                    <span class="current-value">Current: ${gameState.community_fund.toLocaleString()}</span>
                </div>
            </div>
            
            <div class="config-group">
                <h4>Property Rules</h4>
                
                <div class="config-row checkbox-row">
                    <input type="checkbox" id="auction_required" name="auction_required" ${gameConfig.auction_required ? 'checked' : ''}>
                    <label for="auction_required">Properties must be auctioned if not purchased</label>
                </div>
                
                <div class="config-row">
                    <label for="property_multiplier">Property Value Multiplier</label>
                    <input type="range" id="property_multiplier" name="property_multiplier" 
                           min="0.5" max="2.0" step="0.1" value="${gameConfig.property_multiplier || 1.0}">
                    <span class="range-value">${gameConfig.property_multiplier || 1.0}x</span>
                </div>
                
                <div class="config-row">
                    <label for="rent_multiplier">Rent Multiplier</label>
                    <input type="range" id="rent_multiplier" name="rent_multiplier" 
                           min="0.5" max="2.0" step="0.1" value="${gameConfig.rent_multiplier || 1.0}">
                    <span class="range-value">${gameConfig.rent_multiplier || 1.0}x</span>
                </div>
                
                <div class="config-row">
                    <label for="improvement_cost_factor">Improvement Cost (% of Property Value)</label>
                    <input type="range" id="improvement_cost_factor" name="improvement_cost_factor" 
                           min="0.3" max="0.7" step="0.05" value="${gameConfig.improvement_cost_factor || 0.5}">
                    <span class="range-value">${((gameConfig.improvement_cost_factor || 0.5) * 100).toFixed(0)}%</span>
                </div>
            </div>
            
            <div class="config-group">
                <h4>Financial System</h4>
                
                <div class="config-row">
                    <label for="base_tax_rate">Base Income Tax Rate</label>
                    <input type="range" id="base_tax_rate" name="base_tax_rate" 
                           min="0.05" max="0.25" step="0.01" value="${gameConfig.base_tax_rate || 0.1}">
                    <span class="range-value">${((gameConfig.base_tax_rate || 0.1) * 100).toFixed(0)}%</span>
                </div>
                
                <div class="config-row">
                    <label for="base_loan_rate">Base Loan Interest Rate</label>
                    <input type="range" id="base_loan_rate" name="base_loan_rate" 
                           min="0.05" max="0.2" step="0.01" value="${gameConfig.base_loan_rate || 0.1}">
                    <span class="range-value">${((gameConfig.base_loan_rate || 0.1) * 100).toFixed(0)}%</span>
                </div>
                
                <div class="config-row">
                    <label for="base_cd_rate">Base CD Interest Rate</label>
                    <input type="range" id="base_cd_rate" name="base_cd_rate" 
                           min="0.03" max="0.15" step="0.01" value="${gameConfig.base_cd_rate || 0.08}">
                    <span class="range-value">${((gameConfig.base_cd_rate || 0.08) * 100).toFixed(0)}%</span>
                </div>
                
                <div class="config-row">
                    <label for="max_debt_ratio">Maximum Debt-to-Asset Ratio</label>
                    <input type="range" id="max_debt_ratio" name="max_debt_ratio" 
                           min="1.0" max="3.0" step="0.1" value="${gameConfig.max_debt_ratio || 2.0}">
                    <span class="range-value">${gameConfig.max_debt_ratio || 2.0}x</span>
                </div>
                
                <div class="config-row checkbox-row">
                    <input type="checkbox" id="allow_bankruptcy" name="allow_bankruptcy" ${gameConfig.allow_bankruptcy ? 'checked' : ''}>
                    <label for="allow_bankruptcy">Allow bankruptcy (if disabled, players must sell assets instead)</label>
                </div>
            </div>
            
            <div class="config-group">
                <h4>Crime System</h4>
                
                <div class="config-row checkbox-row">
                    <input type="checkbox" id="enable_crime" name="enable_crime" ${gameConfig.enable_crime ? 'checked' : ''}>
                    <label for="enable_crime">Enable theft and tax evasion mechanics</label>
                </div>
                
                <div class="config-row">
                    <label for="jail_bail_amount">Jail Bail Amount</label>
                    <input type="number" id="jail_bail_amount" name="jail_bail_amount" 
                           min="50" max="500" step="50" value="${gameConfig.jail_bail_amount || 200}">
                </div>
                
                <div class="config-row">
                    <label for="theft_success_rate">Theft Success Rate</label>
                    <input type="range" id="theft_success_rate" name="theft_success_rate" 
                           min="0.3" max="0.9" step="0.05" value="${gameConfig.theft_success_rate || 0.7}">
                    <span class="range-value">${((gameConfig.theft_success_rate || 0.7) * 100).toFixed(0)}%</span>
                </div>
                
                <div class="config-row">
                    <label for="audit_probability">Base Audit Probability</label>
                    <input type="range" id="audit_probability" name="audit_probability" 
                           min="0.05" max="0.3" step="0.05" value="${gameConfig.audit_probability || 0.1}">
                    <span class="range-value">${((gameConfig.audit_probability || 0.1) * 100).toFixed(0)}%</span>
                </div>
            </div>
            
            <div class="config-group">
                <h4>Inflation Engine</h4>
                
                <div class="config-row checkbox-row">
                    <input type="checkbox" id="enable_inflation" name="enable_inflation" ${gameConfig.enable_inflation !== false ? 'checked' : ''}>
                    <label for="enable_inflation">Enable dynamic inflation system</label>
                </div>
                
                <div class="config-row">
                    <label for="recession_threshold">Recession Threshold ($)</label>
                    <input type="number" id="recession_threshold" name="recession_threshold" 
                           min="1000" max="10000" step="500" value="${gameConfig.recession_threshold || 5000}">
                </div>
                
                <div class="config-row">
                    <label for="inflation_threshold">Inflation Threshold ($)</label>
                    <input type="number" id="inflation_threshold" name="inflation_threshold" 
                           min="5000" max="20000" step="1000" value="${gameConfig.inflation_threshold || 15000}">
                </div>
                
                <div class="config-row">
                    <label for="inflation_dampening">Economic Transition Dampening</label>
                    <input type="range" id="inflation_dampening" name="inflation_dampening" 
                           min="0.1" max="0.5" step="0.05" value="${gameConfig.inflation_dampening || 0.25}">
                    <span class="range-value">${((gameConfig.inflation_dampening || 0.25) * 100).toFixed(0)}%</span>
                </div>
            </div>
            
            <div class="config-group">
                <h4>Bot Players</h4>
                
                <div class="config-row">
                    <label for="bot_difficulty">Default Bot Difficulty</label>
                    <select id="bot_difficulty" name="bot_difficulty">
                        <option value="easy" ${gameConfig.bot_difficulty === 'easy' ? 'selected' : ''}>Easy</option>
                        <option value="medium" ${gameConfig.bot_difficulty === 'medium' ? 'selected' : ''}>Medium</option>
                        <option value="hard" ${gameConfig.bot_difficulty === 'hard' ? 'selected' : ''}>Hard</option>
                    </select>
                </div>
                
                <div class="config-row checkbox-row">
                    <input type="checkbox" id="adaptive_difficulty" name="adaptive_difficulty" ${gameConfig.adaptive_difficulty ? 'checked' : ''}>
                    <label for="adaptive_difficulty">Enable adaptive difficulty for bots</label>
                </div>
                
                <div class="config-row">
                    <label for="bot_turn_delay">Bot Turn Delay (ms)</label>
                    <input type="range" id="bot_turn_delay" name="bot_turn_delay" 
                           min="500" max="5000" step="500" value="${gameConfig.bot_turn_delay || 2000}">
                    <span class="range-value">${gameConfig.bot_turn_delay || 2000}ms</span>
                </div>
                
                <div class="config-row">
                    <button id="add-bot" class="secondary-btn">Add Bot Player</button>
                    <button id="remove-all-bots" class="danger-btn">Remove All Bots</button>
                </div>
            </div>
            
            <div class="button-row">
                <button id="save-config" class="primary-btn">Save Configuration</button>
                <button id="reset-defaults" class="secondary-btn">Reset to Defaults</button>
                <button id="export-config" class="secondary-btn">Export Configuration</button>
                <button id="import-config" class="secondary-btn">Import Configuration</button>
            </div>
        </div>
    `;
    
    configSection.innerHTML = html;
    
    // Add event listeners for all controls
    document.querySelectorAll('.config-panel select, .config-panel input').forEach(element => {
        element.addEventListener('change', handleConfigChange);
    });
    
    document.querySelectorAll('.config-panel input[type="range"]').forEach(range => {
        range.addEventListener('input', updateRangeValue);
    });
    
    document.getElementById('save-config').addEventListener('click', saveConfiguration);
    document.getElementById('reset-defaults').addEventListener('click', resetDefaultConfiguration);
    document.getElementById('export-config').addEventListener('click', exportConfiguration);
    document.getElementById('import-config').addEventListener('click', importConfiguration);
    document.getElementById('add-bot').addEventListener('click', showAddBotDialog);
    document.getElementById('remove-all-bots').addEventListener('click', confirmRemoveAllBots);
    document.getElementById('modify-fund').addEventListener('click', showModifyFundDialog);
}

function handleConfigChange(event) {
    const element = event.target;
    const name = element.name;
    let value;
    
    // Get appropriate value based on input type
    if (element.type === 'checkbox') {
        value = element.checked;
    } else if (element.type === 'number' || element.type === 'range') {
        value = parseFloat(element.value);
    } else {
        value = element.value;
    }
    
    // Update local config object
    gameConfig[name] = value;
    
    // If this is a critical setting that requires immediate update, send to server
    const criticalSettings = ['turn_timeout', 'community_fund_mode', 'enable_inflation'];
    if (criticalSettings.includes(name)) {
        api.updateGameConfig({ [name]: value })
            .then(response => {
                if (response.success) {
                    showNotification(`Updated ${name} setting`);
                } else {
                    showError(`Failed to update ${name}`);
                    // Revert UI to match server state
                    element.value = response.current_value;
                }
            })
            .catch(error => {
                showError('Error updating configuration');
                console.error(error);
            });
    }
}

function updateRangeValue(event) {
    const range = event.target;
    const valueDisplay = range.nextElementSibling;
    
    // Format the value appropriately (percentage or multiplier)
    if (range.id.includes('rate') || range.id.includes('factor') || range.id.includes('dampening')) {
        valueDisplay.textContent = `${(parseFloat(range.value) * 100).toFixed(0)}%`;
    } else if (range.id.includes('multiplier') || range.id.includes('ratio')) {
        valueDisplay.textContent = `${parseFloat(range.value).toFixed(1)}x`;
    } else if (range.id.includes('delay')) {
        valueDisplay.textContent = `${range.value}ms`;
    } else {
        valueDisplay.textContent = range.value;
    }
}

function saveConfiguration() {
    // Send full configuration to server
    api.updateGameConfig(gameConfig)
        .then(response => {
            if (response.success) {
                showNotification('Game configuration saved successfully');
            } else {
                showError('Failed to save configuration');
            }
        })
        .catch(error => {
            showError('Error saving configuration');
            console.error(error);
        });
}

function resetDefaultConfiguration() {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
        api.resetGameConfig()
            .then(response => {
                if (response.success) {
                    // Update local config
                    gameConfig = response.config;
                    // Refresh the UI
                    renderGameRulesConfig();
                    showNotification('Configuration reset to defaults');
                } else {
                    showError('Failed to reset configuration');
                }
            })
            .catch(error => {
                showError('Error resetting configuration');
                console.error(error);
            });
    }
}

function exportConfiguration() {
    // Create configuration export
    const configExport = {
        game_version: gameState.version,
        export_date: new Date().toISOString(),
        config: gameConfig
    };
    
    // Convert to JSON string
    const configJson = JSON.stringify(configExport, null, 2);
    
    // Create download link
    const blob = new Blob([configJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pinopoly_config_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    
    // Cleanup
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 0);
}

function importConfiguration() {
    // Create file input
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';
    
    input.onchange = (event) => {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const importedConfig = JSON.parse(e.target.result);
                
                // Validate the imported configuration
                if (!importedConfig.config) {
                    throw new Error('Invalid configuration format');
                }
                
                // Confirm import
                if (confirm('Are you sure you want to import this configuration?')) {
                    // Send to server
                    api.updateGameConfig(importedConfig.config)
                        .then(response => {
                            if (response.success) {
                                // Update local config
                                gameConfig = response.config;
                                // Refresh the UI
                                renderGameRulesConfig();
                                showNotification('Configuration imported successfully');
                            } else {
                                showError('Failed to import configuration');
                            }
                        })
                        .catch(error => {
                            showError('Error importing configuration');
                            console.error(error);
                        });
                }
            } catch (error) {
                showError('Invalid configuration file');
                console.error(error);
            }
        };
        
        reader.readAsText(file);
    };
    
    input.click();
}

function showAddBotDialog() {
    // Create dialog HTML
    const dialogHtml = `
        <div class="dialog-content">
            <h3>Add Bot Player</h3>
            
            <div class="form-row">
                <label for="bot-name">Bot Name:</label>
                <input type="text" id="bot-name" placeholder="Enter bot name">
            </div>
            
            <div class="form-row">
                <label for="bot-type">Bot Personality:</label>
                <select id="bot-type">
                    <option value="Conservative">Conservative</option>
                    <option value="Aggressive">Aggressive</option>
                    <option value="Strategic">Strategic</option>
                    <option value="Shark">Shark</option>
                    <option value="Investor">Investor</option>
                </select>
            </div>
            
            <div class="form-row">
                <label for="bot-difficulty">Bot Difficulty:</label>
                <select id="bot-difficulty">
                    <option value="easy">Easy</option>
                    <option value="medium" selected>Medium</option>
                    <option value="hard">Hard</option>
                </select>
            </div>
            
            <div class="form-row">
                <label for="bot-starting-cash">Starting Cash:</label>
                <input type="number" id="bot-starting-cash" min="500" max="5000" step="100" value="2000">
            </div>
            
            <div class="button-row">
                <button id="add-bot-confirm" class="primary-btn">Add Bot</button>
                <button id="add-bot-cancel" class="secondary-btn">Cancel</button>
            </div>
        </div>
    `;
    
    // Show dialog
    showDialog(dialogHtml);
    
    // Add event listeners
    document.getElementById('add-bot-confirm').addEventListener('click', () => {
        const name = document.getElementById('bot-name').value.trim() || generateBotName();
        const type = document.getElementById('bot-type').value;
        const difficulty = document.getElementById('bot-difficulty').value;
        const startingCash = parseInt(document.getElementById('bot-starting-cash').value);
        
        addBotPlayer(name, type, difficulty, startingCash);
        closeDialog();
    });
    
    document.getElementById('add-bot-cancel').addEventListener('click', closeDialog);
}

function addBotPlayer(name, type, difficulty, startingCash) {
    // Check if game is full
    const playerCount = gameState.players.length;
    const maxPlayers = gameConfig.max_players || 8;
    
    if (playerCount >= maxPlayers) {
        showError(`Cannot add bot: Maximum ${maxPlayers} players reached`);
        return;
    }
    
    // Send request to add bot
    api.addBot({
        name: name,
        type: type,
        difficulty: difficulty,
        starting_cash: startingCash
    })
    .then(response => {
        if (response.success) {
            showNotification(`Added ${type} bot: ${name}`);
            // Update game state with new bot
            gameState.players.push(response.bot);
            updatePlayersList();
        } else {
            showError(`Failed to add bot: ${response.error}`);
        }
    })
    .catch(error => {
        showError('Error adding bot');
        console.error(error);
    });
}

function confirmRemoveAllBots() {
    const botCount = gameState.players.filter(p => p.is_bot).length;
    
    if (botCount === 0) {
        showNotification('No bots to remove');
        return;
    }
    
    if (confirm(`Are you sure you want to remove all ${botCount} bot players?`)) {
        api.removeAllBots()
            .then(response => {
                if (response.success) {
                    showNotification(`Removed ${response.removed_count} bots`);
                    // Update game state - remove bots
                    gameState.players = gameState.players.filter(p => !p.is_bot);
                    updatePlayersList();
                } else {
                    showError(`Failed to remove bots: ${response.error}`);
                }
            })
            .catch(error => {
                showError('Error removing bots');
                console.error(error);
            });
    }
}

function showModifyFundDialog() {
    // Create dialog HTML
    const dialogHtml = `
        <div class="dialog-content">
            <h3>Modify Community Fund</h3>
            
            <div class="form-row">
                <label for="current-fund">Current Amount:</label>
                <input type="text" id="current-fund" value="${gameState.community_fund.toLocaleString()}" disabled>
            </div>
            
            <div class="form-row">
                <label for="fund-action">Action:</label>
                <select id="fund-action">
                    <option value="add">Add to Fund</option>
                    <option value="subtract">Subtract from Fund</option>
                    <option value="set">Set Exact Amount</option>
                </select>
            </div>
            
            <div class="form-row">
                <label for="fund-amount">Amount:</label>
                <input type="number" id="fund-amount" min="1" max="10000" step="100" value="500">
            </div>
            
            <div class="form-row">
                <label for="fund-reason">Reason:</label>
                <input type="text" id="fund-reason" placeholder="Admin adjustment">
            </div>
            
            <div class="button-row">
                <button id="modify-fund-confirm" class="primary-btn">Apply</button>
                <button id="modify-fund-cancel" class="secondary-btn">Cancel</button>
            </div>
        </div>
    `;
    
    // Show dialog
    showDialog(dialogHtml);
    
    // Add event listeners
    document.getElementById('modify-fund-confirm').addEventListener('click', () => {
        const action = document.getElementById('fund-action').value;
        const amount = parseInt(document.getElementById('fund-amount').value);
        const reason = document.getElementById('fund-reason').value.trim() || 'Admin adjustment';
        
        modifyCommunityFund(action, amount, reason);
        closeDialog();
    });
    
    document.getElementById('modify-fund-cancel').addEventListener('click', closeDialog);
}

function modifyCommunityFund(action, amount, reason) {
    // Calculate new amount
    let newAmount = gameState.community_fund;
    
    if (action === 'add') {
        newAmount += amount;
    } else if (action === 'subtract') {
        newAmount = Math.max(0, newAmount - amount);
    } else if (action === 'set') {
        newAmount = amount;
    }
    
    // Send request to server
    api.modifyCommunityFund({
        action: action,
        amount: amount,
        new_amount: newAmount,
        reason: reason
    })
    .then(response => {
        if (response.success) {
            showNotification(`Community Fund ${action}ed: ${amount.toLocaleString()}`);
            // Update local state
            gameState.community_fund = response.new_amount;
            // Update fund display
            document.querySelector('.fund-status h4').textContent = `Community Fund: ${gameState.community_fund.toLocaleString()}`;
        } else {
            showError(`Failed to modify Community Fund: ${response.error}`);
        }
    })
    .catch(error => {
        showError('Error modifying Community Fund');
        console.error(error);
    });
}
```

### 11.2 Server-Side Configuration Management

The server implements a flexible configuration management system that stores all game rules in the database and allows them to be modified during gameplay without requiring code changes.

```python
# models/config.py
class GameConfig(db.Model):
    """Stores all configurable game rules and parameters"""
    __tablename__ = 'game_config'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Game setup
    difficulty = db.Column(db.String(20), default='normal')
    max_players = db.Column(db.Integer, default=8)
    lap_limit = db.Column(db.Integer, default=0)  # 0 = infinite
    turn_timeout = db.Column(db.Integer, default=60)  # seconds
    
    # Free Parking & Community Fund
    community_fund_mode = db.Column(db.String(50), default='free_parking_half')
    
    # Property rules
    auction_required = db.Column(db.Boolean, default=True)
    property_multiplier = db.Column(db.Float, default=1.0)
    rent_multiplier = db.Column(db.Float, default=1.0)
    improvement_cost_factor = db.Column(db.Float, default=0.5)
    
    # Financial system
    base_tax_rate = db.Column(db.Float, default=0.1)
    base_loan_rate = db.Column(db.Float, default=0.1)
    base_cd_rate = db.Column(db.Float, default=0.08)
    max_debt_ratio = db.Column(db.Float, default=2.0)
    allow_bankruptcy = db.Column(db.Boolean, default=True)
    
    # Crime system
    enable_crime = db.Column(db.Boolean, default=True)
    jail_bail_amount = db.Column(db.Integer, default=200)
    theft_success_rate = db.Column(db.Float, default=0.7)
    audit_probability = db.Column(db.Float, default=0.1)
    
    # Inflation engine
    enable_inflation = db.Column(db.Boolean, default=True)
    recession_threshold = db.Column(db.Integer, default=5000)
    stable_threshold = db.Column(db.Integer, default=10000)
    inflation_threshold = db.Column(db.Integer, default=15000)
    high_inflation_threshold = db.Column(db.Integer, default=20000)
    inflation_dampening = db.Column(db.Float, default=0.25)
    
    # Bot players
    bot_difficulty = db.Column(db.String(20), default='medium')
    adaptive_difficulty = db.Column(db.Boolean, default=True)
    bot_turn_delay = db.Column(db.Integer, default=2000)  # milliseconds
    
    # Admin info
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    @staticmethod
    def get_config():
        """Get current game configuration or create default"""
        config = GameConfig.query.first()
        if not config:
            config = GameConfig()
            db.session.add(config)
            db.session.commit()
        return config
    
    def to_dict(self):
        """Convert config to dictionary for API response"""
        return {
            'difficulty': self.difficulty,
            'max_players': self.max_players,
            'lap_limit': self.lap_limit,
            'turn_timeout': self.turn_timeout,
            'community_fund_mode': self.community_fund_mode,
            'auction_required': self.auction_required,
            'property_multiplier': self.property_multiplier,
            'rent_multiplier': self.rent_multiplier,
            'improvement_cost_factor': self.improvement_cost_factor,
            'base_tax_rate': self.base_tax_rate,
            'base_loan_rate': self.base_loan_rate,
            'base_cd_rate': self.base_cd_rate,
            'max_debt_ratio': self.max_debt_ratio,
            'allow_bankruptcy': self.allow_bankruptcy,
            'enable_crime': self.enable_crime,
            'jail_bail_amount': self.jail_bail_amount,
            'theft_success_rate': self.theft_success_rate,
            'audit_probability': self.audit_probability,
            'enable_inflation': self.enable_inflation,
            'recession_threshold': self.recession_threshold,
            'stable_threshold': self.stable_threshold,
            'inflation_threshold': self.inflation_threshold,
            'high_inflation_threshold': self.high_inflation_threshold,
            'inflation_dampening': self.inflation_dampening,
            'bot_difficulty': self.bot_difficulty,
            'adaptive_difficulty': self.adaptive_difficulty,
            'bot_turn_delay': self.bot_turn_delay
        }
    
    def update_from_dict(self, config_dict):
        """Update config from dictionary"""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.now()
        db.session.commit()
        return self

# api/admin.py
@app.route('/api/admin/config', methods=['GET'])
def get_game_config():
    """Get current game configuration"""
    config = GameConfig.get_config()
    return jsonify({
        'success': True,
        'config': config.to_dict()
    })

@app.route('/api/admin/config', methods=['POST'])
def update_game_config():
    """Update game configuration"""
    try:
        data = request.json
        config = GameConfig.get_config()
        
        # Update configuration
        config.update_from_dict(data)
        
        # Broadcast config update to all clients
        socketio.emit('config_updated', {
            'config': config.to_dict(),
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'config': config.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/admin/config/reset', methods=['POST'])
def reset_game_config():
    """Reset game configuration to defaults"""
    try:
        # Delete existing config
        GameConfig.query.delete()
        db.session.commit()
        
        # Create new default config
        config = GameConfig()
        db.session.add(config)
        db.session.commit()
        
        # Broadcast config update to all clients
        socketio.emit('config_updated', {
            'config': config.to_dict(),
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'config': config.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/admin/fund', methods=['POST'])
def modify_community_fund():
    """Modify the community fund"""
    try:
        data = request.json
        action = data.get('action')
        amount = data.get('amount', 0)
        reason = data.get('reason', 'Admin adjustment')
        
        # Get game state
        game_state = GameState.query.first()
        old_amount = game_state.community_fund
        
        # Calculate new amount
        if action == 'add':
            game_state.community_fund += amount
        elif action == 'subtract':
            game_state.community_fund = max(0, game_state.community_fund - amount)
        elif action == 'set':
            game_state.community_fund = amount
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid action'
            }), 400
        
        # Save changes
        db.session.commit()
        
        # Log transaction
        transaction = Transaction(
            from_player_id=None,
            to_player_id=None,
            amount=abs(game_state.community_fund - old_amount),
            transaction_type='admin_fund_adjustment',
            description=reason
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Broadcast update to all clients
        socketio.emit('community_fund_update', {
            'old_balance': old_amount,
            'new_balance': game_state.community_fund,
            'change': game_state.community_fund - old_amount,
            'source_type': 'admin_adjustment',
            'reason': reason
        })
        
        return jsonify({
            'success': True,
            'previous_amount': old_amount,
            'new_amount': game_state.community_fund,
            'action': action,
            'amount': amount
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# Configurations are applied throughout the game logic
def apply_config_to_game_systems():
    """Apply current configuration to all game systems"""
    config = GameConfig.get_config()
    
    # Update inflation engine settings
    inflation_engine.update_settings({
        'enabled': config.enable_inflation,
        'recession_threshold': config.recession_threshold,
        'stable_threshold': config.stable_threshold,
        'inflation_threshold': config.inflation_threshold,
        'high_inflation_threshold': config.high_inflation_threshold,
        'dampening_factor': config.inflation_dampening
    })
    
    # Update tax system settings
    tax_system.update_settings({
        'base_rate': config.base_tax_rate,
        'audit_probability': config.audit_probability
    })
    
    # Update banking system settings
    banking_system.update_settings({
        'base_loan_rate': config.base_loan_rate,
        'base_cd_rate': config.base_cd_rate,
        'max_debt_ratio': config.max_debt_ratio,
        'allow_bankruptcy': config.allow_bankruptcy
    })
    
    # Update property system settings
    property_system.update_settings({
        'auction_required': config.auction_required,
        'property_multiplier': config.property_multiplier,
        'rent_multiplier': config.rent_multiplier,
        'improvement_cost_factor': config.improvement_cost_factor
    })
    
    # Update community fund settings
    community_fund.update_settings({
        'mode': config.community_fund_mode
    })
    
    # Update crime system settings
    crime_system.update_settings({
        'enabled': config.enable_crime,
        'jail_bail_amount': config.jail_bail_amount,
        'theft_success_rate': config.theft_success_rate
    })
    
    # Update bot system settings
    bot_system.update_settings({
        'default_difficulty': config.bot_difficulty,
        'adaptive_difficulty': config.adaptive_difficulty,
        'turn_delay': config.bot_turn_delay
    })
```

### 11.3 Configuration Profiles

To make it easy to switch between different game setups, Pi-nopoly supports saving and loading configuration profiles:

```python
# models/config_profile.py
class ConfigProfile(db.Model):
    """Stores named configuration profiles"""
    __tablename__ = 'config_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    config_data = db.Column(db.Text, nullable=False)  # JSON string
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    @property
    def config(self):
        """Get configuration dictionary from JSON"""
        return json.loads(self.config_data)
    
    @config.setter
    def config(self, config_dict):
        """Set configuration dictionary as JSON"""
        self.config_data = json.dumps(config_dict)
    
    @staticmethod
    def create_from_current():
        """Create a profile from the current game configuration"""
        config = GameConfig.get_config()
        profile = ConfigProfile(
            name=f"Configuration {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description="Saved from current configuration",
            config_data=json.dumps(config.to_dict())
        )
        return profile

# Admin API for profile management
@app.route('/api/admin/config/profiles', methods=['GET'])
def get_config_profiles():
    """Get all configuration profiles"""
    profiles = ConfigProfile.query.all()
    return jsonify({
        'success': True,
        'profiles': [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'is_default': p.is_default,
            'created_at': p.created_at.isoformat()
        } for p in profiles]
    })

@app.route('/api/admin/config/profiles', methods=['POST'])
def create_config_profile():
    """Create a new configuration profile"""
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        config_data = data.get('config')
        
        if not name:
            return jsonify({
                'success': False,
                'error': 'Profile name is required'
            }), 400
        
        # Create profile from current config if no config provided
        if not config_data:
            profile = ConfigProfile.create_from_current()
            profile.name = name
            profile.description = description
        else:
            profile = ConfigProfile(
                name=name,
                description=description,
                config_data=json.dumps(config_data)
            )
        
        db.session.add(profile)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'profile': {
                'id': profile.id,
                'name': profile.name,
                'description': profile.description,
                'is_default': profile.is_default,
                'created_at': profile.created_at.isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/admin/config/profiles/<int:profile_id>', methods=['GET'])
def get_config_profile(profile_id):
    """Get a specific configuration profile"""
    profile = ConfigProfile.query.get(profile_id)
    if not profile:
        return jsonify({
            'success': False,
            'error': 'Profile not found'
        }), 404
    
    return jsonify({
        'success': True,
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'description': profile.description,
            'config': profile.config,
            'is_default': profile.is_default,
            'created_at': profile.created_at.isoformat()
        }
    })

@app.route('/api/admin/config/profiles/<int:profile_id>/apply', methods=['POST'])
def apply_config_profile(profile_id):
    """Apply a configuration profile to the current game"""
    profile = ConfigProfile.query.get(profile_id)
    if not profile:
        return jsonify({
            'success': False,
            'error': 'Profile not found'
        }), 404
    
    try:
        # Get current config
        config = GameConfig.get_config()
        
        # Update with profile config
        config.update_from_dict(profile.config)
        
        # Apply new configuration to game systems
        apply_config_to_game_systems()
        
        # Broadcast update to clients
        socketio.emit('config_updated', {
            'config': config.to_dict(),
            'profile_name': profile.name,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'config': config.to_dict(),
            'profile_name': profile.name
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400## SECTION 13: HIGH AVAILABILITY & FAILURE RECOVERY

Pi-nopoly implements comprehensive high availability and failure recovery mechanisms to ensure uninterrupted gameplay even when issues occur. This is particularly important for a game that's exclusively accessible via Cloudflare Tunnel.

### 13.1 Resilient System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   PRIMARY COMPONENTS                     │
│                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │ Flask App   │    │   SQLite     │    │ Cloudflare │  │
│  │ Server      │◄──►│  Database    │◄──►│ Tunnel     │  │
│  └─────────────┘    └──────────────┘    └────────────┘  │
│         ▲                  ▲                 ▲          │
└─────────┼──────────────────┼─────────────────┼──────────┘
          │                  │                 │
┌─────────┼──────────────────┼─────────────────┼──────────┐
│         │                  │                 │          │
│  ┌──────▼──────┐    ┌──────▼─────┐    ┌─────▼────────┐  │
│  │ Monitoring  │    │ Automatic  │    │ Connection   │  │
│  │ System      │    │ Recovery   │    │ Manager      │  │
│  └─────────────┘    └────────────┘    └──────────────┘  │
│                                                         │
│                  RESILIENCE SYSTEMS                      │
└─────────────────────────────────────────────────────────┘
```

#### Component Monitoring

```python
class SystemMonitor:
    def __init__(self, check_interval=30):
        self.check_interval = check_interval  # seconds
        self.component_status = {
            "flask_server": True,
            "database": True,
            "cloudflare_tunnel": True,
            "websocket_server": True
        }
        self.alert_thresholds = {
            "cpu_usage": 80,  # percent
            "memory_usage": 70,  # percent
            "response_time": 500,  # ms
            "database_size": 100  # MB
        }
        self.monitoring_thread = None
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        self.monitoring_thread = Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                self._check_system_health()
                time.sleep(self.check_interval)
            except Exception as e:
                logging.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(5)  # Wait before retrying
    
    def _check_system_health(self):
        """Check health of all system components"""
        # Check Flask server
        flask_status = self._check_flask_server()
        self.component_status["flask_server"] = flask_status
        
        # Check SQLite database
        db_status = self._check_database()
        self.component_status["database"] = db_status
        
        # Check Cloudflare tunnel
        tunnel_status = self._check_cloudflare_tunnel()
        self.component_status["cloudflare_tunnel"] = tunnel_status
        
        # Check WebSocket server
        ws_status = self._check_websocket_server()
        self.component_status["websocket_server"] = ws_status
        
        # Check system resources
        self._check_system_resources()
        
        # Take action if any component is down
        if not all(self.component_status.values()):
            self._handle_component_failure()
    
    def _check_flask_server(self):
        """Verify Flask server is responding"""
        try:
            response = requests.get("http://localhost:5000/api/health", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def _check_database(self):
        """Verify database is accessible and not corrupted"""
        try:
            # Try a simple query
            with app.app_context():
                result = db.session.execute(text("SELECT 1")).fetchone()
                return result is not None
        except Exception:
            return False
    
    def _check_cloudflare_tunnel(self):
        """Verify Cloudflare tunnel is active"""
        try:
            # Check if cloudflared process is running
            result = subprocess.run(
                ["pgrep", "cloudflared"], 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_websocket_server(self):
        """Verify WebSocket server is accepting connections"""
        try:
            # Create a test client and connect
            client = socketio.test_client(app)
            return client.is_connected()
        except Exception:
            return False
    
    def _check_system_resources(self):
        """Monitor system resource usage"""
        # Check CPU usage
        cpu_percent = psutil.cpu_percent()
        if cpu_percent > self.alert_thresholds["cpu_usage"]:
            logging.warning(f"High CPU usage: {cpu_percent}%")
        
        # Check memory usage
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > self.alert_thresholds["memory_usage"]:
            logging.warning(f"High memory usage: {memory_percent}%")
        
        # Check disk space
        disk_usage = psutil.disk_usage('/')
        if disk_usage.percent > 85:
            logging.warning(f"Low disk space: {disk_usage.percent}%")
        
        # Check database size
        try:
            db_size = os.path.getsize(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')) / (1024 * 1024)
            if db_size > self.alert_thresholds["database_size"]:
                logging.warning(f"Database is large: {db_size:.2f} MB")
        except Exception:
            pass
    
    def _handle_component_failure(self):
        """React to component failures"""
        # Log the failure
        failed_components = [k for k, v in self.component_status.items() if not v]
        logging.error(f"Component failure detected: {', '.join(failed_components)}")
        
        # Trigger appropriate recovery action
        recovery_manager.handle_failures(failed_components)
```

### 13.2 Automatic Recovery Mechanisms

```python
class RecoveryManager:
    def __init__(self, socketio):
        self.socketio = socketio
        self.recovery_attempts = {
            "flask_server": 0,
            "database": 0,
            "cloudflare_tunnel": 0,
            "websocket_server": 0
        }
        self.max_recovery_attempts = 3
        self.recovery_cooldown = 300  # seconds
        self.last_recovery_time = {
            "flask_server": 0,
            "database": 0,
            "cloudflare_tunnel": 0,
            "websocket_server": 0
        }
    
    def handle_failures(self, failed_components):
        """Coordinate recovery for failed components"""
        recovery_results = {}
        
        for component in failed_components:
            # Check if we've exceeded max attempts
            current_time = time.time()
            time_since_last = current_time - self.last_recovery_time.get(component, 0)
            
            # Reset counter if enough time has passed
            if time_since_last > self.recovery_cooldown:
                self.recovery_attempts[component] = 0
            
            # Check if max attempts reached
            if self.recovery_attempts[component] >= self.max_recovery_attempts:
                recovery_results[component] = {
                    "success": False,
                    "reason": "Max recovery attempts exceeded"
                }
                continue
            
            # Attempt recovery
            recovery_method = getattr(self, f"_recover_{component}", None)
            if recovery_method:
                result = recovery_method()
                recovery_results[component] = result
                
                # Update attempts counter
                self.recovery_attempts[component] += 1
                self.last_recovery_time[component] = current_time
            else:
                recovery_results[component] = {
                    "success": False,
                    "reason": "No recovery method available"
                }
        
        # Notify admin about recovery attempts
        self._notify_admin(failed_components, recovery_results)
        
        # Return results
        return recovery_results
    
    def _recover_flask_server(self):
        """Restart Flask server"""
        try:
            # Use systemd to restart service
            subprocess.run(["sudo", "systemctl", "restart", "pinopoly.service"], check=True)
            
            # Wait for service to start
            time.sleep(5)
            
            # Verify server is responding
            for _ in range(3):  # Try up to 3 times
                try:
                    response = requests.get("http://localhost:5000/api/health", timeout=2)
                    if response.status_code == 200:
                        return {"success": True}
                except Exception:
                    pass
                time.sleep(2)
            
            return {"success": False, "reason": "Server did not respond after restart"}
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    def _recover_database(self):
        """Recover database from backup if corrupted"""
        try:
            # Check if database is just locked
            try:
                with app.app_context():
                    result = db.session.execute(text("PRAGMA quick_check")).fetchone()
                if result and result[0] == "ok":
                    # Database is fine, just connection issues
                    db.session.remove()  # Close all sessions
                    return {"success": True, "action": "Cleared database sessions"}
            except Exception:
                pass  # Continue with recovery
            
            # Database might be corrupted, restore from backup
            backup_path = self._find_latest_backup()
            if not backup_path:
                return {"success": False, "reason": "No backup found"}
            
            # Stop Flask server to release database
            subprocess.run(["sudo", "systemctl", "stop", "pinopoly.service"], check=True)
            
            # Restore from backup
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            shutil.copy(backup_path, db_path)
            
            # Restart Flask server
            subprocess.run(["sudo", "systemctl", "start", "pinopoly.service"], check=True)
            
            return {"success": True, "action": f"Restored from backup: {os.path.basename(backup_path)}"}
        except Exception as e:
            # Try to ensure server is restarted even after error
            try:
                subprocess.run(["sudo", "systemctl", "start", "pinopoly.service"])
            except Exception:
                pass
            return {"success": False, "reason": str(e)}
    
    def _recover_cloudflare_tunnel(self):
        """Restart Cloudflare tunnel"""
        try:
            # Restart cloudflared service
            subprocess.run(["sudo", "systemctl", "restart", "cloudflared"], check=True)
            
            # Wait for service to start
            time.sleep(5)
            
            # Check if tunnel is running
            result = subprocess.run(["pgrep", "cloudflared"], capture_output=True)
            if result.returncode == 0:
                return {"success": True}
            else:
                return {"success": False, "reason": "Tunnel did not start after restart"}
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    def _recover_websocket_server(self):
        """Restart WebSocket server"""
        # WebSocket server is part of Flask, so restart Flask
        return self._recover_flask_server()
    
    def _find_latest_backup(self):
        """Find most recent database backup"""
        backup_dir = "/home/pi/pinopoly/backups"
        if not os.path.exists(backup_dir):
            return None
        
        backups = glob.glob(os.path.join(backup_dir, "pinopoly_db_*.sqlite"))
        if not backups:
            return None
        
        # Sort by modification time (newest first)
        backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return backups[0]
    
    def _notify_admin(self, failed_components, recovery_results):
        """Notify admin about failure and recovery attempts"""
        # Prepare notification message
        message = "System Recovery Report\n\n"
        message += f"Failed Components: {', '.join(failed_components)}\n\n"
        
        for component, result in recovery_results.items():
            status = "Success" if result.get("success") else "Failed"
            reason = result.get("reason", "")
            action = result.get("action", "")
            
            message += f"{component}: {status}\n"
            if action:
                message += f"Action: {action}\n"
            if reason:
                message += f"Reason: {reason}\n"
            message += "\n"
        
        # Log the message
        logging.warning(message)
        
        # Emit to admin socket
        self.socketio.emit('system_recovery', {
            'failed_components': failed_components,
            'recovery_results': recovery_results,
            'timestamp': datetime.now().isoformat()
        }, room='admin')
```

### 13.3 Client-Side Resilience

```javascript
// client.js - Connection resilience implementation

class ResilientConnection {
    constructor(url) {
        this.url = url;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.gameState = null;
        this.pendingActions = [];
        this.handlers = {};
        this.connected = false;
        this.reconnecting = false;
    }
    
    connect() {
        this.socket = io(this.url, {
            reconnection: true,
            reconnectionAttempts: this.maxReconnectAttempts,
            reconnectionDelay: this.reconnectDelay,
            reconnectionDelayMax: this.maxReconnectDelay,
            timeout: 10000
        });
        
        // Connection events
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.connected = true;
            this.reconnectAttempts = 0;
            this.reconnecting = false;
            this._processPendingActions();
            this._triggerHandler('connect');
            
            // Request current game state
            this.socket.emit('request_game_state', {}, (response) => {
                if (response.success) {
                    this.gameState = response.state;
                    this._triggerHandler('state_updated', this.gameState);
                }
            });
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('Disconnected:', reason);
            this.connected = false;
            this._triggerHandler('disconnect', reason);
            
            if (reason === 'io server disconnect') {
                // Server initiated disconnect, try reconnecting
                this.socket.connect();
            }
        });
        
        this.socket.on('reconnecting', (attemptNumber) => {
            console.log(`Reconnection attempt ${attemptNumber}`);
            this.reconnecting = true;
            this._triggerHandler('reconnecting', attemptNumber);
        });
        
        this.socket.on('reconnect_failed', () => {
            console.log('Failed to reconnect');
            this.reconnecting = false;
            this._triggerHandler('reconnect_failed');
            this._showOfflineMode();
        });
        
        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this._triggerHandler('error', error);
        });
        
        // Game state updates
        this.socket.on('game_state_update', (state) => {
            this.gameState = state;
            this._triggerHandler('state_updated', state);
        });
    }
    
    send(event, data, callback) {
        if (this.connected) {
            this.socket.emit(event, data, callback);
        } else {
            // Store action to perform when reconnected
            this.pendingActions.push({
                event: event,
                data: data,
                callback: callback,
                timestamp: Date.now()
            });
            this._triggerHandler('action_queued', { event, data });
            
            // If not currently trying to reconnect, attempt to connect
            if (!this.reconnecting) {
                this.reconnecting = true;
                this.connect();
            }
        }
    }
    
    on(event, handler) {
        if (!this.handlers[event]) {
            this.handlers[event] = [];
        }
        this.handlers[event].push(handler);
    }
    
    _triggerHandler(event, data) {
        const handlers = this.handlers[event] || [];
        handlers.forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error(`Error in ${event} handler:`, error);
            }
        });
    }
    
    _processPendingActions() {
        // Filter out actions older than 5 minutes
        const currentTime = Date.now();
        const validActions = this.pendingActions.filter(
            action => currentTime - action.timestamp < 5 * 60 * 1000
        );
        
        if (validActions.length !== this.pendingActions.length) {
            console.log(`Dropped ${this.pendingActions.length - validActions.length} expired actions`);
        }
        
        // Process valid actions
        validActions.forEach(action => {
            console.log(`Processing queued action: ${action.event}`);
            this.socket.emit(action.event, action.data, action.callback);
        });
        
        // Clear the queue
        this.pendingActions = [];
    }
    
    _showOfflineMode() {
        // Notify user of offline mode
        UI.showOfflineNotification({
            title: "You're offline",
            message: "Can't connect to the game server. Some features will be limited.",
            actions: [{
                label: "Retry Connection",
                handler: () => this.connect()
            }]
        });
    }
}
```

### 13.4 Game State Preservation

```python
class GameStateManager:
    def __init__(self, db, socketio, backup_interval=300):
        self.db = db
        self.socketio = socketio
        self.backup_interval = backup_interval  # seconds
        self.last_backup_time = 0
        self.backup_thread = None
        self.emergency_state_cache = {}  # In-memory cache of critical game state
    
    def start_backup_thread(self):
        """Start automatic backup thread"""
        self.backup_thread = Thread(target=self._backup_loop)
        self.backup_thread.daemon = True
        self.backup_thread.start()
    
    def _backup_loop(self):
        """Periodic database backup loop"""
        while True:
            try:
                current_time = time.time()
                if current_time - self.last_backup_time >= self.backup_interval:
                    self._create_backup()
                    self._update_emergency_cache()
                    self.last_backup_time = current_time
                time.sleep(60)  # Check every minute
            except Exception as e:
                logging.error(f"Error in backup loop: {str(e)}")
                time.sleep(60)  # Still sleep after error
    
    def _create_backup(self):
        """Create a backup of the SQLite database"""
        try:
            # Get database path
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            
            # Create backup directory if it doesn't exist
            backup_dir = "/home/pi/pinopoly/backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create timestamped backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f"pinopoly_db_{timestamp}.sqlite")
            
            # Create backup using SQLite's backup API
            conn = sqlite3.connect(db_path)
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
            conn.close()
            
            # Retain only the 5 most recent backups
            self._cleanup_old_backups(backup_dir, 5)
            
            logging.info(f"Created database backup: {backup_path}")
            return backup_path
        except Exception as e:
            logging.error(f"Backup failed: {str(e)}")
            return None
    
    def _cleanup_old_backups(self, backup_dir, keep_count):
        """Remove old backups, keeping only the most recent ones"""
        try:
            backups = glob.glob(os.path.join(backup_dir, "pinopoly_db_*.sqlite"))
            if len(backups) <= keep_count:
                return  # Not enough to clean up
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Remove older backups
            for old_backup in backups[keep_count:]:
                os.remove(old_backup)
                logging.info(f"Removed old backup: {old_backup}")
        except Exception as e:
            logging.error(f"Cleanup of old backups failed: {str(e)}")
    
    def _update_emergency_cache(self):
        """Update in-memory cache of critical game state"""
        try:
            with app.app_context():
                # Get current game state
                game_state = GameState.query.first()
                if not game_state:
                    return
                
                # Cache essential game data
                self.emergency_state_cache = {
                    "current_player_id": game_state.current_player_id,
                    "current_lap": game_state.current_lap,
                    "inflation_state": game_state.inflation_state,
                    "community_fund": game_state.community_fund,
                    "players": [],
                    "properties": []
                }
                
                # Cache active players
                players = Player.query.filter_by(in_game=True).all()
                for player in players:
                    self.emergency_state_cache["players"].append({
                        "id": player.id,
                        "username": player.username,
                        "cash": player.cash,
                        "position": player.position,
                        "bot_type": player.bot_type
                    })
                
                # Cache property ownership
                properties = Property.query.all()
                for prop in properties:
                    self.emergency_state_cache["properties"].append({
                        "id": prop.id,
                        "name": prop.name,
                        "owner_id": prop.owner_id,
                        "improvement_level": prop.improvement_level
                    })
        except Exception as e:
            logging.error(f"Emergency cache update failed: {str(e)}")
    
    def get_emergency_state(self):
        """Get the cached emergency state"""
        return self.emergency_state_cache
    
    def restore_from_backup(self, backup_path=None):
        """Restore game from backup or emergency cache"""
        if backup_path:
            # Restore from specified backup file
            return self._restore_database(backup_path)
        else:
            # Find latest backup
            backup_dir = "/home/pi/pinopoly/backups"
            backups = glob.glob(os.path.join(backup_dir, "pinopoly_db_*.sqlite"))
            if backups:
                # Sort by modification time (newest first)
                backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                return self._restore_database(backups[0])
            else:
                # No backups available, try to use emergency cache
                return self._restore_from_emergency_cache()
    
    def _restore_database(self, backup_path):
        """Restore database from backup file"""
        try:
            # Get database path
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            
            # Close all database connections
            self.db.session.remove()
            
            # Copy backup file over current database
            shutil.copy(backup_path, db_path)
            
            # Notify all clients of restoration
            self.socketio.emit('game_restored', {
                'source': 'database_backup',
                'timestamp': datetime.now().isoformat()
            })
            
            logging.info(f"Restored database from backup: {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Database restoration failed: {str(e)}")
            return False
    
    def _restore_from_emergency_cache(self):
        """Attempt to restore critical game state from memory cache"""
        if not self.emergency_state_cache:
            logging.error("No emergency cache available for restoration")
            return False
        
        try:
            with app.app_context():
                # Get current game state
                game_state = GameState.query.first()
                if not game_state:
                    logging.error("No game state record found to restore into")
                    return False
                
                # Restore basic game state
                game_state.current_player_id = self.emergency_state_cache["current_player_id"]
                game_state.current_lap = self.emergency_state_cache["current_lap"]
                game_state.inflation_state = self.emergency_state_cache["inflation_state"]
                game_state.community_fund = self.emergency_state_cache["community_fund"]
                
                # Restore player positions and cash
                for player_data in self.emergency_state_cache["players"]:
                    player = Player.query.get(player_data["id"])
                    if player:
                        player.cash = player_data["cash"]
                        player.position = player_data["position"]
                
                # Restore property ownership
                for prop_data in self.emergency_state_cache["properties"]:
                    prop = Property.query.get(prop_data["id"])
                    if prop:
                        prop.owner_id = prop_data["owner_id"]
                        prop.improvement_level = prop_data["improvement_level"]
                
                # Commit changes
                self.db.session.commit()
                
                # Notify all clients of restoration
                self.socketio.emit('game_restored', {
                    'source': 'emergency_cache',
                    'timestamp': datetime.now().isoformat()
                })
                
                logging.info("Restored game state from emergency cache")
                return True
        except Exception as e:
            logging.error(f"Emergency state restoration failed: {str(e)}")
            return False
```

### 13.5 Cloudflare Tunnel Resilience

```bash
#!/bin/bash
# cloudflare-monitor.sh - Monitor and recover Cloudflare tunnel

# Configuration
TUNNEL_NAME="pinopoly"
CHECK_INTERVAL=60  # seconds
MAX_FAILURES=3
LOG_FILE="/var/log/cloudflare-monitor.log"

# Initialize variables
failure_count=0
last_recovery_time=0
recovery_cooldown=300  # 5 minutes

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

check_tunnel() {
    # Check if cloudflared process is running
    if ! pgrep cloudflared > /dev/null; then
        log "ERROR: cloudflared process not found"
        return 1
    fi
    
    # Check if tunnel is connected
    if ! cloudflared tunnel info "$TUNNEL_NAME" | grep -q "Active connectors.*1"; then
        log "ERROR: Tunnel $TUNNEL_NAME not connected"
        return 1
    fi
    
    # Check connectivity through tunnel
    DOMAIN=$(cloudflared tunnel info "$TUNNEL_NAME" | grep -oP 'Hostname:\s*\K[^\s]+' | head -1)
    if [ -z "$DOMAIN" ]; then
        log "ERROR: Could not determine tunnel domain"
        return 1
    fi
    
    # Test HTTP connection
    if ! curl -s --max-time 5 "https://$DOMAIN/api/health" | grep -q "ok"; then
        log "ERROR: HTTP check failed for $DOMAIN"
        return 1
    fi
    
    # All checks passed
    return 0
}

recover_tunnel() {
    current_time=$(date +%s)
    time_since_last=$((current_time - last_recovery_time))
    
    # Check cooldown period
    if [ $time_since_last -lt $recovery_cooldown ]; then
        log "WARNING: Recovery attempted too soon, waiting for cooldown"
        return 1
    fi
    
    log "Attempting to recover Cloudflare tunnel..."
    
    # Stop the service
    systemctl stop cloudflared
    sleep 2
    
    # Kill any remaining processes
    if pgrep cloudflared > /dev/null; then
        pkill cloudflared
        sleep 1
    fi
    
    # Start the service
    systemctl start cloudflared
    last_recovery_time=$current_time
    
    # Wait for tunnel to initialize
    log "Waiting for tunnel to initialize..."
    sleep 10
    
    # Check if recovery was successful
    if check_tunnel; then
        log "Recovery successful"
        return 0
    else
        log "Recovery failed"
        return 1
    fi
}

# Main monitoring loop
log "Starting Cloudflare tunnel monitor"

while true; do
    if check_tunnel; then
        log "Tunnel is running normally"
        failure_count=0
    else
        failure_count=$((failure_count + 1))
        log "Tunnel check failed ($failure_count of $MAX_FAILURES)"
        
        if [ $failure_count -ge $MAX_FAILURES ]; then
            log "Maximum failures reached, attempting recovery"
            if recover_tunnel; then
                failure_count=0
            fi
        fi
    fi
    
    sleep $CHECK_INTERVAL
done
```

### 13.6 Comprehensive Disaster Recovery Plan

In case of complete system failure, Pi-nopoly implements a disaster recovery procedure:

#### Recovery Steps

1. **Hardware Failure**
   - Replace Raspberry Pi hardware if needed
   - Restore OS from backup image
   - Reinstall required packages

2. **Database Recovery**
   - Restore from latest backup:
     ```bash
     sqlite3 /home/pi/pinopoly/pinopoly.db ".restore## SECTION 13: HIGH AVAILABILITY & FAILURE RECOVERY

Pi-nopoly implements comprehensive high availability and failure recovery mechanisms to ensure uninterrupted gameplay even when issues occur. This is particularly important for a game that's exclusively accessible via Cloudflare Tunnel.

### 13.1 Resilient System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   PRIMARY COMPONENTS                     │
│                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │ Flask App   │    │   SQLite     │    │ Cloudflare │  │
│  │ Server      │◄──►│  Database    │◄──►│ Tunnel     │  │
│  └─────────────┘    └──────────────┘    └────────────┘  │
│         ▲                  ▲                 ▲          │
└─────────┼──────────────────┼─────────────────┼──────────┘
          │                  │                 │
┌─────────┼──────────────────┼─────────────────┼──────────┐
│         │                  │                 │          │
│  ┌──────▼──────┐    ┌──────▼─────┐    ┌─────▼────────┐  │
│  │ Monitoring  │    │ Automatic  │    │ Connection   │  │
│  │ System      │    │ Recovery   │    │ Manager      │  │
│  └─────────────┘    └────────────┘    └──────────────┘  │
│                                                         │
│                  RESILIENCE SYSTEMS                      │
└─────────────────────────────────────────────────────────┘
```

#### Component Monitoring

```python
class SystemMonitor:
    def __init__(self, check_interval=30):
        self.check_interval = check_interval  # seconds
        self.component_status = {
            "flask_server": True,
            "database": True,
            "cloudflare_tunnel": True,
            "websocket_server": True
        }
        self.alert_thresholds = {
            "cpu_usage": 80,  # percent
            "memory_usage": 70,  # percent
            "response_time": 500,  # ms
            "database_size": 100  # MB
        }
        self.monitoring_thread = None
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        self.monitoring_thread = Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                self._check_system_health()
                time.sleep(self.check_interval)
            except Exception as e:
                logging.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(5)  # Wait before retrying
    
    def _check_system_health(self):
        """Check health of all system components"""
        # Check Flask server
        flask_status = self._check_flask_server()
        self.component_status["flask_server"] = flask_status
        
        # Check SQLite database
        db_status = self._check_database()
        self.component_status["database"] = db_status
        
        # Check Cloudflare tunnel
        tunnel_status = self._check_cloudflare_tunnel()
        self.component_status["cloudflare_tunnel"] = tunnel_status
        
        # Check WebSocket server
        ws_status = self._check_websocket_server()
        self.component_status["websocket_server"] = ws_status
        
        # Check system resources
        self._check_system_resources()
        
        # Take action if any component is down
        if not all(self.component_status.values()):
            self._handle_component_failure()
    
    def _check_flask_server(self):
        """Verify Flask server is responding"""
        try:
            response = requests.get("http://localhost:5000/api/health", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def _check_database(self):
        """Verify database is accessible and not corrupted"""
        try:
            # Try a simple query
            with app.app_context():
                result = db.session.execute(text("SELECT 1")).fetchone()
                return result is not None
        except Exception:
            return False
    
    def _check_cloudflare_tunnel(self):
        """Verify Cloudflare tunnel is active"""
        try:
            # Check if cloudflared process is running
            result = subprocess.run(
                ["pgrep", "cloudflared"], 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_websocket_server(self):
        """Verify WebSocket server is accepting connections"""
        try:
            # Create a test client and connect
            client = socketio.test_client(app)
            return client.is_connected()
        except Exception:
            return False
    
    def _check_system_resources(self):
        """Monitor system resource usage"""
        # Check CPU usage
        cpu_percent = psutil.cpu_percent()
        if cpu_percent > self.alert_thresholds["cpu_usage"]:
            logging.warning(f"High CPU usage: {cpu_percent}%")
        
        # Check memory usage
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > self.alert_thresholds["memory_usage"]:
            logging.warning(f"High memory usage: {memory_percent}%")
        
        # Check disk space
        disk_usage = psutil.disk_usage('/')
        if disk_usage.percent > 85:
            logging.warning(f"Low disk space: {disk_usage.percent}%")
        
        # Check database size
        try:
            db_size = os.path.getsize(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')) / (1024 * 1024)
            if db_size > self.alert_thresholds["database_size"]:
                logging.warning(f"Database is large: {db_size:.2f} MB")
        except Exception:
            pass
    
    def _handle_component_failure(self):
        """React to component failures"""
        # Log the failure
        failed_components = [k for k, v in self.component_status.items() if not v]
        logging.error(f"Component failure detected: {', '.join(failed_components)}")
        
        # Trigger appropriate recovery action
        recovery_manager.handle_failures(failed_components)
```

### 13.2 Automatic Recovery Mechanisms

```python
class RecoveryManager:
    def __init__(self,### 5.5 Enhanced Bot Tuning & Difficulty Scaling

To create a more balanced gameplay experience for human players facing bots, Pi-nopoly implements sophisticated bot tuning mechanisms:

#### Bot Difficulty Levels

Each bot personality type now has three difficulty levels:

```python
class BotDifficultyManager:
    """Manages bot difficulty settings and adjustments"""
    
    def __init__(self):
        # Difficulty levels affect decision quality
        self.difficulty_levels = {
            "easy": {
                "decision_accuracy": 0.7,    # Bots make optimal decisions 70% of time
                "value_estimation_error": 0.2,  # 20% error in property valuation
                "planning_horizon": 2,       # Looks 2 turns ahead
                "risk_tolerance_modifier": -0.2  # Less risk-taking
            },
            "medium": {
                "decision_accuracy": 0.85,
                "value_estimation_error": 0.1,
                "planning_horizon": 4,
                "risk_tolerance_modifier": 0
            },
            "hard": {
                "decision_accuracy": 0.95,
                "value_estimation_error": 0.05,
                "planning_horizon": 6,
                "risk_tolerance_modifier": 0.1
            }
        }
        
        # Default personality parameters
        self.personality_base_params = {
            "Conservative": {
                "risk_tolerance": 0.3,
                "expansion_drive": 0.4,
                "monopoly_focus": 0.5,
                "improvement_threshold": 0.7,
                "trade_favorability_required": 1.2
            },
            "Aggressive": {
                "risk_tolerance": 0.8,
                "expansion_drive": 0.9,
                "monopoly_focus": 0.6,
                "improvement_threshold": 0.4,
                "trade_favorability_required": 0.9
            },
            "Strategic": {
                "risk_tolerance": 0.6,
                "expansion_drive": 0.6,
                "monopoly_focus": 0.9,
                "improvement_threshold": 0.5,
                "trade_favorability_required": 1.0
            },
            "Shark": {
                "risk_tolerance": 0.7,
                "expansion_drive": 0.5,
                "monopoly_focus": 0.4,
                "improvement_threshold": 0.6,
                "trade_favorability_required": 0.8
            },
            "Investor": {
                "risk_tolerance": 0.5,
                "expansion_drive": 0.3,
                "monopoly_focus": 0.4,
                "improvement_threshold": 0.8,
                "trade_favorability_required": 1.1
            }
        }
    
    def get_bot_parameters(self, bot_type, difficulty):
        """Generate parameters for a bot based on type and difficulty"""
        # Get base parameters for personality
        base_params = self.personality_base_params.get(
            bot_type, 
            self.personality_base_params["Strategic"]  # Default to Strategic
        )
        
        # Get difficulty modifiers
        diff_mods = self.difficulty_levels.get(
            difficulty, 
            self.difficulty_levels["medium"]  # Default to medium
        )
        
        # Apply difficulty modifiers
        adjusted_params = base_params.copy()
        
        # Adjust risk tolerance based on difficulty
        adjusted_params["risk_tolerance"] += diff_mods["risk_tolerance_modifier"]
        adjusted_params["risk_tolerance"] = max(0.1, min(0.9, adjusted_params["risk_tolerance"]))
        
        # Add difficulty-specific parameters
        adjusted_params.update({
            "decision_accuracy": diff_mods["decision_accuracy"],
            "value_estimation_error": diff_mods["value_estimation_error"],
            "planning_horizon": diff_mods["planning_horizon"]
        })
        
        return adjusted_params
```

#### Human-like Decision Flaws

To make bots more human-like and prevent them from being too perfect, Pi-nopoly implements intentional decision flaws:

```python
class BotDecisionEngine:
    """Core decision-making engine for bots with humanizing features"""
    
    def __init__(self, bot_type, difficulty, player_id):
        self.player_id = player_id
        self.difficulty_manager = BotDifficultyManager()
        self.params = self.difficulty_manager.get_bot_parameters(bot_type, difficulty)
        
        # Memory and psychology components
        self.memory = BotMemory(player_id, forgetfulness=1-self.params["decision_accuracy"])
        self.psychology = BotPsychology(self.params)
        
    def make_property_decision(self, property_id, current_cash):
        """Decide whether to buy a property with human-like flaws"""
        # Get true property value
        true_value = self._calculate_true_property_value(property_id)
        
        # Apply estimation error (bots don't assess perfectly)
        error_margin = self.params["value_estimation_error"]
        estimation_error = random.uniform(-error_margin, error_margin)
        perceived_value = true_value * (1 + estimation_error)
        
        # Check if bot makes optimal decision
        makes_optimal = random.random() < self.params["decision_accuracy"]
        
        # Get property price
        property_obj = Property.query.get(property_id)
        property_price = property_obj.current_price
        
        # Optimal decision would be to buy if value > price
        optimal_decision = true_value > property_price
        
        # Apply psychological factors
        psychological_adjustment = self.psychology.get_purchase_adjustment(
            property_obj, perceived_value, current_cash
        )
        
        # Remember similar properties and their outcomes
        memory_bias = self.memory.get_property_bias(property_obj.group_name)
        
        # Final decision accounting for all factors
        if makes_optimal:
            # Bot makes mathematically optimal decision
            decision = optimal_decision
        else:
            # Bot makes flawed decision based on biases
            perceived_value_adjusted = perceived_value * (1 + psychological_adjustment) * (1 + memory_bias)
            decision = perceived_value_adjusted > property_price
        
        # Record the decision for future reference
        self.memory.record_property_decision(property_id, decision, property_obj.group_name)
        
        return {
            "decision": decision,
            "true_value": true_value,
            "perceived_value": perceived_value,
            "price": property_price,
            "optimal": optimal_decision,
            "followed_optimal": decision == optimal_decision,
            "psychological_factor": psychological_adjustment,
            "memory_bias": memory_bias
        }
```

#### Bot Psychology Module

```python
class BotPsychology:
    """Simulates human-like psychological factors in bot decision making"""
    
    def __init__(self, params):
        self.params = params
        self.mood = 0.0  # -1.0 (pessimistic) to 1.0 (optimistic)
        self.recent_events = []  # Track events that affect psychology
        self.risk_aversion_baseline = 1.0 - self.params["risk_tolerance"]
        self.confirmation_bias = 0.2  # Tendency to repeat past decisions
        self.recency_bias = 0.3  # Weight of recent events
        
    def update_mood(self, event_type, magnitude):
        """Update bot mood based on game events"""
        # Events can be positive or negative
        self.recent_events.append((event_type, magnitude))
        
        # Keep only recent events (last 5)
        if len(self.recent_events) > 5:
            self.recent_events.pop(0)
        
        # Calculate mood from events with recency bias
        total_effect = 0
        total_weight = 0
        
        for i, (_, magnitude) in enumerate(self.recent_events):
            # More recent events have more weight
            weight = 1 + i * self.recency_bias
            total_effect += magnitude * weight
            total_weight += weight
        
        if total_weight > 0:
            self.mood = total_effect / total_weight
            # Bound between -1 and 1
            self.mood = max(-1.0, min(1.0, self.mood))
    
    def get_purchase_adjustment(self, property_obj, perceived_value, current_cash):
        """Calculate psychological adjustment for property purchase decision"""
        # Base risk aversion affects valuation
        risk_factor = self.risk_aversion_baseline
        
        # Mood affects risk perception
        mood_adjustment = self.mood * 0.2  # Up to ±20% effect
        
        # Cash position affects perception (low cash = more cautious)
        cash_ratio = property_obj.current_price / max(current_cash, 1)
        cash_stress = max(0, min(0.5, (cash_ratio - 0.5)))  # Max 50% negative effect
        
        # Loss aversion - stronger negative reaction to potential losses
        loss_aversion = 0.0
        if perceived_value < property_obj.current_price:
            value_ratio = perceived_value / property_obj.current_price
            loss_aversion = (1.0 - value_ratio) * 0.3  # Up to 30% negative effect
        
        # Combine all psychological factors
        total_adjustment = mood_adjustment - (risk_factor * cash_stress) - loss_aversion
        
        return total_adjustment
```

#### Adaptive Difficulty System

To ensure human players remain competitive, Pi-nopoly implements an adaptive difficulty system:

```python
class AdaptiveDifficultySystem:
    """Dynamically adjusts bot difficulty based on game state"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.adjustment_interval = 3  # Adjust every 3 full rounds
        self.last_adjustment_lap = 0
        self.performance_metrics = {}  # player_id -> metrics
        
    def check_for_adjustment(self):
        """Check if it's time to adjust bot difficulty"""
        game_state = GameState.query.first()
        current_lap = game_state.current_lap
        
        if current_lap - self.last_adjustment_lap >= self.adjustment_interval:
            self._adjust_bot_difficulty()
            self.last_adjustment_lap = current_lap
    
    def _adjust_bot_difficulty(self):
        """Analyze game state and adjust bot difficulties"""
        # Get all players
        players = Player.query.filter_by(in_game=True).all()
        human_players = [p for p in players if not p.bot_type]
        bot_players = [p for p in players if p.bot_type]
        
        if not human_players or not bot_players:
            return  # Nothing to adjust
        
        # Calculate performance metrics
        human_metrics = self._calculate_player_metrics(human_players)
        bot_metrics = self._calculate_player_metrics(bot_players)
        
        # Calculate average metrics
        avg_human_networth = sum(m["net_worth"] for m in human_metrics) / len(human_metrics)
        avg_bot_networth = sum(m["net_worth"] for m in bot_metrics) / len(bot_metrics)
        
        # Determine if adjustment needed
        ratio = avg_human_networth / avg_bot_networth if avg_bot_networth > 0 else 1.0
        
        if ratio < 0.7:
            # Humans falling significantly behind
            self._decrease_bot_difficulty(bot_players)
        elif ratio > 1.3:
            # Humans significantly ahead
            self._increase_bot_difficulty(bot_players)
    
    def _calculate_player_metrics(self, players):
        """Calculate performance metrics for a list of players"""
        metrics = []
        
        for player in players:
            # Calculate net worth
            net_worth = self._calculate_net_worth(player.id)
            
            # Calculate property count
            property_count = Property.query.filter_by(owner_id=player.id).count()
            
            # Calculate monopoly count
            monopoly_count = self._calculate_monopoly_count(player.id)
            
            # Store metrics
            metrics.append({
                "player_id": player.id,
                "is_bot": bool(player.bot_type),
                "net_worth": net_worth,
                "property_count": property_count,
                "monopoly_count": monopoly_count
            })
        
        return metrics
    
    def _decrease_bot_difficulty(self, bot_players):
        """Make bots easier to compete against"""
        for bot in bot_players:
            bot_config = BotConfig.query.filter_by(player_id=bot.id).first()
            
            if not bot_config:
                continue
                
            # Lower difficulty one step
            if bot_config.difficulty == "hard":
                bot_config.difficulty = "medium"
            elif bot_config.difficulty == "medium":
                bot_config.difficulty = "easy"
                
            # Lower decision accuracy slightly
            bot_config.decision_accuracy *= 0.9  # 10% reduction
            
            # Increase estimation error
            bot_config.value_estimation_error *= 1.2  # 20% increase
            
            db.session.commit()
        
        # Notify admin of adjustment
        self.socketio.emit('bot_difficulty_adjusted', {
            'direction': 'decreased',
            'reason': 'Human players falling behind'
        }, room='admin')
    
    def _increase_bot_difficulty(self, bot_players):
        """Make bots more challenging"""
        for bot in bot_players:
            bot_config = BotConfig.query.filter_by(player_id=bot.id).first()
            
            if not bot_config:
                continue
                
            # Raise difficulty one step
            if bot_config.difficulty == "easy":
                bot_config.difficulty = "medium"
            elif bot_config.difficulty == "medium":
                bot_config.difficulty = "hard"
                
            # Improve decision accuracy slightly
            bot_config.decision_accuracy = min(0.95, bot_config.decision_accuracy * 1.1)
            
            # Decrease estimation error
            bot_config.value_estimation_error *= 0.8  # 20% reduction
            
            db.session.commit()
        
        # Notify admin of adjustment
        self.socketio.emit('bot_difficulty_adjusted', {
            'direction': 'increased',
            'reason': 'Human players significantly ahead'
        }, room='admin')
```# Pi-nopoly: Comprehensive Design Document

## SECTION 1: GAME OVERVIEW & ARCHITECTURE

Pi-nopoly is a modern economic strategy board game running on a Raspberry Pi 5 with internet accessibility exclusively via Cloudflare Tunnel. The system integrates complex financial mechanics including inflation, taxes, loans, and property investment in a digital board game experience that can be played remotely from anywhere in the world.

### 1.1 System Architecture
- **Server**: Raspberry Pi 5 (8GB RAM)
- **Backend**: Python/Flask
- **Database**: SQLite
- **Communication**: WebSockets for real-time updates
- **Internet Access**: Cloudflare Tunnel for all game connectivity
- **Interfaces**: Web-based for all devices
  - Mobile UI for players (responsive web design)
  - Admin dashboard for game control (tablet optimized)
  - TV display for board visualization

### 1.2 Network Configuration
- **Internet-Only Mode**: Cloudflare Tunnel for all connections
  - Secure HTTPS connections
  - No port forwarding required
  - Custom domain support (optional)
  - End-to-end encryption
  - No local network dependency
- **WebSocket Protocol**: For all real-time game updates
- **HTTP/REST API**: For player actions and game management
- **Authentication**: PIN-based player access

### 1.3 Remote Play Features
- **Global Accessibility**: Play from anywhere with internet access
- **Multi-Device Support**: Mobile, tablet, laptop, desktop
- **Low Latency Design**: Optimized for responsive remote play
- **Disconnect Handling**: Auto-reconnection and state preservation
- **Spectator Mode**: Watch games without participating

### 1.4 Project Dependencies
```
Flask==2.3.3
Flask-SocketIO==5.3.6
SQLAlchemy==2.0.23
eventlet==0.33.3
python-engineio==4.8.0
python-socketio==5.10.0
cloudflared==2023.7.0 (for Cloudflare Tunnel)
```

## SECTION 2: GAME RULES & FLOW

### 2.1 Game Setup
1. Players join via web browser with username + PIN
   - Local players connect to WiFi
   - Remote players connect via Cloudflare Tunnel URL
2. Admin sets difficulty level (Easy/Normal/Hard)
   - Easy: Start with $3000, lower tax rates
   - Normal: Start with $2000, standard tax rates
   - Hard: Start with $1000, higher tax rates
3. House rules configured by vote:
   - Free Parking Fund: ON/OFF
   - Auction Required: ON/OFF
   - Lap Limit: Infinite/10/20/30
   - AI Players: 0-6
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

The inflation engine is Pi-nopoly's signature economic system and core differentiator from traditional board games. It creates a dynamic economic environment that responds to player actions and game progression.

#### Inflation Engine Architecture

The inflation engine operates as a separate module constantly monitoring the game's economic state, with these components:

```
┌─────────────────────────────────────────────────────────┐
│                   INFLATION ENGINE                       │
│                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │ Cash Monitor│    │ Economic     │    │ Adjustment │  │
│  │ Service     │◄──►│ State Manager│◄──►│ Calculator │  │
│  └─────────────┘    └──────────────┘    └────────────┘  │
│         ▲                  ▲                 ▲          │
└─────────┼──────────────────┼─────────────────┼──────────┘
          │                  │                 │
┌─────────┼──────────────────┼─────────────────┼──────────┐
│         │                  │                 │          │
│  ┌──────▼──────┐    ┌──────▼─────┐    ┌─────▼────────┐  │
│  │ Transaction │    │ Game       │    │ Visualization│  │
│  │ Logger      │    │ Event Hooks│    │ Service      │  │
│  └─────────────┘    └────────────┘    └──────────────┘  │
│                                                         │
│                   CORE GAME SYSTEM                       │
└─────────────────────────────────────────────────────────┘
```

#### Economic State Assessment
The system continuously tracks the total money in circulation:
- **Recession**: < $5K
- **Stable**: $5K-$10K
- **Inflation**: $10K-$15K
- **High Inflation**: $15K-$20K
- **Overheated**: > $20K

#### State Transition Logic
```python
# Inflation Engine State Transition (conceptual)
class InflationEngine:
    def __init__(self, socketio):
        self.socketio = socketio
        self.current_state = "stable"
        self.inflation_factor = 1.0
        self.thresholds = {
            "recession": 5000,
            "stable": 10000,
            "inflation": 15000,
            "high": 20000,
            "overheated": float('inf')
        }
        self.factors = {
            "recession": 0.8,
            "stable": 1.0,
            "inflation": 1.3,
            "high": 1.6,
            "overheated": 2.0
        }
        self.smoothing_window = []  # For gradual transitions
        
    def assess_economic_state(self):
        """Calculate current state based on total cash in game"""
        # Get total cash in circulation
        total_cash = sum(p.cash for p in Player.query.all())
        
        # Use moving average for smoothing (prevent wild oscillation)
        self.smoothing_window.append(total_cash)
        if len(self.smoothing_window) > 3:  # Keep last 3 readings
            self.smoothing_window.pop(0)
        
        smoothed_cash = sum(self.smoothing_window) / len(self.smoothing_window)
        
        # Determine state from smoothed value
        new_state = "recession"
        for state, threshold in self.thresholds.items():
            if smoothed_cash < threshold:
                new_state = state
                break
        
        # If state changed, trigger transition
        if new_state != self.current_state:
            self._transition_to_state(new_state)
            
        return {
            "state": self.current_state,
            "factor": self.inflation_factor,
            "total_cash": total_cash
        }
    
    def _transition_to_state(self, new_state):
        """Handle transition between economic states"""
        old_state = self.current_state
        old_factor = self.inflation_factor
        self.current_state = new_state
        
        # Calculate new inflation factor with smoothing
        target_factor = self.factors[new_state]
        # Gradual transition (25% of the way to target)
        self.inflation_factor = old_factor + 0.25 * (target_factor - old_factor)
        
        # Apply economic effects
        self._update_property_values()
        self._update_interest_rates()
        self._update_tax_rates()
        
        # Broadcast economic update to all clients
        self.socketio.emit('economic_update', {
            'old_state': old_state,
            'new_state': new_state,
            'inflation_factor': self.inflation_factor,
            'transition_message': self._get_transition_message(old_state, new_state)
        })
    
    def _update_property_values(self):
        """Update all property values based on new inflation factor"""
        properties = Property.query.all()
        for prop in properties:
            # Update price with smoothing
            old_price = prop.current_price
            base_price = prop.base_price
            target_price = int(base_price * self.inflation_factor)
            prop.current_price = int(old_price + 0.25 * (target_price - old_price))
            
            # Update rent with smoothing
            old_rent = prop.current_rent
            base_rent = prop.base_rent
            target_rent = int(base_rent * self.inflation_factor)
            prop.current_rent = int(old_rent + 0.25 * (target_rent - old_rent))
        
        db.session.commit()
    
    def _update_interest_rates(self):
        """Update loan and CD rates based on economic state"""
        # Determine interest rate modifier
        modifiers = {
            "recession": -0.02,
            "stable": 0.0,
            "inflation": 0.03,
            "high": 0.06,
            "overheated": 0.10
        }
        modifier = modifiers[self.current_state]
        
        # Update active loans (except fixed-rate CDs)
        loans = Loan.query.filter(
            Loan.is_active == True, 
            Loan.is_cd == False
        ).all()
        
        for loan in loans:
            # Apply new rate with dampening
            base_rate = 0.10  # 10% base rate
            loan.interest_rate = max(0.05, base_rate + modifier)  # Min 5%
        
        db.session.commit()
    
    def _update_tax_rates(self):
        """Update income tax rates based on economic state"""
        # Get game state singleton
        game_state = GameState.query.first()
        
        # Base tax rate is 10%
        base_rate = 0.10
        
        # Adjust based on economic state
        modifiers = {
            "recession": -0.03,  # 7% tax in recession
            "stable": 0.0,       # 10% tax in stable
            "inflation": 0.03,   # 13% tax in inflation
            "high": 0.05,        # 15% tax in high inflation
            "overheated": 0.07   # 17% tax in overheated
        }
        
        modifier = modifiers[self.current_state]
        game_state.tax_rate = base_rate + modifier
        
        db.session.commit()
    
    def _get_transition_message(self, old_state, new_state):
        """Generate a message describing the economic transition"""
        messages = {
            "recession": {
                "recession": "The economy remains in recession.",
                "stable": "The economy is improving from recession to stability!",
                "inflation": "The economy has dramatically improved from recession to inflation!",
                "high": "The economy has explosively grown from recession to high inflation!",
                "overheated": "Economic miracle! From recession to overheated in one cycle!"
            },
            "stable": {
                "recession": "The economy has entered a recession!",
                "stable": "The economy remains stable.",
                "inflation": "Inflation is beginning to rise!",
                "high": "The economy has rapidly accelerated to high inflation!",
                "overheated": "The economy has dangerously overheated!"
            },
            # Additional transition messages...
        }
        
        try:
            return messages[old_state][new_state]
        except KeyError:
            return f"The economy has transitioned from {old_state} to {new_state}."
```

#### Economic Impact Multipliers
Each economic state has different multipliers affecting various game aspects:

| Economic State | Property Values | Rent Amounts | Loan Rates | CD Returns | Tax Rates |
|----------------|----------------|-------------|------------|------------|-----------|
| Recession      | 0.8x           | 0.8x        | -2%        | -1%        | -3%       |
| Stable         | 1.0x           | 1.0x        | Base       | Base       | Base      |
| Inflation      | 1.3x           | 1.3x        | +3%        | +2%        | +3%       |
| High Inflation | 1.6x           | 1.6x        | +6%        | +3%        | +5%       |
| Overheated     | 2.0x           | 2.0x        | +10%       | +5%        | +7%       |

#### Visual Economic Indicators
The inflation engine powers visual indicators across all interfaces:
- **Color-Coded Economic Meter**: Shows current state (blue=recession to red=overheated)
- **Property Value Trends**: Charts showing value changes over time
- **Interest Rate Table**: Current rates for all financial instruments
- **Economic News Ticker**: System-generated economic updates
- **Forecasting Panel**: Projection of economic direction based on current cash trends

#### Strategic Game Impact
The inflation engine creates these dynamic gameplay elements:
- Property values fluctuate, affecting investment strategies
- Loan costs vary, creating optimal borrowing windows
- Rent income scales, altering property ROI calculations
- Tax rates shift, influencing income reporting strategies
- CD returns adjust, creating strategic investment timing

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

The Community Fund is Pi-nopoly's central economic redistribution mechanism. It collects money from various game actions and redistributes it according to game rules.

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

#### Implementation Architecture
```python
class CommunityFund:
    def __init__(self, socketio):
        self.socketio = socketio
        self.distribution_modes = {
            "free_parking_full": {
                "name": "Free Parking (Full)",
                "description": "Player gets entire fund when landing on Free Parking",
                "percentage": 1.0
            },
            "free_parking_half": {
                "name": "Free Parking (Half)",
                "description": "Player gets half the fund when landing on Free Parking",
                "percentage": 0.5
            },
            "free_parking_fixed": {
                "name": "Free Parking (Fixed)",
                "description": "Player gets $500 when landing on Free Parking",
                "fixed_amount": 500
            },
            "free_parking_disabled": {
                "name": "Free Parking (Disabled)",
                "description": "No money from landing on Free Parking",
                "percentage": 0
            },
            "bank_holiday": {
                "name": "Bank Holiday",
                "description": "Distribute fund equally to all players periodically",
                "trigger_amount": 2000,
                "percentage": 0.7
            }
        }
    
    def add(self, amount, source_type, source_id=None, description=None):
        """Add money to the community fund"""
        if amount <= 0:
            return False
            
        # Get game state
        game_state = GameState.query.first()
        
        # Add to fund
        old_balance = game_state.community_fund
        game_state.community_fund += amount
        db.session.commit()
        
        # Log transaction
        transaction = Transaction(
            from_player_id=source_id,
            to_player_id=None,  # Community fund is not a player
            amount=amount,
            transaction_type=f"community_fund_{source_type}",
            description=description or f"Added to Community Fund ({source_type})"
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Broadcast update
        self.socketio.emit('community_fund_update', {
            'old_balance': old_balance,
            'new_balance': game_state.community_fund,
            'change': amount,
            'source_type': source_type
        })
        
        # Check if fund is large enough for bank holiday
        config = self._get_active_config()
        if (config.get('name') == "Bank Holiday" and 
            game_state.community_fund >= config.get('trigger_amount', 0)):
            self.trigger_bank_holiday()
        
        return True
    
    def withdraw(self, amount, target_player_id, reason):
        """Withdraw money from the community fund"""
        if amount <= 0:
            return False
            
        # Get game state
        game_state = GameState.query.first()
        
        # Check if fund has enough
        if game_state.community_fund < amount:
            amount = game_state.community_fund  # Take what's available
            
        if amount <= 0:
            return False
            
        # Update fund
        old_balance = game_state.community_fund
        game_state.community_fund -= amount
        
        # Add money to player
        player = Player.query.get(target_player_id)
        if not player:
            return False
            
        player.cash += amount
        db.session.commit()
        
        # Log transaction
        transaction = Transaction(
            from_player_id=None,  # Community fund is not a player
            to_player_id=target_player_id,
            amount=amount,
            transaction_type=f"community_fund_withdrawal",
            description=reason
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Broadcast update
        self.socketio.emit('community_fund_update', {
            'old_balance': old_balance,
            'new_balance': game_state.community_fund,
            'change': -amount,
            'target_player_id': target_player_id,
            'reason': reason
        })
        
        return True
    
    def handle_free_parking(self, player_id):
        """Handle player landing on Free Parking space"""
        config = self._get_active_config()
        
        # Check if Free Parking is disabled
        if "Free Parking (Disabled)" in config.get('name', ''):
            return {"success": True, "amount": 0, "message": "Free Parking has no effect"}
        
        # Get game state
        game_state = GameState.query.first()
        player = Player.query.get(player_id)
        
        if not player:
            return {"success": False, "reason": "Player not found"}
        
        # Calculate amount to give
        amount = 0
        if 'fixed_amount' in config:
            amount = config['fixed_amount']
        else:
            amount = int(game_state.community_fund * config.get('percentage', 0))
        
        # Withdraw from community fund
        if amount > 0:
            success = self.withdraw(
                amount, 
                player_id, 
                f"Free Parking: {config.get('name')}"
            )
            
            if success:
                return {
                    "success": True, 
                    "amount": amount,
                    "message": f"Collected ${amount} from Free Parking!"
                }
        
        return {"success": True, "amount": 0, "message": "Free Parking has no effect"}
    
    def trigger_bank_holiday(self):
        """Trigger a bank holiday distribution event"""
        # Get game state
        game_state = GameState.query.first()
        
        # Get config
        config = self._get_active_config()
        if config.get('name') != "Bank Holiday":
            return {"success": False, "reason": "Bank Holiday mode not active"}
        
        # Calculate amount to distribute
        total_distribution = int(game_state.community_fund * config.get('percentage', 0.7))
        
        if total_distribution <= 0:
            return {"success": False, "reason": "No funds to distribute"}
        
        # Get active players
        players = Player.query.filter_by(in_game=True).all()
        
        if not players:
            return {"success": False, "reason": "No active players"}
        
        # Calculate amount per player
        amount_per_player = total_distribution // len(players)
        
        if amount_per_player <= 0:
            return {"success": False, "reason": "Distribution too small"}
        
        # Update fund
        old_balance = game_state.community_fund
        game_state.community_fund -= total_distribution
        db.session.commit()
        
        # Distribute to players
        distributions = []
        for player in players:
            player.cash += amount_per_player
            distributions.append({
                "player_id": player.id,
                "amount": amount_per_player
            })
        
        db.session.commit()
        
        # Log transaction
        transaction = Transaction(
            from_player_id=None,
            to_player_id=None,
            amount=total_distribution,
            transaction_type="community_fund_bank_holiday",
            description=f"Bank Holiday: {len(players)} players received ${amount_per_player} each"
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Broadcast update
        self.socketio.emit('bank_holiday', {
            'total_amount': total_distribution,
            'amount_per_player': amount_per_player,
            'player_count': len(players),
            'distributions': distributions,
            'new_fund_balance': game_state.community_fund
        })
        
        return {
            "success": True,
            "total_distributed": total_distribution,
            "amount_per_player": amount_per_player,
            "player_count": len(players)
        }
    
    def _get_active_config(self):
        """Get active distribution configuration"""
        # Check game configuration
        game_config = GameConfig.query.first()
        if not game_config:
            return self.distribution_modes["free_parking_disabled"]
        
        mode_key = game_config.community_fund_mode
        return self.distribution_modes.get(mode_key, self.distribution_modes["free_parking_disabled"])
```

### 4.2 Free Parking Configuration

In Pi-nopoly, Free Parking behavior is configurable by the admin and directly tied to the Community Fund. 

#### Free Parking Options
- **Full Amount**: Player gets the entire Community Fund
- **Half Amount**: Player gets 50% of the Community Fund
- **Fixed Amount**: Player gets a fixed amount (default: $500)
- **Disabled**: Free Parking has no monetary effect

#### Configuration in Admin Panel
```javascript
// Free Parking Configuration UI
function renderFreeParkingConfig() {
    const configSection = document.getElementById('free-parking-config');
    
    const options = [
        { 
            id: "free_parking_full", 
            label: "Full Amount", 
            description: "Player gets the entire Community Fund when landing on Free Parking"
        },
        { 
            id: "free_parking_half", 
            label: "Half Amount", 
            description: "Player gets 50% of the Community Fund when landing on Free Parking"
        },
        { 
            id: "free_parking_fixed", 
            label: "Fixed Amount", 
            description: "Player gets $500 when landing on Free Parking"
        },
        { 
            id: "free_parking_disabled", 
            label: "Disabled", 
            description: "Free Parking has no monetary effect"
        },
        { 
            id: "bank_holiday", 
            label: "Bank Holiday", 
            description: "Distribute fund equally to all players when it reaches $2000"
        }
    ];
    
    const html = `
        <div class="config-panel">
            <h3>Free Parking & Community Fund</h3>
            <p>Configure how the Community Fund is distributed</p>
            
            <div class="config-options">
                ${options.map(option => `
                    <div class="config-option">
                        <input type="radio" 
                               name="community_fund_mode" 
                               id="${option.id}" 
                               value="${option.id}"
                               ${gameConfig.community_fund_mode === option.id ? 'checked' : ''}>
                        <label for="${option.id}">
                            <span class="option-name">${option.label}</span>
                            <span class="option-description">${option.description}</span>
                        </label>
                    </div>
                `).join('')}
            </div>
            
            <div class="fund-status">
                <h4>Community Fund: ${gameState.community_fund.toLocaleString()}</h4>
                
                <div class="admin-actions">
                    <button id="modify-fund" class="secondary-btn">Modify Fund</button>
                    <button id="trigger-distribution" class="primary-btn">Trigger Distribution</button>
                </div>
            </div>
        </div>
    `;
    
    configSection.innerHTML = html;
    
    // Add event listeners
    document.querySelectorAll('input[name="community_fund_mode"]').forEach(radio => {
        radio.addEventListener('change', updateCommunityFundMode);
    });
    
    document.getElementById('modify-fund').addEventListener('click', showModifyFundDialog);
    document.getElementById('trigger-distribution').addEventListener('click', triggerDistribution);
}

function updateCommunityFundMode(event) {
    const mode = event.target.value;
    
    // Send update to server
    api.updateGameConfig({ community_fund_mode: mode })
        .then(response => {
            if (response.success) {
                showNotification('Community Fund mode updated');
                gameConfig.community_fund_mode = mode;
            } else {
                showError('Failed to update Community Fund mode');
            }
        })
        .catch(error => {
            showError('Error updating Community Fund mode');
            console.error(error);
        });
}
```

## SECTION 5: BOT/AI PLAYERS SYSTEM

### 5.1 Dynamic Bot Management

Pi-nopoly supports up to 8 total players (human or AI) in any combination, with the ability to dynamically add or remove bot players during gameplay.

#### Player Capacity
- **Maximum Players**: 8 players total (any mix of human/AI)
- **Minimum Players**: 2 players (can be 2 humans, 2 bots, or 1 of each)
- **Dynamic Joining**: Players can join ongoing games
- **Dynamic Bot Addition**: Admin can add bots to reach desired player count
- **Bot Replacement**: Bots can temporarily substitute for disconnected human players

#### Bot Management Interface
- **Admin Controls**: Add/remove bots at any time
- **Bot Configuration**: Customize bot personality and strategy
- **Balance Adjustments**: Modify bot difficulty to match player skill
- **Auto-fill Option**: Automatically add bots to reach desired player count
- **Dynamic Difficulty**: Bots adapt to match the skill level of human players

#### Implementation Architecture
```python
class BotManager:
    def __init__(self, game_engine, socketio):
        self.game_engine = game_engine
        self.socketio = socketio
        self.active_bots = {}  # bot_id -> Bot instance
        self.available_types = ["Conservative", "Aggressive", "Strategic", "Shark", "Investor"]
        
    def add_bot(self, bot_type=None, name=None):
        """Add a new bot player to the game"""
        # Check if game is full (8 players max)
        current_players = Player.query.filter_by(in_game=True).count()
        if current_players >= 8:
            return {"error": "Game is full, maximum 8 players reached"}
        
        # Auto-select bot type if not specified
        if not bot_type:
            bot_type = random.choice(self.available_types)
        
        # Generate name if not provided
        if not name:
            name = f"{bot_type} Bot #{len(self.active_bots) + 1}"
        
        # Create bot player in database
        bot_player = Player(
            username=name,
            pin="BOT" + ''.join(random.choices('0123456789', k=4)),
            cash=self._get_starting_cash(),
            position=0,
            bot_type=bot_type,
            in_game=True
        )
        db.session.add(bot_player)
        db.session.commit()
        
        # Create bot instance based on type
        bot_instance = self._create_bot_instance(bot_type, bot_player.id)
        self.active_bots[bot_player.id] = bot_instance
        
        # Broadcast bot joined event
        self.socketio.emit('player_joined', {
            'id': bot_player.id,
            'username': bot_player.username,
            'is_bot': True,
            'bot_type': bot_type
        })
        
        return {
            "success": True, 
            "bot_id": bot_player.id,
            "name": name,
            "type": bot_type
        }
    
    def remove_bot(self, bot_id):
        """Remove a bot from the game"""
        if bot_id not in self.active_bots:
            return {"error": "Bot not found"}
        
        # Get bot player
        bot_player = Player.query.get(bot_id)
        if not bot_player or not bot_player.bot_type:
            return {"error": "Not a valid bot player"}
        
        # Handle bot property liquidation
        self._liquidate_bot_assets(bot_id)
        
        # Mark as inactive
        bot_player.in_game = False
        db.session.commit()
        
        # Remove from active bots
        del self.active_bots[bot_id]
        
        # Broadcast bot removed event
        self.socketio.emit('player_left', {
            'id': bot_id,
            'username': bot_player.username,
            'was_bot': True
        })
        
        return {"success": True, "bot_id": bot_id}
    
    def replace_player_with_bot(self, player_id):
        """Temporarily replace a disconnected player with a bot"""
        player = Player.query.get(player_id)
        if not player:
            return {"error": "Player not found"}
        
        # Create a bot with the same assets
        bot_type = "Conservative"  # Default safe bot type for replacement
        
        # Set bot flag but keep player data
        player.bot_type = bot_type
        db.session.commit()
        
        # Create bot instance
        bot_instance = self._create_bot_instance(bot_type, player_id)
        self.active_bots[player_id] = bot_instance
        
        # Broadcast player replaced event
        self.socketio.emit('player_replaced_by_bot', {
            'id': player_id,
            'username': player.username,
            'bot_type': bot_type
        })
        
        return {"success": True, "player_id": player_id, "bot_type": bot_type}
    
    def take_bot_turn(self, bot_id):
        """Execute a turn for a bot player"""
        if bot_id not in self.active_bots:
            return {"error": "Bot not found"}
        
        # Get bot instance
        bot = self.active_bots[bot_id]
        
        # Execute bot turn logic
        turn_result = bot.execute_turn()
        
        # Return turn results
        return turn_result
    
    def _create_bot_instance(self, bot_type, player_id):
        """Create appropriate bot instance based on type"""
        if bot_type == "Conservative":
            return ConservativeBot(self.game_engine, player_id)
        elif bot_type == "Aggressive":
            return AggressiveBot(self.game_engine, player_id)
        elif bot_type == "Strategic":
            return StrategicBot(self.game_engine, player_id)
        elif bot_type == "Shark":
            return SharkBot(self.game_engine, player_id)
        elif bot_type == "Investor":
            return InvestorBot(self.game_engine, player_id)
        else:
            # Default to balanced bot
            return StrategicBot(self.game_engine, player_id)
    
    def _liquidate_bot_assets(self, bot_id):
        """Handle the liquidation of a bot's assets when removed"""
        # Get all properties
        properties = Property.query.filter_by(owner_id=bot_id).all()
        
        # Return properties to bank
        for prop in properties:
            prop.owner_id = None
            prop.improvement_level = 0
            prop.has_lien = False
        
        # Clear any loans
        loans = Loan.query.filter_by(player_id=bot_id, is_active=True).all()
        for loan in loans:
            loan.is_active = False
        
        db.session.commit()
```

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

### 5.3 Bot AI Implementation

Each bot makes decisions using a combination of these algorithms:

#### Property Valuation Algorithm
```python
def calculate_property_value(self, property_id):
    """Calculate the true value of a property to this bot"""
    property_obj = Property.query.get(property_id)
    base_value = property_obj.current_price
    
    # Get all properties in this group
    group_properties = Property.query.filter_by(
        group_name=property_obj.group_name
    ).all()
    
    # Check if we own others in this group
    owned_in_group = sum(
        1 for p in group_properties 
        if p.owner_id == self.player_id
    )
    
    # Calculate group completion value
    group_size = len(group_properties)
    completion_factor = 1.0
    
    if owned_in_group > 0:
        # The more we own in a group, the more valuable the remaining pieces
        completion_factor += (owned_in_group / group_size) * 1.5
    
    # Check if this would complete a group
    if owned_in_group + 1 == group_size:
        # Complete group is worth much more (monopoly bonus)
        completion_factor += 1.0
    
    # Check landing probability (based on dice statistics)
    landing_probability = self._calculate_landing_probability(property_obj.position)
    probability_factor = 1.0 + (landing_probability * 5.0)  # Adjust weight
    
    # Consider current economic phase
    game_state = GameState.query.first()
    economic_adjustment = 1.0
    
    if game_state.inflation_state == "recession":
        # Properties less valuable in recession unless high rent
        economic_adjustment = 0.8
    elif game_state.inflation_state in ["inflation", "high", "overheated"]:
        # Properties more valuable during inflation
        economic_adjustment = 1.2
    
    # Calculate final value
    adjusted_value = base_value * completion_factor * probability_factor * economic_adjustment
    
    # Bot-specific adjustments
    if self.bot_type == "Conservative":
        # Conservative bots value safe properties more
        if property_obj.group_name in ["brown", "light_blue"]:
            adjusted_value *= 1.2
    elif self.bot_type == "Aggressive":
        # Aggressive bots value high-end properties more
        if property_obj.group_name in ["green", "blue"]:
            adjusted_value *= 1.3
    
    return adjusted_value
```

#### Financial Decision Engine
```python
def make_financial_decision(self):
    """Decide what financial moves to make based on current situation"""
    player = Player.query.get(self.player_id)
    
    # Calculate net worth and liquidity
    net_worth = self._calculate_net_worth()
    liquidity_ratio = player.cash / max(net_worth, 1)
    
    decisions = []
    
    # Check if we should take a loan
    if self._should_take_loan(liquidity_ratio):
        loan_amount = self._calculate_optimal_loan_amount()
        decisions.append(("take_loan", loan_amount))
    
    # Check if we should create a CD
    if self._should_create_cd(liquidity_ratio):
        cd_amount = self._calculate_optimal_cd_amount()
        cd_term = self._choose_cd_term()
        decisions.append(("create_cd", cd_amount, cd_term))
    
    # Check if we should improve properties
    properties_to_improve = self._find_properties_to_improve()
    for prop_id in properties_to_improve:
        decisions.append(("improve_property", prop_id))
    
    # Check if we should take out HELOCs
    properties_for_heloc = self._find_properties_for_heloc()
    for prop_id in properties_for_heloc:
        heloc_amount = self._calculate_heloc_amount(prop_id)
        decisions.append(("take_heloc", prop_id, heloc_amount))
    
    return decisions
```

#### Trade Evaluation System
```python
def evaluate_trade(self, trade_data):
    """Evaluate a trade proposal and decide whether to accept"""
    # Calculate value of what we're giving up
    outgoing_value = 0
    for prop_id in trade_data["giving_properties"]:
        outgoing_value += self.calculate_property_value(prop_id)
    outgoing_value += trade_data["giving_cash"]
    
    # Calculate value of what we're receiving
    incoming_value = 0
    for prop_id in trade_data["receiving_properties"]:
        incoming_value += self.calculate_property_value(prop_id)
    incoming_value += trade_data["receiving_cash"]
    
    # Apply bot-specific trade strategy
    value_ratio = incoming_value / max(outgoing_value, 1)
    
    if self.bot_type == "Conservative":
        # Conservative bots require clearly favorable trades
        return value_ratio >= 1.2
    elif self.bot_type == "Aggressive":
        # Aggressive bots accept more balanced trades
        return value_ratio >= 0.9
    elif self.bot_type == "Strategic":
        # Strategic bots evaluate based on completing sets
        if self._trade_completes_set(trade_data["receiving_properties"]):
            return value_ratio >= 0.8
        return value_ratio >= 1.1
    
    # Default evaluation
    return value_ratio >= 1.0
```

#### Risk Analysis Module
```python
def calculate_risk_metrics(self):
    """Calculate various risk metrics for decision making"""
    player = Player.query.get(self.player_id)
    
    # Calculate bankruptcy risk
    properties = Property.query.filter_by(owner_id=self.player_id).all()
    property_value = sum(p.current_price for p in properties)
    
    loans = Loan.query.filter_by(
        player_id=self.player_id,
        is_cd=False,
        is_active=True
    ).all()
    
    total_debt = sum(loan.amount for loan in loans)
    
    # Calculate upcoming expenses (next 1-3 turns)
    other_players_properties = Property.query.filter(
        Property.owner_id.isnot(None),
        Property.owner_id != self.player_id
    ).all()
    
    # Calculate probable landing spots
    landing_probabilities = self._calculate_landing_probabilities(player.position)
    
    # Estimate potential rent expenses
    estimated_rent_expense = sum(
        self._calculate_rent(p) * landing_probabilities.get(p.position, 0)
        for p in other_players_properties
    )
    
    # Calculate debt-to-asset ratio
    debt_asset_ratio = total_debt / max(player.cash + property_value, 1)
    
    # Calculate liquidity ratio
    liquidity_ratio = player.cash / max(estimated_rent_expense, 1)
    
    return {
        "debt_asset_ratio": debt_asset_ratio,
        "liquidity_ratio": liquidity_ratio,
        "estimated_rent_expense": estimated_rent_expense,
        "bankruptcy_risk": self._calculate_bankruptcy_risk(
            debt_asset_ratio, liquidity_ratio
        )
    }
```

### 5.4 Bot Turn Execution

When it's a bot's turn, the system executes these actions:

#### Turn Sequence
1. **Pre-Roll Actions**:
   - Financial decisions (loans, CDs, improvements)
   - Handle existing trades
   - Propose new trades if strategic
   - Report income if passing GO

2. **Roll & Move**:
   - Roll dice with randomized delay (0.5-2s)
   - Process movement with animated token

3. **Landing Actions**:
   - Buy property if available and valuable
   - Pay rent if required
   - Handle special tiles (Chance, etc.)
   - Jail decisions based on strategy

4. **Post-Roll Actions**:
   - Improve properties if strategic
   - Handle financial matters
   - Consider additional trades

5. **Turn End**:
   - Notify all players of completed bot turn
   - Transition to next player

#### Bot Visualization
- **Turn Indicator**: Visual indicator showing bot is "thinking"
- **Action Logging**: All bot actions displayed in game log
- **Delay Parameters**: Configurable delays between bot actions
- **Animation Speed**: Adjustable animation speed for bot turns

## SECTION 6: USER INTERFACES

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

## SECTION 7: TECHNICAL IMPLEMENTATION

### 7.1 Database Schema

#### Players Table
```sql
CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    pin TEXT NOT NULL,
    cash INTEGER DEFAULT 0,
    position INTEGER DEFAULT 0,
    jail_status INTEGER DEFAULT 0,
    suspicion_score REAL DEFAULT 0.0,
    last_income INTEGER DEFAULT 0,
    in_game BOOLEAN DEFAULT TRUE,
    bot_type TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Properties Table
```sql
CREATE TABLE properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    position INTEGER NOT NULL,
    group_name TEXT NOT NULL,
    base_price INTEGER NOT NULL,
    current_price INTEGER NOT NULL,
    base_rent INTEGER NOT NULL,
    current_rent INTEGER NOT NULL,
    improvement_level INTEGER DEFAULT 0,
    owner_id INTEGER DEFAULT NULL,
    has_lien BOOLEAN DEFAULT FALSE,
    lien_amount INTEGER DEFAULT 0,
    FOREIGN KEY (owner_id) REFERENCES players (id)
);
```

#### Loans/CDs Table
```sql
CREATE TABLE loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    interest_rate REAL NOT NULL,
    start_lap INTEGER NOT NULL,
    length_laps INTEGER NOT NULL,
    is_cd BOOLEAN DEFAULT FALSE,
    property_id INTEGER DEFAULT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (player_id) REFERENCES players (id),
    FOREIGN KEY (property_id) REFERENCES properties (id)
);
```

#### Game State Table
```sql
CREATE TABLE game_state (
    id INTEGER PRIMARY KEY,
    current_player_id INTEGER,
    current_lap INTEGER DEFAULT 0,
    total_laps INTEGER DEFAULT 0,
    community_fund INTEGER DEFAULT 0,
    inflation_state TEXT DEFAULT 'stable',
    inflation_factor REAL DEFAULT 1.0,
    tax_rate REAL DEFAULT 0.1,
    FOREIGN KEY (current_player_id) REFERENCES players (id)
);
```

### 7.2 API Endpoints & Multi-Interface Routes

#### Core Web Routes
- `GET /` - Landing page for all users
- `GET /play` - Player game interface
- `GET /admin` - Admin dashboard interface
- `GET /board` - TV board display
- `GET /join` - New player registration
- `POST /login` - Player/admin authentication

#### Game Management API
- `POST /api/game/new` - Create new game
- `POST /api/game/join` - Join game with PIN
- `GET /api/game/state` - Get current game state
- `POST /api/game/start` - Start the game
- `POST /api/game/end` - End the game
- `GET /api/game/players` - List all current players
- `POST /api/game/config` - Update game configuration

#### Player Actions API
- `POST /api/player/roll` - Roll dice
- `POST /api/player/buy` - Buy property
- `POST /api/player/end-turn` - End current turn
- `POST /api/player/report-income` - Report income at GO
- `POST /api/player/improve-property` - Add improvements
- `POST /api/player/jail-action` - Handle jail options
- `GET /api/player/status` - Get player's current status

#### Financial System API
- `POST /api/finance/loan/new` - Take out a loan
- `POST /api/finance/loan/repay` - Repay a loan
- `POST /api/finance/cd/new` - Create a CD
- `POST /api/finance/cd/withdraw` - Withdraw from CD
- `POST /api/finance/heloc/new` - Take out a HELOC
- `GET /api/finance/interest-rates` - Get current rates

#### Trading System API
- `POST /api/trade/propose` - Propose a trade
- `POST /api/trade/respond` - Accept/reject a trade
- `GET /api/trade/list` - List active trades
- `DELETE /api/trade/cancel` - Cancel a proposed trade

#### Admin Controls API
- `POST /api/admin/modify-cash` - Modify player cash
- `POST /api/admin/transfer-property` - Transfer property
- `POST /api/admin/trigger-audit` - Trigger audit for player
- `POST /api/admin/add-bot` - Add AI player
- `POST /api/admin/modify-game-state` - Override game state
- `GET /api/admin/system-status` - Get server status

#### TV Display API
- `GET /api/board/state` - Get current board state
- `GET /api/board/players` - Get player positions
- `GET /api/board/properties` - Get property ownership
- `GET /api/board/events` - Get recent game events

### 7.3 WebSocket Events & Interface Coordination

#### Connection Management
- `connect` - Client connects to WebSocket server
- `disconnect` - Client disconnects from server
- `register_device` - Register device role (player/admin/tv)
- `heartbeat` - Connection alive check
- `reconnect` - Reestablish lost connection

#### Game Events (All Interfaces)
- `player_joined` - New player joined game
- `game_started` - Game has started
- `game_paused` - Game paused by admin
- `game_resumed` - Game resumed from pause
- `game_ended` - Game has ended
- `game_state_update` - Game state change

#### Player-Specific Events
- `your_turn` - Notify player it's their turn
- `dice_rolled` - Dice results and movement
- `property_decision` - Purchase decision required
- `income_report` - Income reporting required at GO
- `jail_options` - Jail escape options
- `trade_proposed` - Trade offer received
- `audit_notice` - Player is being audited

#### Admin-Specific Events
- `player_status_update` - Player status changes
- `suspicious_activity` - Potential rule violation
- `trade_approval_needed` - Admin approval required
- `system_alert` - Technical issue detected
- `bot_action_taken` - AI player made a move

#### TV Board-Specific Events
- `board_refresh` - Full board state update
- `player_moved` - Player token movement
- `property_ownership_changed` - Property ownership visual update
- `economy_phase_changed` - Visual economic indicator update
- `highlight_action` - Highlight specific board action

#### Game Progress Events (All Interfaces)
- `property_purchased` - Property bought by player
- `rent_paid` - Rent transaction occurred
- `turn_ended` - Current turn ended
- `player_bankrupt` - Player has gone bankrupt
- `card_drawn` - Chance/Community Chest card drawn

#### Financial Events (All Interfaces)
- `cash_update` - Player cash changed
- `property_update` - Property status changed
- `loan_created` - New loan/CD created
- `loan_updated` - Loan/CD terms modified
- `inflation_changed` - Economic state changed
- `community_fund_update` - Fund balance changed

#### Interface Synchronization Events
- `tv_board_ready` - TV display is online and ready
- `admin_action` - Admin performed game action
- `view_switch` - TV board switching display modes
- `zoom_property` - Focus on specific property detail
- `notification_broadcast` - System-wide announcement

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

#### Implementation Architecture
```
┌─────────────────┐    ┌────────────────┐    ┌────────────────┐
│ Raspberry Pi    │    │ Cloudflare     │    │ Player Devices │
│                 │    │ Network        │    │                │
│ ┌─────────────┐ │    │                │    │ ┌────────────┐ │
│ │Flask + SQLite│◄────┼────────────────┼────┤►│Mobile Browser│
│ └─────────────┘ │    │                │    │ └────────────┘ │
│                 │    │                │    │                │
│ ┌─────────────┐ │    │                │    │ ┌────────────┐ │
│ │Cloudflared  │◄────┼────────────────┼────┤►│Admin Tablet │
│ │Agent        │ │    │                │    │ └────────────┘ │
│ └─────────────┘ │    │                │    │                │
│                 │    │                │    │ ┌────────────┐ │
│                 │    │                │    │ │TV Browser  │ │
└─────────────────┘    └────────────────┘    │ └────────────┘ │
                                              └────────────────┘
```

### 8.2 Cloudflare Tunnel Setup

#### Account and Installation
1. **Create Cloudflare Account**: Free tier is sufficient
2. **Install Cloudflared Agent**:
   ```bash
   # Download and install cloudflared
   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o cloudflared
   chmod +x cloudflared
   sudo mv cloudflared /usr/local/bin
   
   # Authenticate with Cloudflare
   cloudflared tunnel login
   ```

#### Tunnel Configuration
1. **Create Tunnel**:
   ```bash
   # Create a named tunnel
   cloudflared tunnel create pinopoly
   
   # Configure tunnel (creates ~/.cloudflared/config.yml)
   ```

2. **Configuration File**:
   ```yaml
   # ~/.cloudflared/config.yml
   tunnel: [TUNNEL-ID]
   credentials-file: /home/pi/.cloudflared/[TUNNEL-ID].json
   
   ingress:
     - hostname: pinopoly.yourdomain.com
       service: http://localhost:5000
     - service: http_status:404
   ```

3. **Route Traffic**:
   ```bash
   # Create DNS record (if using custom domain)
   cloudflared tunnel route dns pinopoly pinopoly.yourdomain.com
   
   # Or use the Cloudflare-provided subdomain
   # e.g., https://pinopoly-tunnel.trycloudflare.com
   ```

4. **Start Tunnel Service**:
   ```bash
   # Create systemd service for auto-start
   sudo cloudflared service install
   
   # Enable and start the service
   sudo systemctl enable cloudflared
   sudo systemctl start cloudflared
   ```

### 8.3 Game Server Configuration for Cloudflare-Only Access

#### Flask Server Setup
```python
# app.py configuration for Cloudflare Tunnel
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SERVER_NAME'] = 'pinopoly.yourdomain.com'  # Optional
app.config['PREFERRED_URL_SCHEME'] = 'https'

# For WebSockets
socketio = SocketIO(app, 
                    cors_allowed_origins="*",
                    path="/ws",
                    async_mode='eventlet')

# Bind only to localhost since all traffic comes through Cloudflare
if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000)
```

#### Security Headers
```python
@app.after_request
def add_security_headers(response):
    # Enforce HTTPS with Cloudflare
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content security policy
    response.headers['Content-Security-Policy'] = "default-src 'self' https: wss:; script-src 'self' 'unsafe-inline' https:; style-src 'self' 'unsafe-inline' https:;"
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response
```

### 8.4 WebSocket Configuration for Cloudflare

#### Client-Side WebSocket Connection
```javascript
// Connect to WebSockets through Cloudflare Tunnel
const socket = io({
    path: '/ws',  // Custom path for WebSockets
    transports: ['websocket'],
    secure: true,
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 1000
});

// Handle connection issues
socket.on('connect_error', (error) => {
    console.error('Connection Error:', error);
    showReconnectionMessage();
});

socket.on('reconnect', (attemptNumber) => {
    console.log('Reconnected after ' + attemptNumber + ' attempts');
    hideReconnectionMessage();
});
```

### 8.5 URL Structure with Cloudflare Domain

With Cloudflare Tunnel as the exclusive access method, all URLs include the Cloudflare domain:

- **Player Interface**: `https://pinopoly.yourdomain.com/play?id=[PLAYER_ID]&pin=[PIN]`
- **Admin Console**: `https://pinopoly.yourdomain.com/admin?key=[ADMIN_KEY]`
- **TV Board Display**: `https://pinopoly.yourdomain.com/board?display=tv&key=[DISPLAY_KEY]`

### 8.6 Device Connection Diagram

```
                               ┌────────────────────────┐
                               │                        │
                ┌──────────────┤     Cloudflare         ├───────────────┐
                │              │     Tunnel             │               │
                │              │                        │               │
                │              └────────────────────────┘               │
                │                                                       │
                ▼                                                       ▼
      ┌──────────────────┐                                  ┌──────────────────┐
      │  Admin Tablet    │                                  │  Players'        │
      │  https://pinopoly│                                  │  Mobile Devices  │
      │  .yourdomain.com │                                  │  https://pinopoly│
      │  /admin?key=xyz  │                                  │  .yourdomain.com │
      └──────────────────┘                                  │  /play?id=123    │
                                                            └──────────────────┘
                │                                                      │
                │                                                      │
                │              ┌────────────────────────┐              │
                │              │                        │              │
                └──────────────┤ Raspberry Pi 5 Server  ├──────────────┘
                               │ (Running Pi-nopoly)    │
                               │                        │
                               └────────────────────────┘
                                          ▲
                                          │
                                          │
                               ┌────────────────────────┐
                               │  TV Display            │
                               │  https://pinopoly      │
                               │  .yourdomain.com       │
                               │  /board?display=tv     │
                               └────────────────────────┘
```

### 8.7 Performance Optimization for Cloudflare

#### Latency Reduction Techniques
- **WebSocket Connection Pooling**: Maintain persistent connections
- **Payload Size Optimization**: Minimize data transfer
- **Compression**: Enable gzip/brotli compression
- **Caching Strategy**: Cache static assets at Cloudflare edge
- **Response Time Monitoring**: Track and optimize server responses

#### High Availability
- **Connection Monitoring**: Automatic reconnection if tunnel disconnects
- **Health Checks**: Regular verification of tunnel status
- **Fallback Mechanisms**: Graceful degradation if connection issues occur

### 8.8 Security Considerations for Cloudflare-Only Access

#### Authentication
- **PIN-Based Authentication**: All players require a PIN to join
- **Admin Authentication**: Secure key required for admin access
- **Session Validation**: Regular validation of session integrity
- **Rate Limiting**: Prevent brute force attacks

#### Data Protection
- **End-to-End Encryption**: All traffic encrypted via TLS
- **Input Validation**: Strict validation of all user inputs
- **Content Security Policy**: Prevent XSS and injection attacks
- **Regular Security Scans**: Monitor for vulnerabilities

## SECTION 9: DEVELOPMENT ROADMAP

### 9.1 Phase 1: Core Engine (Weeks 1-3)
- Database setup and models
- Basic game loop
- Property and movement mechanics
- Local network testing

### 9.2 Phase 2: Financial Systems (Weeks 4-6)
- Banking system
- Loans and CDs
- Property improvements
- Inflation engine

### 9.3 Phase 3: User Interfaces (Weeks 7-9)
- Player mobile interface
- Admin dashboard
- TV board display
- UI testing and refinement

### 9.4 Phase 4: Advanced Features (Weeks 10-12)
- AI player implementation
- Trade system
- Audit and tax mechanics
- Crime system

### 9.5 Phase 5: Cloudflare Integration (Weeks 13-14)
- Cloudflare Tunnel setup
- Remote play testing
- Security hardening
- Performance optimization

### 9.6 Phase 6: Final Testing & Deployment (Weeks 15-16)
- Multi-player stress testing
- Bug fixes
- Documentation
- Final deployment

## SECTION 10: PRODUCTION DEPLOYMENT

### 10.1 Raspberry Pi Configuration
- **OS**: Raspberry Pi OS Lite (64-bit)
- **Service Setup**: Systemd for auto-start
- **Resource Monitoring**: CPU, memory, network tracking
- **Backup Strategy**: Daily database backups
- **Display Configuration**: HDMI settings for TV board display

### 10.2 Network Configuration
- **Cloudflare Tunnel Setup**: Primary connection method for all devices
- **Firewall Settings**: Restrict to needed ports only
- **QoS Configuration**: Optimize traffic for Cloudflare Tunnel
- **DNS Settings**: Configure custom domain (optional)
- **Connection Security**: TLS encryption for all traffic

### 10.3 Multi-Device Setup
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

- **URL Distribution**:
  - QR codes for quick player access
  - Preset bookmarks for regular players
  - TV display auto-startup script with Cloudflare URL
  - Admin bookmark with saved credentials

### 10.4 Startup Automation
- **Auto-Launch Script**:
  ```bash
  #!/bin/bash
  # Start Pi-nopoly server
  cd /home/pi/pinopoly
  source venv/bin/activate
  gunicorn --worker-class eventlet -w 1 app:app -b 127.0.0.1:5000 &
  
  # Ensure Cloudflare Tunnel is running
  cloudflared tunnel run pinopoly &
  
  # Launch TV display in kiosk mode
  sleep 5
  chromium-browser --kiosk --start-fullscreen "https://your-pinopoly-domain.com/board?display=tv&key=TV_DISPLAY_KEY"
  ```

- **Systemd Service**:
  ```ini
  [Unit]
  Description=Pi-nopoly Game Server
  After=network.target

  [Service]
  User=pi
  WorkingDirectory=/home/pi/pinopoly
  ExecStart=/home/pi/pinopoly/venv/bin/gunicorn --worker-class eventlet -w 1 app:app -b 0.0.0.0:5000
  Restart=always

  [Install]
  WantedBy=multi-user.target
  ```

### 10.5 Maintenance Procedures
- **Update Protocol**: Safe update procedure
- **Backup Restoration**: Restore from backup steps
- **Troubleshooting Guide**: Common issues and fixes
- **Performance Tuning**: Optimization guidance
- **Multi-Device Diagnostics**: Connection testing tools

## SECTION 11: DYNAMIC CONFIGURATION SYSTEM

### 11.1 Configuration Architecture

Pi-nopoly implements a comprehensive dynamic configuration system that allows real-time adjustment of game parameters without requiring code changes or restarts. This system has three layers:

#### Configuration Layers
1. **Base Configuration**: Default values stored in `config.py`
2. **Database Configuration**: Adjustable values stored in database
3. **Runtime Configuration**: In-memory values that can be modified during gameplay

#### Configuration Categories
- **Game Mechanics**: Rules, timing, movement
- **Economic Variables**: Interest rates, inflation thresholds
- **Property Values**: Prices, rents, improvement costs
- **Player Settings**: Starting cash, loan limits
- **System Settings**: Network, performance, display options

### 11.2 Admin Console Configuration Controls

The admin console provides a comprehensive configuration interface:

#### Real-Time Game Adjustments
- **Economy Controls Panel**:
  - Adjust inflation thresholds
  - Modify interest rates
  - Change tax percentages
  - Set community fund distribution rules
  
- **Property Controls Panel**:
  - Modify property prices globally or individually
  - Adjust rent multipliers
  - Change improvement costs
  - Set mortgage values
  
- **Game Rules Panel**:
  - Toggle house rules (Free Parking, auctions, etc.)
  - Set turn timeouts
  - Adjust dice mechanics (doubles rules, etc.)
  - Configure jail settings (bail amounts, stay duration)
  
- **Player Settings Panel**:
  - Change starting cash amount
  - Set loan limits and terms
  - Adjust audit probabilities
  - Configure AI player behavior

#### Live Effect Preview
- Real-time visualization of how changes will affect game balance
- Estimated impact metrics for each adjustment
- Comparison view between current and proposed settings
- Confirmation dialog showing affected players/properties

#### Save/Load Configuration Profiles
- Save current configuration as named profile
- Load pre-configured game setups
- Export/import configurations between systems
- Quick templates (Quick Game, Economic Challenge, etc.)

### 11.3 Backend Configuration System

#### Configuration Database
```sql
CREATE TABLE config_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    value TEXT NOT NULL,
    data_type TEXT NOT NULL,
    description TEXT,
    min_value TEXT,
    max_value TEXT,
    is_runtime_adjustable BOOLEAN DEFAULT TRUE,
    requires_restart BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE config_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE profile_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    option_id INTEGER NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES config_profiles (id),
    FOREIGN KEY (option_id) REFERENCES config_options (id)
);
```

#### Configuration API Endpoints
- `GET /api/admin/config` - Get all configuration options
- `GET /api/admin/config/category/:category` - Get options by category
- `POST /api/admin/config/update` - Update specific options
- `GET /api/admin/config/profiles` - Get saved configuration profiles
- `POST /api/admin/config/profiles/save` - Save current config as profile
- `POST /api/admin/config/profiles/load/:id` - Load specified profile

### 11.4 Core Game Parameters (All Adjustable)

#### Economic Parameters
```python
# Default configuration in config.py 
# (all accessible through admin interface)

ECONOMIC_CONFIG = {
    # Inflation thresholds
    'recession_threshold': 5000,
    'stable_threshold': 10000,
    'inflation_threshold': 15000,
    'high_inflation_threshold': 20000,
    
    # Inflation effects
    'recession_property_modifier': 0.8,
    'recession_interest_modifier': -0.02,
    'inflation_property_modifier': 1.3, 
    'inflation_interest_modifier': 0.03,
    'high_inflation_property_modifier': 1.6,
    'high_inflation_interest_modifier': 0.06,
    'overheated_property_modifier': 2.0,
    'overheated_interest_modifier': 0.1,
    
    # Interest rates
    'base_loan_rate': 0.1,
    'base_cd_rate_3_lap': 0.08,
    'base_cd_rate_5_lap': 0.12,
    'base_cd_rate_7_lap': 0.18,
    'base_heloc_rate': 0.12,
    
    # Tax system
    'base_income_tax_rate': 0.1,
    'tax_evasion_penalty_multiplier': 2.0,
    'audit_probability_base': 0.1,
    'audit_wealth_factor': 0.02,  # per $1000 above $5000
}

# Player settings
PLAYER_CONFIG = {
    'starting_cash_easy': 3000,
    'starting_cash_normal': 2000,
    'starting_cash_hard': 1000,
    'base_line_of_credit': 1000,
    'max_debt_net_worth_ratio': 2.0,
    'jail_bail_amount': 200,
    'jail_reduced_bail': 100,
    'jail_turn_limit': 3,
    'lawyer_cost': 125,
    'lawyer_success_rate': 0.3,
    'theft_success_rate': 0.7,
}

# Property settings
PROPERTY_CONFIG = {
    'group_bonus_multiplier': 1.5,
    'improvement_cost_factor': 0.5,  # 50% of property value
    'improvement_rent_multiplier': 2.0,
    'mortgage_value_factor': 0.5,  # 50% of property value
    'heloc_value_factor': 0.7,  # 70% of property value
    'heloc_foreclosure_turns': 4,
    'auction_minimum_bid_factor': 0.7,  # 70% of property value
}

# Game mechanics
GAME_CONFIG = {
    'turn_timeout_seconds': 60,
    'free_parking_fund_enabled': True,
    'auction_required': True,
    'go_amount': 200,
    'total_laps': 0,  # 0 for infinite
    'final_lap_cd_value_factor': 0.8,  # 80% value in final laps
}
```

### 11.5 Configuration Change Broadcasting

When configuration changes are made, the system automatically:

1. **Validates** the new values against allowed ranges
2. **Updates** the database configuration
3. **Broadcasts** changes to all clients via WebSockets
4. **Applies** changes to the runtime game state
5. **Logs** the configuration change in the event log

```python
# Example implementation
def update_configuration(category, name, value):
    # Validate the new value
    config_option = ConfigOption.query.filter_by(category=category, name=name).first()
    
    if not config_option:
        return {'error': 'Configuration option not found'}
    
    # Type conversion based on data_type
    if config_option.data_type == 'int':
        try:
            value = int(value)
            if config_option.min_value and value < int(config_option.min_value):
                return {'error': f'Value below minimum of {config_option.min_value}'}
            if config_option.max_value and value > int(config_option.max_value):
                return {'error': f'Value above maximum of {config_option.max_value}'}
        except ValueError:
            return {'error': 'Invalid integer value'}
    
    # Update the database
    config_option.value = str(value)
    config_option.updated_at = datetime.now()
    db.session.commit()
    
    # Update runtime configuration
    app.config[f"{category.upper()}_{name.upper()}"] = value
    
    # Broadcast change to all clients
    socketio.emit('config_updated', {
        'category': category,
        'name': name,
        'value': value,
        'requires_restart': config_option.requires_restart
    })
    
    # Log the change
    log_event('CONFIG_CHANGE', f"Changed {category}.{name} to {value}")
    
    return {'success': True, 'value': value}
```

### 11.6 Configuration Interface Examples

#### JSON Configuration API
```json
{
  "economic": {
    "recession_threshold": {
      "value": 5000,
      "type": "int",
      "min": 1000,
      "max": 10000,
      "description": "Total cash threshold for recession state",
      "runtime_adjustable": true
    },
    "base_loan_rate": {
      "value": 0.1,
      "type": "float",
      "min": 0.01,
      "max": 0.5,
      "description": "Base interest rate for loans",
      "runtime_adjustable": true
    }
  },
  "player": {
    "starting_cash_normal": {
      "value": 2000,
      "type": "int",
      "min": 500,
      "max": 5000,
      "description": "Starting cash in normal difficulty",
      "runtime_adjustable": false
    }
  }
}
```

#### Admin UI Components
```html
<!-- Example configuration slider in admin UI -->
<div class="config-slider">
  <label for="recession-threshold">Recession Threshold ($)</label>
  <input type="range" id="recession-threshold" 
         min="1000" max="10000" step="500" 
         value="5000" 
         data-category="economic" 
         data-name="recession_threshold">
  <span class="value-display">$5,000</span>
  <button class="reset-btn" data-default="5000">Reset</button>
</div>

<!-- Example configuration toggle -->
<div class="config-toggle">
  <label for="free-parking-fund">Free Parking Fund</label>
  <input type="checkbox" id="free-parking-fund" 
         checked 
         data-category="game" 
         data-name="free_parking_fund_enabled">
  <button class="reset-btn" data-default="true">Reset</button>
</div>
```

## SECTION 12: ASYNCHRONOUS & PREMIUM GAMEPLAY EXPERIENCE

### 12.1 Asynchronous Architecture

Pi-nopoly is built on a fully asynchronous architecture that allows multiple players to interact with the game simultaneously, regardless of whose turn it is. This creates a premium, modern gameplay experience similar to high-quality online games.

#### Architectural Principles
- **Full Concurrency**: All players can access their interfaces simultaneously
- **Non-Blocking Operations**: Player actions don't block other players
- **Real-Time Synchronization**: Changes instantly propagate to all connected devices
- **Background Processing**: Game logic runs independently of user interfaces
- **Event-Driven Design**: Game progresses based on event triggers, not sequential code

#### Core Asynchronous Components
```
┌─────────────────────┐     ┌───────────────┐     ┌─────────────────┐
│ User Interfaces     │     │ Event System  │     │ Game Engine     │
│ (Multiple Devices)  │◄───►│ (WebSockets)  │◄───►│ (Background)    │
└─────────────────────┘     └───────────────┘     └─────────────────┘
         ▲                         ▲                      ▲
         │                         │                      │
         ▼                         ▼                      ▼
┌─────────────────────┐     ┌───────────────┐     ┌─────────────────┐
│ Player Actions      │     │ State Manager │     │ Database        │
│ (Async API Calls)   │────►│ (Atomic Ops)  │────►│ (Transactions)  │
└─────────────────────┘     └───────────────┘     └─────────────────┘
```

### 12.2 Non-Turn-Based Player Activities

Players can perform these actions regardless of whose turn it is:

#### Finance Management
- Review financial portfolio
- Manage loans and CDs
- Calculate investment returns
- Plan property improvements
- Analyze risk metrics
- Check tax obligations

#### Trade Activities
- Propose trades to other players
- Review incoming trade offers
- Counter-offer existing proposals
- Analyze property portfolios
- Calculate trade valuations

#### Strategic Planning
- View property ownership map
- Check risk of landing on opponents' properties
- Plan purchase/improvement strategy
- Calculate probability outcomes
- Review economic trends
- Track opponent wealth

#### Social Interaction
- In-game chat with other players
- Negotiate deals informally
- Form strategic alliances
- React to game events with emoji

### 12.3 Premium Interface Components

The gameplay experience features premium interface elements typically found in high-quality online games:

#### Animation & Visual Effects
- **Dice Roll**: 3D physics-based rolling animation
- **Player Movement**: Smooth token movement with easing
- **Property Purchase**: Visual ownership transition effect
- **Money Transfer**: Animated currency flow between players
- **State Changes**: Visual transitions for economic phases

#### Sound Design
- **Ambient Background**: Background sounds based on economic phase
- **Event Sounds**: Distinct sounds for key game events
- **Alert Tones**: Notification sounds for player's turn, trades, etc.
- **Success/Failure**: Auditory feedback for actions
- **Volume Controls**: Individual volume settings for each sound category

#### Haptic Feedback (Mobile)
- Vibration patterns for dice rolls
- Subtle feedback for successful purchases
- Alert vibration for turn notification
- Custom patterns for different event types

#### Visual Polish
- **Theme Support**: Light/dark mode
- **Smooth Transitions**: All state changes have proper animations
- **Loading States**: Animated placeholders during data fetching
- **Micro-interactions**: Subtle feedback for all user actions
- **Consistent Design Language**: Professional visual identity throughout

### 12.4 Concurrent User Experience

The system supports these concurrent user scenarios:

#### Multi-Device Interaction
- Player A rolls dice on their turn
- Player B is simultaneously reviewing their properties
- Player C is analyzing the economic trends
- Player D is preparing a trade offer
- Admin is monitoring game health
- TV display updates to show all changes in real-time

#### Transaction Concurrency
- Multiple financial transactions processed simultaneously
- Trade proposals can occur during other player actions
- Property improvements can be purchased outside of turns
- Loan applications processed in the background

#### Conflict Resolution
- **Atomic Database Operations**: Ensure data consistency
- **Optimistic UI Updates**: Show changes immediately, confirm after server response
- **Conflict Detection**: Identify and resolve conflicting actions
- **Retry Mechanism**: Gracefully handle and retry failed operations
- **Version Tracking**: Ensure clients have current game state

### 12.5 Technical Implementation

#### Asynchronous Backend
```python
# Example of asynchronous event processing
@socketio.on('propose_trade')
def handle_trade_proposal(data):
    # Create background task for processing
    socketio.start_background_task(
        process_trade_proposal,
        data['proposer_id'],
        data['receiver_id'],
        data['offer']
    )
    
    # Return immediately to client
    return {'status': 'processing', 'trade_id': generate_id()}

def process_trade_proposal(proposer_id, receiver_id, offer):
    # This runs in background thread
    try:
        # Process the trade proposal
        trade = create_trade_proposal(proposer_id, receiver_id, offer)
        
        # Notify involved players
        socketio.emit('trade_proposed', 
                     trade.to_dict(),
                     room=get_player_room(receiver_id))
        
        socketio.emit('trade_submitted',
                     trade.to_dict(),
                     room=get_player_room(proposer_id))
                     
        # Notify all spectators
        socketio.emit('trade_activity',
                     {'proposer': get_player_name(proposer_id),
                      'receiver': get_player_name(receiver_id)},
                     broadcast=True)
    except Exception as e:
        # Handle errors and notify user
        socketio.emit('trade_error',
                     {'error': str(e)},
                     room=get_player_room(proposer_id))
```

#### Concurrent UI Updates
```javascript
// Frontend handling of concurrent updates
// This allows the UI to remain responsive while actions are processing

// Optimistic updates for immediate feedback
function buyProperty(propertyId) {
    // Show immediate visual feedback
    UI.showBuyingAnimation(propertyId);
    
    // Add to local state optimistically
    const property = gameState.properties[propertyId];
    property.ownerId = currentPlayerId;
    UI.updatePropertyDisplay(property);
    
    // Send to server
    api.buyProperty(propertyId)
        .then(response => {
            // Confirmed by server, update with actual data
            gameState.updateProperty(response.property);
            gameState.updatePlayerCash(response.playerCash);
            UI.hideLoadingIndicator();
        })
        .catch(error => {
            // Revert optimistic update on error
            property.ownerId = null;
            UI.updatePropertyDisplay(property);
            UI.showErrorMessage(error.message);
        });
}

// Real-time WebSocket updates
socket.on('property_updated', (updatedProperty) => {
    // Another player's action affected this property
    if (updatedProperty.id === currentlyViewingPropertyId) {
        // If we're looking at this property, show a non-blocking notification
        UI.showFloatingNotification(`This property was just ${updatedProperty.owner ? 'purchased' : 'updated'}`);
    }
    
    // Update local state
    gameState.updateProperty(updatedProperty);
    
    // Refresh UI if needed, without interrupting user
    UI.refreshPropertyList();
});
```

### 12.6 Responsive Design for All Devices

The game provides a premium experience across all device types:

#### Mobile-First Design
- Touch-optimized controls
- Swipe gestures for navigation
- Bottom navigation for one-handed use
- Responsive to all screen sizes
- Portrait and landscape orientations

#### Tablet Optimization
- Split-view interface for more information
- Enhanced data visualizations
- Multi-column layouts
- Drag-and-drop trade interface
- Property comparison tools

#### Desktop Enhancement
- Keyboard shortcuts
- Hover states for additional information
- Multi-window support
- Advanced statistical views
- Detailed economic analysis

#### TV Display Experience
- Large, readable text from distance
- Focused on essential information
- Animated transitions between views
- High-contrast color scheme
- Periodic cycling through different data views

### 12.7 Premium User Experience Features

#### Contextual Help System
- Tooltip explanations for all game concepts
- Contextual hints based on player situation
- Interactive tutorials for new players
- Suggested actions based on game state
- Rich onboarding experience

#### Personalization
- Player color themes
- Custom token selection
- Interface layout preferences
- Notification preferences
- Accessibility options

#### Social Features
- Player profiles
- Game history statistics
- Achievement tracking
- Custom player emoji reactions
- Game replay highlights

#### Ambient Awareness
- Economic phase highlighted in UI color scheme
- Background patterns reflect game progress
- Unobtrusive alerts for important events
- Visual cues for turn status
- Dynamic UI elements based on player performance

## CHECKLIST: COMPREHENSIVE DESIGN VERIFICATION

To ensure our design document covers all critical aspects of Pi-nopoly implementation, this section serves as a final verification checklist.

### Core Game Systems ✓
- [x] Property system with values, groups, and improvements
- [x] Banking system with transactions and balances
- [x] Financial instruments (loans, CDs, HELOCs)
- [x] Advanced inflation engine with economic phases
- [x] Tax and audit system with evasion mechanics
- [x] Crime system with theft and jail
- [x] Community fund with multiple sources and distributions
- [x] Trading system with property and cash exchange
- [x] Dynamic bot system supporting up to 8 players total
- [x] Turn engine with dice, movement, and actions

### Technical Architecture ✓
- [x] Flask/Python backend implementation
- [x] SQLite database with complete schema
- [x] WebSocket communication for real-time updates
- [x] REST API endpoints for all game actions
- [x] Cloudflare Tunnel as exclusive connectivity method
- [x] Asynchronous processing for concurrent player actions
- [x] Responsive design for all device types
- [x] Authentication and security mechanisms
- [x] Real-time state synchronization across devices
- [x] Dynamic configuration system for game parameters

### User Interfaces ✓
- [x] Player mobile interface with all required tabs
- [x] Admin dashboard with complete game controls
- [x] TV board display with visual game state
- [x] Premium animations and visual effects
- [x] Sound design for game events
- [x] Interface for bot management and configuration
- [x] Asynchronous UI updates with optimistic rendering
- [x] Trade interface with property/cash exchange
- [x] Economic indicators and visualizations
- [x] Player interaction features (chat, reactions)

### Player Experience ✓
- [x] Concurrent access for all players regardless of turn
- [x] Real-time feedback for all game events
- [x] Non-blocking UI design during other players' turns
- [x] Visual polish comparable to commercial games
- [x] Contextual help and tutorials
- [x] Personalization options
- [x] Social features and player interactions
- [x] Strategic depth through economic system
- [x] Scalability from 2-8 players (human or bot)
- [x] Dynamic difficulty adjustments

### Deployment & Operations ✓
- [x] Raspberry Pi setup and optimization
- [x] Cloudflare Tunnel configuration
- [x] System monitoring and maintenance
- [x] Backup and recovery procedures
- [x] Performance optimization techniques
- [x] Security hardening measures
- [x] Update mechanisms
- [x] Startup automation
- [x] Error handling and recovery
- [x] Documentation for operation

All critical aspects of Pi-nopoly have been thoroughly detailed in this document, providing a complete blueprint for implementation.