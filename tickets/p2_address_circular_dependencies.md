# Ticket: Address Circular Dependencies

**Priority:** P2
**Status:** To Do

**Description:**
The codebase frequently uses local imports within methods to mitigate circular dependency issues, particularly involving central models/services like `GameState`, `Banker`, `BotController`, and `SocketController`. While this works, it can obscure dependencies and make the architecture harder to understand. Investigate these instances and refactor where possible to achieve better decoupling.

**Examples Identified:**
-   `src/controllers/adaptive_difficulty_controller.py` imports `active_bots` from `src/controllers/bot_controller.py` inside `adjust_difficulty`.
-   `src/models/game_state.py` imports `.bot_events`, `.economic_phase_change`, `src.controllers.crime_controller`, `src.models.Property` locally within methods like `process_turn_end`.
-   `src/models/banker.py` uses multiple local imports (`.transaction`, `.loan`, `.player`, `.property`, `.game_state`).
-   `src/models/loan.py` imports `.game_state` locally.
-   `src/models/crime.py` imports `Player`, `GameState`, `Property`, `Transaction` locally.
-   `src/routes/remote_routes.py` imports state from `src.controllers.socket_controller` locally.

**Tasks:**
1.  Identify all instances of local imports used to break cycles.
2.  Analyze the dependency graph for these modules.
3.  Explore refactoring techniques:
    -   Dependency Injection: Pass required instances/data during initialization or method calls.
    -   Event-Based Communication: Use signals or an event bus (like Socket.IO for some cases, or potentially a simpler internal pub/sub) to decouple components.
    -   Extracting Functionality: Move functions/classes causing the cycle to a new, lower-level module.
    -   Interface Segregation: Define interfaces that components depend on, rather than concrete implementations.
4.  Implement the chosen refactoring strategy, prioritizing the most problematic cycles.

**Acceptance Criteria:**
-   The number of local imports used solely to break circular dependencies is significantly reduced.
-   Module dependencies are clearer and easier to trace.
-   Code maintainability and testability are improved. 