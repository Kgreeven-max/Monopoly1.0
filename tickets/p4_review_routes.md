# Ticket: Review Routes

**Priority:** P4
**Status:** To Do

**Description:**
The code review process has covered controllers and some models, but the API routes defined in `src/routes/` have not been formally reviewed and tracked in `code-review.md`. Although detailed notes on routes exist in `shared-component-notes.md` (synthesized from controller reviews), a dedicated pass on the route files themselves is needed, and the checklist must be updated.

**Files/Directory to Review:**
-   `src/routes/` (all files within)

**Tasks:**
1.  List all route files from `src/routes/` in the appropriate section of `code-review.md`.
2.  Review each route file, focusing on:
    -   Correctness of endpoint paths and HTTP methods.
    -   Appropriate request data parsing (JSON, query parameters).
    -   Proper validation of required inputs.
    -   Correct authentication/authorization checks (player PIN, admin key, display key).
    -   Clear delegation to controller methods.
    -   Consistent and informative JSON response formatting (success and error cases).
    -   Adherence to RESTful principles where applicable.
3.  Document findings and create follow-up tickets for any issues.
4.  Update the checklist in `code-review.md` as each file is reviewed.

**Acceptance Criteria:**
-   All files in `src/routes/` are listed and checked off in `code-review.md`.
-   Route definitions are confirmed to be correct and consistent.
-   Any necessary fixes or improvements to routes have corresponding tickets created. 