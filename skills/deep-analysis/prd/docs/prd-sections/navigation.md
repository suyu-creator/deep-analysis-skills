# Section Pack: Navigation

> **Insert into**: Technical Contract [position: 3] (`full` mode) / Behavioral Contract — after Edge Cases [position: 4] (`slim` mode)
> **When**: Any feature with user-facing navigation — screens, pages, routes.

### Navigation

> **GUIDE**
> **What**: How users reach this feature and how they leave it.
> **Why**: Without explicit navigation specs, devs guess at entry points, back behavior, and deep link support.
> **Slim mode — product facts only**: state that the screen has a stable, purpose-named authenticated route and that direct navigation (bookmark, pasted address, browser history) behaves per the gate FRs. The concrete path, the path constant, the routing file, and any route-file cleanup (dead constants to delete) are dev-owned — cleanup items go to implementation tickets, not PRD prose. In `full` mode the concrete path maps in Route Mapping.

#### Entry Points

- [How users reach this feature — e.g., "Tap 'New Order' on Dashboard" or "Navigate to /settings/notifications"]

#### Back / Dismiss Behavior

- [What happens on back press / browser back at each step]

#### Deep Links

- [URI pattern if applicable, or "Not applicable"]
