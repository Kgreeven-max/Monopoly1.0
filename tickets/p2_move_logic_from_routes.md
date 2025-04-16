# Ticket: Move Logic from Routes to Controllers

**Priority:** P2
**Status:** To Do

**Description:**
Some route handler functions contain business logic that should ideally reside within controller classes. This keeps the route layer thin and focused on HTTP request/response handling and basic validation, improving separation of concerns and testability.

**Example Identified:**
-   In `src/routes/game_routes.py`, the `/api/game/property/action` route directly calls `AuctionSystem.start_auction` when the action is 'decline', instead of delegating this logic to the `GameController`.

**Tasks:**
1.  Review all route files in `src/routes/`.
2.  Identify instances where route handlers perform complex logic beyond basic input validation, authentication checks, and calling a single controller method.
3.  Relocate the identified business logic to the appropriate controller class(es).
4.  Update the route handler to simply call the relevant controller method(s).

**Acceptance Criteria:**
-   Route handlers in `src/routes/` primarily handle request parsing, authentication/authorization, and delegation to controllers.
-   Core business logic resides within the controller classes (`src/controllers/`).
-   Code structure adheres better to the intended separation of concerns (Routes -> Controllers -> Models/Services). 