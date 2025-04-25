import logging
from flask import jsonify, current_app
import os
import psutil
import platform
import datetime
import time
import uuid
import random
from src.models import db
from src.models.game_state import GameState
from src.models.player import Player
from src.models.property import Property
from src.models.finance.loan import Loan # Needed for player details
from src.models.transaction import Transaction
from src.models.bots.base_bot import BotPlayer
from src.models.event import Event, EventType, EventStatus
from src.models.crime import Crime

logger = logging.getLogger(__name__)

class AdminController:
    """Controller for handling administrative actions"""

    def get_admin_game_status(self):
        """Retrieves the overall game status for the admin dashboard."""
        try:
            game_state = GameState.get_instance()
            if not game_state:
                return {"success": False, "error": "Game state not initialized"}

            players = Player.query.all()
            properties = Property.query.all()

            return {
                "success": True,
                "game_state": game_state.to_dict(),
                "player_count": len(players),
                "property_count": len(properties),
                "active_players": sum(1 for p in players if p.in_game),
                "bank_owned_properties": sum(1 for p in properties if not p.owner_id)
            }
        except Exception as e:
            logger.error(f"Error getting admin game status: {e}", exc_info=True)
            return {"success": False, "error": "Failed to retrieve admin game status"}

    def get_admin_player_details(self, player_id):
        """Retrieves detailed information about a specific player for admin view."""
        try:
            player = Player.query.get(player_id)
            if not player:
                return {"success": False, "error": "Player not found"}

            # Assuming relationships are set up correctly (e.g., player.properties, player.loans)
            # Ensure Loan model is imported if needed for player.loans relationship
            return {
                "success": True,
                "player": player.to_dict(),
                "properties": [p.to_dict() for p in player.properties],
                "loans": [l.to_dict() for l in player.loans],
                "net_worth": player.calculate_net_worth()
            }
        except Exception as e:
            logger.error(f"Error getting admin player details for ID {player_id}: {e}", exc_info=True)
            return {"success": False, "error": "Failed to retrieve player details"}

    def reset_game(self):
        """Resets the game by updating the existing game state."""
        try:
            # Get GameController from app_config
            game_controller = current_app.config.get('game_controller')
            if not game_controller:
                logger.error("GameController not found in app config")
                return {"success": False, "error": "Game controller not initialized"}

            # Get current game state 
            from src.models.game_state import GameState
            game_state = GameState.get_instance()
            
            if not game_state:
                logger.error("No game state found")
                return {"success": False, "error": "Game state not found"}
                
            # Reset the game state directly instead of creating a new one
            game_state.reset()
            
            # Reset all players still in game
            from src.models.player import Player
            from src.models.property import Property
            
            players = Player.query.filter_by(in_game=True).all()
            for player in players:
                player.position = 0
                player.money = 1500  # Default starting cash
                player.in_game = False  # Remove all players
                player.is_in_jail = False
                player.jail_turns = 0
                
                # Reset player's properties
                properties = Property.query.filter_by(owner_id=player.id).all()
                for prop in properties:
                    prop.owner_id = None
                    prop.is_mortgaged = False
                    prop.houses = 0
                    prop.hotel = False
                    db.session.add(prop)
                
                db.session.add(player)
            
            # Clear all bots
            bots = Player.query.filter_by(is_bot=True).all()
            for bot in bots:
                bot.in_game = False
                db.session.add(bot)
                
            # Clear the active_bots dictionary if it exists
            from src.controllers.bot_controller import active_bots
            active_bots.clear()
            
            db.session.commit()
            
            # Initialize properties for this game
            if hasattr(game_controller, '_initialize_properties'):
                game_controller._initialize_properties(game_state.game_id)
            
            logger.info(f"Game reset successfully. Game ID: {game_state.game_id}")
            return {
                "success": True,
                "game_id": game_state.game_id,
                "message": "Game reset successfully"
            }
                    
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to reset game: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to reset game: {str(e)}"}
    
    def modify_player_cash(self, player_id, amount, reason):
        """
        Modifies a player's cash balance as an admin action.
        
        Args:
            player_id (int): ID of the player to modify cash for
            amount (int/float): Amount to modify (positive for adding, negative for subtracting)
            reason (str): Reason for the modification
            
        Returns:
            Dict with operation result
        """
        try:
            # Verify player exists
            player = Player.query.get(player_id)
            if not player:
                return {"success": False, "error": "Player not found"}
            
            # Get banker from app config
            banker = current_app.config.get('banker')
            if not banker:
                logger.error("Banker not found in app config")
                return {"success": False, "error": "Banking system not initialized"}
            
            # Get game state
            game_state = GameState.get_instance()
            if not game_state:
                return {"success": False, "error": "Game state not initialized"}
            
            # Record previous balance for logging
            previous_balance = player.money
            
            # Perform the cash modification
            if amount > 0:
                # Adding money
                transaction_result = banker.transfer_to_player(
                    player_id=player_id,
                    amount=abs(amount),
                    reason=f"Admin cash adjustment: {reason}"
                )
            else:
                # Subtracting money
                transaction_result = banker.transfer_from_player(
                    player_id=player_id,
                    amount=abs(amount),
                    reason=f"Admin cash adjustment: {reason}"
                )
            
            if not transaction_result.get('success'):
                return transaction_result
            
            # Create an admin transaction record
            transaction = Transaction(
                player_id=player_id,
                amount=amount,
                description=f"Admin cash adjustment: {reason}",
                transaction_type="ADMIN_ADJUSTMENT",
                timestamp=datetime.datetime.now()
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Log the action
            logger.info(f"Admin modified player {player.username} (ID: {player_id}) cash by {amount}. "
                        f"Previous balance: {previous_balance}, New balance: {player.money}. Reason: {reason}")
            
            # Notify clients of the update
            socket_controller = current_app.config.get('socket_controller')
            if socket_controller:
                socket_controller.notify_player_update(player_id)
                socket_controller.notify_admin_action({
                    "action": "cash_modified",
                    "player_id": player_id,
                    "username": player.username,
                    "amount": amount,
                    "previous_balance": previous_balance,
                    "new_balance": player.money,
                    "reason": reason,
                    "timestamp": datetime.datetime.now().isoformat()
                })
            
            return {
                "success": True,
                "player_id": player_id,
                "username": player.username,
                "previous_balance": previous_balance,
                "new_balance": player.money,
                "amount_changed": amount,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error modifying player cash for ID {player_id}: {e}", exc_info=True)
            db.session.rollback()
            return {"success": False, "error": f"Failed to modify player cash: {str(e)}"}

    def transfer_property(self, property_id, from_player_id, to_player_id, reason):
        """
        Transfers property ownership between players or to/from bank.
        
        Args:
            property_id (int): ID of the property to transfer
            from_player_id (int or None): ID of the current owner (None for bank)
            to_player_id (int or None): ID of the new owner (None for bank)
            reason (str): Reason for the transfer
            
        Returns:
            Dict with operation result
        """
        try:
            # Verify property exists
            property_obj = Property.query.get(property_id)
            if not property_obj:
                return {"success": False, "error": "Property not found"}
            
            # Verify current ownership
            if from_player_id is not None and property_obj.owner_id != from_player_id:
                return {"success": False, "error": "Current owner does not match the property's actual owner"}
            
            # Get player objects (if applicable)
            from_player = None
            to_player = None
            
            if from_player_id is not None:
                from_player = Player.query.get(from_player_id)
                if not from_player:
                    return {"success": False, "error": "Source player not found"}
            
            if to_player_id is not None:
                to_player = Player.query.get(to_player_id)
                if not to_player:
                    return {"success": False, "error": "Target player not found"}
            
            # Record previous ownership for logging
            previous_owner_id = property_obj.owner_id
            previous_owner_name = "Bank" if previous_owner_id is None else Player.query.get(previous_owner_id).username
            
            # Update property ownership
            property_obj.owner_id = to_player_id
            
            # If transferring to bank, reset property development
            if to_player_id is None:
                property_obj.houses = 0
                property_obj.hotel = False
                property_obj.is_mortgaged = False
            
            db.session.commit()
            
            # Log the transfer
            new_owner_name = "Bank" if to_player_id is None else to_player.username
            logger.info(f"Admin transferred property {property_obj.name} (ID: {property_id}) "
                       f"from {previous_owner_name} to {new_owner_name}. Reason: {reason}")
            
            # Notify clients of the update
            socket_controller = current_app.config.get('socket_controller')
            if socket_controller:
                # Notify about property update
                socket_controller.notify_property_update(property_id)
                
                # Notify affected players
                if from_player_id is not None:
                    socket_controller.notify_player_update(from_player_id)
                
                if to_player_id is not None:
                    socket_controller.notify_player_update(to_player_id)
                
                # Notify admins about the action
                socket_controller.notify_admin_action({
                    "action": "property_transferred",
                    "property_id": property_id,
                    "property_name": property_obj.name,
                    "from_player_id": from_player_id,
                    "from_player_name": previous_owner_name,
                    "to_player_id": to_player_id,
                    "to_player_name": new_owner_name,
                    "reason": reason,
                    "timestamp": datetime.datetime.now().isoformat()
                })
            
            return {
                "success": True,
                "property_id": property_id,
                "property_name": property_obj.name,
                "from_player_id": from_player_id,
                "from_player_name": previous_owner_name,
                "to_player_id": to_player_id,
                "to_player_name": new_owner_name,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error transferring property {property_id}: {e}", exc_info=True)
            db.session.rollback()
            return {"success": False, "error": f"Failed to transfer property: {str(e)}"}

    def trigger_player_audit(self, player_id):
        """
        Triggers a comprehensive audit of player's activities and finances.
        
        Args:
            player_id (int): ID of the player to audit
            
        Returns:
            Dict with audit results
        """
        try:
            # Verify player exists
            player = Player.query.get(player_id)
            if not player:
                return {"success": False, "error": "Player not found"}
            
            # Get transactions for player
            transactions = Transaction.query.filter_by(player_id=player_id).order_by(Transaction.timestamp.desc()).all()
            
            # Get properties owned by player
            properties = Property.query.filter_by(owner_id=player_id).all()
            
            # Get loans for player
            loans = Loan.query.filter_by(player_id=player_id).all()
            
            # Calculate total income and expenses
            income = sum(t.amount for t in transactions if t.amount > 0)
            expenses = sum(abs(t.amount) for t in transactions if t.amount < 0)
            
            # Calculate total property value
            property_value = sum(p.current_value for p in properties)
            
            # Calculate improvement value
            improvement_value = sum((p.houses * p.house_price) + (p.hotel * (p.house_price * 5)) for p in properties)
            
            # Calculate total debt
            outstanding_debt = sum(l.remaining_balance for l in loans)
            
            # Calculate net worth
            net_worth = player.cash + property_value + improvement_value - outstanding_debt
            
            # Compare net worth to game average
            all_players = Player.query.all()
            all_net_worths = [p.calculate_net_worth() for p in all_players if p.in_game and p.id != player_id]
            average_net_worth = sum(all_net_worths) / len(all_net_worths) if all_net_worths else 0
            
            # Flag suspicious transactions (large or frequent in short time)
            suspicious_transactions = []
            large_threshold = 1000  # Example threshold for large transactions
            
            # Group transactions by time periods to check for frequency
            time_grouped_transactions = {}
            for t in transactions:
                # Group by hour
                hour_key = t.timestamp.strftime("%Y-%m-%d %H")
                if hour_key not in time_grouped_transactions:
                    time_grouped_transactions[hour_key] = []
                time_grouped_transactions[hour_key].append(t)
                
                # Flag large transactions
                if abs(t.amount) > large_threshold:
                    suspicious_transactions.append({
                        "id": t.id,
                        "amount": t.amount,
                        "description": t.description,
                        "timestamp": t.timestamp.isoformat(),
                        "reason": "Large amount"
                    })
            
            # Flag frequent transactions
            frequency_threshold = 5  # Example threshold for number of transactions per hour
            for hour, hour_transactions in time_grouped_transactions.items():
                if len(hour_transactions) > frequency_threshold:
                    for t in hour_transactions:
                        if not any(st["id"] == t.id for st in suspicious_transactions):
                            suspicious_transactions.append({
                                "id": t.id,
                                "amount": t.amount,
                                "description": t.description,
                                "timestamp": t.timestamp.isoformat(),
                                "reason": f"High frequency ({len(hour_transactions)} transactions in one hour)"
                            })
            
            # Prepare audit report
            audit_report = {
                "success": True,
                "player_id": player_id,
                "username": player.username,
                "timestamp": datetime.datetime.now().isoformat(),
                "financial_summary": {
                    "cash": player.cash,
                    "total_income": income,
                    "total_expenses": expenses,
                    "property_value": property_value,
                    "improvement_value": improvement_value,
                    "outstanding_debt": outstanding_debt,
                    "net_worth": net_worth,
                    "game_average_net_worth": average_net_worth,
                    "variance_from_average": net_worth - average_net_worth
                },
                "properties": [p.to_dict() for p in properties],
                "loans": [l.to_dict() for l in loans],
                "recent_transactions": [t.to_dict() for t in transactions[:20]],  # Last 20 transactions
                "suspicious_transactions": suspicious_transactions,
                "credit_score": player.credit_score
            }
            
            # Log the audit
            logger.info(f"Admin triggered audit for player {player.username} (ID: {player_id})")
            
            # Notify admins about the audit
            socket_controller = current_app.config.get('socket_controller')
            if socket_controller:
                socket_controller.notify_admin_action({
                    "action": "player_audit_completed",
                    "player_id": player_id,
                    "username": player.username,
                    "audit_summary": {
                        "net_worth": net_worth,
                        "suspicious_count": len(suspicious_transactions)
                    },
                    "timestamp": datetime.datetime.now().isoformat()
                })
            
            return audit_report
            
        except Exception as e:
            logger.error(f"Error auditing player {player_id}: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to complete player audit: {str(e)}"}

    def add_bot_player(self, bot_name, bot_type):
        """
        Adds a new bot player to the game.
        
        Args:
            bot_name (str): Name of the bot to create
            bot_type (str): Type of bot (conservative, aggressive, strategic, opportunistic)
            
        Returns:
            Dict with operation result
        """
        try:
            # Validate bot type
            valid_bot_types = ["conservative", "aggressive", "strategic", "opportunistic"]
            if bot_type.lower() not in valid_bot_types:
                return {
                    "success": False, 
                    "error": f"Invalid bot type. Valid types are: {', '.join(valid_bot_types)}"
                }
            
            # Get game state
            game_state = GameState.get_instance()
            if not game_state:
                return {"success": False, "error": "Game state not initialized"}
            
            # Check if game is already full
            max_players = 8  # Typical max players in a game
            active_players = Player.query.filter_by(in_game=True).count()
            if active_players >= max_players:
                return {"success": False, "error": "Game is full, cannot add more players"}
            
            # Get the bot controller from app config
            bot_controller = current_app.config.get('bot_controller')
            if not bot_controller:
                logger.error("BotController not found in app config")
                return {"success": False, "error": "Bot controller not initialized"}
            
            # Create the bot
            result = bot_controller.create_bot(bot_name, bot_type.lower())
            
            if not result.get('success'):
                return result
            
            new_bot_id = result.get('bot_id')
            
            # Log the action
            logger.info(f"Admin added bot player {bot_name} (ID: {new_bot_id}) of type {bot_type}")
            
            # Notify clients of the update
            socket_controller = current_app.config.get('socket_controller')
            if socket_controller:
                socket_controller.notify_game_state_update()
                socket_controller.notify_bot_added({
                    "bot_id": new_bot_id,
                    "bot_name": bot_name,
                    "bot_type": bot_type
                })
            
            return {
                "success": True,
                "bot_id": new_bot_id,
                "bot_name": bot_name,
                "bot_type": bot_type,
                "message": f"Bot player {bot_name} added successfully"
            }
            
        except Exception as e:
            logger.error(f"Error adding bot player {bot_name}: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to add bot player: {str(e)}"}

    def modify_game_state(self, state_changes, reason):
        """
        Modifies the game state with specified changes.
        
        Args:
            state_changes (dict): Dictionary of state variables to change and their new values
            reason (str): Reason for the modification
            
        Returns:
            Dict with operation result
        """
        try:
            # Get game state
            game_state = GameState.get_instance()
            if not game_state:
                return {"success": False, "error": "Game state not initialized"}
            
            # Validate state changes
            if not isinstance(state_changes, dict) or not state_changes:
                return {"success": False, "error": "State changes must be a non-empty dictionary"}
            
            # Track applied changes for logging
            applied_changes = {}
            rejected_changes = {}
            
            # Apply each state change if it's a valid attribute of game state
            for key, value in state_changes.items():
                if hasattr(game_state, key):
                    # Save the old value for logging
                    old_value = getattr(game_state, key)
                    
                    # Apply the change
                    setattr(game_state, key, value)
                    applied_changes[key] = {"old": old_value, "new": value}
                else:
                    rejected_changes[key] = {"error": f"Attribute '{key}' does not exist on game state"}
            
            # If no changes were applied, return an error
            if not applied_changes:
                return {
                    "success": False, 
                    "error": "No valid changes applied", 
                    "rejected_changes": rejected_changes
                }
            
            # Commit changes to database
            db.session.commit()
            
            # Log the action
            logger.info(f"Admin modified game state with changes: {applied_changes}. Reason: {reason}")
            if rejected_changes:
                logger.warning(f"Some game state changes were rejected: {rejected_changes}")
            
            # Notify clients of the update
            socket_controller = current_app.config.get('socket_controller')
            if socket_controller:
                socket_controller.notify_game_state_update()
                socket_controller.notify_admin_action({
                    "action": "game_state_modified",
                    "applied_changes": applied_changes,
                    "rejected_changes": rejected_changes,
                    "reason": reason,
                    "timestamp": datetime.datetime.now().isoformat()
                })
            
            return {
                "success": True,
                "applied_changes": applied_changes,
                "rejected_changes": rejected_changes,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error modifying game state: {e}", exc_info=True)
            db.session.rollback()
            return {"success": False, "error": f"Failed to modify game state: {str(e)}"}
        
    def get_system_status(self):
        """
        Retrieves system status information for the admin dashboard.
        
        Returns:
            Dict with system status information
        """
        try:
            # Get memory usage
            memory = psutil.virtual_memory()
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.5)
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            
            # Get process information
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
            process_cpu = process.cpu_percent(interval=0.5)
            process_threads = process.num_threads()
            process_start_time = datetime.datetime.fromtimestamp(process.create_time()).isoformat()
            
            # Get database statistics
            try:
                player_count = Player.query.count()
                property_count = Property.query.count()
                transaction_count = Transaction.query.count()
                bot_count = BotPlayer.query.count()
                
                db_stats = {
                    "players": player_count,
                    "properties": property_count,
                    "transactions": transaction_count,
                    "bots": bot_count
                }
            except Exception as db_error:
                logger.error(f"Error getting database statistics: {db_error}")
                db_stats = {"error": str(db_error)}
            
            # Get game state
            game_state = GameState.get_instance()
            game_running = game_state is not None
            
            # Get active socket connections
            socket_controller = current_app.config.get('socket_controller')
            if socket_controller:
                try:
                    active_connections = socket_controller.get_connection_count()
                except Exception as sc_error:
                    logger.error(f"Error getting socket connections: {sc_error}")
                    active_connections = {"error": str(sc_error)}
            else:
                active_connections = {"error": "Socket controller not initialized"}
            
            # System uptime
            uptime_seconds = int(time.time() - psutil.boot_time())
            days, remainder = divmod(uptime_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime = f"{days}d {hours}h {minutes}m {seconds}s"
            
            return {
                "success": True,
                "timestamp": datetime.datetime.now().isoformat(),
                "system": {
                    "os": platform.system(),
                    "platform": platform.platform(),
                    "python_version": platform.python_version(),
                    "hostname": platform.node(),
                    "uptime": uptime
                },
                "resources": {
                    "memory": {
                        "total": round(memory.total / (1024 * 1024 * 1024), 2),  # GB
                        "available": round(memory.available / (1024 * 1024 * 1024), 2),  # GB
                        "used_percent": memory.percent
                    },
                    "cpu": {
                        "percent": cpu_percent,
                        "cores": psutil.cpu_count(logical=False),
                        "logical_cores": psutil.cpu_count(logical=True)
                    },
                    "disk": {
                        "total": round(disk.total / (1024 * 1024 * 1024), 2),  # GB
                        "free": round(disk.free / (1024 * 1024 * 1024), 2),  # GB
                        "used_percent": disk.percent
                    }
                },
                "application": {
                    "process_id": os.getpid(),
                    "memory_usage_mb": round(process_memory, 2),
                    "cpu_percent": process_cpu,
                    "threads": process_threads,
                    "start_time": process_start_time,
                    "game_running": game_running,
                    "active_connections": active_connections
                },
                "database": db_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to retrieve system status: {str(e)}"}

    def remove_player(self, player_id, handle_properties='bank', reason='Admin removal'):
        """
        Remove a player from the game.
        
        Args:
            player_id: ID of the player to remove
            handle_properties: How to handle player properties ('bank' or 'auction')
            reason: Reason for removal
            
        Returns:
            Dict with operation result
        """
        try:
            # 1. Verify player exists
            player = Player.query.get(player_id)
            if not player:
                return {"success": False, "error": "Player not found"}
            
            # 2. Handle player properties based on disposition preference
            if handle_properties == 'bank':
                # Transfer all properties to bank
                properties = Property.query.filter_by(owner_id=player_id).all()
                for prop in properties:
                    prop.owner_id = None  # Bank ownership
                    prop.is_mortgaged = False  # Reset mortgage status
                    prop.houses = 0  # Remove houses
                    prop.hotel = False  # Remove hotel
                db.session.commit()
                logger.info(f"Properties of player {player.username} transferred to bank")
                
            elif handle_properties == 'auction':
                # Queue properties for auction
                properties = Property.query.filter_by(owner_id=player_id).all()
                auction_controller = current_app.config.get('auction_controller')
                if auction_controller:
                    for prop in properties:
                        auction_controller.queue_property_for_auction(prop.id, f"Admin removal of player {player.username}")
                    logger.info(f"Properties of player {player.username} queued for auction")
                else:
                    logger.error("Auction controller not available for property auction")
                    return {"success": False, "error": "Auction controller not available"}
            
            # 3. Mark player as not in game
            player.in_game = False
            db.session.commit()
            
            # 4. Handle socket disconnection if player is connected
            socket_controller = current_app.config.get('socket_controller')
            if socket_controller:
                # Get connection status
                status = socket_controller.get_player_connection_status(player_id)
                if status.get('status') == 'connected':
                    # Disconnect socket
                    socketio = current_app.config.get('socketio')
                    if socketio and status.get('socket_id'):
                        try:
                            socketio.server.disconnect(status.get('socket_id'))
                            logger.info(f"Socket for player {player_id} disconnected")
                        except Exception as e:
                            logger.warning(f"Could not disconnect socket for player {player_id}: {str(e)}")
                    
                    # Cancel reconnect timer and remove from tracking
                    socket_controller.cancel_reconnect_timer(player_id)
                    socket_controller.remove_connected_player_entry(player_id)
                    
                    # Notify all clients
                    game_state = GameState.get_instance()
                    if game_state:
                        socket_controller.notify_all_player_removed(player_id, player.username, game_state.game_id)
            
            # 5. Log the action
            logger.info(f"Player {player.username} (ID: {player_id}) removed by admin. Reason: {reason}")
            
            return {
                "success": True,
                "message": f"Player {player.username} removed from game",
                "player_id": player_id,
                "username": player.username,
                "properties_handled": handle_properties
            }
            
        except Exception as e:
            logger.error(f"Error removing player {player_id}: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Failed to remove player: {str(e)}"} 

    def audit_economic_system(self, fix_issues=False):
        """
        Perform a full audit of the economic system.
        
        Args:
            fix_issues (bool): Whether to attempt to fix discovered issues
            
        Returns:
            Dict with audit results
        """
        try:
            logger.info(f"Starting economic system audit (fix_issues={fix_issues})")
            
            audit_results = {
                "success": True,
                "message": "Audit completed successfully",
                "issues_found": 0,
                "issues_fixed": 0,
                "reports": [],
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Get all players
            players = Player.query.all()
            logger.info(f"Auditing {len(players)} players")
            
            # Get banker
            banker = current_app.config.get('banker')
            if not banker:
                logger.warning("Banker not found in app config")
                audit_results["reports"].append({
                    "type": "system_configuration",
                    "severity": "high",
                    "entity": "banker",
                    "description": "Banker not found in app configuration"
                })
                audit_results["issues_found"] += 1
            
            # Step 1: Verify all players have valid money values
            for player in players:
                try:
                    if not hasattr(player, 'money') or player.money is None:
                        issue = {
                            "type": "missing_money",
                            "severity": "high",
                            "entity": f"player-{player.id}",
                            "description": f"Player {player.username} (ID: {player.id}) has no money attribute or value"
                        }
                        
                        if fix_issues:
                            player.money = 1500  # Default starting value
                            db.session.add(player)
                            audit_results["issues_fixed"] += 1
                            issue["fixed"] = True
                            issue["fix_description"] = f"Set player money to default value of 1500"
                        
                        audit_results["issues_found"] += 1
                        audit_results["reports"].append(issue)
                except Exception as player_error:
                    logger.error(f"Error checking player {player.id if hasattr(player, 'id') else 'unknown'}: {str(player_error)}")
                    audit_results["reports"].append({
                        "type": "player_check_error",
                        "severity": "medium",
                        "entity": f"player-{player.id if hasattr(player, 'id') else 'unknown'}",
                        "description": f"Error checking player: {str(player_error)}"
                    })
                    audit_results["issues_found"] += 1
            
            # Step 2: Check for negative money without bankruptcy status
            for player in players:
                try:
                    if hasattr(player, 'money') and player.money < 0 and hasattr(player, 'in_game') and player.in_game:
                        issue = {
                            "type": "negative_balance",
                            "severity": "medium",
                            "entity": f"player-{player.id}",
                            "description": f"Player {player.username} has negative balance ({player.money}) but is still in game"
                        }
                        
                        if fix_issues:
                            # Don't automatically bankrupt players, just report it
                            pass
                        
                        audit_results["issues_found"] += 1
                        audit_results["reports"].append(issue)
                except Exception as player_error:
                    logger.error(f"Error checking player bankruptcy status {player.id if hasattr(player, 'id') else 'unknown'}: {str(player_error)}")
                    audit_results["reports"].append({
                        "type": "player_bankruptcy_check_error",
                        "severity": "medium",
                        "entity": f"player-{player.id if hasattr(player, 'id') else 'unknown'}",
                        "description": f"Error checking player bankruptcy status: {str(player_error)}"
                    })
                    audit_results["issues_found"] += 1
            
            # Step 3: Check game state
            try:
                game_state = GameState.query.first()
                if game_state:
                    if not hasattr(game_state, 'inflation_state') or not game_state.inflation_state:
                        issue = {
                            "type": "missing_economic_state",
                            "severity": "medium",
                            "entity": "game_state",
                            "description": "Game state is missing inflation_state"
                        }
                        
                        if fix_issues:
                            game_state.inflation_state = "normal"
                            db.session.add(game_state)
                            audit_results["issues_fixed"] += 1
                            issue["fixed"] = True
                            issue["fix_description"] = "Set inflation_state to 'normal'"
                        
                        audit_results["issues_found"] += 1
                        audit_results["reports"].append(issue)
                    
                    if not hasattr(game_state, 'inflation_rate'):
                        issue = {
                            "type": "missing_inflation_rate",
                            "severity": "low",
                            "entity": "game_state",
                            "description": "Game state is missing inflation_rate"
                        }
                        
                        if fix_issues:
                            game_state.inflation_rate = 0.0
                            db.session.add(game_state)
                            audit_results["issues_fixed"] += 1
                            issue["fixed"] = True
                            issue["fix_description"] = "Set inflation_rate to 0.0"
                        
                        audit_results["issues_found"] += 1
                        audit_results["reports"].append(issue)
                else:
                    audit_results["issues_found"] += 1
                    audit_results["reports"].append({
                        "type": "missing_game_state",
                        "severity": "critical",
                        "entity": "game_state",
                        "description": "No game state record found"
                    })
            except Exception as game_state_error:
                logger.error(f"Error checking game state: {str(game_state_error)}")
                audit_results["reports"].append({
                    "type": "game_state_check_error",
                    "severity": "high",
                    "entity": "game_state",
                    "description": f"Error checking game state: {str(game_state_error)}"
                })
                audit_results["issues_found"] += 1
            
            # Step 4: Check community fund
            try:
                community_fund = current_app.config.get('community_fund')
                if not community_fund:
                    audit_results["issues_found"] += 1
                    audit_results["reports"].append({
                        "type": "missing_community_fund",
                        "severity": "high",
                        "entity": "community_fund",
                        "description": "Community fund is not initialized"
                    })
            except Exception as community_fund_error:
                logger.error(f"Error checking community fund: {str(community_fund_error)}")
                audit_results["reports"].append({
                    "type": "community_fund_check_error",
                    "severity": "medium",
                    "entity": "community_fund",
                    "description": f"Error checking community fund: {str(community_fund_error)}"
                })
                audit_results["issues_found"] += 1
            
            # Commit any fixes
            if fix_issues and audit_results["issues_fixed"] > 0:
                try:
                    db.session.commit()
                    logger.info(f"Fixed {audit_results['issues_fixed']} issues during economic audit")
                except Exception as commit_error:
                    logger.error(f"Error committing fixes: {str(commit_error)}")
                    audit_results["reports"].append({
                        "type": "commit_error",
                        "severity": "high",
                        "entity": "database",
                        "description": f"Error committing fixes: {str(commit_error)}"
                    })
                    audit_results["issues_found"] += 1
                    # Reset issues_fixed count since the commit failed
                    audit_results["issues_fixed"] = 0
            
            # Generate summary message
            if audit_results["issues_found"] == 0:
                audit_results["message"] = "No issues found in economic system"
            else:
                if audit_results["issues_fixed"] > 0:
                    audit_results["message"] = f"Found {audit_results['issues_found']} issues and fixed {audit_results['issues_fixed']}"
                else:
                    audit_results["message"] = f"Found {audit_results['issues_found']} issues (fix_issues=false)"
            
            logger.info(f"Audit completed: {audit_results['message']}")
            return audit_results
            
        except Exception as e:
            logger.error(f"Error auditing economic system: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to complete economic audit: {str(e)}",
                "timestamp": datetime.datetime.now().isoformat()
            }

    def audit_game_state(self):
        """
        Performs a comprehensive audit of the entire game state including all players,
        properties, economic conditions, and game rule compliance.
        
        Returns:
            Dict with comprehensive game audit report
        """
        try:
            # 1. Get game state and necessary managers
            game_state = GameState.get_instance()
            if not game_state:
                return {"success": False, "error": "Game state not initialized"}
            
            # 2. Player analysis
            players = Player.query.all()
            active_players = [p for p in players if p.in_game]
            
            player_analysis = {
                "total_count": len(players),
                "active_count": len(active_players),
                "bots_count": sum(1 for p in active_players if isinstance(p, BotPlayer)),
                "humans_count": sum(1 for p in active_players if not isinstance(p, BotPlayer)),
                "in_jail_count": sum(1 for p in active_players if p.jail_turns_remaining > 0),
                "wealthiest_player": {
                    "id": None,
                    "username": None,
                    "net_worth": 0
                },
                "most_propertied_player": {
                    "id": None,
                    "username": None,
                    "property_count": 0
                }
            }
            
            # Find wealthiest and most-propertied players
            for player in active_players:
                net_worth = player.calculate_net_worth()
                property_count = len(player.properties)
                
                if net_worth > player_analysis["wealthiest_player"]["net_worth"]:
                    player_analysis["wealthiest_player"] = {
                        "id": player.id,
                        "username": player.username,
                        "net_worth": net_worth
                    }
                
                if property_count > player_analysis["most_propertied_player"]["property_count"]:
                    player_analysis["most_propertied_player"] = {
                        "id": player.id,
                        "username": player.username,
                        "property_count": property_count
                    }
            
            # 3. Game progression analysis
            properties = Property.query.all()
            
            game_progression = {
                "turn_number": game_state.turn_count,
                "current_player_id": game_state.current_player_id,
                "properties_owned_percent": sum(1 for p in properties if p.owner_id is not None) / len(properties) if properties else 0,
                "properties_developed_percent": sum(1 for p in properties if p.houses > 0 or p.hotel) / len(properties) if properties else 0,
                "game_duration_minutes": (datetime.datetime.now() - game_state.start_time).total_seconds() / 60 if hasattr(game_state, 'start_time') else 0,
                "average_turn_duration_seconds": game_state.total_turn_time / max(1, game_state.turn_count) if hasattr(game_state, 'total_turn_time') else 0,
                "estimated_completion_percent": min(100, max(0, (sum(1 for p in properties if p.owner_id is not None) / len(properties) * 100) if properties else 0))
            }
            
            # 4. Rule compliance checks
            rule_compliance = {
                "violations": [],
                "warnings": []
            }
            
            # Check for property development rule violations
            for prop in properties:
                if prop.houses > 4 and not prop.hotel:
                    rule_compliance["violations"].append({
                        "type": "property_development",
                        "message": f"Property {prop.name} has {prop.houses} houses without converting to hotel",
                        "property_id": prop.id
                    })
                
                if prop.houses > 0 and prop.is_mortgaged:
                    rule_compliance["violations"].append({
                        "type": "property_development",
                        "message": f"Property {prop.name} has houses while being mortgaged",
                        "property_id": prop.id
                    })
            
            # Check for monopoly rule violations
            property_groups = {}
            for prop in properties:
                if prop.property_group not in property_groups:
                    property_groups[prop.property_group] = []
                property_groups[prop.property_group].append(prop)
            
            for group, props in property_groups.items():
                if len(props) <= 1:
                    continue  # Skip non-monopoly groups
                
                # Check if all properties in the group have the same owner
                owners = set(p.owner_id for p in props)
                if len(owners) == 1 and None not in owners:  # Monopoly exists
                    owner_id = list(owners)[0]
                    
                    # Check for uneven development
                    house_counts = [p.houses for p in props]
                    if max(house_counts) - min(house_counts) > 1:
                        rule_compliance["violations"].append({
                            "type": "uneven_development",
                            "message": f"Uneven development in {group} group owned by Player {owner_id}",
                            "property_group": group,
                            "owner_id": owner_id,
                            "house_counts": house_counts
                        })
            
            # Check for potential game stalling
            if hasattr(game_state, 'last_turn_time'):
                time_since_last_turn = (datetime.datetime.now() - game_state.last_turn_time).total_seconds() / 60
                if time_since_last_turn > 15:  # 15 minutes
                    rule_compliance["warnings"].append({
                        "type": "game_stalling",
                        "message": f"No turn has been taken for {int(time_since_last_turn)} minutes",
                        "idle_time_minutes": int(time_since_last_turn)
                    })
            
            # 5. Game balance analysis
            game_balance = {
                "outcome_predictability": "low",  # Default
                "leading_player": None,
                "catch_up_possibility": "high",  # Default
                "endgame_likelihood": "low"  # Default
            }
            
            # Calculate player wealth distribution to determine game balance
            if active_players:
                player_net_worths = [(p.id, p.username, p.calculate_net_worth()) for p in active_players]
                player_net_worths.sort(key=lambda x: x[2], reverse=True)
                
                # Determine if there's a clear leader
                if len(player_net_worths) >= 2:
                    top_player = player_net_worths[0]
                    second_player = player_net_worths[1]
                    
                    # If top player has significantly more wealth than the second
                    if top_player[2] > second_player[2] * 1.5:
                        game_balance["outcome_predictability"] = "high"
                        game_balance["leading_player"] = {
                            "id": top_player[0],
                            "username": top_player[1],
                            "net_worth": top_player[2]
                        }
                        
                        # If top player's lead is very significant
                        if top_player[2] > second_player[2] * 2.5:
                            game_balance["catch_up_possibility"] = "low"
                            game_balance["endgame_likelihood"] = "high"
                    else:
                        # Game is competitive
                        game_balance["outcome_predictability"] = "medium" if top_player[2] > second_player[2] * 1.2 else "low"
                        
                        # Calculate if the game is nearing endgame
                        if game_progression["properties_owned_percent"] > 0.8 and game_progression["properties_developed_percent"] > 0.4:
                            game_balance["endgame_likelihood"] = "high"
                        elif game_progression["properties_owned_percent"] > 0.6 and game_progression["properties_developed_percent"] > 0.2:
                            game_balance["endgame_likelihood"] = "medium"
            
            # 6. Compile the final audit report
            audit_report = {
                "success": True,
                "timestamp": datetime.datetime.now().isoformat(),
                "game_id": game_state.game_id,
                "player_analysis": player_analysis,
                "game_progression": game_progression,
                "rule_compliance": rule_compliance,
                "game_balance": game_balance,
                "recommendations": []
            }
            
            # 7. Generate recommendations based on the analysis
            if rule_compliance["violations"]:
                audit_report["recommendations"].append({
                    "type": "rule_violation",
                    "severity": "high",
                    "message": f"Fix {len(rule_compliance['violations'])} rule violations found in the game"
                })
            
            if game_balance["outcome_predictability"] == "high" and game_balance["catch_up_possibility"] == "low":
                audit_report["recommendations"].append({
                    "type": "game_balance",
                    "severity": "medium",
                    "message": "Game is highly unbalanced. Consider implementing catch-up mechanics or offering financial aid to trailing players."
                })
            
            if game_progression["estimated_completion_percent"] > 80 and game_balance["endgame_likelihood"] == "high":
                audit_report["recommendations"].append({
                    "type": "game_progression",
                    "severity": "low",
                    "message": "Game is nearing completion. Consider preparing for the next game session."
                })
            
            # Check for inactive players
            if player_analysis["total_count"] > player_analysis["active_count"]:
                audit_report["recommendations"].append({
                    "type": "inactive_players",
                    "severity": "medium",
                    "message": f"There are {player_analysis['total_count'] - player_analysis['active_count']} inactive players. Consider removing them to improve game performance."
                })
            
            # 8. Log the audit completion
            logger.info(f"Game state audit completed. Found {len(audit_report['recommendations'])} recommendations.")
            
            return audit_report
            
        except Exception as e:
            logger.error(f"Error performing game state audit: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to complete game state audit: {str(e)}"}

    def get_system_health_trends(self, hours=24):
        """
        Analyzes system health metrics over time to identify trends and potential issues.
        
        Args:
            hours (int): Number of hours of historical data to analyze
            
        Returns:
            Dict with system health trends and potential issues
        """
        try:
            # In a production system, this would retrieve data from a system metrics
            # database or time-series database. For this implementation, we'll
            # generate some simulated historical data based on current metrics

            # Get current metrics
            current_metrics = self.get_system_status()
            if not current_metrics.get('success'):
                return {"success": False, "error": "Failed to get current system metrics"}
            
            # Create time intervals
            now = datetime.datetime.now()
            intervals = []
            
            # Generate intervals (every 1 hour for the requested time range)
            for i in range(hours):
                intervals.append(now - datetime.timedelta(hours=i))
            
            # Simulate historical metrics with some random variation
            historical_metrics = []
            base_cpu_percent = current_metrics['resources']['cpu']['percent']
            base_memory_percent = current_metrics['resources']['memory']['used_percent']
            base_disk_percent = current_metrics['resources']['disk']['used_percent']
            
            import random
            for interval in intervals:
                # Add random variations to simulate changing metrics
                time_factor = 1 + ((now - interval).total_seconds() / (3600 * hours))  # Older data has more potential variation
                
                # Create simulated metrics for this interval
                cpu_variance = random.uniform(-10, 10) * time_factor
                memory_variance = random.uniform(-5, 5) * time_factor
                disk_variance = random.uniform(-2, 2) * time_factor
                
                # Ensure metrics stay within reasonable bounds
                cpu_percent = max(0.1, min(99.9, base_cpu_percent + cpu_variance))
                memory_percent = max(10, min(95, base_memory_percent + memory_variance))
                disk_percent = max(5, min(98, base_disk_percent + disk_variance))
                
                historical_metrics.append({
                    "timestamp": interval.isoformat(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "active_players": random.randint(0, 8),  # Simulate varying player counts
                    "response_time_ms": random.randint(50, 500)  # Simulate varying response times
                })
            
            # Sort by timestamp (oldest first)
            historical_metrics.sort(key=lambda x: x["timestamp"])
            
            # Calculate trends
            cpu_trend = self._calculate_trend([m["cpu_percent"] for m in historical_metrics])
            memory_trend = self._calculate_trend([m["memory_percent"] for m in historical_metrics])
            disk_trend = self._calculate_trend([m["disk_percent"] for m in historical_metrics])
            response_time_trend = self._calculate_trend([m["response_time_ms"] for m in historical_metrics])
            
            # Check for concerning patterns
            issues = []
            
            # CPU spikes
            cpu_values = [m["cpu_percent"] for m in historical_metrics]
            if max(cpu_values) > 90:
                issues.append({
                    "type": "cpu_spike",
                    "severity": "high",
                    "message": f"CPU usage spiked to {max(cpu_values):.1f}%",
                    "timestamp": historical_metrics[cpu_values.index(max(cpu_values))]["timestamp"]
                })
            
            # Memory growth
            if memory_trend > 0.5 and current_metrics['resources']['memory']['used_percent'] > 80:
                issues.append({
                    "type": "memory_growth",
                    "severity": "medium",
                    "message": "Memory usage is growing steadily and currently high",
                    "current_value": current_metrics['resources']['memory']['used_percent']
                })
            
            # Disk space concerns
            if current_metrics['resources']['disk']['used_percent'] > 90:
                issues.append({
                    "type": "disk_space",
                    "severity": "high",
                    "message": "Disk space usage is critically high",
                    "current_value": current_metrics['resources']['disk']['used_percent']
                })
            
            # Response time degradation
            if response_time_trend > 5:
                issues.append({
                    "type": "response_degradation",
                    "severity": "medium",
                    "message": "Response times are steadily increasing",
                    "trend": f"+{response_time_trend:.1f} ms/hour"
                })
            
            # Prepare visualization data in a format suitable for charts
            visualization_data = {
                "timestamps": [m["timestamp"] for m in historical_metrics],
                "cpu": [m["cpu_percent"] for m in historical_metrics],
                "memory": [m["memory_percent"] for m in historical_metrics],
                "disk": [m["disk_percent"] for m in historical_metrics],
                "response_times": [m["response_time_ms"] for m in historical_metrics],
                "active_players": [m["active_players"] for m in historical_metrics]
            }
            
            # Build the response
            return {
                "success": True,
                "current_metrics": current_metrics,
                "trends": {
                    "cpu": {
                        "trend": cpu_trend,
                        "unit": "percent/hour",
                        "interpretation": "increasing" if cpu_trend > 0.1 else "decreasing" if cpu_trend < -0.1 else "stable"
                    },
                    "memory": {
                        "trend": memory_trend,
                        "unit": "percent/hour",
                        "interpretation": "increasing" if memory_trend > 0.1 else "decreasing" if memory_trend < -0.1 else "stable"
                    },
                    "disk": {
                        "trend": disk_trend,
                        "unit": "percent/hour",
                        "interpretation": "increasing" if disk_trend > 0.05 else "decreasing" if disk_trend < -0.05 else "stable"
                    },
                    "response_time": {
                        "trend": response_time_trend,
                        "unit": "ms/hour",
                        "interpretation": "degrading" if response_time_trend > 1 else "improving" if response_time_trend < -1 else "stable"
                    }
                },
                "issues": issues,
                "historical_data": historical_metrics,
                "visualization_data": visualization_data
            }
        except Exception as e:
            logger.error(f"Error analyzing system health trends: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to analyze system health trends: {str(e)}"}
    
    def _calculate_trend(self, values):
        """
        Calculate the trend (slope) of a series of values using simple linear regression.
        
        Args:
            values (list): List of numeric values
            
        Returns:
            float: Trend value (change per unit)
        """
        if not values or len(values) < 2:
            return 0
        
        n = len(values)
        x = list(range(n))
        
        # Calculate means
        mean_x = sum(x) / n
        mean_y = sum(values) / n
        
        # Calculate slope (using least squares method)
        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        # Return slope
        return numerator / denominator 

    def manage_event(self, event_data, event_id=None):
        """
        Creates, updates, or retrieves a game event.
        
        Args:
            event_data (dict): Data for the event, including type, parameters, scheduling
            event_id (str, optional): ID of event to update, or None to create new
            
        Returns:
            Dict with operation result
        """
        try:
            # Validate event data
            if not event_data or not isinstance(event_data, dict):
                return {"success": False, "error": "Event data is required and must be a dictionary"}
            
            # Get game state
            game_state = GameState.get_instance()
            if not game_state:
                return {"success": False, "error": "Game state not initialized"}
            
            # Check if this is an update or create operation
            if event_id:
                # Get existing event
                event = Event.query.get(event_id)
                if not event:
                    return {"success": False, "error": f"Event with ID {event_id} not found"}
                
                # Update existing event
                operation = "updated"
            else:
                # Create new event
                event = Event()
                event.id = str(uuid.uuid4())
                event.status = EventStatus.SCHEDULED
                event.creation_time = datetime.datetime.now()
                operation = "created"
            
            # Update event properties
            event.event_type = event_data.get('event_type', event.event_type if hasattr(event, 'event_type') else EventType.GENERIC)
            event.title = event_data.get('title', event.title if hasattr(event, 'title') else f"Event {event.id}")
            event.description = event_data.get('description', event.description if hasattr(event, 'description') else "")
            event.parameters = event_data.get('parameters', event.parameters if hasattr(event, 'parameters') else {})
            
            # Handle scheduling
            if 'scheduled_time' in event_data:
                # Parse datetime string or use provided datetime object
                if isinstance(event_data['scheduled_time'], str):
                    event.scheduled_time = datetime.datetime.fromisoformat(event_data['scheduled_time'])
                else:
                    event.scheduled_time = event_data['scheduled_time']
            elif operation == "created":
                # Default to immediate execution for new events if no time specified
                event.scheduled_time = datetime.datetime.now()
            
            # Set target players (all or specific)
            if 'target_player_ids' in event_data:
                event.target_player_ids = event_data['target_player_ids']
            elif 'all_players' in event_data and event_data['all_players']:
                # Target all players currently in game
                players = Player.query.filter_by(in_game=True).all()
                event.target_player_ids = [p.id for p in players]
            elif operation == "created":
                # Default to all players for new events
                players = Player.query.filter_by(in_game=True).all()
                event.target_player_ids = [p.id for p in players]
            
            # Set repeatability
            event.is_repeating = event_data.get('is_repeating', event.is_repeating if hasattr(event, 'is_repeating') else False)
            if event.is_repeating:
                event.repeat_interval = event_data.get('repeat_interval', event.repeat_interval if hasattr(event, 'repeat_interval') else 24 * 60 * 60)  # Default: daily
                event.max_repetitions = event_data.get('max_repetitions', event.max_repetitions if hasattr(event, 'max_repetitions') else None)
                event.repetitions_completed = event_data.get('repetitions_completed', event.repetitions_completed if hasattr(event, 'repetitions_completed') else 0)
            
            # Save to database
            if operation == "created":
                db.session.add(event)
            db.session.commit()
            
            # Log the operation
            logger.info(f"Event {event.id} {operation}")
            
            # Schedule event with event system
            event_system = current_app.config.get('event_system')
            if event_system:
                event_system.schedule_event(event.id)
                logger.info(f"Event {event.id} scheduled with event system")
            else:
                logger.warning("Event system not available, event scheduled but may not execute automatically")
            
            return {
                "success": True,
                "event_id": event.id,
                "operation": operation,
                "event": event.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error managing event: {e}", exc_info=True)
            db.session.rollback()
            return {"success": False, "error": f"Failed to manage event: {str(e)}"}

    def get_events(self, filters=None):
        """
        Get events with optional filtering.
        
        Args:
            filters (dict, optional): Filters to apply, such as status, type, player_id
            
        Returns:
            Dict with list of events
        """
        try:
            query = Event.query
            
            # Apply filters if provided
            if filters:
                if 'status' in filters:
                    query = query.filter(Event.status == filters['status'])
                
                if 'event_type' in filters:
                    query = query.filter(Event.event_type == filters['event_type'])
                
                if 'player_id' in filters:
                    # Filter for events targeting specific player
                    player_id = filters['player_id']
                    # This would require a more complex query in a real implementation,
                    # as target_player_ids is likely stored as JSON/Array
                    # For simplicity, we'll filter in Python
                    all_events = query.all()
                    filtered_events = [e for e in all_events if player_id in e.target_player_ids]
                    
                    return {
                        "success": True,
                        "events": [e.to_dict() for e in filtered_events],
                        "count": len(filtered_events)
                    }
                
                if 'start_time' in filters:
                    if isinstance(filters['start_time'], str):
                        start_time = datetime.datetime.fromisoformat(filters['start_time'])
                    else:
                        start_time = filters['start_time']
                    query = query.filter(Event.scheduled_time >= start_time)
                
                if 'end_time' in filters:
                    if isinstance(filters['end_time'], str):
                        end_time = datetime.datetime.fromisoformat(filters['end_time'])
                    else:
                        end_time = filters['end_time']
                    query = query.filter(Event.scheduled_time <= end_time)
            
            # Get events
            events = query.order_by(Event.scheduled_time).all()
            
            return {
                "success": True,
                "events": [e.to_dict() for e in events],
                "count": len(events)
            }
            
        except Exception as e:
            logger.error(f"Error getting events: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to get events: {str(e)}"}

    def delete_event(self, event_id):
        """
        Delete an event.
        
        Args:
            event_id (str): ID of the event to delete
            
        Returns:
            Dict with operation result
        """
        try:
            # Get the event
            event = Event.query.get(event_id)
            if not event:
                return {"success": False, "error": f"Event with ID {event_id} not found"}
            
            # Delete the event
            db.session.delete(event)
            db.session.commit()
            
            # Log the operation
            logger.info(f"Event {event_id} deleted")
            
            # Unschedule event from event system
            event_system = current_app.config.get('event_system')
            if event_system:
                event_system.unschedule_event(event_id)
                logger.info(f"Event {event_id} unscheduled from event system")
            else:
                logger.warning("Event system not available, event deleted but may not be unscheduled properly")
            
            return {
                "success": True,
                "event_id": event_id,
                "message": f"Event {event_id} deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting event {event_id}: {e}", exc_info=True)
            db.session.rollback()
            return {"success": False, "error": f"Failed to delete event: {str(e)}"}

    def trigger_event_now(self, event_id):
        """
        Trigger an event immediately, regardless of its scheduled time.
        
        Args:
            event_id (str): ID of the event to trigger
            
        Returns:
            Dict with operation result
        """
        try:
            # Get the event
            event = Event.query.get(event_id)
            if not event:
                return {"success": False, "error": f"Event with ID {event_id} not found"}
            
            # Check if event is already completed or in progress
            if event.status == EventStatus.COMPLETED:
                return {"success": False, "error": f"Event {event_id} has already been completed"}
            
            if event.status == EventStatus.IN_PROGRESS:
                return {"success": False, "error": f"Event {event_id} is already in progress"}
            
            # Get the event system
            event_system = current_app.config.get('event_system')
            if not event_system:
                return {"success": False, "error": "Event system not available"}
            
            # Trigger the event
            result = event_system.execute_event(event_id)
            
            if result.get('success'):
                return {
                    "success": True,
                    "event_id": event_id,
                    "message": f"Event {event_id} triggered successfully",
                    "result": result
                }
            else:
                return {
                    "success": False,
                    "event_id": event_id,
                    "error": f"Failed to trigger event: {result.get('error', 'Unknown error')}"
                }
            
        except Exception as e:
            logger.error(f"Error triggering event {event_id}: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to trigger event: {str(e)}"}

    def create_random_event(self, event_type=None, scheduled_delay_minutes=None):
        """
        Create a random game event of the specified type or a random type.
        
        Args:
            event_type (EventType, optional): Specific type of event to create, or random if None
            scheduled_delay_minutes (int, optional): Minutes to delay event, or random if None
            
        Returns:
            Dict with operation result
        """
        try:
            # Get game state
            game_state = GameState.get_instance()
            if not game_state:
                return {"success": False, "error": "Game state not initialized"}
            
            # Get active players
            active_players = Player.query.filter_by(in_game=True).all()
            if not active_players:
                return {"success": False, "error": "No active players to create event for"}
            
            # Randomly select event type if not specified
            if not event_type:
                event_types = [
                    EventType.MARKET_CRASH,
                    EventType.ECONOMIC_BOOM,
                    EventType.BANK_ERROR,
                    EventType.PROPERTY_DAMAGE,
                    EventType.COMMUNITY_BONUS,
                    EventType.TAX_AUDIT,
                    EventType.RENOVATION_OPPORTUNITY,
                    EventType.SPECIAL_AUCTION
                ]
                event_type = random.choice(event_types)
            
            # Determine random scheduling if not specified
            if scheduled_delay_minutes is None:
                # Random delay between 1 and 30 minutes
                scheduled_delay_minutes = random.randint(1, 30)
            
            scheduled_time = datetime.datetime.now() + datetime.timedelta(minutes=scheduled_delay_minutes)
            
            # Prepare event data based on type
            event_data = {
                "event_type": event_type,
                "scheduled_time": scheduled_time,
                "is_repeating": False
            }
            
            # Customize event based on type
            if event_type == EventType.MARKET_CRASH:
                event_data.update({
                    "title": "Market Crash",
                    "description": "A sudden market crash affects property values",
                    "parameters": {
                        "severity": random.uniform(0.1, 0.3),  # 10-30% reduction
                        "affected_property_types": random.sample(["residential", "commercial", "industrial", "utilities"], k=random.randint(1, 3))
                    }
                })
            
            elif event_type == EventType.ECONOMIC_BOOM:
                event_data.update({
                    "title": "Economic Boom",
                    "description": "A sudden economic boom increases property values",
                    "parameters": {
                        "boost": random.uniform(0.1, 0.25),  # 10-25% increase
                        "affected_property_types": random.sample(["residential", "commercial", "industrial", "utilities"], k=random.randint(1, 3))
                    }
                })
            
            elif event_type == EventType.BANK_ERROR:
                # Randomly choose if this is in favor or against the player
                is_favor = random.choice([True, False])
                amount = random.randint(50, 200)
                
                event_data.update({
                    "title": "Bank Error",
                    "description": f"Bank error {'in your favor' if is_favor else 'charged to your account'}",
                    "parameters": {
                        "amount": amount if is_favor else -amount,
                        "message": f"Due to a bank error, {'collect' if is_favor else 'pay'} ${amount}"
                    }
                })
                
                # Choose random players to affect
                target_count = random.randint(1, max(1, len(active_players) // 2))
                target_players = random.sample([p.id for p in active_players], k=target_count)
                event_data["target_player_ids"] = target_players
            
            elif event_type == EventType.PROPERTY_DAMAGE:
                event_data.update({
                    "title": "Property Damage",
                    "description": "Some properties suffer damage requiring repairs",
                    "parameters": {
                        "repair_cost_per_house": random.randint(20, 50),
                        "repair_cost_per_hotel": random.randint(80, 150),
                        "message": "Repair costs must be paid or improvements will be removed"
                    }
                })
                
                # This affects all property owners
                players_with_properties = [p.id for p in active_players if p.properties]
                event_data["target_player_ids"] = players_with_properties
            
            elif event_type == EventType.COMMUNITY_BONUS:
                amount = random.randint(50, 200)
                
                event_data.update({
                    "title": "Community Bonus",
                    "description": "All players receive a community bonus payment",
                    "parameters": {
                        "amount": amount,
                        "message": f"Community bonus: all players receive ${amount}"
                    }
                })
                
                # All players receive this
                event_data["all_players"] = True
            
            elif event_type == EventType.TAX_AUDIT:
                percentage = random.uniform(0.05, 0.15)  # 5-15% tax
                
                event_data.update({
                    "title": "Tax Audit",
                    "description": "Tax audit requires payment based on property value",
                    "parameters": {
                        "percentage": percentage,
                        "minimum_payment": 50,
                        "message": f"Tax audit: pay {int(percentage * 100)}% of your property value"
                    }
                })
                
                # Randomly select 1-3 players to audit
                target_count = min(3, len(active_players))
                if target_count > 0:
                    target_players = random.sample([p.id for p in active_players], k=target_count)
                    event_data["target_player_ids"] = target_players
            
            elif event_type == EventType.RENOVATION_OPPORTUNITY:
                discount = random.uniform(0.2, 0.5)  # 20-50% discount
                
                event_data.update({
                    "title": "Renovation Opportunity",
                    "description": "Limited-time discount on property improvements",
                    "parameters": {
                        "discount": discount,
                        "duration_minutes": random.randint(5, 15),
                        "message": f"Renovation opportunity: {int(discount * 100)}% off all improvements for a limited time"
                    }
                })
                
                # All players can benefit from this
                event_data["all_players"] = True
            
            elif event_type == EventType.SPECIAL_AUCTION:
                event_data.update({
                    "title": "Special Auction",
                    "description": "A special auction will be held for premium properties",
                    "parameters": {
                        "property_count": random.randint(1, 3),
                        "premium_factor": random.uniform(1.1, 1.5),  # Properties worth 10-50% more
                        "message": "Special auction event: premium properties available!"
                    }
                })
                
                # All players can participate in the auction
                event_data["all_players"] = True
            
            # Create the event
            return self.manage_event(event_data)
            
        except Exception as e:
            logger.error(f"Error creating random event: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to create random event: {str(e)}"}

    def get_event_statistics(self):
        """
        Get statistics on events for the admin dashboard.
        
        Returns:
            Dict with event statistics
        """
        try:
            # Get all events
            all_events = Event.query.all()
            
            if not all_events:
                return {
                    "success": True,
                    "message": "No events found",
                    "event_count": 0,
                    "event_types": {},
                    "event_status": {},
                    "time_distribution": {
                        "past_hour": 0,
                        "past_day": 0,
                        "past_week": 0,
                        "future": 0
                    }
                }
            
            # Calculate event type distribution
            event_types = {}
            for event in all_events:
                event_type = event.event_type
                if event_type not in event_types:
                    event_types[event_type] = 0
                event_types[event_type] += 1
            
            # Calculate event status distribution
            event_status = {}
            for event in all_events:
                status = event.status
                if status not in event_status:
                    event_status[status] = 0
                event_status[status] += 1
            
            # Calculate time distribution
            now = datetime.datetime.now()
            one_hour_ago = now - datetime.timedelta(hours=1)
            one_day_ago = now - datetime.timedelta(days=1)
            one_week_ago = now - datetime.timedelta(days=7)
            
            time_distribution = {
                "past_hour": 0,
                "past_day": 0,
                "past_week": 0,
                "future": 0
            }
            
            for event in all_events:
                if event.scheduled_time > now:
                    time_distribution["future"] += 1
                elif event.scheduled_time >= one_hour_ago:
                    time_distribution["past_hour"] += 1
                elif event.scheduled_time >= one_day_ago:
                    time_distribution["past_day"] += 1
                elif event.scheduled_time >= one_week_ago:
                    time_distribution["past_week"] += 1
            
            # Calculate average impact (for completed events)
            completed_events = [e for e in all_events if e.status == EventStatus.COMPLETED]
            avg_impact = {
                "cash": 0,
                "property_value": 0,
                "player_count": 0
            }
            
            if completed_events:
                # This would require tracking event results in a real implementation
                # For simplicity, we'll use random values
                avg_impact = {
                    "cash": random.randint(-100, 200),
                    "property_value": random.randint(-5, 8),
                    "player_count": sum(len(e.target_player_ids) for e in completed_events) / len(completed_events)
                }
            
            return {
                "success": True,
                "event_count": len(all_events),
                "event_types": event_types,
                "event_status": event_status,
                "time_distribution": time_distribution,
                "average_impact": avg_impact,
                "upcoming_count": time_distribution["future"],
                "completed_count": event_status.get(EventStatus.COMPLETED, 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting event statistics: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to get event statistics: {str(e)}"}

    def manage_crime_settings(self, settings):
        """
        Update crime system settings.
        
        Args:
            settings (dict): Crime system settings to update
            
        Returns:
            Dict with operation result
        """
        try:
            # Get game state
            game_state = GameState.get_instance()
            if not game_state:
                return {"success": False, "error": "Game state not initialized"}
            
            # Get crime controller
            crime_controller = current_app.config.get('crime_controller')
            if not crime_controller:
                return {"success": False, "error": "Crime controller not initialized"}
            
            # Validate settings
            if not settings or not isinstance(settings, dict):
                return {"success": False, "error": "Settings must be a non-empty dictionary"}
            
            # Track applied settings
            applied_settings = {}
            
            # Apply settings to crime controller
            if 'crime_probability' in settings:
                value = float(settings['crime_probability'])
                if 0 <= value <= 1:
                    crime_controller.crime_probability = value
                    applied_settings['crime_probability'] = value
                else:
                    return {"success": False, "error": "Crime probability must be between 0 and 1"}
            
            if 'police_patrol_enabled' in settings:
                value = bool(settings['police_patrol_enabled'])
                crime_controller.police_patrol_enabled = value
                applied_settings['police_patrol_enabled'] = value
            
            if 'police_patrol_interval' in settings:
                value = int(settings['police_patrol_interval'])
                if value > 0:
                    crime_controller.police_patrol_interval = value
                    applied_settings['police_patrol_interval'] = value
                else:
                    return {"success": False, "error": "Police patrol interval must be positive"}
            
            if 'police_catch_probability' in settings:
                value = float(settings['police_catch_probability'])
                if 0 <= value <= 1:
                    crime_controller.police_catch_probability = value
                    applied_settings['police_catch_probability'] = value
                else:
                    return {"success": False, "error": "Police catch probability must be between 0 and 1"}
            
            if 'jail_turns' in settings:
                value = int(settings['jail_turns'])
                if value > 0:
                    crime_controller.jail_turns = value
                    applied_settings['jail_turns'] = value
                else:
                    return {"success": False, "error": "Jail turns must be positive"}
            
            if 'crime_types' in settings:
                crime_controller.crime_types = settings['crime_types']
                applied_settings['crime_types'] = settings['crime_types']
            
            if 'fine_multiplier' in settings:
                value = float(settings['fine_multiplier'])
                if value > 0:
                    crime_controller.fine_multiplier = value
                    applied_settings['fine_multiplier'] = value
                else:
                    return {"success": False, "error": "Fine multiplier must be positive"}
            
            # Save changes to database if needed
            # This depends on how the crime controller persists its settings
            if hasattr(crime_controller, 'save_settings'):
                crime_controller.save_settings()
            
            # Log the changes
            logger.info(f"Crime settings updated: {applied_settings}")
            
            # Get current settings after changes
            current_settings = crime_controller.get_settings()
            
            return {
                "success": True,
                "message": "Crime settings updated successfully",
                "updated_settings": applied_settings,
                "current_settings": current_settings
            }
            
        except Exception as e:
            logger.error(f"Error updating crime settings: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to update crime settings: {str(e)}"} 

    def get_crime_settings(self):
        """
        Get current crime system settings.
        
        Returns:
            dict: Current crime settings
        """
        try:
            # Get crime controller
            crime_controller = current_app.config.get('crime_controller')
            if not crime_controller:
                return {"success": False, "error": "Crime controller not initialized"}
            
            # Get current settings
            if hasattr(crime_controller, 'get_settings'):
                return {
                    "success": True,
                    "settings": crime_controller.get_settings()
                }
            
            # Fallback to retrieving individual attributes if no get_settings method
            settings = {
                "crime_probability": getattr(crime_controller, 'crime_probability', 0.2),
                "police_patrol_enabled": getattr(crime_controller, 'police_patrol_enabled', True),
                "police_patrol_interval": getattr(crime_controller, 'police_patrol_interval', 45),
                "police_catch_probability": getattr(crime_controller, 'police_catch_probability', 0.3),
                "jail_turns": getattr(crime_controller, 'jail_turns', 3),
                "fine_multiplier": getattr(crime_controller, 'fine_multiplier', 1.5),
                "crime_types": getattr(crime_controller, 'crime_types', [
                    'theft', 'property_vandalism', 'rent_evasion', 'forgery', 'tax_evasion'
                ])
            }
            
            return {
                "success": True,
                "settings": settings
            }
            
        except Exception as e:
            logger.error(f"Error getting crime settings: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to get crime settings: {str(e)}"}

    def get_crime_statistics(self):
        """
        Get statistics on crimes for the admin dashboard.
        
        Returns:
            dict: Crime statistics
        """
        try:
            from src.models.crime import Crime
            
            # Get crime controller
            crime_controller = current_app.config.get('crime_controller')
            if not crime_controller:
                return {"success": False, "error": "Crime controller not initialized"}
                
            # If the controller has this method, use it
            if hasattr(crime_controller, 'get_crime_statistics'):
                return crime_controller.get_crime_statistics()
            
            # Fallback implementation
            total_crimes = Crime.query.count()
            detected_crimes = Crime.query.filter_by(detected=True).count()
            successful_crimes = Crime.query.filter_by(success=True, detected=False).count()
            
            # Group by crime type
            crime_types = {}
            for crime_type in ['theft', 'property_vandalism', 'rent_evasion', 'forgery', 'tax_evasion']:
                count = Crime.query.filter_by(crime_type=crime_type).count()
                crime_types[crime_type] = count
            
            # Get players with criminal records
            criminals = Player.query.filter(Player.criminal_record > 0).count()
            
            # Get distribution by time
            from datetime import datetime, timedelta
            now = datetime.now()
            
            today = Crime.query.filter(Crime.timestamp > (now - timedelta(days=1))).count()
            this_week = Crime.query.filter(Crime.timestamp > (now - timedelta(days=7))).count()
            this_month = Crime.query.filter(Crime.timestamp > (now - timedelta(days=30))).count()
            
            return {
                "success": True,
                "total_crimes": total_crimes,
                "detected_crimes": detected_crimes,
                "successful_crimes": successful_crimes,
                "detection_rate": round(detected_crimes / total_crimes * 100, 1) if total_crimes > 0 else 0,
                "crime_types": crime_types,
                "criminals": criminals,
                "time_distribution": {
                    "today": today,
                    "this_week": this_week,
                    "this_month": this_month,
                    "all_time": total_crimes
                }
            }
                
        except Exception as e:
            logger.error(f"Error getting crime statistics: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to get crime statistics: {str(e)}"}

    def trigger_random_crime(self, severity=None, target_player_id=None):
        """
        Trigger a random crime event.
        
        Args:
            severity (str, optional): Force a specific severity level (LOW, MEDIUM, HIGH)
            target_player_id (int, optional): Force a specific player to be targeted
            
        Returns:
            dict: Result of the random crime
        """
        try:
            from src.models.crime import Crime, Theft, PropertyVandalism, RentEvasion, Forgery, TaxEvasion
            import random
            
            # Get active players
            players = Player.query.filter_by(in_game=True, is_bankrupt=False).all()
            if not players:
                return {"success": False, "error": "No active players in the game"}
            
            # Select player to commit crime (exclude target if specified)
            eligible_players = [p for p in players if p.id != target_player_id]
            if not eligible_players:
                return {"success": False, "error": "No eligible players to commit crimes"}
                
            criminal = random.choice(eligible_players)
            
            # Select crime type based on severity
            crime_types = {
                'LOW': ['rent_evasion'],
                'MEDIUM': ['theft', 'property_vandalism', 'tax_evasion'],
                'HIGH': ['forgery']
            }
            
            # If severity is not specified, choose randomly
            if not severity:
                all_types = ['theft', 'property_vandalism', 'rent_evasion', 'forgery', 'tax_evasion']
                crime_type = random.choice(all_types)
            else:
                if severity not in crime_types:
                    return {"success": False, "error": f"Invalid severity level: {severity}"}
                crime_type = random.choice(crime_types[severity])
            
            # Set up parameters
            params = {}
            
            if crime_type == 'theft':
                # Choose target player
                if target_player_id:
                    target = Player.query.get(target_player_id)
                    if not target or target.id == criminal.id:
                        potential_targets = [p for p in players if p.id != criminal.id]
                        if not potential_targets:
                            return {"success": False, "error": "No valid targets for theft"}
                        target = random.choice(potential_targets)
                else:
                    potential_targets = [p for p in players if p.id != criminal.id]
                    if not potential_targets:
                        return {"success": False, "error": "No valid targets for theft"}
                    target = random.choice(potential_targets)
                
                params['target_player_id'] = target.id
                # Amount between 10-20% of target's money
                params['amount'] = int(target.money * random.uniform(0.1, 0.2))
                
            elif crime_type == 'property_vandalism':
                # Find a property owned by someone else
                all_properties = Property.query.filter(Property.owner_id.isnot(None), Property.owner_id != criminal.id).all()
                if not all_properties:
                    return {"success": False, "error": "No valid properties for vandalism"}
                
                target_property = random.choice(all_properties)
                params['target_property_id'] = target_property.id
                # Damage between 10-30% of property value
                params['amount'] = int(target_property.current_price * random.uniform(0.1, 0.3))
                
            elif crime_type == 'rent_evasion':
                # Find properties owned by others
                all_properties = Property.query.filter(Property.owner_id.isnot(None), Property.owner_id != criminal.id).all()
                if not all_properties:
                    return {"success": False, "error": "No valid properties for rent evasion"}
                
                target_property = random.choice(all_properties)
                params['target_property_id'] = target_property.id
                # Rent amount (using base rent as estimate)
                params['amount'] = target_property.base_rent
                
            elif crime_type == 'forgery':
                # Amount between 100-500
                params['amount'] = random.randint(100, 500)
                
            elif crime_type == 'tax_evasion':
                # Amount between 10-30% of player's money
                params['amount'] = int(criminal.money * random.uniform(0.1, 0.3))
            
            # Get crime controller
            crime_controller = current_app.config.get('crime_controller')
            if not crime_controller:
                return {"success": False, "error": "Crime controller not initialized"}
            
            # Commit the crime
            result = crime_controller.commit_crime(criminal.id, crime_type, **params)
            
            # Add admin-triggered flag
            result['admin_triggered'] = True
            result['criminal_name'] = criminal.username
            
            return result
            
        except Exception as e:
            logger.error(f"Error triggering random crime: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to trigger random crime: {str(e)}"}

    def get_crime_history(self, filters=None, limit=50):
        """
        Get history of crimes with optional filtering.
        
        Args:
            filters (dict, optional): Filtering options
            limit (int, optional): Maximum number of results to return
            
        Returns:
            dict: Crime history
        """
        try:
            from src.models.crime import Crime
            from datetime import datetime
            
            # Start with a base query
            query = Crime.query
            
            # Apply filters
            if filters:
                if 'player_id' in filters:
                    query = query.filter_by(player_id=filters['player_id'])
                
                if 'start_date' in filters:
                    try:
                        start_date = datetime.fromisoformat(filters['start_date'])
                        query = query.filter(Crime.timestamp >= start_date)
                    except ValueError:
                        pass
                
                if 'end_date' in filters:
                    try:
                        end_date = datetime.fromisoformat(filters['end_date'])
                        query = query.filter(Crime.timestamp <= end_date)
                    except ValueError:
                        pass
            
            # Order by timestamp descending (most recent first)
            query = query.order_by(Crime.timestamp.desc())
            
            # Apply limit
            crimes = query.limit(limit).all()
            
            # Format results
            results = []
            for crime in crimes:
                crime_dict = crime.to_dict()
                # Add player info
                player = Player.query.get(crime.player_id)
                if player:
                    crime_dict['player_name'] = player.username
                
                # Add target info if applicable
                if crime.target_player_id:
                    target_player = Player.query.get(crime.target_player_id)
                    if target_player:
                        crime_dict['target_player_name'] = target_player.username
                
                results.append(crime_dict)
            
            return {
                "success": True,
                "count": len(results),
                "crimes": results
            }
            
        except Exception as e:
            logger.error(f"Error getting crime history: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to get crime history: {str(e)}"}

    def release_player_from_jail(self, player_id):
        """
        Release a player from jail.
        
        Args:
            player_id (int): ID of the player to release
            
        Returns:
            dict: Result of the jail release
        """
        try:
            # Get player
            player = Player.query.get(player_id)
            if not player:
                return {"success": False, "error": "Player not found"}
            
            # Check if player is in jail
            if not player.in_jail:
                return {"success": False, "error": "Player is not in jail"}
            
            # Release player
            player.in_jail = False
            player.jail_turns = 0
            db.session.add(player)
            db.session.commit()
            
            # Log the action
            logger.info(f"Admin released player {player.username} (ID: {player_id}) from jail")
            
            # Notify clients if socket controller exists
            socket_controller = current_app.config.get('socket_controller')
            if socket_controller:
                socket_controller.notify_player_update(player_id)
                socket_controller.notify_admin_action({
                    "action": "jail_release",
                    "player_id": player_id,
                    "player_name": player.username,
                    "message": f"Admin released {player.username} from jail",
                    "timestamp": datetime.datetime.now().isoformat()
                })
            
            return {
                "success": True,
                "player_id": player_id,
                "player_name": player.username,
                "message": f"Successfully released {player.username} from jail"
            }
            
        except Exception as e:
            logger.error(f"Error releasing player from jail: {e}", exc_info=True)
            db.session.rollback()
            return {"success": False, "error": f"Failed to release player from jail: {str(e)}"}

    def send_player_to_jail(self, player_id, turns=None, reason="Admin action"):
        """
        Send a player to jail.
        
        Args:
            player_id (int): ID of the player to send to jail
            turns (int, optional): Number of turns to spend in jail
            reason (str, optional): Reason for sending to jail
            
        Returns:
            dict: Result of the jail action
        """
        try:
            # Get player
            player = Player.query.get(player_id)
            if not player:
                return {"success": False, "error": "Player not found"}
            
            # Check if player is already in jail
            if player.in_jail:
                return {"success": False, "error": "Player is already in jail"}
            
            # Use the go_to_jail method if available
            if hasattr(player, 'go_to_jail'):
                player.go_to_jail()
            else:
                # Manual implementation
                player.in_jail = True
                jail_position = 10  # Typically this is the jail position
                player.position = jail_position
                if turns:
                    player.jail_turns = turns
                else:
                    player.jail_turns = 3  # Default jail time
            
            db.session.add(player)
            db.session.commit()
            
            # Log the action
            logger.info(f"Admin sent player {player.username} (ID: {player_id}) to jail for {player.jail_turns} turns. Reason: {reason}")
            
            # Notify clients if socket controller exists
            socket_controller = current_app.config.get('socket_controller')
            if socket_controller:
                socket_controller.notify_player_update(player_id)
                socket_controller.notify_admin_action({
                    "action": "sent_to_jail",
                    "player_id": player_id,
                    "player_name": player.username,
                    "turns": player.jail_turns,
                    "reason": reason,
                    "message": f"Admin sent {player.username} to jail for {player.jail_turns} turns",
                    "timestamp": datetime.datetime.now().isoformat()
                })
            
            return {
                "success": True,
                "player_id": player_id,
                "player_name": player.username,
                "turns": player.jail_turns,
                "reason": reason,
                "message": f"Successfully sent {player.username} to jail for {player.jail_turns} turns"
            }
            
        except Exception as e:
            logger.error(f"Error sending player to jail: {e}", exc_info=True)
            db.session.rollback()
            return {"success": False, "error": f"Failed to send player to jail: {str(e)}"}

    def get_jail_status(self):
        """
        Get current jail status (who is in jail).
        
        Returns:
            dict: Current jail status
        """
        try:
            # Get players in jail
            jailed_players = Player.query.filter_by(in_jail=True).all()
            
            players_data = []
            for player in jailed_players:
                players_data.append({
                    "id": player.id,
                    "name": player.username,
                    "turns_remaining": player.jail_turns,
                    "has_jail_card": player.get_out_of_jail_cards > 0,
                    "position": player.position
                })
            
            return {
                "success": True,
                "jailed_players": players_data,
                "count": len(players_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting jail status: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to get jail status: {str(e)}"}

    def get_transactions(self, filters=None, limit=100, offset=0):
        """
        Get transaction history with filtering options.
        
        Args:
            filters (dict): Filter criteria (player_id, type, min_amount, max_amount, etc.)
            limit (int): Maximum number of transactions to return
            offset (int): Offset for pagination
            
        Returns:
            Dictionary with transaction results
        """
        try:
            query = Transaction.query
            
            # Apply filters if provided
            if filters:
                if 'player_id' in filters:
                    player_id = filters['player_id']
                    query = query.filter((Transaction.from_player_id == player_id) | 
                                        (Transaction.to_player_id == player_id))
                
                if 'type' in filters:
                    query = query.filter(Transaction.transaction_type == filters['type'])
                
                if 'min_amount' in filters:
                    query = query.filter(Transaction.amount >= filters['min_amount'])
                
                if 'max_amount' in filters:
                    query = query.filter(Transaction.amount <= filters['max_amount'])
                
                if 'start_date' in filters:
                    start_date = datetime.datetime.fromisoformat(filters['start_date'])
                    query = query.filter(Transaction.timestamp >= start_date)
                
                if 'end_date' in filters:
                    end_date = datetime.datetime.fromisoformat(filters['end_date'])
                    query = query.filter(Transaction.timestamp <= end_date)
            
            # Get total count for pagination
            total = query.count()
            
            # Apply pagination
            transactions = query.order_by(Transaction.timestamp.desc()).limit(limit).offset(offset).all()
            
            # Format transactions
            transactions_list = []
            for transaction in transactions:
                # Get player names for readability
                from_player_name = None
                to_player_name = None
                
                if transaction.from_player_id:
                    from_player = Player.query.get(transaction.from_player_id)
                    if from_player:
                        from_player_name = from_player.username
                
                if transaction.to_player_id:
                    to_player = Player.query.get(transaction.to_player_id)
                    if to_player:
                        to_player_name = to_player.username
                
                transactions_list.append({
                    "id": transaction.id,
                    "from_player_id": transaction.from_player_id,
                    "from_player_name": from_player_name,
                    "to_player_id": transaction.to_player_id,
                    "to_player_name": to_player_name,
                    "amount": transaction.amount,
                    "transaction_type": transaction.transaction_type,
                    "description": transaction.description,
                    "timestamp": transaction.timestamp.isoformat(),
                    "lap_number": transaction.lap_number
                })
            
            return {
                "success": True,
                "transactions": transactions_list,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error(f"Error getting transactions: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
            
    def create_transaction(self, from_player_id, to_player_id, amount, transaction_type="admin_transfer", description="Admin created transaction"):
        """
        Create a new transaction between players or between player and bank.
        
        Args:
            from_player_id (int, optional): Source player ID (None for bank)
            to_player_id (int, optional): Destination player ID (None for bank)
            amount (int): Transaction amount (positive number)
            transaction_type (str): Type of transaction
            description (str): Description of the transaction
            
        Returns:
            Dict with operation result
        """
        try:
            if amount <= 0:
                return {"success": False, "error": "Amount must be positive"}
                
            # Validate players exist if IDs provided
            from_player = None
            to_player = None
            
            if from_player_id:
                from_player = Player.query.get(from_player_id)
                if not from_player:
                    return {"success": False, "error": f"Source player with ID {from_player_id} not found"}
                    
                # Check if player has enough money
                if from_player.money < amount:
                    return {"success": False, "error": f"Source player doesn't have enough money (has ${from_player.money}, needs ${amount})"}
            
            if to_player_id:
                to_player = Player.query.get(to_player_id)
                if not to_player:
                    return {"success": False, "error": f"Destination player with ID {to_player_id} not found"}
            
            # Get previous balances for logging
            from_previous_balance = from_player.money if from_player else None
            to_previous_balance = to_player.money if to_player else None
            
            # Create transaction record
            transaction = Transaction(
                from_player_id=from_player_id,
                to_player_id=to_player_id,
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                timestamp=datetime.datetime.now()
            )
            
            # Update player balances
            if from_player:
                from_player.money -= amount
                
            if to_player:
                to_player.money += amount
                
            # Save changes
            db.session.add(transaction)
            
            if from_player:
                db.session.add(from_player)
                
            if to_player:
                db.session.add(to_player)
                
            db.session.commit()
            
            # Log the action
            logger.info(f"Admin created transaction: {transaction_type}, amount: ${amount}, "
                       f"from: {from_player.username if from_player else 'Bank'}, "
                       f"to: {to_player.username if to_player else 'Bank'}, "
                       f"description: {description}")
            
            # Notify clients of the update via socket if available
            socket_controller = current_app.config.get('socket_controller')
            if socket_controller:
                # Notify about player updates
                if from_player_id:
                    socket_controller.notify_player_update(from_player_id)
                    
                if to_player_id:
                    socket_controller.notify_player_update(to_player_id)
                
                # Notify admins about the action
                socket_controller.notify_admin_action({
                    "action": "transaction_created",
                    "transaction_id": transaction.id,
                    "from_player_id": from_player_id,
                    "from_player_name": from_player.username if from_player else "Bank",
                    "to_player_id": to_player_id,
                    "to_player_name": to_player.username if to_player else "Bank",
                    "amount": amount,
                    "transaction_type": transaction_type,
                    "description": description,
                    "timestamp": datetime.datetime.now().isoformat()
                })
            
            return {
                "success": True,
                "transaction_id": transaction.id,
                "from_player_id": from_player_id,
                "from_player_name": from_player.username if from_player else "Bank",
                "from_previous_balance": from_previous_balance,
                "from_new_balance": from_player.money if from_player else None,
                "to_player_id": to_player_id,
                "to_player_name": to_player.username if to_player else "Bank",
                "to_previous_balance": to_previous_balance,
                "to_new_balance": to_player.money if to_player else None,
                "amount": amount,
                "transaction_type": transaction_type,
                "description": description
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating transaction: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def get_all_loans(self, filters=None):
        """
        Get all loans in the system with filtering options.
        
        Args:
            filters (dict): Filter criteria (player_id, status, etc.)
            
        Returns:
            Dictionary with loans results
        """
        try:
            query = Loan.query
            
            # Apply filters if provided
            if filters:
                if 'player_id' in filters:
                    query = query.filter(Loan.player_id == filters['player_id'])
                
                if 'status' in filters:
                    # Map 'status' to 'is_active'
                    is_active = filters['status'] == 'active'
                    query = query.filter(Loan.is_active == is_active)
                
                if 'loan_type' in filters:
                    query = query.filter(Loan.loan_type == filters['loan_type'])
                
                if 'min_amount' in filters:
                    query = query.filter(Loan.amount >= filters['min_amount'])
                
                if 'max_amount' in filters:
                    query = query.filter(Loan.amount <= filters['max_amount'])
            
            # Get total statistics
            total_loans = query.count()
            active_loans = query.filter(Loan.is_active == True).count()
            
            # Get the loans
            loans = query.all()
            
            # Gather total loan values
            total_principal = sum(loan.amount for loan in loans)
            total_current_value = sum(loan.outstanding_balance for loan in loans)
            
            # Format loans
            loans_list = []
            for loan in loans:
                # Get player name for readability
                player_name = None
                player = Player.query.get(loan.player_id)
                if player:
                    player_name = player.username
                
                loans_list.append({
                    "id": loan.id,
                    "player_id": loan.player_id,
                    "player_name": player_name,
                    "amount": loan.amount,
                    "interest_rate": loan.interest_rate,
                    "current_value": loan.outstanding_balance,
                    "status": 'active' if loan.is_active else 'paid',
                    "loan_type": loan.loan_type,
                    "creation_lap": loan.start_lap,
                    "length_laps": loan.length_laps,
                    "due_lap": loan.start_lap + loan.length_laps,
                    "last_payment_lap": None,  # Not available in current model
                    "property_id": loan.property_id,
                    "creation_date": loan.created_at.isoformat() if loan.created_at else None,
                    "is_active": loan.is_active
                })
            
            # Get game state for current lap
            game_state = GameState.get_instance()
            current_lap = game_state.current_lap if game_state else 0
            
            return {
                "success": True,
                "loans": loans_list,
                "total_loans": total_loans,
                "active_loans": active_loans,
                "total_principal": total_principal,
                "total_current_value": total_current_value,
                "current_lap": current_lap
            }
            
        except Exception as e:
            logger.error(f"Error getting all loans: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def get_player_financial_data(self, player_id=None):
        """
        Get financial data for a specific player or all players.
        
        Args:
            player_id (int, optional): If provided, get data for this player only.
            
        Returns:
            Dict with player financial data
        """
        try:
            if player_id:
                # Get specific player
                player = Player.query.get(player_id)
                if not player:
                    return {"success": False, "error": "Player not found"}
                
                # Get player's loans
                loans = Loan.query.filter_by(player_id=player_id).all()
                
                # Calculate net worth
                net_worth = player.money
                for prop in player.properties:
                    net_worth += prop.price # Use base price for simplicity
                
                # Calculate loan totals
                loans_total = sum(loan.amount for loan in loans if loan.is_active)
                
                return {
                    "success": True,
                    "player": {
                        "id": player.id,
                        "name": player.username,
                        "money": player.money,
                        "net_worth": net_worth,
                        "credit_score": player.credit_score,
                        "properties_count": len(player.properties),
                        "properties_value": sum(prop.price for prop in player.properties),
                        "active_loans": len([loan for loan in loans if loan.is_active]),
                        "loans_total": loans_total
                    }
                }
            else:
                # Get all players
                players = Player.query.filter_by(in_game=True).all()
                
                player_data = []
                for player in players:
                    # Get player's loans
                    loans = Loan.query.filter_by(player_id=player.id).all()
                    
                    # Calculate net worth
                    net_worth = player.money
                    for prop in player.properties:
                        net_worth += prop.price # Use base price for simplicity
                    
                    # Calculate loan totals
                    loans_total = sum(loan.amount for loan in loans if loan.is_active)
                    
                    player_data.append({
                        "id": player.id,
                        "name": player.username,
                        "money": player.money,
                        "net_worth": net_worth,
                        "credit_score": player.credit_score,
                        "properties_count": len(player.properties),
                        "properties_value": sum(prop.price for prop in player.properties),
                        "active_loans": len([loan for loan in loans if loan.is_active]),
                        "loans_total": loans_total
                    })
                
                total_money = sum(p["money"] for p in player_data) if player_data else 0
                total_net_worth = sum(p["net_worth"] for p in player_data) if player_data else 0
                total_loans = sum(p["loans_total"] for p in player_data) if player_data else 0
                
                return {
                    "success": True,
                    "players": player_data,
                    "total_players": len(player_data),
                    "total_money": total_money,
                    "total_net_worth": total_net_worth,
                    "total_loans": total_loans
                }
                
        except Exception as e:
            logger.error(f"Error getting player financial data: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to retrieve player financial data: {str(e)}"}