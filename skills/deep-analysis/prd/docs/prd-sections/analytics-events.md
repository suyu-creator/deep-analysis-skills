# Section Pack: Analytics Events

> **Insert into**: Behavioral Contract — after Acceptance Criteria [position: 1]
> **When**: Any feature that should be tracked with analytics events.
> **Separation note**: This table is the source of truth for event names and properties. FRs and ACs in the Behavioral Contract reference events using semantic trigger names (e.g., "the page-viewed analytics event") — not raw event names. The table itself holds the actual `event_name` values.

#### Analytics Events

> **GUIDE**
> **What**: All analytics events for this feature — view events and interaction events.
> **Why**: Every screen/page must fire a view event so user journeys are readable in analytics tools.
> **How**:
> - Follow the naming convention established in the codebase (check project-context.md or existing events)
> - Every screen/page MUST have a view event
> - Interaction events track what users do (taps, submissions, errors)
> - Include event properties when relevant
> - Check existing events in the codebase first to avoid duplicates
> - Every event gets a stable ID: AE-001, AE-002, ...
> - **Failure classes are semantic (`slim` mode)**: property values are product-semantic enums — outcomes (`copied | failed`), failure classes named by what they mean to support/product (`unreachable | rejected | unusable_response | incomplete_record`), suppression reasons. No HTTP status numbers, no status-encoding rules ("`0` for transport failure", "`200` for a success response that could not be interpreted"), no wire-level class names (`transport`, `http_error`, `parse_error`, `error_status_code`). A failure class earns a property value because support treats it differently — how each class is detected and encoded on the wire is dev-owned. If a class cannot be named without HTTP vocabulary, it is dev-owned diagnostics, not a PRD property.
> - When failure classes are used, add one dev-owned note under the table in place of any encoding rules: teams may attach additional diagnostic properties (status codes, correlation identifiers, precise error causes); their naming and encoding, and the mapping from wire observations to the semantic classes, are dev-owned and documented in the analytics catalog, not the PRD.
> - If the project maintains a central analytics event catalog (see Registry-Mirrored Catalogs in project-context.md), mirror every event addition, property change, and removal into the catalog in the same PRD edit — the lockstep applies to property updates and removals, not just new event names
>
> **AC-binding rules** (writer):
> - When an AC fires an analytics event, the AC MUST list every required property on that event, matching the Properties column in this table exactly. Whenever this table is updated, grep every AC referencing that event and update the AC's property list in the same edit.
> - For every analytics event whose Trigger describes a successful data outcome (not just a user interaction), add an AC binding the event by name and listing every property. If any event in this table is named by zero ACs, nothing will ever test it.
> - ACs MUST reference events by AE-number (e.g., "fires AE-001"), NOT by literal event name inline. This table is the single source of truth for event names and properties; the AC asserts when the event fires and under what conditions.

| # | Event Name | Trigger | Properties | Description |
|---|---|---|---|---|
| AE-001 | `[event_name]` | [Screen becomes visible] | [properties] | [Screen view event] |
| AE-002 | `[event_name]` | [User action] | [properties] | [Interaction event] |
