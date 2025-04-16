# Pi-nopoly Refactoring Plan

This document outlines the phased approach for refactoring the Pi-nopoly codebase to improve structure, stability, and maintainability, using `Monopoly-game-master` as a conceptual reference for core logic.

## Phase 1: Core Structure Refactoring (Foundation First)

Goal: Establish a solid, well-organized foundation based on Python best practices and address critical structural issues identified in `code-review.md` and `tickets/`.

- [ ] 1.  **Address Circular Dependencies & Logic Placement:**
    *   Move business logic out of route files (e.g., `game_routes.py`, `player_routes.py`) into appropriate controllers (e.g., `GameController`, `PlayerController`). (Addresses `tickets/p2_move_logic_from_routes.md`)
    *   Resolve circular import issues that arise during logic migration. (Addresses `tickets/p2_address_circular_dependencies.md`)
- [ ] 2.  **Refactor Large Components:**
    *   Break down oversized models and controllers (e.g., `bot_player.py`, `auction_system.py`, `special_space.py`, `crime.py`, `bot_events.py`) into smaller, single-responsibility modules. (Addresses `tickets/p2_refactor_large_components.md`)
- [ ] 3.  **Clean Up `app.py`:**
    *   Temporarily comment out/remove imports and registrations for non-functional/missing route files (`property_routes`, `auction_routes`, `bot_event_routes`, `remote_routes`).
    *   Refine core service initialization (e.g., `Banker`, `CommunityFund`, `EventSystem`) using Application Context or Dependency Injection patterns instead of relying solely on `app.config`.
- [ ] 4.  **Basic Game Loop Verification:**
    *   Ensure the fundamental Monopoly turn sequence (roll, move, land on basic spaces) functions correctly within the refactored structure.

## Phase 2: Stabilize Existing Features

Goal: Ensure all *currently active* features function correctly within the newly refactored core structure.

- [ ] 1.  **Functionality Check:** Verify features like basic player actions, finance operations (loans, CDs if active), special space handling (cards, taxes if active), and community fund interactions work as expected.
- [ ] 2.  **Bug Fixing:** Address any regressions or bugs introduced during the Phase 1 refactoring.

## Phase 3: Integrate Missing & Advanced Features (Build the House)

Goal: Incrementally add back missing components and layer in advanced systems onto the stable core.

- [ ] 1.  **Re-integrate Routes & Controllers:**
    *   Systematically re-introduce previously commented-out routes (`property`, `auction`, `bot_event`) ensuring they align with the refactored controller structure.
    *   Verify or create the corresponding models and controllers (`PropertyController`, `AuctionController`, etc.).
- [ ] 2.  **Implement Remote Play:**
    *   Address `cloudflared` dependency and installation issues (`pinopoly.log`).
    *   Fix `RemoteController` initialization and related errors.
    *   Resolve `qrcode`/`Pillow` dependency issues if necessary.
    *   Integrate `remote_routes.py`.
- [ ] 3.  **Layer Advanced Systems:**
    *   Incrementally implement, refine, and integrate complex systems:
        *   Full Crime System
        *   Advanced AI Bot Logic & Adaptive Difficulty
        *   Game Modes
        *   Social Features (Chat, Alliances, Reputation)
    *   Ensure clean integration with the core structure.

## Guiding Principles

*   Follow `.cursorrules` guidelines.
*   Prioritize stability and clarity.
*   Work incrementally, verifying changes often.
*   Keep documentation (`code-review.md`, `project-status.md`, this plan) updated. 