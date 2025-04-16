# Prioritized Ticket List

Based on the holistic review and detailed component notes, here is a prioritized list of actionable tickets:

## P1: Stability & Core Functionality

-   [ ] **Persist Auction State:** The `AuctionSystem` currently uses in-memory state (`active_auctions`), meaning auctions are lost on server restart. Investigate and implement database persistence for active auctions (`src/models/auction_system.py`). **Status: In Progress (Created `src/models/auction.py`, need migration + `AuctionSystem` refactor).**
-   [x] **Complete Model Reviews:** Finish the code review for the remaining models in `src/models/` to ensure correctness and identify potential issues. Focus on critical unreviewed models like `crime.py`, `bot_player.py`, `special_space.py`, `property.py`, `bot_events.py`, `event_system.py`, `jail_card.py` and subdirectories (`social/*`, `finance/*`). Update `code-review.md` as reviews are completed. **Status: Completed (Identified several required P2/P3 refactors - see `code-review.md` comments).**

## P2: Refactoring & Decoupling (Identified during Model Review)

-   [ ] **Refactor Large Files:** Break down overly large files into smaller, more focused modules. High priority:
    -   `src/models/bot_player.py` (>1000 lines)
    -   `src/models/bot_events.py` (>1000 lines)
    -   `src/controllers/socket_controller.py` (>900 lines) (From previous notes)
    -   `src/models/property.py` (>900 lines) (From previous notes)
    -   `src/models/special_space.py` (629 lines)
    -   `src/models/auction_system.py` (530 lines)
    -   `src/models/crime.py` (479 lines)
-   [ ] **Address Circular Dependencies:** 
    - Investigate and resolve the circular dependency between `bot_events.py` and `bot_controller.py` (via `get_active_bots()`).
    - Investigate and resolve potential circular dependencies requiring local imports in `src/models/__init__.py` (`get_banker`, `get_auction_system`).
-   [ ] **Move Logic from Models/Services:** Relocate business logic currently residing in model files or incorrectly placed services:
    -   `src/models/crime.py` (Execution/detection logic to Controller/Service)
    -   `src/models/bot_player.py` (Game logic, turn execution to Controllers/Services)
    -   `src/models/special_space.py` (`CardDeck`, `TaxSpace` logic to Controller/Service)
    -   `src/models/bot_events.py` (Event execution/parameterization logic to Controller/Service)
    -   `src/models/auction_system.py` (Should be Controller/Service, not Model. Needs concurrency review.)
    -   `src/models/event_system.py` (Should be Controller/Service, not Model. Needs state persistence review.)
-   [ ] **Decouple Components:** Reduce tight coupling identified during reviews:
    -   Decouple `Loan` model from `GameState`.
    -   Decouple `EventSystem` from `socketio`, `banker`, `community_fund`, `GameState`.
    -   Decouple `AuctionSystem` from `socketio`, `banker`, models.
    -   Decouple `CardDeck`/`TaxSpace` from `GameState`, `Banker`, etc.
    -   Decouple `BotPlayer` from `GameState`, other models.
-   [ ] **Remove Global State:** Refactor `src/models/__init__.py` to remove global singletons (`get_banker`, `get_auction_system`) and use Dependency Injection.
-   [ ] **Move Logic from Routes:** Relocate business logic currently residing directly in route handlers into the appropriate controllers. Example: Auction start logic in `game_routes.py` (`/api/game/property/action` for 'decline'). (From previous notes)
-   [ ] **Clarify Banker/Finance/Property Controller Responsibilities:** Review the interactions between `Banker`, `FinanceController`, `PropertyController`, and `GameController` regarding financial transactions (loans, purchases, sales) to ensure clear responsibility boundaries and avoid functional overlap. (From previous notes)
-   [ ] **Review SocketController Authentication:** Investigate and ensure proper authentication/authorization is applied to handlers within `src/controllers/socket_controller.py`, particularly for social features.

## P3: Consistency & Cleanup (Identified during Model Review)

-   [ ] **Consolidate DB Commits:** Review model/service methods and remove `db.session.commit()` calls. Ensure commits are handled by the calling controller/service at the end of an operation. Affects: `crime.py`, `bot_player.py`, `special_space.py`, `bot_events.py`, `loan.py`.
-   [ ] **Replace Magic Numbers:** Replace hardcoded numeric literals with named constants. Affects: `crime.py`, `bot_player.py`, `event_system.py`, `bot_events.py`.
-   [ ] **Standardize Naming Conventions:** Address minor inconsistencies, such as `money` in `Player` model vs. `cash` used elsewhere. Perform a codebase search for similar inconsistencies. (From previous notes)
-   [ ] **Review `RemoteController` Scope:** Evaluate if `get_connected_players` truly belongs in `RemoteController` or if it's better suited elsewhere (e.g., `SocketController` or `AdminController`). (From previous notes)

## P4: Feature Completeness & Future Review

-   [ ] **Review Routes:** Populate and review the `src/routes/` section in `code-review.md`. Although notes exist in `shared-component-notes.md`, the checklist needs updating.
-   [ ] **Review Client Code:** Initiate code reviews for the client-side components, services, and pages (`client/src/*`), adding relevant files to `code-review.md`.
-   [ ] **Review Other Files:** Identify and review any other relevant project files not yet covered (e.g., `__init__.py`, setup scripts, utility functions), adding them to `code-review.md`. 