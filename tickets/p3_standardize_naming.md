# Ticket: Standardize Naming Conventions

**Priority:** P3
**Status:** To Do

**Description:**
Minor inconsistencies in naming conventions were noted during the review (e.g., `money` attribute in `Player` model vs. `cash` parameter/variable used elsewhere). Conduct a broader search for similar inconsistencies in variable names, function parameters, and potentially model attributes across the codebase and standardize them for better readability and consistency.

**Example Identified:**
-   `Player.money` attribute vs. `cash` used in parameters/logic (e.g., `Team.calculate_score`, `Team.process_income_sharing`, `Banker` methods, etc.).

**Tasks:**
1.  Perform codebase searches (e.g., using `grep` or IDE features) for common terms with potential variations (e.g., `money`/`cash`, `balance`/`amount`, `player_id`/`user_id`, `prop`/`property`).
2.  Identify clear inconsistencies.
3.  Choose a standard convention for each identified case (e.g., consistently use `cash` for player funds).
4.  Refactor the code to apply the chosen standard names.
5.  Ensure changes do not break functionality.

**Acceptance Criteria:**
-   Naming conventions for common concepts (like player funds) are consistent across the backend codebase.
-   Readability is improved due to consistent terminology. 