# Ticket: Review RemoteController Scope

**Priority:** P3
**Status:** To Do

**Description:**
The `RemoteController` (`src/controllers/remote_controller.py`), primarily focused on managing the Cloudflare Tunnel process, includes a `get_connected_players` method. This method seems slightly out of scope for a controller dedicated to the tunnel infrastructure itself. Evaluate if this functionality is better placed in a more relevant controller.

**Relevant Files:**
-   `src/controllers/remote_controller.py`
-   `src/routes/remote_routes.py` (uses the method in `/api/remote/players`)
-   `src/controllers/socket_controller.py` (manages `connected_players` state)
-   `src/controllers/admin_controller.py` (handles other admin info retrieval)

**Tasks:**
1.  Analyze the purpose and implementation of `RemoteController.get_connected_players`.
2.  Determine the most logical location for this functionality, considering:
    -   `SocketController`: Already manages the `connected_players` data structure.
    -   `AdminController`: Provides other administrative views and information.
    -   Keep in `RemoteController`: If there's a strong argument for it being tightly coupled to remote play management.
3.  Refactor the code to move the method and its usage (in `remote_routes.py`) to the chosen controller if necessary.
4.  Update relevant documentation or comments.

**Acceptance Criteria:**
-   The `get_connected_players` functionality resides in the most appropriate controller based on architectural principles (separation of concerns, cohesion).
-   The `/api/remote/players` route correctly calls the method from its new location (if moved). 