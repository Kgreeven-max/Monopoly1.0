# Ticket: Clarify Financial Controller Responsibilities

**Priority:** P2
**Status:** To Do

**Description:**
There appears to be potential overlap or unclear boundaries in responsibilities between the `Banker` service class, `FinanceController`, `PropertyController`, and `GameController` regarding financial transactions (especially property purchases/sales, loans, CDs). Review these interactions to establish clear, documented boundaries and ensure functionality isn't duplicated or misplaced.

**Areas of Focus:**
-   **Property Purchase/Sale:** Who initiates, who validates, who performs the transaction (`Player` vs `Banker` vs `PropertyController` vs `GameController`)?
-   **Loan/CD Creation:** How do `FinanceController.create_loan/create_cd` interact with `Banker.provide_loan/accept_deposit`? Is the division of labor (e.g., detailed eligibility in FinanceController, core transaction in Banker) clear and consistently applied?
-   **Mortgage/Unmortgage:** Where is the cash transfer logic handled (`PropertyController`, `Banker`, `GameController`)?

**Tasks:**
1.  Map out the typical flow for key financial operations involving these components (e.g., player buys property, player takes loan, player mortgages property).
2.  Analyze the code in `src/models/banker.py`, `src/controllers/finance_controller.py`, `src/controllers/property_controller.py`, and relevant parts of `src/controllers/game_controller.py`.
3.  Identify specific areas of overlap or ambiguity.
4.  Refactor if necessary to consolidate logic and enforce clear responsibility boundaries. For example, ensure `FinanceController` handles player requests and complex eligibility, while `Banker` handles the core transaction with the bank.
5.  Document the established responsibilities (e.g., in controller docstrings or relevant architecture documents).

**Acceptance Criteria:**
-   The roles of `Banker`, `FinanceController`, `PropertyController`, and `GameController` in financial operations are clearly defined and distinct.
-   Code related to these operations is located in the appropriate component based on the defined responsibilities.
-   Functional duplication is eliminated.
-   Documentation reflects the clarified responsibilities. 