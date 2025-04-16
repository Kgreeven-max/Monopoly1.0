# Ticket: Complete Model Reviews

**Priority:** P1
**Status:** Completed

**Description:**
Finish the code review for the remaining models in `src/models/` to ensure correctness and identify potential issues before further development or refactoring. This is crucial for overall stability and understanding the existing codebase.

**Files to Review:**
-   `src/models/crime.py`
-   `src/models/bot_player.py`
-   `src/models/special_space.py`
-   `src/models/property.py`
-   `src/models/bot_events.py`
-   `src/models/auction_system.py`
-   `src/models/event_system.py`
-   `src/models/economic_phase_change.py`
-   `src/models/jail_card.py`
-   `src/models/social/*` (subdirectory)
-   `src/models/finance/*` (subdirectory)
-   `src/models/__init__.py`

**Tasks:**
1.  [x] Thoroughly review each listed file and subdirectory.
2.  [x] Document findings (issues, questions, suggestions) - primarily as comments in `code-review.md`.
3.  [x] Update the checklist in `code-review.md` as each model/subdirectory is completed.
4.  [x] Create follow-up tickets for any actionable issues identified during the review. (Note: Issues identified and documented in `code-review.md` comments, and corresponding P2/P3 tickets created/updated in `tickets/index.md`).

**Acceptance Criteria:**
-   [x] All models listed above are reviewed.
-   [x] `code-review.md` accurately reflects the completion status and review notes.
-   [x] Any critical issues found are documented and have corresponding tickets created/updated in `tickets/index.md`. 