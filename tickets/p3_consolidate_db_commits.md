# Ticket: Consolidate Database Commits

**Priority:** P3
**Status:** To Do

**Description:**
Some model methods, particularly within the crime system (`src/models/crime.py`), perform multiple `db.session.commit()` calls within a single logical operation (e.g., after setting initial details, after detection check, after successful execution). While functionally correct, committing multiple times within one high-level action can be less efficient. Review these instances and consolidate commits where appropriate.

**Example Identified:**
-   `Crime` subclass `execute()` methods in `src/models/crime.py` sometimes commit multiple times.

**Tasks:**
1.  Scan model methods (especially those performing complex operations or state changes) for multiple `db.session.commit()` calls within the same function scope.
2.  Analyze if these multiple commits are necessary or if they can be consolidated into a single commit at the end of the logical operation.
3.  Refactor the methods to use a single commit where feasible, ensuring atomicity of the operation is maintained.
4.  Verify that the refactoring does not introduce unintended side effects or data inconsistencies, especially in error scenarios (ensure rollbacks still work correctly).

**Acceptance Criteria:**
-   Unnecessary multiple commits within single model operations are eliminated.
-   Database interactions are potentially more efficient.
-   Atomicity of operations is preserved. 