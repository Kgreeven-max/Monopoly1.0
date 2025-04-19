# Shared Component Notes (Controllers Batch 1)

### src/controllers/team_controller.py Notes

*   **Purpose:** Manages team creation, player assignment, team-specific turn processing (like income sharing and score calculation), status retrieval, property transfers between teams, and checking team-based win conditions.
*   **Dependencies:** `logging`, `src.models` (`db`, `Team`, `Player`, `Property`, `Game`), `src.models.game_mode.GameMode`, `datetime`, `socketio` (optional). Relies heavily on the database session (`db.session`) for persistence.
*   **Key Functions:**
    *   `create_teams`: Initializes teams and assigns players according to provided configurations, respecting `GameMode` settings.
    *   `_assign_players_to_teams`: Private helper for assigning players during team creation.
    *   `process_team_turn`: Executes team-specific logic at the end of a turn, such as income sharing and score updates, based on `GameMode` rules.
    *   `get_team_status`: Fetches and returns the current status of all teams in a game.
    *   `transfer_property`: Facilitates moving property ownership between teams, contingent on `GameMode` allowing property sharing.
    *   `check_team_win_condition`: Evaluates if a winning state has been reached for teams, considering elimination (last team remaining) or reaching a time limit (highest score).
*   **Observations/Potential Points:**
    *   Consistent error handling pattern using try/except blocks, logging errors, and returning structured success/failure dictionaries.
    *   Functionality is tightly coupled with `GameMode` settings which enable/disable specific team mechanics.
    *   Includes an optional `socketio` instance, presumably for real-time updates related to team actions, though its direct use isn't visible within these methods. Further investigation in calling code or `socket_controller.py` might be needed to see how notifications are emitted.
    *   Win condition logic covers both player/team elimination and score comparison at a game time limit.

### src/controllers/auction_controller.py Notes

*   **Purpose:** This file sets up and manages the socket event handlers related to the property auction system. It acts as the communication bridge between client actions (via websockets) and the backend auction logic.
*   **Dependencies:** `flask_socketio` (`emit`), `logging`, `flask` (`request`), `src.models.auction_system.AuctionSystem`, `src.models.player.Player`. (Also imports `Property` and `CommunityFund`, likely used by the `AuctionSystem`). Relies on a `banker` object and Flask app configuration (`ADMIN_KEY`).
*   **Key Components:**
    *   `register_auction_events(socketio, banker)`: Initializes a global `AuctionSystem` instance and registers all auction-related socket event handlers (`@socketio.on(...)`).
    *   **Event Handlers:**
        *   `handle_start_auction`: Initiates a standard auction for a property (can be triggered by admin).
        *   `handle_start_foreclosure`: Initiates a foreclosure auction (admin only).
        *   `handle_place_bid`: Processes a player's bid, including player PIN validation and bid amount validation.
        *   `handle_pass_auction`: Processes a player's decision to pass on bidding.
        *   `handle_get_auctions`: Returns a list of active auctions.
        *   `handle_get_auction`: Returns details for a specific auction.
        *   `handle_cancel_auction`: Allows an admin to cancel an ongoing auction.
    *   `get_auction_system()`: Provides access to the singleton `AuctionSystem` instance.
*   **Observations/Potential Points:**
    *   Uses a global variable (`auction_system`) to hold the state/logic controller, implying a singleton pattern.
    *   Implements basic authorization checks (player PIN, admin key) before processing actions.
    *   Leverages `flask_socketio` extensively for real-time communication, emitting confirmations or errors back to the originating client (`room=request.sid`).
    *   The core auction mechanics (timing, bid tracking, winner determination) are delegated to the `AuctionSystem` model, keeping this controller focused on communication and validation.
    *   Admin functionality (starting foreclosure, cancelling auctions) is gated by an `ADMIN_KEY` from the application configuration.

### src/controllers/adaptive_difficulty_controller.py Notes

*   **Purpose:** Implements a system to dynamically adjust the difficulty of AI (bot) players based on the performance difference between human and bot players. The goal is to maintain a competitive balance during the game.
*   **Dependencies:** `logging`, `random`, `datetime`, `src.models` (`db`, `Player`, `Property`, `GameState`). It also dynamically imports `active_bots` from `src.controllers.bot_controller` when adjusting difficulty. An optional `socketio` instance is used for notifications.
*   **Key Functions:**
    *   `__init__`: Sets up initial state, including difficulty adjustment parameters and the last assessment time.
    *   `assess_game_balance`: Calculates performance metrics (net worth, properties, cash) for human and bot players, computes a balance score, and determines if a difficulty adjustment ('easier' or 'harder') is needed. Runs at most every 5 minutes.
    *   `adjust_difficulty`: Modifies the difficulty level (`easy`, `medium`, `hard`) of active bots based on the assessment result. It fetches bot instances from `active_bots` and applies parameter adjustments. Notifies admins via Socket.IO if available.
    *   `_calculate_player_metrics`: Private helper to compute average net worth, properties, and cash for a given list of players.
    *   `_calculate_new_difficulty`: Private helper to determine the next difficulty level (up or down) based on the current level.
    *   `_apply_difficulty_adjustments`: Private helper that applies specific parameter changes (like `decision_accuracy`, `planning_horizon`, `risk_tolerance`) to a bot based on its new difficulty level and potentially its type (e.g., `ConservativeBot`, `AggressiveBot`).
*   **Observations/Potential Points:**
    *   Uses a time-based throttle (`last_assessment_time`) to limit the frequency of balance assessments.
    *   The balance calculation is based on a weighted average of net worth, property count, and cash ratios between humans and bots. Thresholds (0.7, 1.3) trigger adjustments.
    *   Difficulty adjustment involves changing the bot's difficulty string (`'easy'`, `'medium'`, `'hard'`) and then applying corresponding numerical parameter changes (e.g., accuracy, planning horizon).
    *   There's a circular dependency potential: this controller imports from `bot_controller` (`active_bots`) inside a method (`adjust_difficulty`). While this avoids import errors at startup, it's less clean than importing at the top level. If `bot_controller` also imports this controller, it could be problematic.
    *   Adjustments are applied to *active* bot instances retrieved from the `active_bots` dictionary in `bot_controller`, meaning it modifies the in-memory state of the bots directly.
    *   Includes logic to apply bot-type-specific modifiers on top of the standard difficulty adjustments.

### src/controllers/crime_controller.py Notes

*   **Purpose:** Manages the crime system within the game, allowing players to attempt various criminal activities and handling the consequences, detection, and tracking of these actions.
*   **Dependencies:** `logging`, `random`, `datetime`, `flask_socketio` (`emit`), `src.models` (`db`, `Player`, `Property`, `GameState`, `Crime` and its subclasses like `Theft`, `PropertyVandalism`, etc.).
*   **Key Functions:**
    *   `__init__`: Initializes the controller, optionally taking a `socketio` instance for notifications and tracking the last police patrol time.
    *   `commit_crime`: Allows a player to attempt a specific `crime_type` (e.g., 'theft', 'vandalism'). Delegates the actual crime logic and detection roll to the `Player` model's `commit_crime` method. Broadcasts detected crimes or privately notifies the player on success using Socket.IO.
    *   `get_player_crimes`: Retrieves a player's *detected* criminal history. Undetected crimes are not exposed here.
    *   `check_for_police_patrol`: A periodic check (minimum 30 minutes) that randomly detects recent, previously undetected crimes based on game difficulty. Detected crimes trigger consequences, update player records, and are broadcast.
    *   `_broadcast_crime_detection`: Private helper to send a Socket.IO 'game_event' notification to all players when a crime is detected.
    *   `_notify_player_of_crime`: Private helper to send a private Socket.IO notification to the player who successfully committed an undetected crime.
    *   `get_crime_statistics` (partially visible): Seems intended to gather overall crime statistics for the game.
    *   `process_property_damage_repair` (partially visible): Appears to handle the repair of property damage potentially caused by crimes like vandalism.
*   **Observations/Potential Points:**
    *   The core logic for executing a crime and its immediate detection chance resides within the `Player` model (`player.commit_crime`). This controller orchestrates the action and handles broader system effects like police patrols and notifications.
    *   Uses a two-tiered detection system: immediate chance upon committing the crime, and a later chance via random police patrols.
    *   Detection probability during patrols is influenced by the game's `difficulty` setting.
    *   Employs Socket.IO for real-time updates: public broadcasts for detected crimes and private messages for successful, undetected ones.
    *   Manages player `criminal_record` and `community_standing` based on crime outcomes.
    *   Relies on specific `Crime` subclasses (`Theft`, `PropertyVandalism`, etc.) defined in `src/models/crime.py` for different crime types and consequences.

### src/controllers/remote_controller.py Notes

*   **Purpose:** Manages the setup and control of a Cloudflare Tunnel (`cloudflared`) to expose the local Flask application to the internet for remote players.
*   **Dependencies:** `logging`, `os`, `json`, `requests` (imported but not used?), `subprocess`, `flask` (`current_app`), `datetime`, `re` (used locally in `create_tunnel`), `time` (used locally in `start_tunnel` and `stop_tunnel`).
*   **Key Functions:**
    *   `__init__`: Initializes the controller, finds the `cloudflared` binary path, and sets the config file path.
    *   `_find_cloudflared_binary`: Attempts to locate the `cloudflared` executable on the system PATH or common locations.
    *   `check_cloudflared_installed`: Checks if the binary was found.
    *   `get_cloudflared_version`: Retrieves the installed `cloudflared` version using `subprocess`.
    *   `check_tunnel_config`, `load_tunnel_config`, `save_tunnel_config`: Handle reading/writing the tunnel configuration JSON file (`cloudflared_config.json`).
    *   `create_tunnel`: Executes `cloudflared tunnel create` to set up a new tunnel, extracts the tunnel ID, and saves a basic configuration file (including a placeholder hostname like `pinopoly.tunnel.your-subdomain.com`).
    *   `start_tunnel`: Executes `cloudflared tunnel run` as a background process using `subprocess.Popen`. Waits briefly and attempts to confirm the process started. Stores the tunnel URL and process handle.
    *   `stop_tunnel`: Terminates the running `cloudflared` process (`self.tunnel_process`). Uses `terminate()` first, then `kill()` if necessary.
    *   `get_tunnel_status` (partially visible): Likely checks the status of the tunnel process and configuration.
    *   `delete_tunnel` (partially visible): Likely executes `cloudflared tunnel delete` and removes the local configuration file.
    *   `get_connected_players` (partially visible): Purpose unclear from the partial view, might relate to players connected via the tunnel? Seems potentially out of place in this controller.
*   **Observations/Potential Points:**
    *   Relies heavily on the `cloudflared` command-line tool being installed and executable.
    *   Uses `subprocess` to interact with the `cloudflared` tool, capturing output and handling potential errors.
    *   Manages the tunnel process lifecycle (`start`, `stop`).
    *   Configuration (tunnel ID, name, ingress rules) is stored locally in `cloudflared_config.json`.
    *   The default ingress rule uses a placeholder hostname (`pinopoly.tunnel.your-subdomain.com`). This would need to be manually configured in Cloudflare DNS or changed to a more suitable setup for actual use.
    *   Includes basic checks (`time.sleep`) after starting/stopping the process, which might not be fully reliable for ensuring the tunnel is operational or fully stopped.
    *   The `requests` library is imported but doesn't seem to be used in the visible code.
    *   The `get_connected_players` method seems slightly out of scope for a controller focused solely on managing the Cloudflare Tunnel process itself.

### src/controllers/game_controller.py Notes

*   **Purpose:** Acts as the central orchestrator for the game's overall flow and state. Manages game lifecycle (creation, start, end), player addition, core game state access, configuration, historical record retrieval, and handling player-initiated property actions. It also appears responsible for turn progression.
*   **Dependencies:** `logging`, `datetime`, `flask` (`request`), `src.models` (`db`, `Player`, `GameState`, `Property`, `Transaction`, `GameHistory`, `GameMode`), `src.controllers.team_controller.TeamController`, `src.controllers.game_mode_controller.GameModeController`.
*   **Key Functions:**
    *   `__init__`: Sets up the logger, stores the `socketio` instance, and initializes instances of `GameModeController` and `TeamController`, indicating interaction with game mode and team functionalities.
    *   `create_new_game`: Initializes or resets the `GameState` singleton with specified parameters (difficulty, limits, rules).
    *   `add_player`: Adds a human player during the 'setup' phase, assigning starting cash based on difficulty and ensuring username uniqueness.
    *   `start_game`: Changes the game status to 'active', records the start time, determines the first player, and validates the minimum player count.
    *   `end_game`: Sets the game status to 'ended', records the end time, determines the winner using `_determine_winner`, and logs the game outcome in `GameHistory`.
    *   `_determine_winner`: Calculates the net worth (cash + property value) of non-bankrupt players and identifies the winner.
    *   `get_game_state`: Retrieves the current high-level status and configuration of the game.
    *   `get_players`: Returns information about players currently participating in the game.
    *   `update_game_config`: Provides a mechanism to modify game settings, potentially during the setup phase or even mid-game.
    *   `get_game_history_by_id`, `get_all_game_history`: Fetches records of past completed games.
    *   `handle_property_action`: Serves as a primary entry point for player actions related to properties (buy, mortgage, improve, etc.). It validates the player's PIN and delegates the specific action to internal helper methods (`_handle_*`).
    *   `_handle_buy_property`, `_handle_mortgage_property`, `_handle_unmortgage_property`, `_handle_repair_property`, `_handle_improve_property`: Internal methods containing the logic for specific property actions, likely involving financial transactions and updates to player/property states.
    *   `end_turn`: Manages the transition to the next player's turn, potentially triggering checks for game end conditions, lap completion logic, and interaction with other systems (like team processing or events).
*   **Observations/Potential Points:**
    *   This controller is central to game operation, coordinating state changes, player actions, and interactions with other controllers.
    *   Uses a singleton pattern for `GameState`, ensuring a single source of truth for the current game's status.
    *   Winner determination is based purely on net worth. Team-based win conditions are likely handled by `TeamController`, possibly invoked during `end_turn` or a separate check.
    *   Property actions are handled here, including PIN validation. The responsibility division between this and `property_controller.py` should be noted; this controller seems focused on player *requests* for property actions, while `property_controller.py` might manage property state more broadly.
    *   The `end_turn` function is critical and likely complex, handling player rotation, lap counting, and potentially calling out to other controllers or systems.
    *   Standard pattern of returning structured success/error dictionaries.

### src/controllers/socket_controller.py Notes

*   **Purpose:** This controller serves as the central hub for all real-time communication using Flask-SocketIO. It initializes various game subsystems, registers event handlers from other specialized controllers (auction, property, bot, social), and defines handlers for core connection logic, chat, player actions, game events, and connection management.
*   **Dependencies:** `flask_socketio` (`emit`, `join_room`, `leave_room`), `logging`, `datetime`, `uuid`, `flask` (`request`, `current_app`), `src.models` (`db`, `Player`, `GameState`, `Property`, `EventSystem`, `Banker`, `CommunityFund`, `get_banker`, `get_auction_system`), various other controllers (`auction`, `property`, `bot`, `bot_event`, `special_space`, `social`, `social.socket_handlers`), `eventlet` (used for disconnect timeouts).
*   **Key Components:**
    *   **Global Instances:** Manages global instances of `banker`, `community_fund`, `event_system`, `socketio`, `special_space_controller`, and tracks player connections (`connected_players`, `player_reconnect_timers`).
    *   `register_socket_events(app_socketio)`: The main initialization function. It sets up global service instances (Banker, CommunityFund, EventSystem, SpecialSpaceController, SocialController), ensures the `GameState` exists, stores these instances in the Flask app config for broader access, and calls registration functions from other controllers (`register_auction_events`, `register_property_events`, `register_bot_events`, `register_bot_event_handlers`, `register_social_socket_handlers`).
    *   **Core Connection Handlers:**
        *   `handle_connect`: Logs connection and sends acknowledgment.
        *   `handle_disconnect`: Logs disconnection, updates `connected_players`, and initiates a reconnection timer (`eventlet.spawn_after`) if remote play is enabled. If the timer expires, it notifies others and may auto-end the player's turn.
        *   `handle_register_device`: Allows clients to identify themselves as 'player', 'admin', or 'tv', authenticating them and placing their socket into appropriate rooms (e.g., `player_X`, `game_Y`, `admin`, `tv`, `channel_Z`, `alliance_A`).
        *   `handle_heartbeat`, `handle_ping_player`, `handle_ping_response`, `handle_ping`: Implement mechanisms to check connection liveness.
    *   **Game Action Handlers:**
        *   `handle_chat_message`: Relays chat messages to appropriate rooms (delegated to `SocialController`).
        *   `handle_end_turn`: Processes a player's request to end their turn, likely triggering game logic in `GameState` or `GameController`.
        *   `handle_repair_property`, `handle_draw_chance_card`, `handle_draw_community_chest_card`, `handle_land_on_special_space`: Trigger specific game actions, often delegating logic to other controllers/models (e.g., `SpecialSpaceController`, `EventSystem`).
    *   **Player/Game Management Handlers:**
        *   `handle_join_game`: Allows a player to join the main game room.
        *   `handle_get_connection_status`: Returns the current connection status of players.
        *   `handle_remove_player`: Allows an admin to remove a player from the game.
    *   **Social Feature Handlers:**
        *   `handle_join_channel`, `handle_leave_channel`, `handle_message_reaction`: Manage chat channel subscriptions and message interactions (delegated to `SocialController`).
    *   `handle_remote_player_connect`: (Partially visible function, not a socket handler) Likely involved in processing reconnections.
*   **Observations/Potential Points:**
    *   This file is very large (over 900 lines) and has many responsibilities. It acts as both an initializer for many core systems and the primary router for socket events. Consider potential refactoring opportunities to break down responsibilities further.
    *   Uses global variables for core services (`banker`, `community_fund`, etc.). While initialized centrally, globals can sometimes make dependencies less clear. Storing them in `app.config` provides an alternative access method.
    *   The disconnection handling logic is complex, involving timers (`eventlet`) and state tracking (`connected_players`, `player_reconnect_timers`) to manage temporary disconnections vs. timeouts, especially for remote play.
    *   It registers handlers from many other controller files, making it the central integration point for real-time features.
    *   The use of specific rooms (`player_X`, `game_Y`, `admin`, `tv`, `channel_Z`, `alliance_A`) is key to targeting messages efficiently.
    *   Authentication/Authorization is performed within handlers (e.g., checking PINs, admin keys).

### src/controllers/finance_controller.py Notes

*   **Purpose:** Manages various player financial activities beyond basic cash transactions. This includes standard loans, Certificates of Deposit (CDs), Home Equity Lines of Credit (HELOCs), loan repayment, CD withdrawal, checking eligibility, calculating interest rates, retrieving loan information, and handling player bankruptcy.
*   **Dependencies:** `datetime`, `logging`, `typing` (`Dict`, `List`, etc.), `src.models` (`db`, `finance.loan.Loan`, `Player`, `Property`, `GameState`, `Transaction`). It also accepts optional `socketio` and `banker` instances for communication and potentially transaction processing (though direct `banker` use isn't visible in the reviewed methods).
*   **Key Functions:**
    *   `__init__`: Stores optional `socketio` and `banker` instances.
    *   `create_loan`: Creates a standard fixed-term loan for a player after validating credentials, eligibility (`_is_eligible_for_loan`), calculating interest (`_calculate_loan_interest_rate`), disbursing funds, and recording the transaction.
    *   `repay_loan`: Handles partial or full repayment of a loan, verifying ownership, checking available cash, processing the repayment via the `Loan` model, updating player cash, and recording the transaction.
    *   `create_cd`: Allows a player to invest cash into a CD for a fixed term (3, 5, or 7 laps). Validates cash, term, calculates interest (`_calculate_cd_interest_rate`), deducts cash, creates a `Loan` record (representing the bank's liability), and records the transaction.
    *   `withdraw_cd`: Processes the withdrawal of a CD, checking if it has matured, calculating potential early withdrawal penalties, paying out the principal + interest (minus penalty), updating player cash, marking the CD `Loan` as repaid, and recording the transaction.
    *   `create_heloc`: Creates a HELOC loan secured against a player's property. Validates ownership, checks if the property is mortgaged, calculates the maximum allowed amount (`_calculate_max_heloc_amount`) and interest rate (`_calculate_heloc_interest_rate`), disburses funds, creates the `Loan`, and records the transaction.
    *   `get_interest_rates`: Retrieves current interest rates for various financial products (loans, CDs, HELOCs), likely influenced by game state or economic factors.
    *   `get_player_loans`: Fetches all active financial instruments (loans, CDs, HELOCs) for a specific player.
    *   `declare_bankruptcy`: Handles the process when a player goes bankrupt. This likely involves liquidating assets (properties), clearing debts, marking the player as bankrupt, and removing them from active play. It interacts with the `Banker` for asset liquidation.
    *   **Internal Helper Methods:**
        *   `_is_eligible_for_loan`: Checks if a player meets criteria for a loan (e.g., debt-to-income ratio, existing loans).
        *   `_calculate_loan_interest_rate`, `_calculate_cd_interest_rate`, `_calculate_heloc_interest_rate`: Determine interest rates based on game factors (e.g., economic phase, player risk, term length).
        *   `_calculate_max_heloc_amount`: Calculates the maximum loan amount available against a property's equity.
*   **Observations/Potential Points:**
    *   Uses the `Loan` model from `src/models/finance/loan.py` to represent various financial instruments (standard loans, CDs, HELOCs), distinguishing them by `loan_type`.
    *   Integrates financial concepts like interest rates (potentially dynamic), term lengths, eligibility checks, and collateral (for HELOCs).
    *   Includes a bankruptcy mechanism with asset liquidation.
    *   Relies on PIN authentication for player-initiated financial actions.
    *   Uses type hints (`-> Dict`, `player_id: int`) for better code clarity.
    *   Interaction with the `Banker` model seems implied for transactions and bankruptcy, although not directly visible in all method signatures shown.
    *   Emits Socket.IO events for key financial actions (loan creation, repayment, etc.) if `socketio` is provided.

### src/controllers/property_controller.py Notes

*   **Purpose:** This file defines socket event handlers specifically for player actions related to properties. It handles buying, declining (which may trigger an auction), improving, removing improvements, mortgaging, unmortgaging, and potentially more complex actions like requesting community approval or commissioning environmental studies for development.
*   **Dependencies:** `flask_socketio` (`emit`), `logging`, `flask` (`request`), `src.models` (`db`, `Player`, `Property`, `GameState`, `Transaction`), `src.controllers.auction_controller` (`get_auction_system`), `datetime`. Requires `socketio` and `banker` instances passed during registration.
*   **Key Functions (Socket Handlers):**
    *   `register_property_events(socketio, banker)`: Registers all property-related socket event handlers and gets the auction system instance.
    *   `handle_buy_property`: Processes a player's request to buy an unowned property. Validates credentials, property availability, and player cash. Updates ownership, deducts cash, records the transaction, and broadcasts the purchase.
    *   `handle_decline_property`: Handles a player choosing not to buy an available property. Validates credentials and property status. Checks `GameState` if an auction is required upon decline; if so, calls `auction_system.start_auction`. Broadcasts the decline or auction start.
    *   `handle_improve_property`: Processes a player's request to add an improvement (e.g., house, hotel) to a property they own. Validates credentials, ownership, checks if improvement is allowed (`property_obj.can_improve`), calculates cost (`property_obj.calculate_improvement_cost`), deducts cash, updates property state (`property_obj.improve`), records the transaction, and broadcasts the improvement. Includes cost breakdown in error messages.
    *   `handle_remove_improvement`: Allows a player to sell an improvement back to the bank (likely at a loss). Validates, checks ownership, calculates refund, updates property state, adds cash, records transaction, broadcasts.
    *   `handle_request_community_approval`: Seems to handle a game mechanic where players need community approval for certain developments. Likely involves costs, checks player standing, and potentially triggers a waiting period or event.
    *   `handle_commission_environmental_study`: Handles another potential development prerequisite, commissioning an environmental study. Involves costs, time delays, and affects property state regarding development readiness.
    *   `handle_mortgage_property`: Processes a player mortgaging a property they own. Validates, checks ownership, updates property state, gives cash (mortgage value) to the player, records transaction, broadcasts.
    *   `handle_unmortgage_property`: Processes a player paying to unmortgage a property. Validates, checks ownership and mortgage status, deducts cash (mortgage value + interest), updates property state, records transaction, broadcasts.
*   **Observations/Potential Points:**
    *   This controller acts as the primary interface for property-related *socket events*. The core logic for *how* properties behave (calculating costs, checking improvement rules, etc.) resides within the `Property` model (`src/models/property.py`).
    *   Relies heavily on the `Property` model's methods (e.g., `can_improve`, `calculate_improvement_cost`, `improve`).
    *   Integrates with the `AuctionSystem` via `get_auction_system()` when properties are declined.
    *   Includes complex game mechanics like community approval and environmental studies, suggesting significant depth beyond standard Monopoly rules. These involve costs, player standing checks, and potential time delays.
    *   Handles both the financial transaction (cash deduction/addition) and the state update (property ownership, improvement level, mortgage status).
    *   Uses PIN validation for player-initiated actions.
    *   Broadcasts significant property changes to all players using `socketio.emit` and sends confirmations back to the requesting player using `emit(..., room=request.sid)`.

### src/controllers/special_space_controller.py Notes

*   **Purpose:** Manages the logic associated with landing on non-property spaces on the game board. This includes handling Chance and Community Chest card draws, processing taxes, sending players to jail, and managing Free Parking effects. It also initializes the special spaces and card decks.
*   **Dependencies:** `typing`, `json`, `random`, `flask_socketio` (`emit`), `datetime`, `src.models` (`special_space` (Card, SpecialSpace, CardDeck, TaxSpace), `Player`, `GameState`, `Banker`, `CommunityFund`, `db`). Requires `socketio`, `banker`, and `community_fund` instances during initialization.
*   **Key Functions:**
    *   `__init__`: Initializes the controller, storing `socketio`, `banker`, and `community_fund`. Crucially, it also creates instances of `CardDeck` for Chance and Community Chest, and an instance of `TaxSpace` to handle tax logic.
    *   `handle_special_space`: The main entry point when a player lands on a special space. It identifies the `space_type` based on the position and calls the appropriate internal method (e.g., `process_chance_card`, `process_community_chest_card`, `tax_handler.process_tax`, `send_to_jail`, `handle_free_parking`).
    *   `process_chance_card`: Draws a card from the `chance_deck`, executes its action using `chance_deck.execute_card_action`, and emits the result via Socket.IO.
    *   `process_community_chest_card`: Draws a card from the `community_chest_deck`, executes its action using `community_chest_deck.execute_card_action`, and emits the result.
    *   `send_to_jail`: Updates the player's state to move them to the jail position, set `in_jail` status, and assign jail turns. Emits the event.
    *   `handle_free_parking`: Checks game settings if Free Parking accumulates funds. If so and funds exist in `CommunityFund`, it transfers the funds to the player via the `Banker`. Emits the result.
    *   `initialize_special_spaces`: Populates the `SpecialSpace` table in the database with definitions for spaces like GO, Jail, Free Parking, Tax spaces, Chance, and Community Chest, clearing any existing ones first.
    *   `initialize_cards`: (Partially visible) Likely responsible for populating the `Card` table with the specific text and actions for all Chance and Community Chest cards, potentially loading from a JSON file or defining them in code. This would be called by the `CardDeck` instances.
*   **Observations/Potential Points:**
    *   This controller orchestrates actions for special spaces, but the detailed logic for card effects and tax calculation resides in the respective model classes (`CardDeck`, `TaxSpace`).
    *   `CardDeck` appears to manage drawing, shuffling (implicitly), and executing the logic defined for each `Card`.
    *   The `TaxSpace` class handles the specifics of calculating and collecting taxes.
    *   Free Parking functionality is configurable (whether it collects fees/fines).
    *   Initialization methods (`initialize_special_spaces`, `initialize_cards`) are likely called once during application setup to populate the database.
    *   Uses Socket.IO extensively to notify the frontend about card draws, jail events, and other special space outcomes.
    *   Relies on injected instances of `Banker` and `CommunityFund` for financial transactions related to cards, taxes, or Free Parking.

### src/controllers/game_mode_controller.py Notes

*   **Purpose:** Manages different game modes (Classic, Speed, Co-op, Tycoon, Market Crash, Team Battle). It provides information about available modes, initializes a game with specific mode settings, updates settings, and checks for mode-specific win conditions. It also handles mode-specific events like market crashes.
*   **Dependencies:** `json`, `logging`, `flask` (`current_app`), `src.models` (`db`, `Game`, `Player`, `Property`, `game_mode.GameMode`), `datetime`, `random`. Requires an optional `socketio` instance.
*   **Key Functions:**
    *   `__init__`: Stores the `socketio` instance.
    *   `get_available_modes`: Returns a structured dictionary describing the different game modes, their rules, objectives, win conditions, etc.
    *   `initialize_game_mode`: Fetches or creates the `GameMode` record for a specific game using `GameMode.create_for_game`. Calls `_initialize_game_systems` to apply mode settings (starting cash, time limits, etc.) to the `Game` and `Player` models. Broadcasts the selected mode.
    *   `update_game_mode_settings`: Allows modification of `GameMode` settings after initialization, potentially even mid-game. Updates the `GameMode` record and calls `_update_game_systems` to apply changes. Broadcasts the update.
    *   `get_game_mode_settings`: Retrieves the current settings for the active game mode.
    *   `_initialize_game_systems`: Private helper to apply initial settings based on the `GameMode` (e.g., player cash, game timers, inflation, event frequency). Calls `_configure_properties` and `_configure_teams`.
    *   `_update_game_systems`: Private helper to apply updated settings to the game state, potentially reconfiguring properties if needed.
    *   `_configure_properties`: Private helper to apply mode-specific configurations to properties (e.g., reduced starting values in Market Crash mode, adding mode-specific data fields).
    *   `_configure_teams`: Private helper, likely configures team-related settings based on `GameMode` (details not fully visible).
    *   `check_win_condition`: Evaluates if the game has ended based on the *active game mode's* specific win condition (e.g., last player standing, highest score after time, collective goals, team victory). This differs from the basic net worth check in `GameController`.
    *   `process_market_crash_events`: (Partially visible) Handles events specific to the "Market Crash" mode, likely involving random economic shifts, property value changes, etc.
*   **Observations/Potential Points:**
    *   Uses a factory pattern (`GameMode.create_for_game`) to instantiate the correct `GameMode` object based on the `mode_id`.
    *   Clearly separates game mode logic from the core game flow (`GameController`).
    *   Allows for significant customization of game rules and objectives through different modes.
    *   Win condition checking is mode-dependent, allowing for varied goals (bankruptcy, score, cooperative objectives).
    *   Includes logic for specific complex modes like "Market Crash," which involves dynamic changes to property values and economic state.
    *   Handles applying mode settings to various parts of the game state (Game, Player, Property).
    *   Uses Socket.IO to broadcast mode selection and updates.

### src/controllers/bot_controller.py Notes

*   **Purpose:** Manages AI players (bots) in the game. It handles their creation, removal, settings updates, and orchestrates their actions during the game through a dedicated action processing thread. It also provides initialization functions.
*   **Dependencies:** `logging`, `random`, `time`, `threading`, `flask_socketio` (`emit`), `flask` (`request`), `src.models` (`db`, `Player`, `GameState`), `src.models.bot_player` (various `BotPlayer` subclasses), `src.controllers.auction_controller` (`get_auction_system`), `src.controllers.bot_event_controller` (`handle_bot_event`, `handle_scheduled_event`).
*   **Key Components:**
    *   `active_bots`: A global dictionary mapping `player_id` to active `BotPlayer` strategy instances (e.g., `ConservativeBot`, `AggressiveBot`).
    *   `bot_action_lock`: A `threading.Lock` to prevent race conditions when multiple bots might try to act concurrently.
    *   `bot_action_thread`: A `threading.Thread` that runs the main bot action loop (`process_bot_actions`).
    *   `register_bot_events(socketio, banker)`: Registers socket handlers for admin actions related to bots.
        *   `handle_create_bot`: Creates a new bot player (`Player` record with `is_bot=True`), assigns a random PIN, instantiates the appropriate `BotPlayer` subclass based on `type`, adds it to `active_bots`, saves to DB, starts the action thread if needed, and broadcasts the creation. Requires admin PIN validation.
        *   `handle_remove_bot`: Removes a bot from `active_bots`, marks the `Player` as not `in_game`, saves to DB, and broadcasts the removal. Requires admin PIN.
        *   `handle_update_bot_settings`: Allows an admin to change a bot's name, type (strategy), or difficulty. Updates the `Player` record and replaces the instance in `active_bots` if type/difficulty changes. Broadcasts the update. Requires admin PIN.
        *   `handle_trigger_bot_market_timing`: (Admin-only) Seems to allow manually triggering a market timing event for a specific bot, likely for testing purposes.
    *   `init_bots_from_database()`: Loads existing bot players from the database at startup and populates the `active_bots` dictionary with corresponding strategy instances.
    *   `start_bot_action_thread(socketio, banker)`: Starts the background thread (`bot_action_thread`) that runs `process_bot_actions` if it's not already running.
    *   `process_bot_actions(socketio, banker)`: The main loop running in the background thread. It likely iterates through `active_bots`, checks game state (whose turn it is, auction status, etc.), and calls appropriate methods on the bot instances (e.g., `take_turn`, `participate_in_auction`) within the `bot_action_lock`. It seems to delegate turn processing and auction participation to `process_bot_turns` and `process_bot_auctions`. It also seems to handle bot events via `handle_bot_event` and scheduled events.
    *   `process_bot_turns(socketio)`: Handles the logic for bots taking their turns when it's their turn in the game sequence.
    *   `process_bot_auctions(socketio)`: Handles bot participation (bidding/passing) in ongoing auctions.
*   **Observations/Potential Points:**
    *   Uses a background thread (`threading.Thread`) for bot actions to avoid blocking the main Flask application thread. Requires careful handling of shared resources (like the database session and `active_bots`) using the `bot_action_lock`.
    *   The core decision-making logic for each bot type resides in the `BotPlayer` subclasses (`ConservativeBot`, `AggressiveBot`, etc.) defined in `src/models/bot_player.py`. This controller manages the *instances* and orchestrates *when* they act.
    *   `active_bots` dictionary holds the *in-memory* state and strategy objects for bots currently playing.
    *   Admin controls (create, remove, update) are protected by an admin PIN stored in `GameState`.
    *   Integrates with other controllers/systems like `AuctionController` (for auctions) and `BotEventController` (for handling bot-specific events).
    *   The separation of `process_bot_actions`, `process_bot_turns`, and `process_bot_auctions` suggests a structured approach within the action loop.

### src/controllers/bot_event_controller.py Notes

*   **Purpose:** Handles events initiated *by* bots or events that significantly affect the game state due to bot/economic simulation (like Market Crashes). It registers handlers for player responses to these events (e.g., responding to a trade offer, answering a challenge) and provides the logic to process the initial event trigger.
*   **Dependencies:** `logging`, `random`, `datetime`, `flask_socketio` (`emit`), `flask` (`request`), `uuid`, `src.models` (`db`, `Player`, `Property`, `GameState`), `src.models.bot_events` (various event classes like `TradeProposal`, `MarketCrash`, `BotChallenge`, and functions like `process_restore_market_prices`).
*   **Key Components:**
    *   `active_events`: A global dictionary storing information about ongoing events initiated by bots (like trades or challenges) that require player responses. The key is a unique `event_id`.
    *   `register_bot_event_handlers(socketio)`: Registers socket event handlers for players *responding* to bot-initiated events.
        *   `handle_trade_response`: Processes a player's 'accept' or 'reject' response to a trade proposal stored in `active_events`. Executes the trade via the `TradeProposal` object if accepted and broadcasts the outcome.
        *   `handle_challenge_response`: Processes a player's answer to a `BotChallenge`. Checks the answer against the stored correct answer, executes the challenge outcome (award prize) via the `BotChallenge` object if correct, and broadcasts the result.
        *   `handle_market_event_info`: Allows players to request information about currently active market events (crashes/booms) by checking property discount/premium states.
    *   `handle_bot_event(event_data, socketio)`: The main entry point called (likely by `BotController` or the bot action loop) when a bot's logic decides to trigger an event. It generates a unique `event_id` and calls the appropriate internal handler based on `event_type`.
    *   **Internal Event Handlers (`_handle_*`)**:
        *   `_handle_trade_proposal`: Creates a `TradeProposal` object based on the bot's desired trade, stores it in `active_events` with the `event_id`, and emits a `trade_proposed` event via Socket.IO to the target player. Includes logic for automatically cancelling the trade after a timeout.
        *   `_handle_property_auction`: Initiates a special bot-driven auction (potentially for properties the bot wants to sell or acquire strategically) using the `PropertyAuction` event class.
        *   `_handle_market_crash`: Triggers a market crash event using the `MarketCrash` class. This likely involves applying discounts to properties, broadcasting the event, and potentially scheduling a recovery event (`process_restore_market_prices`).
        *   `_handle_economic_boom`: Triggers an economic boom event using the `EconomicBoom` class, likely applying premiums to properties and broadcasting.
        *   `_handle_bot_challenge`: Creates a `BotChallenge` (e.g., dice prediction, quiz), stores it in `active_events`, and broadcasts the challenge details to relevant players. Includes timeout logic to end the challenge.
    *   `handle_scheduled_event(event_type, event_data, socketio)`: A separate entry point likely used for events triggered by a scheduler rather than direct bot action (e.g., the market recovering after a crash duration).
*   **Observations/Potential Points:**
    *   This controller bridges bot decision-making (`BotController`, `BotPlayer` models) with interactive game events that require player input or affect the broader game state.
    *   Uses a pattern of creating specific event objects (`TradeProposal`, `MarketCrash`, etc. from `src/models/bot_events.py`) that encapsulate the logic for that event type.
    *   Manages the lifecycle of interactive events (trades, challenges) using the `active_events` dictionary and potentially timeouts (implemented using `eventlet.spawn_after` or similar, though the exact mechanism isn't fully visible in the `_handle_trade_proposal` snippet's timeout function).
    *   Separates the *triggering* of an event (`handle_bot_event`) from the *response handling* (socket handlers like `handle_trade_response`).
    *   Handles large-scale game state changes like market crashes and booms, likely impacting all properties or specific groups.
    *   The `BotChallenge` system adds another layer of interaction beyond standard gameplay.

### src/controllers/social/alliance_controller.py Notes

*   **Purpose:** Manages the lifecycle and interactions of player alliances (similar to guilds or clans). This includes creation, inviting players, handling responses to invites, members leaving, retrieving alliance details, updating settings/roles, and potentially calculating in-game benefits derived from alliances.
*   **Dependencies:** `logging`, `datetime`, `src.models` (`db`, `social.alliance` (Alliance, AllianceMember, AllianceInvite), `social.chat` (Channel, ChannelMember)), `src.controllers.social.chat_controller.ChatController`. Requires a `socketio` instance.
*   **Key Functions:**
    *   `__init__`: Stores `socketio` and initializes an instance of `ChatController` to manage the associated chat channel.
    *   `create_alliance`: Creates a new `Alliance` record, performs validation on name/description length. Automatically creates a corresponding private chat channel using `ChatController`. Adds the creator as the first member with the 'leader' role. Notifies clients via `_notify_alliance_creation`.
    *   `invite_player`: Allows a member with 'leader' or 'officer' role to send an `AllianceInvite` to another player. Checks for existing membership or pending invites. Creates an `AllianceInvite` record. Notifies the invitee via `_notify_alliance_invitation`.
    *   `respond_to_invite`: Handles the invitee's response (accept/decline). Validates the invite belongs to the player and is pending. If accepted, updates the invite status, creates an `AllianceMember` record, adds the player to the alliance's chat channel, and notifies members via `_notify_player_joined`. If declined, updates status and notifies the inviter via `_notify_invite_declined`.
    *   `leave_alliance`: Allows a member to leave an alliance. Handles checks to prevent the last leader from leaving without promoting someone else or disbanding the alliance. Removes the player from the alliance chat. Notifies members via `_notify_player_left`.
    *   `get_player_alliances`: Retrieves a list of alliances a player is a member of.
    *   `get_alliance_details`: Fetches detailed information about a specific alliance, including its members and potentially pending invites (if the requester has permission).
    *   `update_alliance`: Allows leaders/officers to change alliance settings (name, description, public status). Notifies members via `_notify_alliance_updated`.
    *   `update_member_role`: Allows leaders to promote/demote other members (e.g., to 'officer' or 'member'). Requires checks to ensure there's always at least one leader. Notifies relevant parties via `_notify_role_changed`.
    *   `calculate_alliance_benefits`: (Partially visible) Seems intended to calculate potential in-game advantages or interactions between allied players (e.g., reduced rent, shared vision, bonuses).
    *   **Internal Notification Helpers (`_notify_*`)**: Private methods using `self.socketio.emit` to send targeted real-time updates to relevant players/rooms about alliance events (creation, invites, joins, leaves, updates, role changes).
*   **Observations/Potential Points:**
    *   Implements a standard guild/alliance system with roles (leader, officer, member) and permissions.
    *   Tightly integrated with the `ChatController` - each alliance automatically gets a dedicated chat channel.
    *   Uses a separate `AllianceInvite` model to manage the invitation process.
    *   Includes important checks like preventing the last leader from abandoning the alliance.
    *   Provides methods to query alliance information.
    *   The `calculate_alliance_benefits` function points towards alliances having tangible effects on gameplay mechanics, beyond just social grouping.
    *   Relies heavily on Socket.IO for real-time notifications to keep players informed about alliance activities.

### src/controllers/social/chat_controller.py Notes

*   **Purpose:** Manages the in-game chat system. This includes creating public, private, or group channels, sending messages within channels, adding/removing emoji reactions to messages, managing channel membership (joining/leaving), and retrieving channel/message history.
*   **Dependencies:** `logging`, `datetime`, `src.models` (`db`, `social.chat` (Channel, ChannelMember, Message, MessageReaction)), `flask_socketio` (`emit`, `join_room`, `leave_room`). Requires a `socketio` instance.
*   **Key Functions:**
    *   `__init__`: Stores `socketio` and defines the list of allowed `EMOJI_REACTIONS`.
    *   `create_channel`: Creates a new `Channel` record with a specified type ('public', 'private', 'group'). Adds the creator and any initially specified members via `ChannelMember` records. Notifies relevant members via `_notify_channel_creation`.
    *   `send_message`: Creates a new `Message` record associated with a channel. Validates content length and checks if the sender is a member (for non-public channels). Broadcasts the message to channel members via `_broadcast_message`.
    *   `add_reaction`: Adds a `MessageReaction` record linking a player, message, and emoji. Validates the emoji is allowed, checks message existence, and verifies channel membership. Prevents duplicate reactions by the same player with the same emoji. Broadcasts the reaction update via `_broadcast_reaction`.
    *   `remove_reaction`: Removes a `MessageReaction` record. Checks message existence and if the player actually made that reaction. Broadcasts the removal via `_broadcast_reaction_removal`.
    *   `join_channel`: Allows a player to join a 'public' or 'group' channel by creating a `ChannelMember` record. Handles adding the player's socket to the corresponding Socket.IO room. Notifies channel members.
    *   `leave_channel`: Allows a player to leave a channel by deleting the `ChannelMember` record. Handles removing the player's socket from the Socket.IO room. Notifies remaining members.
    *   `get_player_channels`: Retrieves a list of channels a player is currently a member of.
    *   `get_channel_history`: Fetches recent messages for a given channel, potentially with pagination (limit, before_message_id). Checks if the requesting player has access to the channel.
    *   **Internal Notification/Broadcast Helpers (`_notify_*`, `_broadcast_*`)**: Private methods using `self.socketio.emit` to send targeted real-time updates to specific players or entire channel rooms about new channels, messages, and reactions. Uses Socket.IO rooms (`f"channel_{channel_id}"`) extensively.
*   **Observations/Potential Points:**
    *   Implements a relatively standard chat system with channel types, membership management, messages, and emoji reactions.
    *   Leverages the underlying `Channel`, `ChannelMember`, `Message`, and `MessageReaction` models for data persistence.
    *   Uses Socket.IO rooms effectively to broadcast messages and updates only to members of the relevant channel.
    *   Includes validation for message length, emoji types, and channel membership permissions.
    *   Handles adding/removing player sockets from Socket.IO rooms when they join/leave channels.

### src/controllers/social/reputation_controller.py Notes

*   **Purpose:** Manages the player reputation system. This involves tracking various reputation scores (overall, trade, agreement, community, financial), recording events that impact reputation, retrieving reputation data and history, calculating a derived credit score, and providing admin functions for adjustments and resets.
*   **Dependencies:** `logging`, `datetime`, `src.models` (`db`, `social.reputation` (ReputationScore, ReputationEvent)). Requires a `socketio` instance.
*   **Key Functions:**
    *   `__init__`: Stores the `socketio` instance.
    *   `get_player_reputation`: Retrieves a player's current reputation scores (overall and categorized). Creates a default `ReputationScore` record if one doesn't exist using `_get_or_create_reputation`.
    *   `record_reputation_event`: Records an event (e.g., completing a trade, breaking an agreement, helping the community) that affects a player's reputation. It calls the `record_event` method on the `ReputationScore` model, which updates the relevant scores based on the `impact` and `category`. Commits the change and notifies the player via `_notify_reputation_change`.
    *   `get_player_reputation_events`: Fetches a paginated history of `ReputationEvent` records for a player, optionally filtered by category.
    *   `get_credit_score`: Calculates a simplified credit score based on a weighted average of the player's financial and overall reputation scores. This is likely used by other systems (e.g., `FinanceController`) for loan eligibility/rates.
    *   `adjust_reputation`: (Admin function) Allows manual adjustment of specific reputation scores. Records an 'admin_adjustment' `ReputationEvent`. Notifies the player via `_notify_admin_adjustment`.
    *   `reset_reputation`: (Admin function) Resets a player's reputation scores back to default values (e.g., 50). Records an 'admin_reset' `ReputationEvent`. Notifies the player via `_notify_reputation_reset`.
    *   `_get_or_create_reputation`: Private helper to retrieve a player's `ReputationScore` or create one with default values if it doesn't exist.
    *   **Internal Notification Helpers (`_notify_*`)**: Private methods using `self.socketio.emit` to send targeted real-time updates to players about changes to their reputation scores or admin actions.
*   **Observations/Potential Points:**
    *   Implements a multi-faceted reputation system, breaking it down into categories (trade, agreement, community, financial) in addition to an overall score.
    *   The core logic for score calculation based on events likely resides within the `ReputationScore.record_event` method in the model.
    *   Provides a mechanism (`get_credit_score`) to translate reputation into a single score usable for financial decisions.
    *   Includes admin controls for moderation and adjustment.
    *   Uses Socket.IO for real-time feedback to players about reputation changes.
    *   Events are stored in the `ReputationEvent` table, providing an auditable history of reputation changes.

### src/controllers/social/socket_handlers.py Notes

*   **Purpose:** This file specifically registers additional Socket.IO event handlers related to the social features (chat, alliances, reputation) that might not fit directly into the main controllers for those features, or which rely on the overarching `SocialController`. It acts as a central registration point for miscellaneous social socket events.
*   **Dependencies:** `logging`, `flask_socketio` (`emit`, `join_room`, `leave_room`), models (`social.chat`, `social.alliance`, `social.reputation`, `Player`), `db`. Requires `socketio` and an instance of `SocialController` passed during registration.
*   **Key Functions (Socket Handlers):**
    *   `register_social_socket_handlers(socketio, social_controller)`: The main function called (likely from `SocketController`) to register the handlers defined within this file.
    *   `handle_channel_typing`: Broadcasts a "user is typing" indicator to members of a specific chat channel when a user starts/stops typing. Verifies channel membership before broadcasting.
    *   `handle_alliance_proposal`: Handles a player submitting a proposal for a new alliance benefit (likely part of a governance system). It delegates the actual processing logic to `social_controller.propose_alliance_benefit`.
    *   `handle_alliance_vote`: Handles a player submitting their vote ('yes', 'no', 'abstain') on an active alliance proposal. Delegates processing to `social_controller.vote_on_proposal`.
    *   `handle_reputation_feedback`: Handles a player submitting reputation feedback (e.g., a star rating) about another player for a specific interaction context. Delegates processing to `social_controller.record_reputation_feedback`.
    *   `handle_join_public_channels`: A utility handler likely called upon player connection/registration. It automatically joins the player's socket to the Socket.IO rooms for all existing public chat channels. Uses `social_controller.join_channel` for database updates.
    *   `handle_search_players`: Provides a simple player search functionality (based on username `ilike`) often used for inviting players to channels or alliances. Allows excluding specific IDs and limiting results.
*   **Observations/Potential Points:**
    *   This file acts as a collector for various social-related socket events, keeping the main `SocketController` cleaner.
    *   It relies heavily on the `SocialController` instance passed in during registration to delegate the actual business logic for proposals, votes, and feedback.
    *   Introduces more advanced social features like typing indicators, alliance governance (proposals/voting), and direct player-to-player reputation feedback.
    *   The `handle_join_public_channels` handler simplifies the process of connecting players to general chat rooms.
    *   Provides a basic player search endpoint needed for social interactions.
    *   Error handling generally involves emitting specific error events back to the calling client.

## Model Notes (`src/models/`)

### src/models/team.py Notes

*   **Purpose:** Defines the database model (`SQLAlchemy`) for a Team in team-based game modes. It stores team attributes, configuration settings related to team mechanics, and relationships to the game, players, and properties. It also includes methods for team-specific calculations and actions.
*   **Dependencies:** `. (`db` from `src.models`), `datetime`.
*   **Key Attributes (Columns):**
    *   `id`, `game_id`, `name`, `color`: Basic team identification.
    *   `score`: Calculated team score.
    *   `is_active`: Flag indicating if the team is still in the game.
    *   `shared_cash`: A pool of cash potentially shared by the team (use case not fully clear from this model alone).
    *   `property_sharing_enabled`, `rent_immunity_enabled`, `income_sharing_percent`: Flags and values controlling team-specific rules defined in the `GameMode`.
    *   `created_at`, `updated_at`: Timestamps.
*   **Relationships:**
    *   `game`: Links back to the `GameState`.
    *   `players`: One-to-many relationship with `Player` models belonging to the team.
    *   `properties`: One-to-many relationship with `Property` models owned by the team (if property sharing is enabled).
*   **Key Methods:**
    *   `to_dict()`: Serializes the team object into a dictionary suitable for API responses, including calculated counts for players and properties.
    *   `calculate_score()`: Calculates the team's score based on shared cash, owned property values, and the cash of its active players. Updates `self.score`.
    *   `process_income_sharing()`: Implements the logic for income sharing. If enabled (`income_sharing_percent > 0`), it takes a percentage of each active player's cash, pools it, and redistributes it equally among them.
    *   `check_team_status()`: Checks if the team has any active players remaining. If not, marks the team as inactive (`is_active = False`).
*   **Observations/Potential Points:**
    *   Standard SQLAlchemy model definition.
    *   Team mechanics (sharing, immunity, income sharing) are configurable via database columns, likely set by the `GameModeController` based on the chosen mode.
    *   The `calculate_score` method provides a team-level equivalent to individual player net worth.
    *   `process_income_sharing` directly modifies the `cash` attribute of associated `Player` objects.
    *   Team elimination (`check_team_status`) is triggered when all players on the team are no longer active (e.g., bankrupt).

### src/models/player.py Notes

*   **Purpose:** Defines the `Player` model, representing both human and bot participants in the game. It stores core player attributes (ID, name, PIN, cash, position, jail status), flags (admin, bot, active), social metrics (community standing, criminal record), and relationships to other models like properties and crimes. It also includes methods for basic player actions.
*   **Dependencies:** `. (`db` from `src.models`), `datetime`, `logging`. Imports `.crime` locally within the `commit_crime` method.
*   **Key Attributes (Columns):**
    *   `id`, `username`, `pin`: Identification and authentication.
    *   `is_admin`, `is_bot`, `in_game`: Boolean flags defining player type and status.
    *   `money` (renamed from `cash` in some other files?), `position`, `turn_order`: Core game state attributes.
    *   `in_jail`, `jail_turns`, `get_out_of_jail_cards`: Jail-related status.
    *   `last_activity`: Timestamp for tracking activity.
    *   `community_standing`, `criminal_record`: Social/reputation metrics.
*   **Relationships:**
    *   `properties`: One-to-many relationship with `Property` model (properties owned by the player).
    *   `crimes`: One-to-many relationship with `Crime` model (crimes committed by the player). Note: Relationship uses `foreign_keys` argument.
    *   `loans`: (Implied relationship, used in `calculate_net_worth` but not explicitly defined here - likely defined in the `Loan` model via `back_populates`).
*   **Key Methods:**
    *   `pay(amount)`, `receive(amount)`: Simple methods to decrease or increase player money, with basic validation.
    *   `move_to(position)`, `move(spaces)`: Methods to update the player's board position, handling wrapping around the board and detecting passing GO.
    *   `go_to_jail()`, `get_out_of_jail()`, `use_jail_card()`: Manage player state related to being in jail.
    *   `to_dict()`: Serializes essential player data for API/frontend use.
    *   `calculate_net_worth()`: Computes the player's net worth by summing money and property values, then subtracting active loan amounts (and adding active CD amounts).
    *   `send_notification(message, socketio=None)`: Attempts to send a targeted Socket.IO notification to the player if a `socket_id` attribute exists, otherwise logs or broadcasts generally.
    *   `is_active` (property): Computed property to check if the player is actively participating (in game and not bankrupt).
    *   `is_bankrupt` (property): Computed property determining bankruptcy based on negative money with no properties, or explicit `in_game=False` status with zero/negative money.
    *   `commit_crime(crime_type, **kwargs)`: Instantiates the correct `Crime` subclass based on `crime_type`, calls its `execute` method, and if the crime is detected, updates the player's `criminal_record` and `community_standing` and calls the crime's `apply_consequences` method.
*   **Observations/Potential Points:**
    *   Central model for player data.
    *   Inconsistency in naming: uses `money` internally but other parts of the code seem to use `cash`. `calculate_net_worth` also uses `money`.
    *   The `commit_crime` method acts as the entry point for a player attempting a crime, delegating the specific logic to the relevant `Crime` subclass. This links the player action directly to the reputation/consequence system.
    *   The `send_notification` method's reliance on a potentially non-existent `socket_id` attribute suggests that socket information might be dynamically added to player instances elsewhere (perhaps in `SocketController` upon connection/registration).
    *   Bankruptcy logic (`is_bankrupt` property) seems reasonable but relies partly on the `in_game` flag, which might be set elsewhere during the bankruptcy process (e.g., in `FinanceController.declare_bankruptcy`).
    *   Local import of `.crime` within `commit_crime` avoids potential circular import issues if `Crime` models also needed to import `Player`.

### src/models/transaction.py Notes

*   **Purpose:** Defines the `Transaction` model, used to log all financial movements (money transfers) within the game. This provides an audit trail for payments, income, loans, etc.
*   **Dependencies:** `. (`db` from `src.models`), `datetime`. Imports `.game_state` locally within the `create` method.
*   **Key Model (`Transaction`):
    *   **Attributes:** `id`, `from_player_id` (nullable), `to_player_id` (nullable), `amount` (always positive), `transaction_type`, `property_id` (nullable), `loan_id` (nullable), `description` (nullable), `timestamp`, `lap_number` (nullable).
    *   **Relationships:** `from_player`, `to_player` (links to `Player`, uses `foreign_keys`), `property`, `loan`.
    *   **Methods:**
        *   `to_dict()`: Serializes the transaction object for API responses.
        *   `create(...)` (classmethod): A factory method to simplify creating and saving new transaction records. It can infer the `from_player_id` and `to_player_id` based on the sign of the `amount` if only a single `player_id` is provided. It also attempts to automatically fetch the current `lap_number` from the `GameState` singleton and stores the `amount` as a positive value.
*   **Core Functionality:** Provides a database schema and a convenient factory method (`create`) for logging all financial activities, linking them to players, properties, or loans where applicable, and recording the game lap.
*   **Observations/Potential Points:**
    *   Provides a crucial logging mechanism for all financial activity.
    *   Uses nullable foreign keys for `from_player_id` and `to_player_id` to represent interactions with the bank/system. Null indicates the bank.
    *   The `create` classmethod is well-designed, handling direction inference based on amount sign and automatic lap number retrieval (with fallback).
    *   The local import of `GameState` within `create` avoids potential circular dependencies.
    *   Capturing the `lap_number` is useful for analysing game progression and financial activity over time.

### src/models/trade.py Notes

*   **Purpose:** Defines the database models (`Trade` and `TradeItem`) for representing player-to-player trade offers and their contents.
*   **Key Models:**
    *   `Trade(db.Model)`: Represents the overall trade proposal. Stores proposer/receiver IDs, cash offered by each, the trade status ('pending', 'completed', 'rejected', etc.), and potentially other items (like jail cards) in a JSON `details` field. It has relationships to the `Player` models and a one-to-many relationship to `TradeItem` for the properties involved.
    *   `TradeItem(db.Model)`: Represents a single property included in a trade. It links back to the parent `Trade`, the specific `Property` being traded, and includes a boolean `is_from_proposer` to indicate which side is offering the property.
*   **Dependencies:** `. (`db` from `src.models`), `datetime`, `json` (used in `Trade.to_dict`). Relationships link to `Player` and `Property`.
*   **Core Functionality:** Provides the data structure to represent complex trades involving cash, multiple properties from both sides, and potentially other items like "Get Out of Jail Free" cards. Includes a `to_dict` method for serialization which correctly parses the items and details. Uses `cascade='all, delete-orphan'` on the `items` relationship, ensuring items are deleted when a trade is deleted.
*   **Observations:**
    *   Uses a standard two-table approach (`trades`, `trade_items`) for a many-to-many relationship (properties in a trade).
    *   Allows for asymmetrical trades (properties for cash, multiple properties for one).
    *   The `status` field tracks the lifecycle of the trade offer.
    *   The JSON `details` field in `Trade` provides flexibility for including non-standard items (like jail cards) without altering the database schema.
    *   The actual execution logic (validating the trade, transferring ownership/cash upon acceptance) is not part of this model; it resides elsewhere (e.g., `BotEventController` for bot-initiated trades, potentially `GameController` or a dedicated `TradeController` for player-initiated ones).

### src/models/game_history.py Notes

*   **Purpose:** Defines the `GameHistory` model, used to store summary statistics and results of completed games for historical record-keeping and potential leaderboards.
*   **Key Model:**
    *   `GameHistory(db.Model)`: Stores details about a finished game, including:
        *   Basic info: `winner_id`, `end_reason` (e.g., 'normal', 'time_limit'), `duration_minutes`, `total_laps`, `player_count`, `bot_count`.
        *   Game state snapshot: `final_inflation_state`.
        *   Detailed Statistics: `player_stats`, `property_stats`, `economic_stats` stored as JSON strings in `Text` columns. These likely contain final player net worths, property ownership details, economic phase history, etc.
        *   Timestamp: `created_at`.
*   **Dependencies:** `. (`db` from `src.models`), `datetime`, `json` (in `to_dict`). Relationship links to `Player` (for the winner).
*   **Core Functionality:** Provides a database schema to persist detailed results from past games. Includes a `to_dict` method that serializes the record and importantly parses the JSON statistics columns back into Python objects (likely dictionaries/lists) for easier consumption by APIs or frontends.
*   **Observations:**
    *   Serves as an archive for completed game data.
    *   Uses `Text` columns with JSON strings to store complex statistical data (`player_stats`, `property_stats`, `economic_stats`). This is flexible but makes direct SQL querying based on the contents of these stats difficult. The application layer is responsible for parsing and interpreting this data.
    *   The logic for *collecting* these stats during the game and calculating metrics like `duration_minutes` resides elsewhere (most likely in `GameController` when `end_game` is called). This model is purely for storage.

### src/models/game_mode.py Notes

*   **Purpose:** Defines the `GameMode` model, storing the configuration settings for different ways to play the game. It centralizes rule variations for aspects like starting cash, win conditions, time limits, team mechanics, and economic factors.
*   **Dependencies:** `. (`db` from `src.models`), `datetime`, `json`.
*   **Key Attributes (Columns):**
    *   `id`, `game_id`, `mode_type`, `name`: Basic identification.
    *   **Common Settings:** `starting_cash`, `go_salary`, `free_parking_collects_fees`, `auction_enabled`, `max_turns`, `max_time_minutes`, `bankruptcy_threshold`, `event_frequency`, `disaster_impact`, `inflation_factor`, `development_levels_enabled`, `turn_timer_seconds`. These provide a wide range of configurable parameters affecting core gameplay.
    *   `_custom_settings`: A `Text` column storing a JSON string for additional, mode-specific parameters not covered by standard columns (e.g., development milestones in Tycoon mode).
    *   **Team Settings:** `team_based`, `team_trading_enabled`, `team_property_sharing`, `team_rent_immunity`, `team_income_sharing`. Boolean flags and a float value to configure team play rules.
    *   `win_condition`: A string specifying how the game is won in this mode (e.g., 'last_standing', 'net_worth').
    *   `created_at`, `updated_at`: Timestamps.
*   **Relationships:**
    *   `game`: One-to-one relationship back to the `GameState`.
*   **Key Methods:**
    *   `custom_settings` (property): Getter/setter pair that automatically handles JSON serialization/deserialization for the `_custom_settings` column, allowing access via a Python dictionary.
    *   `to_dict()`: Serializes the game mode settings into a dictionary, including team settings (if applicable) and the parsed `custom_settings`.
    *   `create_for_game(cls, game_id, mode_type, settings=None)` (classmethod): A factory method responsible for creating a `GameMode` instance with appropriate default settings based on the requested `mode_type`. It calls internal static methods (`_configure_*`) to apply presets and then overrides with any specific `settings` provided.
    *   `get_mode_name(mode_type)` (staticmethod): Returns a user-friendly display name for a given `mode_type`.
    *   `_configure_*` (staticmethods): Private static methods (e.g., `_configure_classic_mode`, `_configure_speed_mode`) that apply the default preset values for each standard game mode to a `GameMode` instance passed to them.
*   **Observations/Potential Points:**
    *   Provides a powerful and flexible way to define diverse gameplay experiences through configuration.
    *   Uses a combination of dedicated columns for common settings and a JSON field (`_custom_settings`) for extensibility. The property getter/setter simplifies working with the JSON data.
    *   The factory pattern (`create_for_game`) combined with static configuration methods (`_configure_*`) makes creating new games with standard modes straightforward.
    *   This model acts as the central source of truth for game rules that vary between modes. Other controllers/models (like `GameController`, `TeamController`, `Property`) likely query this model to determine how to behave.

### src/models/game_state.py Notes

*   **Purpose:** Defines the `GameState` model, acting as a singleton (enforced by `get_instance` and likely the `id=1` default) to hold the central, global state of the currently active game. This includes turn progression, economic conditions, timers, core rule settings, and temporary effects.
*   **Dependencies:** `. (`db` from `src.models`), `datetime`, `json`. Imports `.bot_events`, `.economic_phase_change`, `src.controllers.crime_controller`, `src.models.Property`, `logging`, `random` locally within methods.
*   **Key Attributes (Columns):**
    *   `id`: Primary key, defaulted to 1 to enforce singleton behavior via `get_instance`.
    *   `current_player_id`: Foreign key to the `Player` whose turn it is.
    *   `current_lap`, `total_laps`, `turn_number`: Track game progression.
    *   `community_fund`: Current amount in the community fund/free parking pool.
    *   `inflation_state`, `inflation_factor`, `tax_rate`, `police_activity`: Variables representing the dynamic economic and security state of the game.
    *   `start_time`, `end_time`, `turn_timer`: Time-related settings and state.
    *   `is_active`: Boolean indicating if a game is currently running.
    *   `difficulty`, `mode`: Game difficulty and mode type.
    *   `game_id`: Unique UUID for identifying the game instance (e.g., for Socket.IO rooms).
    *   `_temporary_effects`: JSON string storing a list of temporary effects (e.g., rent modifiers, market recovery timers).
    *   `last_event_lap`: Tracks the lap when the last major random event occurred.
    *   `_settings`: JSON string storing game-specific settings (potentially loaded from `GameMode` initially).
    *   **Configurable Rules:** `auction_required`, `property_multiplier`, `rent_multiplier`, `improvement_cost_factor`, `event_frequency`. These store core rule parameters potentially loaded from `GameMode`.
*   **Relationships:**
    *   `current_player`: Links to the `Player` model for the active player.
*   **Key Methods:**
    *   `temporary_effects`, `settings` (properties): Getters/setters for handling JSON serialization/deserialization of the `_temporary_effects` and `_settings` columns.
    *   `to_dict()`: Serializes the game state for API/frontend use, including calculated duration and parsed effects/settings.
    *   `calculate_duration_minutes()`: Computes elapsed game time.
    *   `get_instance(cls)` (classmethod): Provides singleton access, retrieving the first (and presumably only) `GameState` record or creating it if it doesn't exist.
    *   `add_temporary_effect(effect)`: Adds a new temporary effect dictionary to the list.
    *   `process_turn_end()`: Processes end-of-turn logic. Decrements `remaining_turns` on temporary effects, triggers expiration logic for effects ending (like restoring market prices or repairing damage by calling out to other modules/controllers), increments `turn_number`, and checks for turn limits.
    *   `advance_lap()`: Increments `current_lap`, calls `process_economic_cycle` and `process_game_mode_lap_effects`.
    *   `process_economic_cycle()`: Periodically (every 4 laps) triggers potential economic phase changes via `EconomicPhaseChange.generate_phase_change` and randomly updates `police_activity`.
    *   `_update_police_activity()`: Randomly adjusts the police activity level.
    *   `process_game_mode_lap_effects()`: Applies lap-based effects specific to the current game mode (e.g., reducing GO salary in Co-op, applying property volatility in Market Crash).
*   **Observations/Potential Points:**
    *   Crucial singleton model holding the live state of the game.
    *   Manages turn/lap progression and triggers associated events (economic changes, temporary effect processing, game mode effects).
    *   Uses JSON columns (`_temporary_effects`, `_settings`) with properties for easier access, allowing flexible storage of complex data.
    *   The `process_turn_end` method is complex, handling the lifecycle of temporary effects and calling out to other modules/controllers (like `bot_events`, `CrimeController`) for effect resolution, highlighting potential coupling. Local imports are used to manage circular dependencies.
    *   Economic simulation (`process_economic_cycle`) and game mode specific effects (`process_game_mode_lap_effects`) add significant dynamic elements to the game state.
    *   The singleton pattern relies on convention (always using `get_instance`) and the `id=1` default.

### src/models/community_fund.py Notes

*   **Purpose:** Defines a `CommunityFund` class (not a direct SQLAlchemy model) responsible for managing the central pool of money often associated with taxes, fines, or the Free Parking space in Monopoly variants.
*   **Dependencies:** `datetime`, `logging`, `typing`, `src.models` (`db`, `GameState`).
*   **Key Components:**
    *   `__init__(socketio=None, game_state=None)`: Initializes the fund. It takes optional `socketio` and `game_state` instances. If `game_state` isn't provided, it queries the database for the singleton instance. It reads the initial fund amount from the `game_state.settings["community_fund"]` dictionary.
    *   `funds` (property): Read-only property to access the current fund amount (`self._funds`).
    *   `add_funds(amount, reason)`: Increases the fund amount, updates the value stored in `game_state.settings`, commits the change to the database, logs the action, and emits a Socket.IO event if available.
    *   `withdraw_funds(amount, reason)`: Decreases the fund amount after checking for sufficient balance. Updates `game_state.settings`, commits, logs, and emits an event. Returns a dictionary indicating success/failure and the new balance.
    *   `clear_funds(reason)`: Resets the fund amount to zero, updates `game_state.settings`, commits, logs, emits an event, and returns the amount that was cleared.
    *   `get_info()`: Returns a simple dictionary containing the current balance and timestamp.
*   **Observations/Potential Points:**
    *   This is a service class rather than a pure data model. It encapsulates the logic for managing the community fund.
    *   It interacts directly with the `GameState` model to persist the fund balance within the `GameState.settings` JSON field. This tightly couples it to `GameState` but avoids needing a separate database table just for the fund amount.
    *   Relies on an injected `socketio` instance for real-time updates to clients.
    *   Provides clear methods for adding, withdrawing, and clearing funds, along with logging and event emission.
    *   The persistence mechanism (storing the value inside `GameState.settings`) might be less efficient for very frequent updates compared to a dedicated column, but is likely acceptable for this purpose.

### src/models/banker.py Notes

*   **Purpose:** Defines a `Banker` class (not a direct SQLAlchemy model) that centralizes logic for financial transactions involving the 'bank'. This includes handling property purchases/sales between players and the bank, issuing loans, accepting deposits (CDs), and paying salaries.
*   **Dependencies:** `. (`db` from `src.models`), `datetime`, `logging`. Imports `.transaction`, `.loan`, `.player`, `.property`, `.game_state` locally within methods.
*   **Key Components/Methods:**
    *   `__init__(socketio)`: Initializes the banker with a `socketio` instance for notifications and a logger.
    *   `process_property_purchase(player, property, game_state)`: Handles a player buying an unowned property from the bank. Checks ownership, player cash, updates player money (`player.pay`), updates property ownership, creates a `Transaction` record, and notifies/broadcasts via Socket.IO.
    *   `process_property_sale_to_bank(player, property, game_state)`: Handles a player selling a property back to the bank. Checks ownership, calculates the sale price (e.g., 85% of current value), updates player money (`player.receive`), updates property ownership (to None/bank), creates a `Transaction`, and notifies/broadcasts.
    *   `provide_loan(player, amount, interest_rate, term_laps, game_state)`: Issues a standard loan to a player. Performs basic credit checks (based on net worth), validates against max loan amount, creates a `Loan` record, updates player money (`player.receive`), creates a `Transaction`, and notifies.
    *   `accept_deposit(player, amount, interest_rate, term_laps, game_state)`: Handles a player creating a Certificate of Deposit (CD). Checks player cash, updates player money (`player.pay`), creates a `Loan` record (marked as `is_cd=True`), creates a `Transaction`, and notifies.
    *   `pay_salary(player, base_amount, game_state)`: Pays the GO salary to a player. Applies economic modifiers (like `inflation_factor` from `GameState`) to the `base_amount`, updates player money (`player.receive`), creates a `Transaction`, and notifies.
*   **Core Functionality:** Encapsulates the mechanics of common financial interactions between players and the bank entity. It handles the necessary checks, updates player and property states, records transactions, and communicates changes.
*   **Observations/Potential Points:**
    *   Acts as a service class for bank-related financial operations.
    *   Interacts with multiple models (`Player`, `Property`, `Loan`, `Transaction`, `GameState`). Local imports are used extensively to avoid circular dependencies.
    *   Includes basic loan eligibility checks based on player net worth.
    *   Applies game state factors (like inflation) to bank operations (e.g., salary payments).
    *   Relies on the injected `socketio` instance for notifications and broadcasting state changes.
    *   Uses the `Transaction.create` factory method for logging.
    *   There's potential overlap in functionality with methods in `FinanceController` (loans/CDs) and `PropertyController`/`GameController` (property actions). The responsibility division seems to be that `Banker` handles the direct interaction *with the bank*, while other controllers handle the *player-initiated request* or more complex financial product management. Clarifying this distinction might be beneficial. For example, `FinanceController.create_loan` likely calls `Banker.provide_loan` after performing more detailed eligibility checks.

### src/models/loan.py Notes

*   **Purpose:** Defines the `Loan` model, representing various financial instruments like standard player loans, Certificates of Deposit (CDs), and potentially Home Equity Lines of Credit (HELOCs - implied by `property_id`).
*   **Dependencies:** `. (`db` from `src.models`), `datetime`, `logging`. Imports `.game_state` locally within methods.
*   **Key Model (`Loan`):
    *   **Attributes:** `id`, `player_id`, `amount`, `interest_rate`, `original_interest_rate`, `start_lap`, `length_laps`, `is_cd` (boolean flag), `property_id` (nullable foreign key for collateral), `is_active` (boolean flag), `created_at`.
    *   **Relationships:** `property` (links to `Property` model, lazy-loaded).
    *   **Methods:**
        *   `to_dict()`: Serializes the loan/CD object, including calculated `remaining_laps` and `current_value`.
        *   `calculate_remaining_laps(current_lap=None)`: Calculates how many laps are left until the loan/CD term ends. Fetches `current_lap` from `GameState` if not provided.
        *   `calculate_current_value(current_lap=None)`: Calculates the current value (for CDs) or amount owed (for loans) based on a simple compound interest formula using `laps_passed`. Fetches `current_lap` from `GameState`.
        *   `adjust_interest_rate(change_amount)`: Modifies the `interest_rate` (min 1%), storing the original rate. Logs the change.
        *   `mark_paid()`: Sets `is_active` to `False`.
        *   `is_paid_off` (property): Read-only property checking the `is_active` status.
        *   `create_loan(...)` (classmethod): Factory method to create and save a new `Loan` or `CD` instance.
*   **Core Functionality:** Provides the data structure for tracking loans and CDs. It stores their state, calculates remaining terms and current values using simple compound interest based on game laps, allows for dynamic interest rate adjustments, and manages the active/paid status.
*   **Observations/Potential Points:**
    *   Uses a single model to represent multiple financial instrument types (Loans, CDs, HELOCs) differentiated by flags (`is_cd`) and optional fields (`property_id`).
    *   Interest calculation (`calculate_current_value`) uses a simple lap-based compound interest model.
    *   Includes functionality to adjust interest rates dynamically, possibly linked to economic events.
    *   Relies on fetching the `current_lap` from `GameState` for calculations, using local imports to avoid circular dependency.
    *   The repayment logic seen in `FinanceController` is *not* present here; this model primarily stores the state and performs calculations. Repayment actions modify the `Loan` state (e.g., via `mark_paid`) but are orchestrated elsewhere.

### src/models/property.py Notes

*   **Purpose:** Defines the `Property` model, representing ownable spaces on the board (streets, railroads, utilities). This is a very detailed model containing core attributes (price, rent, group), ownership status, mortgage status, development levels, damage/liens, and logic for calculating rent, development costs, handling improvements, and responding to market events.
*   **Dependencies:** `. (`db` from `src.models`), `datetime`, `random`. Imports `GameState` locally sometimes.
*   **Key Attributes (Columns):**
    *   Basic: `id`, `name`, `position`, `group_name`, `price`, `rent`, `improvement_cost`, `mortgage_value`.
    *   Dynamic State: `current_price`, `current_rent`, `current_improvement_cost`, `improvement_level`, `is_mortgaged`, `owner_id`.
    *   Advanced Mechanics: `has_lien`, `lien_amount`, `damage_amount`, `is_water_adjacent`.
    *   Enhanced Development: `max_development_level`, `has_community_approval`, `has_environmental_study`, `environmental_study_expires`.
    *   Market Events: `discount_percentage`, `discount_amount`, `premium_percentage`, `premium_amount`.
    *   `rent_levels`: JSON field likely storing rent values for different improvement levels or scenarios (though `calculate_rent` seems to use multipliers primarily).
*   **Relationships:**
    *   `owner`: Links to the `Player` model.
    *   `loans`: (Implied via `backref`) Links to `Loan` model if property is used as collateral (HELOC).
    *   `transactions`: (Implied via `backref`) Links to related `Transaction` records.
*   **Constants:** Defines class-level dictionaries for configuration:
    *   `DEVELOPMENT_LEVELS`: Defines names, rent/value multipliers, max damage, and repair cost factors for each improvement level.
    *   `ZONING_REGULATIONS`: Defines max levels, approval/study requirements, and cost modifiers based on property `group_name`.
    *   `DEVELOPMENT_COSTS`: Base cost percentages for each improvement level.
    *   `ECONOMIC_MULTIPLIERS`: Modifiers for development costs based on `GameState.inflation_state`.
*   **Key Methods:**
    *   `__init__`: Initializes basic attributes and sets `max_development_level` based on `ZONING_REGULATIONS`.
    *   `to_dict()`: Serializes the property state for API/frontend use, including calculated fields like development level name.
    *   `calculate_rent(game_state=None)`: Complex method calculating current rent. Considers base rent, development level multiplier, group monopoly bonus (only if undeveloped), damage reduction, liens, game state inflation, and temporary rent modifiers from `GameState`.
    *   `update_value(new_value)`, `update_rent(new_rent)`: Methods to directly set current price/rent, likely used by market events.
    *   `apply_damage(damage_amount)`, `repair_damage(repair_amount=None)`, `calculate_repair_cost()`: Manage property damage, calculating costs based on `DEVELOPMENT_LEVELS` constants.
    *   `apply_market_crash(percentage)`, `apply_economic_boom(percentage)`, `restore_market_prices()`: Apply/remove price/rent discounts or premiums based on market events.
    *   `mortgage()`, `unmortgage()`: Set/unset the `is_mortgaged` flag. (Actual cash transfer handled elsewhere, e.g., `PropertyController` or `Banker`).
    *   `can_improve(game_state=None)`: Checks if the property can be improved based on current level, max level (zoning), owner having a monopoly, mortgage status, damage, liens, and required approvals/studies.
    *   `improve(game_state=None)`: Increments `improvement_level` if `can_improve` passes. Updates `current_price` and `current_rent` based on `DEVELOPMENT_LEVELS` multipliers and `GameState` inflation.
    *   `calculate_improvement_cost(game_state=None)`: Calculates the cost for the *next* improvement level based on base cost (`DEVELOPMENT_COSTS`), zoning modifier (`ZONING_REGULATIONS`), economic multiplier (`ECONOMIC_MULTIPLIERS`, based on `GameState`), and inflation (`GameState`).
    *   `remove_improvement()`: Decrements `improvement_level`, recalculates value/rent. (Refund logic handled elsewhere).
    *   `request_community_approval(game_state=None)`, `commission_environmental_study(game_state=None)`: Set flags (`has_community_approval`, `has_environmental_study`) indicating these prerequisites are met, potentially with expiration for the study. (Triggering/cost handled elsewhere).
    *   `check_development_requirements(target_level)`: Helper to check approval/study status for a specific target level based on `ZONING_REGULATIONS`.
*   **Observations/Potential Points:**
    *   Very comprehensive model encapsulating most property-related state and logic.
    *   Extends standard Monopoly with concepts like zoning, development prerequisites (approval, studies), damage, liens, and dynamic market effects.
    *   Uses class-level dictionaries extensively for configuration, making rules relatively easy to modify in one place.
    *   Rent and improvement cost calculations are complex, involving multiple factors from the property itself, zoning, game state (economy, inflation), and temporary effects.
    *   Separation of concerns: While this model calculates *costs* and checks *conditions*, the actual *transactions* (paying for improvements, receiving rent) are handled by controllers or service classes like `Banker`.
    *   The number of boolean flags and specific state fields (`has_lien`, `damage_amount`, `has_community_approval`, etc.) indicates a high degree of gameplay complexity.

### src/models/auction_system.py Notes

*   **Purpose:** Defines an `AuctionSystem` class (not a direct SQLAlchemy model) responsible for managing the entire lifecycle of property auctions. This includes starting standard or foreclosure auctions, handling bids and passes, managing timers, determining winners, and processing the final sale.
*   **Dependencies:** `datetime`, `threading`, `uuid`, `logging`, `flask_socketio` (`emit`), `. (`db`), `.property.Property`, `.player.Player`, `.transaction.Transaction`, `.community_fund.CommunityFund`. Requires `socketio` and `banker` instances injected during initialization.
*   **Key Components/Methods:**
    *   `__init__(socketio, banker)`: Initializes the system, storing injected dependencies. Uses `active_auctions` (a dictionary) to store the state of ongoing auctions *in memory*.
    *   `start_auction(property_id)`: Initiates a standard auction for an unowned property. Validates, generates an ID, sets up initial state (minimum bid, eligible players, timer), stores in `active_auctions`, notifies players via Socket.IO, and starts the timer (`_start_auction_timer`).
    *   `start_foreclosure_auction(property_id, owner_id, minimum_bid=None)`: Initiates a foreclosure auction. Similar to `start_auction` but excludes the owner from bidding and may have different defaults.
    *   `_start_auction_timer(auction_id)`: Creates a `threading.Timer` that calls `auction_tick` every second.
    *   `auction_tick()` (nested function): Decrements the timer, broadcasts updates periodically, and calls `_end_auction` when the timer hits zero. Reschedules itself using `threading.Timer`.
    *   `place_bid(auction_id, player_id, bid_amount)`: Processes a player's bid. Validates auction status, player eligibility/cash, and bid amount. Updates auction state (`current_bid`, `current_bidder`), records the bid, resets the timer (to 10 seconds), and broadcasts the update.
    *   `pass_auction(auction_id, player_id)`: Handles a player passing. Validates, adds player to `players_passed`, checks if auction should end early (if only one bidder left), and broadcasts the pass.
    *   `_end_auction(auction_id)`: Determines the winner or handles no-bid scenarios. If a winner exists, it processes the sale using the injected `banker` (or direct model manipulation - the snippet shows direct `Player.pay` and `Property.owner_id` updates), creates a `Transaction`, broadcasts the result, and cleans up the auction from `active_auctions` after a delay. Logic for no-bids or foreclosure proceeds distribution isn't fully visible but implied.
    *   `cancel_auction(auction_id, admin_id)`: Allows manual cancellation by an admin.
    *   `get_active_auctions()`, `get_auction(auction_id)`: Retrieve auction information.
*   **Core Functionality:** Provides a complete, real-time auction management system. It handles different auction types, manages bidding, enforces rules (eligibility, minimum bids), uses timers for pacing, determines outcomes, and integrates with other game systems (players, properties, transactions) to finalize sales.
*   **Observations/Potential Points:**
    *   This is a stateful service class managing auctions entirely in memory (`active_auctions` dictionary). Auction state is not persisted in the database beyond the final property ownership change and transaction record. This means auctions **will not survive server restarts**.
    *   Uses `threading.Timer` for auction countdowns, running callbacks in separate threads. This requires careful handling of shared state, although modifications seem largely contained within the specific auction's dictionary entry.
    *   Handles both standard and foreclosure auctions.
    *   Includes a timer reset mechanism after bids (common in online auctions).
    *   Relies heavily on Socket.IO for broadcasting all stages of the auction process.
    *   Interaction with the `banker` instance passed during init seems intended for processing the final sale, though the visible snippet shows direct model updates. Consistency should be checked.

### src/models/event_system.py Notes

*   **Purpose:** Defines an `EventSystem` class (not a direct SQLAlchemy model) responsible for managing random game events like economic shifts, disasters, and community occurrences. It defines potential events, checks if one should trigger, and applies the event's effects to the game state.
*   **Dependencies:** `datetime`, `random`, `logging`. Needs `socketio`, `banker`, and `community_fund` instances injected. Interacts with `GameState`, `Player`, `Property`, `Loan` models indirectly via method calls or by modifying `GameState`.
*   **Key Components/Methods:**
    *   `__init__(socketio, banker, community_fund)`: Initializes the system, storing injected dependencies. Calls `_define_events` to load the event definitions. Sets cooldown and probability parameters.
    *   `_define_events()`: Returns a dictionary defining various possible events. Each event has a title, description, type, severity, action key, and specific parameters (e.g., `value_modifier`, `damage_percent`, `duration`). Events cover economic changes (boom/crash, interest rates), disasters (hurricane, earthquake, flood), and community occurrences (festival, infrastructure, tax reform).
    *   `check_for_event(game_state)`: Determines if a random event should occur based on the current lap, cooldown (`last_event_lap`), and probability (`event_probability`). If an event triggers, it selects one randomly from the defined events and returns its details.
    *   `apply_event(game_state, event_id)`: Takes a triggered event ID, looks up the event definition, and calls the appropriate internal handler (`_apply_*`) based on the event's `action` key. Broadcasts the triggered event to all players via Socket.IO.
    *   **Internal Event Handlers (`_apply_*`)**: Private methods containing the logic to implement the effects of specific event actions:
        *   `_apply_property_value_change`: Modifies `current_price` and `current_rent` on properties (using `prop.update_value`, `prop.update_rent`).
        *   `_apply_interest_rate_change`: Adjusts the `interest_rate` on active loans using `loan.adjust_interest_rate()`.
        *   `_apply_property_damage`: Applies damage to properties using `prop.apply_damage()`, potentially targeting specific areas ('all', 'random_50_percent', 'water_adjacent'). Notifies affected owners.
        *   `_apply_temporary_rent_boost`: Adds a temporary effect to `GameState` using `game_state.add_temporary_effect()` to modify rent for a set duration.
        *   `_apply_infrastructure_upgrade`: Increases property values and applies a one-time tax to all players, contributing it to the `community_fund`.
        *   `_apply_tax_collection`: Collects a percentage of each player's cash and adds it to the `community_fund`.
*   **Core Functionality:** Provides a mechanism for introducing random, game-wide events that impact economy, property states, and player finances. It manages event triggering based on probability and cooldown, and applies defined effects through interaction with other models and services.
*   **Observations/Potential Points:**
    *   This is a service class managing random events. Event definitions are hardcoded within the `_define_events` method, making them relatively easy to modify but not dynamically loaded.
    *   The triggering mechanism (`check_for_event`) is based on probability per lap cycle, with a cooldown period.
    *   Applies effects by directly calling methods on other models (`Property`, `Loan`) or modifying `GameState` (adding temporary effects).
    *   Uses the `CommunityFund` and `Banker` instances (passed during init) for financial transactions related to events.
    *   Broadcasts triggered events to all players using Socket.IO.
    *   Adds significant dynamism and unpredictability to the game.

### src/models/crime.py Notes

*   **Purpose:** Defines the base `Crime` model and several subclasses representing specific criminal activities (Theft, Vandalism, Rent Evasion, Forgery, Tax Evasion). It uses SQLAlchemy's single-table inheritance pattern (`polymorphic_on='crime_type'`) to store different crime types in the same table. Each subclass implements the specific logic for executing that crime and potentially custom consequences.
*   **Key Models/Classes:**
    *   `Crime(db.Model)`: Base class using SQLAlchemy's single-table inheritance (`polymorphic_on='crime_type'`).
        *   **Attributes:** Stores `player_id` (committer), `crime_type` (discriminator), target IDs (`target_player_id`, `target_property_id`), `amount` involved, boolean flags (`success`, `detected`, `punishment_served`), `timestamp`, and `details` (text log).
        *   **Methods:**
            *   `execute()`: Abstract base method; subclasses implement the specific crime logic.
            *   `detect(game_state)`: Calculates detection probability based on `game_state.difficulty` and `player.community_standing`. Uses `random.random()` to set the `detected` flag.
            *   `apply_consequences()`: Base implementation applies penalties if `detected`: reduces `player.community_standing` and calls `player.go_to_jail()`. Sets `punishment_served`.
            *   `to_dict()`: Serializes the crime record.
    *   `Theft(Crime)`: Subclass for stealing money.
        *   **`execute()`:** Finds the target player, calculates steal amount (percentage of cash, capped), checks if target has money, calls `detect()`. If successful and undetected, transfers money (`target_player.pay()`, `self.player.receive()`) and creates a `Transaction` record. Updates `details`.
    *   `PropertyVandalism(Crime)`: Subclass for damaging property.
        *   **`execute()**:** Finds target property, validates ownership (not self, not unowned), calculates damage amount (percentage of value). Calls `detect()`. If successful and undetected, increases `property.damage_amount`, temporarily reduces `property.current_price`, and adds a temporary effect to `GameState` to eventually restore the value (using `game_state.add_temporary_effect()`). Updates `details`.
    *   Other subclasses (like `RentEvasion`, `Forgery`, `TaxEvasion`) are implied by the file length and likely follow a similar pattern of overriding `execute()` with specific logic and potentially `apply_consequences()` for custom penalties.
*   **Dependencies:** `db`, `datetime`, `random`, `logging`, `Player`, `GameState`, `Property`, `Transaction`.
*   **Core Functionality:** Provides a framework for implementing various crimes. It defines the data structure for crime records, a dynamic detection mechanism, standard consequences (jail, reputation loss), and allows subclasses to define unique execution logic and effects (financial transfer, property damage, temporary state changes).
*   **Observations:**
    *   Effective use of single-table inheritance to manage different crime types within one database table.
    *   Detection logic is well-defined, incorporating game difficulty and player reputation.
    *   Separates the *attempt* (`execute()`) from *detection* (`detect()`) and *punishment* (`apply_consequences()`).
    *   Some crimes (like `PropertyVandalism`) interact with the `GameState`'s temporary effects system to handle delayed consequences or repairs.
    *   Database commits (`db.session.commit()`) happen multiple times within some `execute` methods (e.g., after setting initial details, after detection, after successful execution). Consolidating these into fewer commits might be slightly more efficient, though functionally correct as is.
    *   The logic resides primarily within the models themselves (Active Record pattern).

### src/models/jail_card.py Notes

*   **Purpose:** Defines the `JailCard` model, representing individual "Get Out of Jail Free" cards that players can acquire and use.
*   **Key Model:**
    *   `JailCard(db.Model)`: Stores attributes like `id`, `player_id` (nullable, indicating current owner), `card_type` ('chance' or 'community_chest'), a `used` boolean flag, and timestamps (`acquired_at`, `used_at`).
*   **Dependencies:** `. (`db` from `src.models`), `datetime`. Implicit relationship to `Player` via `player_id`.
*   **Core Functionality:** Tracks the state (ownership, usage) of individual Get Out of Jail Free cards. Provides a `use_card()` method to mark the card as used and record the time. Includes `to_dict()` for serialization.
*   **Observations:**
    *   A straightforward model focused specifically on the state of these cards.
    *   The `player_id` being nullable suggests that these card records might persist in the database even when not held by a player, potentially representing the cards available within the Chance/Community Chest decks. How the link is made when a player draws one isn't shown here but likely handled in `SpecialSpaceController` or `CardDeck`.
    *   The actual game mechanic of using the card (getting the player out of jail) is handled elsewhere (e.g., `Player.use_jail_card()`), triggered by the player action. This model just tracks the card's status.

### `src/models/special_space.py`

*   **Purpose:** This module defines the database models and operational logic for all non-property spaces on the game board. It handles Chance and Community Chest cards, fixed special spaces like Go, Jail, Tax squares, and the interactions players have when landing on or drawing cards related to these spaces.
*   **Key Models/Classes:**
    *   `Card(db.Model)`: Represents individual Chance/Community Chest cards, storing their text, type, and detailed action instructions (e.g., move, pay, collect, go to jail) using `action_type` and JSON `action_data`.
    *   `SpecialSpace(db.Model)`: Represents fixed board locations like 'Go', 'Jail', 'Income Tax', etc., identified by `position` and `space_type`. Can store specific rules or amounts in `action_data`.
    *   `CardDeck`: Manages the drawing, shuffling, discarding, and execution of actions for either the Chance or Community Chest deck. It contains numerous private helper methods (`_handle_move_action`, `_handle_pay_action`, etc.) to implement the diverse card effects, interacting with `Player`, `GameState`, `Banker`, and `CommunityFund`.
    *   `TaxSpace`: Encapsulates the logic for processing payments when a player lands on a tax space. It calculates the tax amount based on rules defined in the `SpecialSpace` (fixed amount or percentage of assets) and uses the `Banker` to handle the transaction.
*   **Dependencies:** Relies heavily on other models (`db`, `GameState`, `Property`, `Player`, `CommunityFund`) and services (`Banker` - passed in, `socketio` - passed in). Uses standard libraries like `datetime`, `random`, `json`.
*   **Core Functionality:** Provides the mechanics for card drawing, shuffling, action execution (player movement, financial transactions, jailing, property repairs, etc.), and tax collection.
*   **Observations:**
    *   Centralizes complex event logic triggered by cards and special spaces.
    *   Uses flexible JSON `action_data` for defining card and space behavior.
    *   The `CardDeck` and `TaxSpace` classes act as service-like components managing interactions, requiring dependencies like `Banker` to be injected.
    *   Handles a wide variety of standard Monopoly card actions and tax rules, including asset-based calculations.
    *   Includes optional `socketio` integration for real-time event broadcasting.
    *   The file is quite large (629 lines), primarily due to the extensive logic within `CardDeck` for handling many different card types.

### `src/models/economic_phase_change.py`

*   **Purpose:** This module defines the `EconomicPhaseChange` database model. This model is used to record instances when the game's economic phase (e.g., 'Normal', 'Boom', 'Bust') changes.
*   **Key Model:**
    *   `EconomicPhaseChange(db.Model)`: Stores information about each phase change, including:
        *   `lap_number`: The game lap when the change occurred.
        *   `old_state`: The economic state before the change.
        *   `new_state`: The economic state after the change.
        *   `inflation_factor`: The new inflation factor applied.
        *   `total_cash`: Total cash in circulation at the time of the change.
        *   `total_property_value`: Total value of all properties at the time of the change.
        *   `description`: Optional textual explanation of the change.
        *   `timestamp`: Time of the change.
*   **Dependencies:** `db` (SQLAlchemy instance), `datetime`.
*   **Core Functionality:** Provides a database representation to log economic shifts, capturing key metrics associated with the change. Includes `__repr__` for basic representation and `to_dict` for API serialization.
*   **Observations:**
    *   A simple data model focused solely on logging economic phase transitions and associated game state metrics.
    *   Likely used for historical tracking and analysis of game dynamics.

### src/models/bot_player.py

*   **Purpose:** Defines the base class (`BotPlayer`) and various subclasses (`ConservativeBot`, `AggressiveBot`, `StrategicBot`, `OpportunisticBot`, `SharkBot`, `InvestorBot`) for implementing different AI player strategies and decision-making logic. This module contains the core AI for bot opponents.
*   **Key Models/Classes:**
    *   `BotPlayer` (Base Class):
        *   **Initialization:** Takes `player_id` and `difficulty` ('easy', 'normal', 'hard'). Loads the associated `Player` model. Sets difficulty-based parameters like `decision_accuracy`, `value_estimation_error`, `risk_tolerance`, and `planning_horizon`.
        *   **Core Turn Logic:** Outlines the turn structure (`execute_turn`): pre-roll actions, roll dice, process move, post-roll actions, end turn. Includes base implementations for dice rolling (`_roll_dice`) and movement (`process_move`).
        *   **Decision Points (Placeholders/Base):** Defines methods intended for subclass override to implement specific strategies:
            *   `perform_pre_roll_actions`: Actions before rolling (e.g., proposing trades, improving properties). Base includes `check_for_special_event`.
            *   `perform_post_roll_actions`: Actions after landing on a space. Base includes `handle_property_space`.
            *   `decide_buy_property`: Logic for deciding whether to buy an unowned property. Base calls `_make_optimal_buy_decision` but introduces randomness based on `decision_accuracy`.
            *   `_make_optimal_buy_decision`: Subclasses implement the core buy/don't buy logic. Base uses `_evaluate_property_value`.
            *   `_evaluate_property_value`: Estimates property value (base implementation).
            *   `decide_auction_bid`: Logic for participating in auctions.
        *   **Base Handlers:**
            *   `handle_property_space`: Base logic for landing on property (buy if unowned, pay rent if owned by others). Includes basic transaction recording.
            *   `check_for_special_event`: Chance to trigger a random `BotEvent`.
            *   `end_turn`: Base method (likely empty, actual turn advancement handled elsewhere).
    *   Subclasses (`ConservativeBot`, `AggressiveBot`, etc.):
        *   Each inherits from `BotPlayer` and typically overrides key decision-making methods (`_make_optimal_buy_decision`, `decide_auction_bid`, `perform_pre_roll_actions`, potentially `_evaluate_property_value`) to reflect their specific strategy (e.g., risk aversion, focus on monopolies, opportunistic trading, long-term investment).
        *   They leverage the base class structure but inject their own logic at critical points. For example, `SharkBot` includes logic to find distressed players for potential trades, while `InvestorBot` focuses on ROI calculations.
*   **Dependencies:** `datetime`, `random`, `logging`, `db`, `Player`, `Property`, `GameState`, `Transaction`, `BotEvent`.
*   **Core Functionality:** Provides the framework and specific implementations for AI player behavior. It simulates turns, makes decisions about buying properties, paying rent, participating in auctions, and potentially initiating trades or other events, based on the assigned strategy and difficulty level.
*   **Observations:**
    *   Very large file (over 1000 lines) due to the base class and multiple detailed subclasses.
    *   Uses a clear inheritance structure to define different AI personalities.
    *   Difficulty levels adjust core parameters affecting decision quality and risk-taking.
    *   Decision-making often involves simulating optimal choices (`_make_optimal_*`) and then applying randomness based on `decision_accuracy` to mimic imperfect play.
    *   Property valuation (`_evaluate_property_value`) and auction bidding (`decide_auction_bid`) logic can be quite complex in some subclasses, considering factors like monopolies, player cash, potential ROI, etc.
    *   Integrates with `BotEvent` to allow bots to trigger strategic events (e.g., proposing trades, potentially market manipulation depending on subclass logic).
    *   Handles basic game mechanics like movement, passing GO, paying rent, and buying properties directly by modifying model states (`Player.cash`, `Property.owner_id`) and creating `Transaction` records. Bankruptcy handling seems mentioned but not fully implemented in the visible base code.

### src/models/bot_events.py

*   **Purpose:** Defines a framework and specific event classes (`BotEvent` subclasses) representing actions or scenarios initiated by bots or affecting the game state significantly (e.g., market changes). These events can be interactive (requiring player response) or automated.
*   **Key Models/Classes:**
    *   `BotEvent` (Base Class): Provides a static factory method `get_random_event(game_state, player_id)` to select and instantiate a suitable event based on weighted probability and current game state validity (using subclass `is_valid` methods). Uses a safe import pattern (`get_active_bots`) for controller data.
    *   `TradeProposal`: Bot initiates a trade offer. Includes logic to select a target player, determine properties to offer/request (strategically aiming to complete monopolies or offload less desirable properties), and calculate a cash difference. The actual offer presentation and response handling are external (likely `BotEventController`).
    *   `PropertyAuction`: Bot decides to auction one of its properties. Includes logic to select a suitable property (e.g., non-monopoly, low value) and calculate a minimum bid. Relies on an external system (e.g., `AuctionSystem` via `BotEventController`) to run the auction.
    *   `MarketCrash`: Simulates a market downturn. Randomly selects property groups, applies price/rent discounts using `Property.apply_market_crash`, and formats event data. Likely triggers a future recovery event (`process_restore_market_prices`).
    *   `EconomicBoom`: Simulates a market upturn. Applies premiums using `Property.apply_economic_boom`. Likely triggers future recovery.
    *   `BotChallenge`: Bot issues a challenge (e.g., quiz, prediction) to other players with a defined reward. External handling for presentation and response.
    *   `MarketTiming`: Bot attempts to capitalize on market conditions (buy low during crashes, sell high during booms). Logic selects affected properties and calculates price changes. Execution involves direct property value updates. Seems tailored for specific bot types (e.g., `OpportunisticBot`).
*   **Helper Functions:**
    *   `process_restore_market_prices`, `process_restore_property_prices`: Standalone functions likely called externally (e.g., by `GameState` temporary effect processing or a scheduler) to revert the effects of `MarketCrash` or `EconomicBoom` events after their duration expires.
*   **Dependencies:** `random`, `logging`, `datetime`, `db`, `Player`, `Property`, `GameState`, `Transaction`, `src.controllers.bot_controller` (via safe import).
*   **Core Functionality:** Provides the definitions and logic for various bot-driven or simulated game events. This includes weighted random event selection, generation of event-specific parameters (trade details, affected properties, price changes), formatting event data for communication (via `get_event_data`), and defining the immediate effects (e.g., applying price changes). Interactive responses and auction mechanics are delegated.
*   **Observations:**
    *   Large file defining multiple complex event types using a class-based structure.
    *   `get_random_event` provides a flexible way to trigger varied events based on weights and validity checks (`is_valid` static methods).
    *   Demonstrates sophisticated bot behaviors, especially in trade proposal logic (strategic property selection) and market timing.
    *   Adds significant economic simulation and dynamic elements to the game.
    *   Clear separation of concerns: these classes define *what* the event is and its immediate impact, while controllers handle the *how* (communication, response handling, auction execution).
    *   Recovery functions (`process_restore_*`) indicate that market events are temporary.

### src/routes/player_routes.py

*   **Purpose:** Defines Flask routes for handling various actions initiated by a player during their turn or related to their status and assets.
*   **Dependencies:** `flask` (`jsonify`, `request`), `src.controllers.player_controller.PlayerController`.
*   **Route Registration:** Uses a `register_player_routes(app)` function to attach the defined routes to the main Flask `app` instance. It instantiates a `PlayerController` to handle the business logic.
*   **Key Routes:**
    *   `/api/player/roll` (POST): Rolls dice for the player.
    *   `/api/player/buy` (POST): Buys the property the player landed on.
    *   `/api/player/end-turn` (POST): Ends the player's current turn.
    *   `/api/player/report-income` (POST): Reports income (likely for passing GO, but data includes `income`).
    *   `/api/player/improve-property` (POST): Adds an improvement to a specified property.
    *   `/api/player/jail-action` (POST): Handles actions while in jail (pay, use card, roll).
    *   `/api/player/status` (GET): Retrieves the player's current status.
    *   `/api/player/properties` (GET): Gets a list of properties owned by the player.
    *   `/api/player/mortgage` (POST): Mortgages a specified property.
    *   `/api/player/unmortgage` (POST): Unmortgages a specified property.
*   **Authentication/Authorization:**
    *   **No explicit login/registration routes** are present in this file.
    *   **Every route consistently requires `player_id` and `pin`** to be passed in the request (either JSON body or query parameters).
    *   These credentials (`player_id`, `pin`) are passed directly to the corresponding `PlayerController` methods for validation and execution. This implies the `PlayerController` is responsible for verifying the PIN against the `player_id` before performing any action. This acts as the primary authentication/authorization mechanism for player-specific actions.
*   **Core Functionality:** Maps HTTP requests for standard player actions to the appropriate methods in `PlayerController`. It handles request data parsing, basic validation (presence of required fields), calling the controller logic, and returning JSON responses (success or error).
*   **Observations:**
    *   Follows a standard Flask Blueprint-like pattern (though not using Blueprints directly, just a registration function).
    *   Relies entirely on the `PlayerController` for game logic and state manipulation.
    *   The PIN-based authentication is simple but potentially insecure if transmitted improperly (depends on HTTPS usage). It's effective for identifying and authorizing actions for a specific player within a game session.
    *   The lack of explicit login/registration suggests these might be handled elsewhere, perhaps during game setup/joining (`game_routes.py`?) or via admin actions (`admin_routes.py`?).

### src/routes/board_routes.py

*   **Purpose:** Defines Flask routes specifically for providing data to a board display interface (likely a passive, read-only view, like a TV display or spectator view). It focuses on retrieving aggregated game state information relevant to visualizing the board and game progress.
*   **Dependencies:** `flask` (`jsonify`, `request`), `src.controllers.board_controller.BoardController`, `src.models.property.Property`, `src.models.game_state.GameState`, `src.models.player.Player`, `src.models` (`get_auction_system`).
*   **Route Registration:** Uses `register_board_routes(app)`. Instantiates a `BoardController`.
*   **Authentication:** All routes use a `display_key` query parameter for authentication/authorization, comparing it against `app.config['DISPLAY_KEY']`. This suggests a simple shared secret mechanism for allowing display devices to access game data.
*   **Key Routes:**
    *   `/api/board/state` (GET): Gets the overall board state (delegated to `BoardController`).
    *   `/api/board/players` (GET): Gets current player positions (delegated to `BoardController`).
    *   `/api/board/properties` (GET): Gets property ownership status (delegated to `BoardController`).
    *   `/api/board/events` (GET): Gets recent game events (delegated to `BoardController`).
    *   `/api/board/register` (POST): Allows a display device to register itself (delegated to `BoardController`).
    *   `/api/board/economy` (GET): Gets the current economic state (inflation, etc.) (delegated to `BoardController`).
    *   `/api/board/auctions` (GET): Gets a list of currently active auctions (delegated to `AuctionSystem`).
    *   `/api/board/auctions/<auction_id>` (GET): Gets details for a specific active auction (delegated to `AuctionSystem`).
    *   `/api/board/property-development/requirements` (GET): Checks and returns the development requirements (approvals, studies) and costs for a specific property and target level. Logic directly queries `Property` and `GameState`.
    *   `/api/board/property-development` (GET): Gets detailed development information (zoning, costs, levels) for all properties within a specified group. Logic directly queries `Property` and `GameState`.
    *   `/api/board/property-development/status` (GET): (Outline only) Likely gets the current development status (approvals, studies) for a specific property.
*   **Core Functionality:** Provides read-only endpoints tailored for a board display. It aggregates data about player positions, property ownership, economic state, ongoing auctions, and complex property development rules.
*   **Observations:**
    *   Clearly separated concerns: These routes are distinct from player action routes (`player_routes.py`) and focus solely on providing data for visualization.
    *   Uses a simple display key for security, suitable for semi-trusted display clients.
    *   Most routes delegate data retrieval logic to `BoardController`, except for auction and detailed property development routes, which interact directly with `AuctionSystem` or `Property`/`GameState` models. This suggests `BoardController` might be primarily an aggregator for common display needs.
    *   The property development routes (`/api/board/property-development/*`) provide detailed insight into the advanced development mechanics (zoning, approvals, studies, costs).

### src/routes/game_routes.py

*   **Purpose:** Defines Flask routes for managing the overall game lifecycle, player joining, retrieving game state, managing configuration, and handling property actions.
*   **Dependencies:** `flask` (`jsonify`, `request`), `src.controllers.game_controller.GameController`, `src.models` (`get_auction_system`).
*   **Route Registration:** Uses `register_game_routes(app)`. Instantiates a `GameController`.
*   **Key Routes:**
    *   `/api/game/new` (POST): Creates a new game session with specified settings (difficulty, limits, etc.). Delegates to `GameController.create_new_game`.
    *   `/api/game/join` (POST): Allows a player to join an existing game during setup. Requires `username` and `pin`. Delegates to `GameController.add_player`. **This is likely where player registration happens.**
    *   `/api/game/state` (GET): Retrieves the current overall game state (delegated to `GameController.get_game_state`).
    *   `/api/game/start` (POST): Starts the game (requires admin key). Delegates to `GameController.start_game`.
    *   `/api/game/end` (POST): Ends the current game (requires admin key). Delegates to `GameController.end_game`.
    *   `/api/game/players` (GET): Retrieves a list of players in the current game (delegated to `GameController.get_players`).
    *   `/api/game/config` (POST): Updates game configuration (requires admin key). Delegates to `GameController.update_game_config`.
    *   `/api/game/history` (GET): Retrieves history of completed games (all or by specific ID). Delegates to `GameController.get_all_game_history` or `get_game_history_by_id`.
    *   `/api/game/property/action` (POST): Handles various property-related actions requested by a player (`buy`, `decline`, `mortgage`, `repair`, etc.). Requires `player_id` and `pin` for authentication. It specifically handles the 'decline' action by directly calling `AuctionSystem.start_auction`. Other actions are delegated to `GameController.handle_property_action`.
*   **Authentication/Authorization:**
    *   Admin actions (`/start`, `/end`, `/config`) require an `admin_key` validated against `app.config['ADMIN_KEY']`.
    *   Player joining (`/join`) requires a `username` and `pin`.
    *   Property actions (`/property/action`) require `player_id` and `pin`.
*   **Core Functionality:** Provides the primary HTTP interface for managing the game itself, adding players, starting/ending, getting state, and handling most property interactions initiated by players.
*   **Observations:**
    *   This file serves as the main entry point for game setup and control via HTTP.
    *   The `/api/game/join` route appears to be the player registration mechanism, associating a username with a PIN for subsequent authentication in other routes (`player_routes.py`, this file's `/property/action`).
    *   There's a slight inconsistency in property action handling: most actions are delegated to `GameController.handle_property_action`, but the 'decline' action directly calls `AuctionSystem.start_auction` within the route handler itself. Consolidating this logic within the `GameController` might be cleaner.
    *   Uses standard Flask request handling and JSON responses. Delegates all core logic to `GameController`.

### src/routes/admin_routes.py

*   **Purpose:** Defines a comprehensive set of Flask routes providing administrative control over the game. This includes managing players (modifying cash, transferring property, removing, adding bots), modifying game state, managing the crime system, controlling adaptive difficulty, triggering events, managing Cloudflare tunnels for remote play, and viewing system/game status.
*   **Dependencies:** `flask` (`jsonify`, `request`, `current_app`), `src.controllers.admin_controller.AdminController`, `src.controllers.crime_controller.CrimeController`, various models (`db`, `GameState`, `Player`, `Property`, `Crime`), `src.controllers.socket_controller` (`event_system`), `logging`, `datetime`. Also likely interacts with `RemoteController` and `AdaptiveDifficultyController` for related routes.
*   **Route Registration:** Uses `register_admin_routes(app)`. Instantiates `AdminController` and `CrimeController`.
*   **Authentication:** Nearly all routes are protected by checking an `admin_key` (passed in request JSON or `X-Admin-Key` header) against `app.config['ADMIN_KEY']`.
*   **Key Routes Grouped by Functionality:**
    *   **Player Management:**
        *   `/api/admin/modify-cash` (POST): Adjust a player's cash.
        *   `/api/admin/transfer-property` (POST): Change property ownership.
        *   `/api/admin/add-bot` (POST): Add a bot player.
        *   `/api/admin/remove-player` (POST): Remove a player (human or bot).
        *   `/api/admin/player/<id>` (GET): Get detailed info about a specific player.
    *   **Game State & Control:**
        *   `/api/admin/modify-game-state` (POST): Directly change core `GameState` attributes.
        *   `/api/admin/status` (GET): Get a high-level admin overview (player count, game state).
        *   `/api/admin/reset` (POST): **Dangerous** - Drops and recreates all database tables.
        *   `/api/admin/trigger-event` (POST): Manually trigger a specific game event.
        *   `/api/admin/list-events` (GET): List available triggerable events.
    *   **Bot Management:**
        *   `/api/admin/bots` (GET): List available bot types/strategies. (Logic likely delegates to `AdminController` or `BotController`).
    *   **Adaptive Difficulty:**
        *   `/api/admin/adaptive-difficulty/assessment` (POST): Manually trigger a game balance assessment.
        *   `/api/admin/adaptive-difficulty/adjust` (POST): Manually adjust bot difficulty.
        *   `/api/admin/adaptive-difficulty/auto-adjust` (POST): Enable/disable automatic difficulty adjustments. (Logic likely delegates to `AdminController` or `AdaptiveDifficultyController`).
    *   **Crime System Management:**
        *   `/api/admin/trigger-audit` (POST): Initiate a tax audit for a player.
        *   `/api/admin/crime/police-activity` (POST): Manually set the police activity level.
        *   `/api/admin/crime/pardon` (POST): Clear a player's criminal record or reduce community standing penalty.
        *   `/api/admin/crime/statistics` (GET): Retrieve crime statistics. (Delegates to `CrimeController`).
    *   **Remote Play (Cloudflare Tunnel):** (Routes start with `/remote`)
        *   `/remote` (GET): Get tunnel status.
        *   `/remote/tunnel/create` (POST), `/start` (POST), `/stop` (POST), `/delete` (DELETE): Manage the tunnel lifecycle.
        *   `/remote/connected-players` (GET): List players connected remotely.
        *   `/remote/timeout` (POST): Configure connection timeout settings.
        *   `/remote/ping-player/<id>` (POST), `/remove-player/<id>` (POST): Admin actions for remote players. (Logic likely delegates to `AdminController` or `RemoteController`).
*   **Core Functionality:** Provides a powerful administrative backend for monitoring and manipulating nearly every aspect of the game state and its subsystems.
*   **Observations:**
    *   Very extensive set of admin capabilities, offering fine-grained control.
    *   Relies heavily on the `AdminController` for most logic, but also directly interacts with other controllers (`CrimeController`) and models/systems (`event_system`, `db`).
    *   The `/api/admin/reset` route is extremely destructive and should be used with extreme caution.
    *   Includes routes for managing the experimental Cloudflare Tunnel integration.
    *   The division of responsibility for bot management, adaptive difficulty, and remote play routes between this file and their respective controllers (`BotController`, `AdaptiveDifficultyController`, `RemoteController`) isn't perfectly clear just from the route definitions; the underlying controllers likely handle the actual logic.
    *   Consistent use of the `admin_key` for authorization.

### src/routes/finance_routes.py

*   **Purpose:** Defines Flask routes for handling various player-initiated financial actions, including managing loans, CDs, HELOCs, and declaring bankruptcy.
*   **Dependencies:** `flask` (`Blueprint`, `jsonify`, `request` - though `Blueprint` isn't actually used), `src.controllers.finance_controller.FinanceController`.
*   **Route Registration:** Uses `register_finance_routes(app)`. It instantiates `FinanceController`, notably retrieving `socketio` and `banker` instances from `app.config` to pass them to the controller. This indicates these services are set up earlier and made available globally via the app config (likely in `SocketController`).
*   **Authentication/Authorization:** All POST routes require `player_id` and `pin` for authentication, which are passed to the `FinanceController`. The GET routes (`/interest-rates`, `/loans`) also require `player_id` and `pin` (as query parameters for `/loans`), implying even read actions are player-specific and authenticated.
*   **Key Routes:**
    *   `/api/finance/loan/new` (POST): Player requests a standard loan.
    *   `/api/finance/loan/repay` (POST): Player makes a payment towards a loan.
    *   `/api/finance/cd/new` (POST): Player deposits money into a CD.
    *   `/api/finance/cd/withdraw` (POST): Player withdraws a CD (potentially early).
    *   `/api/finance/heloc/new` (POST): Player requests a HELOC against a property.
    *   `/api/finance/interest-rates` (GET): Retrieves current interest rates for various products.
    *   `/api/finance/loans` (GET): Retrieves a list of the player's active loans, CDs, and HELOCs.
    *   `/api/finance/bankruptcy` (POST): Player initiates the bankruptcy process.
*   **Core Functionality:** Maps HTTP requests for complex financial actions to the appropriate methods in `FinanceController`. Handles request parsing, basic validation, controller calls, and JSON responses.
*   **Observations:**
    *   Focuses specifically on advanced financial instruments and bankruptcy, separating these from basic player actions (`player_routes.py`) and game control (`game_routes.py`).
    *   Demonstrates a clear dependency on the `FinanceController` for all business logic.
    *   Retrieves shared services (`socketio`, `banker`) from `app.config`, which is a common Flask pattern for making globally initialized objects available.
    *   Consistent use of PIN-based authentication for all player-specific finance actions.

### src/routes/trade_routes.py

*   **Purpose:** Defines Flask routes specifically for managing player-to-player trades.
*   **Dependencies:** `flask` (`jsonify`, `request`), `src.controllers.trade_controller.TradeController`.
*   **Route Registration:** Uses `register_trade_routes(app)`. Instantiates `TradeController`.
*   **Authentication/Authorization:**
    *   Player actions (`/propose`, `/respond`, `/list`, `/cancel`, `/details`) require `player_id` and `pin` (or `proposer_id` and `proposer_pin` for `/propose`).
    *   Admin action (`/admin-approve`) requires `admin_key`.
*   **Key Routes:**
    *   `/api/trade/propose` (POST): A player proposes a trade to another player. Requires details about offered/requested items (`trade_data`).
    *   `/api/trade/respond` (POST): The receiving player accepts or rejects a proposed trade.
    *   `/api/trade/list` (GET): Lists active trades involving the requesting player (both proposed and received).
    *   `/api/trade/cancel` (DELETE): The proposing player cancels their trade offer.
    *   `/api/trade/details` (GET): Gets the full details of a specific trade (likely requires the requester to be involved in the trade).
    *   `/api/trade/admin-approve` (POST): Allows an admin to approve a trade that might have been automatically flagged (e.g., potentially lopsided).
*   **Core Functionality:** Provides the HTTP interface for the player trading system. It maps player actions (propose, respond, cancel, list) to the `TradeController`.
*   **Observations:**
    *   Clear separation of trade-related endpoints.
    *   Relies on `TradeController` for all underlying logic (validation, creation, execution, status updates).
    *   Includes an admin approval mechanism, suggesting some trades might be flagged for review.
    *   Uses standard Flask patterns for request handling and JSON responses.
    *   Consistent PIN-based authentication for player actions and admin key for admin actions.

### src/routes/crime_routes.py

*   **Purpose:** Defines Flask routes for interacting with the game's crime system. This includes allowing players to attempt crimes, retrieve their crime history, and providing admin endpoints to trigger police patrols and get statistics.
*   **Dependencies:** `flask` (`jsonify`, `request`), `src.controllers.crime_controller.CrimeController`, `src.models.player.Player`, `logging`.
*   **Route Registration:** Uses `register_crime_routes(app, socketio=None)`. It initializes a global `crime_controller` instance, passing the `socketio` instance to it.
*   **Authentication/Authorization:**
    *   Player actions (`/commit`, `/history`) require `player_id` and `player_pin`.
    *   Admin actions (`/police-patrol`, `/statistics`) require `admin_key`.
*   **Key Routes:**
    *   `/api/crime/commit` (POST): The main endpoint for a player to attempt a crime. It performs extensive validation (player credentials, valid crime type, required parameters for the specific crime type), then calls `CrimeController.commit_crime`. Logs the outcome.
    *   `/api/crime/history/<player_id>` (GET): Retrieves the *detected* crime history for a specific player. Requires the player's PIN.
    *   `/api/crime/police-patrol` (POST): Admin endpoint to manually trigger the `CrimeController.check_for_police_patrol` logic.
    *   `/api/crime/statistics` (GET): Admin endpoint to retrieve overall crime statistics via `CrimeController.get_crime_statistics`.
    *   `/api/crime/types` (GET): A public (?) endpoint that returns a hardcoded list describing the available crime types, their parameters, risks, and consequences.
*   **Core Functionality:** Provides the HTTP interface for the crime system. It validates player attempts, delegates the core logic to `CrimeController`, and offers admin oversight.
*   **Observations:**
    *   The `/commit` route includes detailed validation logic for different crime types and their specific parameters, ensuring the `CrimeController` receives appropriate data.
    *   Relies on the `CrimeController` for the main crime logic, detection checks, and history retrieval.
    *   The `/types` route provides useful metadata about the crime system, likely for the frontend to display options to the player. It's hardcoded, so changes to crime types in the models/controller would require updating this route definition.
    *   Includes robust error handling using `try...except` blocks in each route.

### src/routes/special_space_routes.py

*   **Purpose:** Defines Flask routes for managing special spaces (non-property locations like Go, Jail, Chance) and the associated Chance/Community Chest cards. Includes routes for players landing on spaces, retrieving information, and admin functions for initialization and management.
*   **Dependencies:** `flask` (`Blueprint`, `jsonify`, `request`, `current_app`), `flask_socketio` (`emit`), `json`, `src.models` (`db`, `special_space` (Card, SpecialSpace), `player.Player`), `src.controllers.special_space_controller.SpecialSpaceController`.
*   **Route Registration:** Uses `register_special_space_routes(app)`. It instantiates `SpecialSpaceController`, retrieving `socketio`, `banker`, and `community_fund` from `app.config` to pass to it. It also stores the controller instance back into `app.config`.
*   **Authentication/Authorization:**
    *   Player action (`/action`) requires `player_id` and `pin`.
    *   Admin actions (`/initialize`, `/cards` POST/PUT/DELETE, `/special-spaces` POST/PUT/DELETE) require `admin_key`.
    *   Public GET routes (`/special-spaces`, `/cards`) appear to be unauthenticated, providing general game setup information.
*   **Key Routes:**
    *   `/api/board/special-spaces` (GET): Get definitions of all special spaces.
    *   `/api/board/special-spaces/<id>` (GET): Get details of a specific special space by ID.
    *   `/api/board/special-spaces/position/<pos>` (GET): Get details of a special space by board position.
    *   `/api/board/special-spaces/action` (POST): Handles the event when a player lands on a special space. Delegates logic to `SpecialSpaceController.handle_special_space`.
    *   `/api/cards` (GET): Gets definitions of all active cards (optionally filtered by type: 'chance'/'community_chest').
    *   `/api/cards/<id>` (GET): Gets details of a specific card.
    *   **Admin Routes:**
        *   `/api/admin/special-spaces/initialize` (POST): Initializes/resets special spaces in the database (delegates to controller).
        *   `/api/admin/cards/initialize` (POST): Initializes/resets cards in the database (delegates to controller).
        *   `/api/admin/cards` (POST): Creates a new custom card.
        *   `/api/admin/cards/<id>` (PUT): Updates an existing card.
        *   `/api/admin/cards/<id>` (DELETE): Deletes/deactivates a card (outline only).
        *   `/api/admin/special-spaces` (POST): Creates a new custom special space (outline only).
        *   `/api/admin/special-spaces/<id>` (PUT/DELETE): Updates/Deletes a special space (outline only).
*   **Core Functionality:** Provides the HTTP interface for special space and card interactions. Handles player actions, provides data retrieval endpoints, and includes comprehensive admin controls for managing and customizing these game elements.
*   **Observations:**
    *   Relies on `SpecialSpaceController` for handling the logic when a player lands on a space and for initialization.
    *   Admin routes allow for significant customization of cards and potentially special spaces directly via the API.
    *   GET routes for spaces/cards provide necessary information for frontends to display the board and card details correctly.
    *   Consistent PIN/Admin Key authentication where appropriate.

### src/routes/community_fund_routes.py

*   **Purpose:** Defines Flask routes for interacting with the game's Community Fund (often associated with Free Parking). Includes a public endpoint to get the fund status and admin endpoints to manage the funds.
*   **Dependencies:** `flask` (`Blueprint`, `jsonify`, `request`, `current_app` - though `Blueprint` isn't used). Relies on the `community_fund` instance being available in `app.config`.
*   **Route Registration:** Uses `register_community_fund_routes(app)`. It retrieves the pre-initialized `community_fund` instance from `app.config`.
*   **Authentication/Authorization:**
    *   The GET route (`/api/community-fund`) appears to be public/unauthenticated.
    *   All POST admin routes (`/api/admin/community-fund/*`) require an `admin_key`.
*   **Key Routes:**
    *   `/api/community-fund` (GET): Returns the current balance and other info about the Community Fund by calling `community_fund.get_info()`.
    *   `/api/admin/community-fund/add` (POST): Admin endpoint to add a specified amount to the fund. Calls `community_fund.add_funds()`.
    *   `/api/admin/community-fund/withdraw` (POST): Admin endpoint to withdraw a specified amount from the fund. Calls `community_fund.withdraw_funds()`.
    *   `/api/admin/community-fund/clear` (POST): Admin endpoint to reset the fund balance to zero. Calls `community_fund.clear_funds()`.
*   **Core Functionality:** Provides the HTTP interface for viewing and administratively managing the Community Fund balance.
*   **Observations:**
    *   Simple and focused set of routes for the Community Fund.
    *   Relies entirely on the `CommunityFund` service class (retrieved from `app.config`) to handle the logic and persistence (which itself uses `GameState.settings`).
    *   Clear separation between public read access and admin write access.

### src/routes/game_mode_routes.py

*   **Purpose:** Defines Flask routes for managing different game modes. It allows listing available modes, selecting a mode for a game, retrieving settings, updating settings, and checking mode-specific win conditions.
*   **Dependencies:** `flask` (`Blueprint`, `jsonify`, `request`, `current_app`), `logging`, `functools` (`wraps`), `src.controllers.game_mode_controller.GameModeController`, `src.models` (`db`, `GameMode`).
*   **Route Registration:** Uses a Flask `Blueprint` (`game_mode_bp`) registered under the `/api/game-modes` prefix. Instantiates `GameModeController`.
*   **Authentication/Authorization:**
    *   Uses a custom decorator `@admin_required` for routes that modify state (`/select`, `/update-settings`, `/list-active`). This decorator checks for the admin key in headers or query parameters.
    *   Public GET routes (`/`, `/check-win`, `/settings`) appear unauthenticated.
*   **Key Routes:**
    *   `/` (GET): Lists all available game modes (delegates to `GameModeController.get_available_modes`).
    *   `/select/<game_id>` (POST): Admin selects and initializes a game mode for a specific game instance (delegates to `GameModeController.initialize_game_mode`).
    *   `/check-win/<game_id>` (GET): Checks if the win condition for the specified game's mode has been met (delegates to `GameModeController.check_win_condition`).
    *   `/settings/<game_id>` (GET): Retrieves the current settings for the game's active mode (delegates to `GameModeController.get_game_mode_settings`).
    *   `/update-settings/<game_id>` (POST): Admin updates specific settings for the game's mode (delegates to `GameModeController.update_game_mode_settings`). Prevents changing the core `mode_type`.
    *   `/list-active` (GET): Admin endpoint to list all active `GameMode` records from the database.
*   **Core Functionality:** Provides the HTTP interface for selecting, configuring, and querying game modes and their status.
*   **Observations:**
    *   Uses Flask Blueprints for organization.
    *   Employs a decorator for admin authentication, keeping route handlers cleaner.
    *   Relies on `GameModeController` for most logic related to initializing and managing mode settings and win conditions.
    *   Provides clear separation between public information routes and admin control routes.

### src/routes/remote_routes.py

*   **Purpose:** Defines Flask routes specifically for managing the remote play functionality, primarily through controlling the Cloudflare Tunnel (`cloudflared`) process. It also includes endpoints for managing remotely connected players.
*   **Dependencies:** `flask` (`Blueprint`, `jsonify`, `request`, `current_app`, `send_file`), `logging`, `functools` (`wraps`), `src.controllers.remote_controller.RemoteController`, `datetime`, `qrcode`, `io`. Imports `socketio`, `connected_players`, `player_reconnect_timers` from `src.controllers.socket_controller` locally.
*   **Route Registration:** Uses Flask `Blueprint` (`remote_bp`) registered under `/api/remote`. Instantiates `RemoteController`.
*   **Authentication/Authorization:**
    *   Most routes require admin authentication using the `@admin_required` decorator.
    *   The `/info` route (providing only the tunnel URL) is public.
*   **Key Routes Grouped by Functionality:**
    *   **Tunnel Management (Admin):**
        *   `/status` (GET): Get detailed tunnel status (running, config, URL).
        *   `/check-installation` (GET): Verify `cloudflared` installation and version.
        *   `/create` (POST): Create a new tunnel configuration.
        *   `/start` (POST): Start the `cloudflared` tunnel process. Stores URL in `app.config`.
        *   `/stop` (POST): Stop the tunnel process. Removes URL from `app.config`.
        *   `/delete` (DELETE): Delete the tunnel configuration and process. Removes URL from `app.config`.
    *   **Public Info:**
        *   `/info` (GET): Publicly accessible endpoint returning whether remote play is enabled and the tunnel URL if active.
    *   **Remote Player Management (Admin):**
        *   `/players` (GET): List remotely connected players (delegates to `RemoteController`).
        *   `/players/ping/<id>` (POST): Send a ping request via Socket.IO to a specific player. Interacts directly with `socketio` and `connected_players` from `SocketController`.
        *   `/players/remove/<id>` (DELETE): Forcibly disconnect a remote player and remove tracking. Interacts directly with `socketio`, `connected_players`, and `player_reconnect_timers` from `SocketController`.
        *   `/timeout` (POST): Update the reconnection timeout setting stored in `app.config['REMOTE_PLAY_TIMEOUT']`.
    *   **Utility (Admin):**
        *   `/qr` (GET): Generates and returns a QR code image containing the connection URL (`/connect`) derived from the active tunnel URL. Uses the `qrcode` library.
*   **Core Functionality:** Provides the administrative HTTP interface for setting up, controlling, and monitoring the Cloudflare Tunnel used for remote play. Also includes tools for managing connected remote players.
*   **Observations:**
    *   Uses a Blueprint for organization.
    *   Relies heavily on `RemoteController` for tunnel process management (`cloudflared` interaction).
    *   Admin routes for managing remote players (`ping`, `remove`) interact directly with global state (`connected_players`, `player_reconnect_timers`, `socketio`) maintained by `SocketController`. This highlights coupling between these modules for remote play features.
    *   The QR code generation endpoint is a convenient utility for sharing the connection URL.
    *   Configuration settings related to remote play (Admin Key, Timeout) are accessed via `current_app.config`.

### src/routes/social/alliance_routes.py

*   **Purpose:** Defines Flask routes for managing player alliances (creation, invites, membership, roles, etc.).
*   **Dependencies:** `flask` (`Blueprint`, `request`, `jsonify`), `src.controllers.social.SocialController`, `logging`.
*   **Route Registration:** Uses a Flask `Blueprint` (`alliance_bp`) registered under `/api/social/alliances`. Instantiates `SocialController` (passing `socketio` received during registration).
*   **Authentication/Authorization:** Authentication (e.g., via player PIN) is implicitly handled within the `SocialController` methods, which require `creator_id`, `updater_id`, `inviter_id`, or `player_id` parameters in the request data. There's no explicit authentication layer visible in the routes themselves.
*   **Key Routes:**
    *   `/` (GET): Get alliances a specific player is a member of (`player_id` query param).
    *   `/` (POST): Create a new alliance (requires `creator_id`, `name`).
    *   `/<alliance_id>` (GET): Get details for a specific alliance. Requires `player_id` query param likely for permission checks within the controller.
    *   `/<alliance_id>` (PUT): Update alliance settings (requires `updater_id` in body).
    *   `/<alliance_id>/invite` (POST): Invite another player (requires `inviter_id`, `invitee_id`).
    *   `/invites/<invite_id>/respond` (POST): Respond to an invitation (requires `player_id` of invitee, `accept` boolean).
    *   `/<alliance_id>/leave` (POST): Leave an alliance (requires `player_id`).
    *   `/<alliance_id>/members/<member_id>/role` (PUT): Update a member's role (requires `updater_id`, `new_role`).
    *   `/benefits` (GET): Calculate alliance benefits between two players (`player1_id`, `player2_id` query params).
*   **Core Functionality:** Provides the HTTP interface for all alliance-related actions and information retrieval.
*   **Observations:**
    *   Well-structured CRUD-like operations for alliances and memberships.
    *   Relies entirely on the `SocialController` (which likely contains or delegates to `AllianceController`) for the business logic and persistence.
    *   Uses path parameters for specific alliance/invite/member IDs and query parameters or JSON body for player IDs and other data.
    *   The `/benefits` route suggests alliances have direct gameplay implications calculated via the controller.

### src/routes/social/chat_routes.py

*   **Purpose:** Defines Flask routes for managing the in-game chat system, including channels, messages, and reactions.
*   **Dependencies:** `flask` (`Blueprint`, `request`, `jsonify`), `src.controllers.social.SocialController`, `logging`.
*   **Route Registration:** Uses Flask `Blueprint` (`chat_bp`) registered under `/api/social/chat`. Instantiates `SocialController` (passing `socketio` received during registration).
*   **Authentication/Authorization:** Similar to `alliance_routes.py`, authentication (e.g., player PIN) seems to be handled implicitly within the `SocialController` methods based on `player_id` or `sender_id` provided in request data. No explicit auth checks are visible in the routes.
*   **Key Routes:**
    *   `/channels` (GET): Get channels a specific player is a member of (`player_id` query param).
    *   `/channels` (POST): Create a new chat channel (requires `creator_id`, `name`).
    *   `/channels/<channel_id>/messages` (GET): Get message history for a channel (supports pagination via `limit` and `before_message_id` query params). Requires `player_id` likely for permission checks.
    *   `/channels/<channel_id>/messages` (POST): Send a message to a channel (requires `sender_id`, `content`).
    *   `/channels/<channel_id>/messages/<message_id>/reactions` (POST): Add an emoji reaction to a message (requires `player_id`, `emoji`).
    *   `/channels/<channel_id>/messages/<message_id>/reactions` (DELETE): Remove an emoji reaction (requires `player_id`, `emoji` query params).
    *   `/channels/<channel_id>/join` (POST): Join a channel (requires `player_id`).
    *   `/channels/<channel_id>/leave` (POST): Leave a channel (requires `player_id`).
*   **Core Functionality:** Provides the HTTP interface for chat interactions.
*   **Observations:**
    *   Standard RESTful structure for managing chat resources (channels, messages, reactions).
    *   Relies entirely on the `SocialController` (which likely contains or delegates to `ChatController`) for business logic, persistence, and real-time broadcasting via Socket.IO.
    *   Includes pagination for retrieving message history.
    *   Uses path parameters for specific channel/message IDs and query parameters/JSON body for player IDs and other data.

### src/routes/social/reputation_routes.py

*   **Purpose:** Defines Flask routes for managing the player reputation system.
*   **Dependencies:** `flask` (`Blueprint`, `request`, `jsonify`), `src.controllers.social.SocialController`, `logging`.
*   **Route Registration:** Uses Flask `Blueprint` (`reputation_bp`) registered under `/api/social/reputation`. Instantiates `SocialController` (passing `socketio` received during registration).
*   **Authentication/Authorization:**
    *   GET routes (`/<player_id>`, `/<player_id>/events`, `/<player_id>/credit`) appear to be public/unauthenticated, allowing anyone to view player reputations.
    *   The POST route for recording events (`/<player_id>/events`) doesn't show explicit authentication, but the action of recording an event might be implicitly authorized by game logic triggering it (e.g., a trade completion).
    *   Admin routes (`/admin/<player_id>/adjust`, `/admin/<player_id>/reset`) require an admin key passed in the `X-Admin-Key` header.
*   **Key Routes:**
    *   `/<player_id>` (GET): Get a player's overall reputation scores.
    *   `/<player_id>/events` (GET): Get a player's reputation event history (supports pagination via `limit`/`offset` and filtering by `category`).
    *   `/<player_id>/events` (POST): Record a new event affecting reputation (requires `event_type`, `description`, `impact`).
    *   `/<player_id>/credit` (GET): Get the player's calculated credit score.
    *   `/admin/<player_id>/adjust` (POST): Admin manually adjusts reputation (requires `adjustment`).
    *   `/admin/<player_id>/reset` (POST): Admin resets reputation to defaults.
*   **Core Functionality:** Provides the HTTP interface for viewing, recording, and administrating player reputation scores and history.
*   **Observations:**
    *   Relies entirely on the `SocialController` (which likely contains or delegates to `ReputationController`) for business logic and persistence.
    *   Offers endpoints for both viewing current reputation/credit score and reviewing the history of events that led to those scores.
    *   Includes admin tools for moderation.
    *   The route for recording events (`POST /<player_id>/events`) seems designed to be called internally by other game systems when reputation-affecting actions occur.

---

### `src/routes/social/__init__.py`

**Summary:**
Serves as the registration point for all social feature routes. Imports registration functions from `chat_routes.py`, `alliance_routes.py`, and `reputation_routes.py` and provides a single `register_social_routes(app, socketio)` function to call them.

**Notes:**
- **Purpose:** Aggregates registration for the social module.
- **Structure:** Imports and calls registration functions from sibling route modules.
- **Functionality:** Centralizes initialization of social routes.
- **`__all__`:** Correctly defined.

**Potential Issues & Improvements:**
- None. Standard and clean structure.

---

### `src/routes/player_routes.py`

**Summary:**
Defines Flask routes under `/api/player/` for player-initiated actions like rolling dice, buying/improving/mortgaging property, ending turn, handling jail, and getting status/assets. Authenticates using player ID and PIN. Delegates logic to `PlayerController`.

**Notes:**
- **Functionality:** Covers standard player turn actions and property management.
- **Controller:** Uses a global `PlayerController` instance.
- **Authentication:** Consistently uses `player_id` and `pin`.
- **Logic Delegation:** Routes delegate logic to `PlayerController`.
- **Overlap/Redundancy:** Significant overlap exists with property actions in `/api/game/property/action` (`game_routes.py`) and possibly socket events (`property_controller.py`). The intended pathway for these actions is unclear.
- **Dependencies:** `flask`, `PlayerController`.

**Potential Issues & Improvements:**
- **CRITICAL:** **Clarify Responsibility:** Consolidate or clearly define the single point of entry for player property actions (buy, improve, mortgage, etc.) to eliminate redundancy between this file, `game_routes.py`, and socket events.
- **Global Controller:** Consider alternative controller instantiation.
- **Blueprint:** Consider using a Flask Blueprint.