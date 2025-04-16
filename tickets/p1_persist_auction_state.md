# Ticket: Persist Auction State

**Priority:** P1
**Status:** To Do

**Description:**
The `AuctionSystem` currently uses in-memory state (`active_auctions`), meaning auctions are lost on server restart. Investigate and implement database persistence for active auctions to ensure game state integrity across server restarts.

**Relevant Files/Modules:**
-   `src/models/auction_system.py`
-   `src/controllers/auction_controller.py`
-   `docs/auction-system.md` (if available)

**Acceptance Criteria:**
-   Active auctions (ID, property, bidders, current bid, timer state) are stored in the database.
-   Upon server restart, the `AuctionSystem` can reload and resume active auctions from the database.
-   Auction timers and state transitions correctly handle persistence. 