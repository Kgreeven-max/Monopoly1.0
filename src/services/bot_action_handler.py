import random
import logging
from ..models import db
from ..models.player import Player
from ..models.property import Property
from ..models.game_state import GameState
from ..models.transaction import Transaction
from ..models.special_space import SpecialSpace

logger = logging.getLogger(__name__)

class BotActionHandler:
    """Handles the execution of core game actions initiated by bots."""
    
    def __init__(self):
        # Dependencies like db session or other services could be injected here
        # For now, it accesses db and models directly
        pass

    def roll_dice(self):
        """Simulates rolling two dice."""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2
        doubles = dice1 == dice2
        logger.debug(f"Dice roll: {dice1}, {dice2} (Total: {total}, Doubles: {doubles})")
        return {
            "dice1": dice1,
            "dice2": dice2,
            "total": total,
            "doubles": doubles
        }

    def process_move(self, player: Player, roll_total: int):
        """Processes player movement, updates position, and handles passing GO."""
        if not player:
            logger.error("process_move called with invalid player object.")
            return None # Or raise error
            
        old_position = player.position
        board_size = 40 # TODO: Get board size from game config/GameState
        new_position = (old_position + roll_total) % board_size
        
        logger.debug(f"Processing move for Player {player.id}: From {old_position} + {roll_total} -> {new_position}")
        
        player.position = new_position
        # TODO: Remove commit - should be handled by calling controller
        # db.session.commit() 
        # Temporarily committing to maintain existing behavior until controller refactor
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Error committing player position update for player {player.id}: {e}", exc_info=True)
            db.session.rollback() # Rollback on error
            # Re-raise or return error indicator?
            raise

        passed_go = (new_position < old_position)
        if passed_go:
            logger.info(f"Player {player.id} passed GO.")
            # TODO: Access GameState more cleanly (pass as argument?)
            game_state = GameState.query.first()
            if game_state:
                game_state.advance_lap()
                go_amount = 200 # TODO: Get GO amount from game config/GameState
                logger.debug(f"Awarding ${go_amount} for passing GO to Player {player.id}")
                player.money += go_amount
                # TODO: Remove commit
                # db.session.commit() 
                # Temporarily committing
                try:
                    db.session.commit()
                    # Record GO transaction
                    # Using Transaction.create assumes a helper method. If not, use db.session.add()
                    go_transaction = Transaction(
                        from_player_id=None, # Bank
                        to_player_id=player.id,
                        amount=go_amount,
                        transaction_type="passed_go",
                        description=f"Passed GO (Lap {game_state.laps_completed})"
                    )
                    db.session.add(go_transaction)
                    # TODO: Remove commit
                    # db.session.commit() 
                    # Temporarily committing transaction
                    db.session.commit()
                    logger.debug(f"Recorded GO transaction {go_transaction.id} for Player {player.id}")
                except Exception as e:
                    logger.error(f"Error committing GO payment/transaction for player {player.id}: {e}", exc_info=True)
                    db.session.rollback()
                    # Should passing GO fail the whole move?
                    raise
            else:
                logger.warning(f"Cannot process passing GO for Player {player.id}: GameState not found.")

        return {
            "old_position": old_position,
            "new_position": new_position,
            "passed_go": passed_go
        }

    def handle_property_space(self, player: Player, property_obj: Property, buy_decision: bool):
        """Handles actions when a player lands on a property space (buy, pay rent)."""
        if not player or not property_obj:
            logger.error(f"handle_property_space called with invalid player or property object.")
            return []
            
        actions = []
        logger.debug(f"Handling property space {property_obj.name} for Player {player.id}. Owner: {property_obj.owner_id}")
        
        # --- Unowned Property --- 
        if property_obj.owner_id is None:
            logger.debug(f"Property is unowned. Bot decision to buy: {buy_decision}")
            if buy_decision:
                price = property_obj.current_price
                if player.money >= price:
                    logger.info(f"Player {player.id} buying {property_obj.name} for ${price}")
                    player.money -= price
                    property_obj.owner_id = player.id
                    # TODO: Remove commit
                    # db.session.commit()
                    # Temporarily committing
                    try:
                        db.session.commit() 
                        # Record transaction
                        purchase_tx = Transaction(
                            from_player_id=player.id,
                            to_player_id=None, # Bank
                            amount=price,
                            transaction_type="property_purchase",
                            property_id=property_obj.id,
                            description=f"Purchase of {property_obj.name}"
                        )
                        db.session.add(purchase_tx)
                        # TODO: Remove commit
                        # db.session.commit()
                        # Temporarily committing
                        db.session.commit()
                        logger.debug(f"Recorded purchase transaction {purchase_tx.id}")
                        
                        actions.append({
                            "action": "buy_property",
                            "property_id": property_obj.id,
                            "property_name": property_obj.name,
                            "price": price
                        })
                    except Exception as e:
                         logger.error(f"Error committing property purchase for Player {player.id}, Property {property_obj.id}: {e}", exc_info=True)
                         db.session.rollback()
                         # Should revert cash/ownership changes? Yes.
                         player.money += price
                         property_obj.owner_id = None # Revert ownership on failed commit
                         # Maybe raise here to signal failure
                         raise
                else:
                    logger.warning(f"Player {player.id} decided to buy {property_obj.name} but lacked funds (${player.money} < ${price})")
                    # Indicate failed attempt
                    actions.append({
                        "action": "buy_property_failed_funds",
                        "property_id": property_obj.id,
                        "property_name": property_obj.name,
                        "price": price
                    })
                    # NOTE: In Monopoly rules, if you decide to buy but can't afford,
                    # you might have to mortgage/sell. If still can't, it goes to auction.
                    # Current logic just fails the purchase. Needs review against game rules.
                    # Triggering auction might be the correct step here.
                    actions.append({
                        "action": "trigger_auction", # Signal to controller
                        "property_id": property_obj.id,
                        "property_name": property_obj.name,
                        "reason": "Decided to buy but lacked funds"
                    })

            else: # Bot decided not to buy
                logger.info(f"Player {player.id} declined to buy {property_obj.name}. Triggering auction.")
                actions.append({
                    "action": "decline_property", # Explicit decline action
                    "property_id": property_obj.id,
                    "property_name": property_obj.name,
                })
                # Signal to controller to start auction
                actions.append({
                    "action": "trigger_auction",
                    "property_id": property_obj.id,
                    "property_name": property_obj.name,
                    "reason": "Player declined purchase"
                })

        # --- Owned by Another Player --- 
        elif property_obj.owner_id != player.id:
            owner = Player.query.get(property_obj.owner_id)
            if owner: 
                # Calculate rent using helper method
                # TODO: Pass dice roll if needed for utilities
                rent_amount = self._calculate_rent(property_obj)
                logger.info(f"Player {player.id} owes ${rent_amount} rent to Player {owner.id} for {property_obj.name}")
                
                if player.money >= rent_amount:
                    player.money -= rent_amount
                    owner.money += rent_amount
                    # TODO: Remove commit
                    # db.session.commit()
                    # Temporarily committing
                    try:
                        db.session.commit()
                        # Record transaction
                        rent_tx = Transaction(
                            from_player_id=player.id,
                            to_player_id=owner.id,
                            amount=rent_amount,
                            transaction_type="rent_payment",
                            property_id=property_obj.id,
                            description=f"Rent for {property_obj.name}"
                        )
                        db.session.add(rent_tx)
                        # TODO: Remove commit
                        # db.session.commit()
                        # Temporarily committing
                        db.session.commit()
                        logger.debug(f"Recorded rent transaction {rent_tx.id}")
                        
                        actions.append({
                            "action": "pay_rent",
                            "property_id": property_obj.id,
                            "property_name": property_obj.name,
                            "owner_id": owner.id,
                            "owner_name": owner.username,
                            "amount": rent_amount
                        })
                    except Exception as e:
                        logger.error(f"Error committing rent payment from {player.id} to {owner.id}: {e}", exc_info=True)
                        db.session.rollback()
                        # Revert cash transfer
                        player.money += rent_amount
                        owner.money -= rent_amount
                        raise
                else:
                    logger.warning(f"Player {player.id} cannot afford rent ${rent_amount} for {property_obj.name}. Available cash: ${player.money}")
                    # Signal to controller that player needs to manage assets or declare bankruptcy
                    actions.append({
                        "action": "needs_to_liquidate_for_rent", 
                        "property_id": property_obj.id,
                        "property_name": property_obj.name,
                        "owner_id": property_obj.owner_id,
                        "rent_amount": rent_amount,
                        "available_cash": player.money
                    })
            else:
                logger.error(f"Rent calculation failed: Owner Player {property_obj.owner_id} not found for property {property_obj.id}")
                # Maybe add an action indicating error? 
                actions.append({"action": "error", "message": "Property owner not found"})

        # --- Owned by Self --- 
        else: # property_obj.owner_id == player.id
            logger.debug(f"Player {player.id} landed on own property {property_obj.name}. No action needed.")
            actions.append({
                "action": "landed_on_own_property",
                "property_id": property_obj.id,
                "property_name": property_obj.name
            })

        return actions

    def handle_chance_space(self, player: Player):
        """Handles actions when a player lands on a Chance space."""
        if not player:
            logger.error("handle_chance_space called with invalid player object.")
            return []
            
        logger.info(f"Player {player.id} landed on a Chance space.")
        
        # We don't need to make any decisions here - the card draw and effects
        # are handled by the SpecialSpaceController, which our caller should invoke
        
        return [{
            "action": "draw_chance_card",
            "player_id": player.id
        }]
    
    def handle_community_chest_space(self, player: Player):
        """Handles actions when a player lands on a Community Chest space."""
        if not player:
            logger.error("handle_community_chest_space called with invalid player object.")
            return []
            
        logger.info(f"Player {player.id} landed on a Community Chest space.")
        
        # We don't need to make any decisions here - the card draw and effects
        # are handled by the SpecialSpaceController, which our caller should invoke
        
        return [{
            "action": "draw_community_chest_card",
            "player_id": player.id
        }]
    
    def handle_tax_space(self, player: Player, tax_space_details):
        """Handles actions when a player lands on a Tax space."""
        if not player or not tax_space_details:
            logger.error("handle_tax_space called with invalid player object or tax details.")
            return []
            
        tax_amount = tax_space_details.get('amount', 0)
        tax_name = tax_space_details.get('name', 'Tax')
        
        logger.info(f"Player {player.id} landed on {tax_name} space, needs to pay ${tax_amount}.")
        
        if player.money >= tax_amount:
            # Bot can afford the tax
            return [{
                "action": "pay_tax",
                "player_id": player.id,
                "tax_name": tax_name,
                "tax_amount": tax_amount
            }]
        else:
            # Bot needs to manage assets to pay tax
            return [{
                "action": "manage_assets_for_tax",
                "player_id": player.id,
                "tax_name": tax_name, 
                "tax_amount": tax_amount,
                "available_cash": player.money
            }]

    def handle_go_to_jail_space(self, player: Player):
        """Handles actions when a player lands on Go To Jail space."""
        if not player:
            logger.error("handle_go_to_jail_space called with invalid player object.")
            return []
            
        logger.info(f"Player {player.id} landed on Go To Jail space.")
        
        # Move player to jail position (which is 10)
        player.position = 10
        player.in_jail = True
        player.jail_turns = 0
        
        try:
            db.session.commit()
            
            return [{
                "action": "went_to_jail",
                "player_id": player.id,
                "message": "Player went to jail"
            }]
        except Exception as e:
            logger.error(f"Error sending player {player.id} to jail: {e}", exc_info=True)
            db.session.rollback()
            raise

    def _calculate_rent(self, property_obj: Property, dice_roll: int = None):
        """Calculates the rent owed for landing on a given property."""
        # Basic rent calculation - Needs significant refinement for Monopoly rules
        if not property_obj.owner_id:
            return 0 # Unowned, no rent

        # TODO: Implement full rent calculation logic based on game rules
        # Factors:
        # 1. Base rent (from rent_level[0]?)
        # 2. Houses/Hotels (rent_level[1-5]?)
        # 3. Monopoly bonus (double base rent if un-improved set owned)
        # 4. Railroads (Number owned by owner: 25, 50, 100, 200)
        # 5. Utilities (Number owned by owner * dice roll: 4x or 10x)
        # 6. Game State modifiers (e.g., double rent events)
        # 7. Mortgaged status (No rent if mortgaged)

        if property_obj.is_mortgaged:
             logger.debug(f"Property {property_obj.name} is mortgaged. Rent is 0.")
             return 0

        base_rent = property_obj.rent_level[0] if property_obj.rent_level else 0
        rent = base_rent # Start with base rent
        owner_id = property_obj.owner_id

        # --- Railroad Specific Rent --- 
        if property_obj.monopoly_group == "Railroad":
            owner_railroads = Property.query.filter_by(owner_id=owner_id, monopoly_group="Railroad", is_mortgaged=False).count()
            if owner_railroads > 0:
                rent = 25 * (2**(owner_railroads - 1)) # 25, 50, 100, 200
                logger.debug(f"Railroad rent: Owner {owner_id} has {owner_railroads} railroads. Rent: ${rent}")
            else: # Should not happen if property_obj is a railroad owned by owner_id
                 logger.warning(f"Could not calculate railroad rent for {property_obj.name}. Owner {owner_id} owns 0 unmortgaged railroads?")
                 rent = 0 

        # --- Utility Specific Rent --- 
        elif property_obj.monopoly_group == "Utility":
            if dice_roll is None:
                logger.warning(f"Dice roll needed to calculate utility rent for {property_obj.name}, but not provided. Using placeholder 7.")
                # This indicates a design issue - dice roll context needs to be available
                dice_roll = 7 # Placeholder - Requires actual dice roll from the turn!
            
            owner_utilities = Property.query.filter_by(owner_id=owner_id, monopoly_group="Utility", is_mortgaged=False).count()
            multiplier = 4 if owner_utilities == 1 else (10 if owner_utilities == 2 else 0)
            rent = dice_roll * multiplier
            logger.debug(f"Utility rent: Owner {owner_id} has {owner_utilities} utilities. Dice roll {dice_roll}. Multiplier {multiplier}. Rent: ${rent}")

        # --- Standard Property Rent (Color Groups) --- 
        else:
            improvement_level = property_obj.improvement_level
            if improvement_level > 0:
                # Rent with houses/hotel
                if improvement_level < len(property_obj.rent_level):
                    rent = property_obj.rent_level[improvement_level]
                    logger.debug(f"Property {property_obj.name} has {improvement_level} improvements. Rent: ${rent}")
                else:
                    logger.error(f"Invalid improvement level {improvement_level} for property {property_obj.name}. Max rent level index: {len(property_obj.rent_level)-1}")
                    rent = property_obj.rent_level[-1] # Use max rent as fallback
            else:
                # Base rent - check for monopoly bonus
                group_properties = Property.query.filter_by(monopoly_group=property_obj.monopoly_group).all()
                all_owned_by_owner = True
                if not group_properties: # Should not happen for standard props
                     all_owned_by_owner = False
                     logger.warning(f"Could not find group properties for {property_obj.monopoly_group} to check monopoly status.")
                else:
                    for prop in group_properties:
                        if prop.owner_id != owner_id or prop.is_mortgaged:
                            all_owned_by_owner = False
                            break
                
                if all_owned_by_owner:
                    rent = base_rent * 2 # Double base rent for un-improved monopoly
                    logger.debug(f"Owner {owner_id} has un-improved monopoly on {property_obj.monopoly_group}. Base rent {base_rent} doubled to {rent}.")
                else:
                    rent = base_rent # Just base rent
                    logger.debug(f"Owner {owner_id} does not have monopoly on {property_obj.monopoly_group}. Rent is base: ${rent}.")

        # TODO: Apply global game state multipliers if any (e.g., event card effects)

        return int(round(rent))

    def end_turn(self, player: Player):
        """Placeholder for any actions needed at the very end of a bot's turn processing."""
        # Currently, just logs. Could be used for state cleanup if needed.
        logger.debug(f"BotActionHandler ending turn processing for Player {player.id}")
        # No direct game state changes needed here usually, handled by GameController. 

    def handle_free_parking_space(self, player: Player):
        """Handles actions when a player lands on Free Parking space."""
        if not player:
            logger.error("handle_free_parking_space called with invalid player object.")
            return []
            
        logger.info(f"Player {player.id} landed on a Free Parking space.")
        
        # We don't need to make any decisions here - the action is handled by the SpecialSpaceController
        
        return [{
            "action": "free_parking",
            "player_id": player.id
        }]

    def handle_market_fluctuation_space(self, player: Player):
        """Handles actions when a player lands on a Market Fluctuation space."""
        if not player:
            logger.error("handle_market_fluctuation_space called with invalid player object.")
            return []
            
        logger.info(f"Player {player.id} landed on a Market Fluctuation space.")
        
        # Market fluctuation is handled by the EconomicCycleController via SpecialSpaceController
        # No decision is needed from the bot - just indicate the action
        
        return [{
            "action": "market_fluctuation",
            "player_id": player.id
        }]

    def process_passing_go(self, player):
        """Process a player passing GO."""
        go_amount = self.get_go_amount()
        player.money += go_amount
        self.logger.info(f"Player {player.id} passed GO and collected ${go_amount}")
        return {
            "passing_go": True,
            "amount": go_amount,
            "new_balance": player.money
        }

    def buy_property(self, player, property_id):
        """Buy a property for a player."""
        # Get the property
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {"success": False, "error": "Property not found"}
        
        # Check if property is already owned
        if property_obj.owner_id:
            return {"success": False, "error": "Property already owned"}
        
        # Check if player has enough money
        price = property_obj.price
        if player.money >= price:
            # Buy the property
            property_obj.owner_id = player.id
            player.money -= price
            db.session.add(property_obj)
            db.session.add(player)
            db.session.commit()
            
            self.logger.info(f"Player {player.id} bought {property_obj.name} for ${price}")
            
            return {
                "success": True,
                "property_id": property_id,
                "property_name": property_obj.name,
                "price": price,
                "new_balance": player.money
            }
        else:
            self.logger.warning(f"Player {player.id} decided to buy {property_obj.name} but lacked funds (${player.money} < ${price})")
            return {
                "success": False,
                "error": "Not enough funds",
                "property_id": property_id,
                "property_name": property_obj.name,
                "price": price,
                "balance": player.money
            }

    def sell_property(self, player, property_id, buyer_id=None, price=None):
        """Sell a property to another player or back to the bank."""
        # Get the property
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {"success": False, "error": "Property not found"}
        
        # Check if player owns the property
        if property_obj.owner_id != player.id:
            return {"success": False, "error": "You don't own this property"}
        
        # If selling to bank, price is half the base price
        if not buyer_id:
            price = property_obj.price // 2
            property_obj.owner_id = None
            player.money += price
            db.session.add(property_obj)
            db.session.add(player)
            db.session.commit()
            
            self.logger.info(f"Player {player.id} sold {property_obj.name} to the bank for ${price}")
            
            return {
                "success": True,
                "property_id": property_id,
                "property_name": property_obj.name,
                "price": price,
                "new_balance": player.money
            }
        
        # If selling to another player, handle the transaction
        # ...

    def pay_rent(self, player, property_id):
        """Pay rent to the owner of a property."""
        # Get the property
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {"success": False, "error": "Property not found"}
        
        # Check if property is owned and not by the current player
        if not property_obj.owner_id or property_obj.owner_id == player.id:
            return {"success": False, "error": "No rent due"}
        
        # Get the owner
        owner = Player.query.get(property_obj.owner_id)
        if not owner:
            return {"success": False, "error": "Owner not found"}
        
        # Calculate rent amount
        rent_amount = self._calculate_rent(property_obj)
        
        # Check if player has enough money
        if player.money >= rent_amount:
            # Pay rent
            player.money -= rent_amount
            owner.money += rent_amount
            db.session.add(player)
            db.session.add(owner)
            db.session.commit()
            
            self.logger.info(f"Player {player.id} paid ${rent_amount} rent to Player {owner.id} for {property_obj.name}")
            
            return {
                "success": True,
                "property_id": property_id,
                "property_name": property_obj.name,
                "rent_amount": rent_amount,
                "owner_id": owner.id,
                "new_balance": player.money
            }
        else:
            self.logger.warning(f"Player {player.id} cannot afford rent ${rent_amount} for {property_obj.name}. Available cash: ${player.money}")
            
            return {
                "success": False,
                "error": "Not enough funds for rent",
                "property_id": property_id,
                "property_name": property_obj.name,
                "rent_amount": rent_amount,
                "owner_id": owner.id,
                "available_cash": player.money
            }

    def pay_tax(self, player, tax_type):
        """Pay tax based on the type of tax."""
        # Calculate tax amount based on type
        if tax_type == "income":
            tax_amount = 200
        elif tax_type == "luxury":
            tax_amount = 75
        else:
            tax_amount = 100  # Default tax amount
        
        # Check if player has enough money
        if player.money >= tax_amount:
            # Pay tax
            player.money -= tax_amount
            db.session.add(player)
            db.session.commit()
            
            self.logger.info(f"Player {player.id} paid ${tax_amount} in {tax_type} tax")
            
            return {
                "success": True,
                "tax_type": tax_type,
                "tax_amount": tax_amount,
                "new_balance": player.money
            }
        else:
            self.logger.warning(f"Player {player.id} cannot afford ${tax_amount} {tax_type} tax")
            
            return {
                "success": False,
                "error": "Not enough funds for tax",
                "tax_type": tax_type,
                "tax_amount": tax_amount,
                "available_cash": player.money
            } 