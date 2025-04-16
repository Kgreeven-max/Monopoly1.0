# Ticket: Refactor Large Controllers/Models

**Priority:** P2
**Status:** To Do

**Description:**
Several key controller and model files have grown significantly large, increasing complexity and hindering maintainability. Refactor these files by breaking them down into smaller, more focused modules or classes based on logical responsibilities.

**Files to Refactor (Prioritized):**
1.  `src/models/bot_player.py` (>1000 lines) - Consider separating base class from specific bot strategy implementations.
2.  `src/controllers/socket_controller.py` (>900 lines) - Consider separating event registration, connection handling, and different event category handlers (game actions, social, admin).
3.  `src/models/property.py` (>900 lines) - Consider extracting logic for specific complex mechanics (e.g., development prerequisites, damage/repair, market events) into helper classes or functions.
4.  `src/models/bot_events.py` (Large) - Review if event types can be grouped or simplified, or if helper functions/classes can be used.
5.  `src/models/special_space.py` (629 lines) - Focus on the `CardDeck` class and its numerous `_handle_*_action` methods. Consider a more structured approach for card action dispatching.

**Tasks:**
1.  For each file, identify distinct responsibilities or complex sections.
2.  Plan the refactoring approach (new modules, helper classes, etc.).
3.  Implement the refactoring incrementally, ensuring tests (if available) still pass or adding tests if necessary.
4.  Update relevant imports and dependencies.

**Acceptance Criteria:**
-   The lines of code in the targeted files are significantly reduced (aiming for < 300 lines per file where feasible, or significantly improved organization).
-   Functionality remains unchanged.
-   Code readability and maintainability are improved. 