# {Initiative Name} — PRD

> This is the base template for all Product Requirements Documents.
> Both `prd-writer` and `prd-reviewer` agents reference this file.
>
> **Title**: Replace `{Initiative Name}` with the initiative name. Always use the format `# {Initiative Name} — PRD`.
>
> **How to use**: Copy this template, fill in every Tier 1 section, include section packs listed in project-context.md.
> Delete the `> **GUIDE**` blocks after filling each section.
>
> **Section order**: Context (what, who) → Behavioral Contract (requirements, constants, vocabulary, display rules, verification, edge cases) → Technical Contract (section packs, dependencies, and — in `full` mode only — APIs, mappings, config) → Boundaries (scope, questions) → evidence appendices (project-specific evidence packs, e.g. a custom mobile-baseline pack and the discrepancy section it feeds). Within each area, follow the numbered insertion-point markers for section pack placement. Evidence is not context: an appendix never sits between Context and the Behavioral Contract — every reader would have to scroll past it to reach the contract.
>
> **Separation principle**: The Behavioral Contract describes *what* the system does (observable by users and testers). The Technical Contract describes *how* it's built (readable by engineers). A requirement passes the behavioral test if a QA engineer can verify it without reading source code. See `.claude/rules/behavioral-separation.md` for the full rules.
>
> **Placement rule (governs both contracts)**: *Every number, rule, and policy the user can see or feel lives in the behavioral layer. A value, format, ordering, or policy may never live only in a technical table, a discrepancy row, or scattered pieces the reader has to assemble.* The Technical Contract may repeat such a value; it must never be its only home.
>
> **Technical Contract mode**: `project-context.md` → PRD Configuration → **Technical Contract → Mode** selects `slim` (default) or `full`; a `/create-prd <initiative> --tc full|slim` run override wins over the project setting. In `slim` mode the PRD-owned technical tables below are omitted and the team's technical design owns that content — the PRD still keeps Product Constants, Semantic Vocabulary and Display Rules in the behavioral layer. In `full` mode the PRD also includes the Technical Contract tables (legacy behavior).
>
> **Section packs**: The prd-writer inserts additional sections from `templates/sections/` based on what's listed in `project-context.md`. Each section pack has an `Insert into` tag with a numbered position (e.g., `Insert into: Technical Contract [position: 1]`). Insert packs in ascending position order. Packs sharing the same position number should be inserted in alphabetical order by section name.

---

## Context

### What

> **GUIDE**
> **What**: One sentence describing what the user/system can do after this is built, followed by brief business context.
> **Why**: Forces you to say clearly what is in scope.
> **How**: Start with "Users can..." or "System can..." and describe the end capability. Then add 1-3 sentences of business context (user pain point, compliance need, etc.).
> **Versioning**: If this PRD supersedes a previous version, add a blockquote:
> `> This PRD supersedes [name] v1. The v1 PRD and all related artifacts are obsolete.`

[One sentence: what the user/system can do after this is built]

---

### User Story

> **GUIDE**
> **What**: "As a [role], I want [goal] so that [benefit]."
> **Why**: Keeps the PRD focused on what the user or system gains.
> **How**: One or two user stories max. If you need more, the feature may be too broad.

As a [role], I want [goal] so that [benefit].

---

<!-- Section packs: Context [position: 1] (e.g., user-journey) -->

## Behavioral Contract

> **Notation**: This section uses semantic concept names for data attributes. Each semantic name that maps to an API field is linked via a `[V#]` marker on first use, pointing to a row in the [Semantic Vocabulary](#semantic-vocabulary) table below. Non-API concepts (routing destinations, configuration URLs, client-side state) use consistent semantic names without V-markers; name the destination or setting semantically on first use (e.g., "post-sign-in destination"), and in `full` mode reference the Technical Contract section that maps it.
>
> **Vocabulary files**: If `semantic-vocabulary/` files exist for the endpoints in this initiative, semantic names MUST match the vocabulary entries. For new fields not yet in vocabulary, the writer proposes entries in the handoff file.
>
> **Separation rule**: FRs, ACs, Edge Cases, and Key Entities must describe observable behavior only — decide every phrase with the three generic tests (rename / designer-choice / QA-observability). The canonical allowed and forbidden item lists are the two Quick Reference sections in `.claude/rules/behavioral-separation.md`; read them before drafting.

### Shared Requirements

> **GUIDE**
> **What**: Reference to the project's shared requirements document listing which SRs this feature inherits and any feature-specific overrides.
> **Why**: Cross-cutting requirements live in one place. Restating them here creates a second copy that drifts out of date.
> **How**: List all applicable SR IDs. For overrides or exclusions, explain what's different and why. If the project has no shared requirements document, delete this section.
> **Ownership**: PM-owned. Agents consume but never add new SRs without explicit user approval.

This feature inherits all shared requirements from `docs/shared-requirements.md`:
- [list applicable SR-NN IDs with short labels]

**Feature-specific overrides:**
- [SR-NN]: [describe override and justification, or "N/A — reason"]

---

### Functional Requirements

> **GUIDE**
> **What**: Numbered "System MUST" statements. Each gets a stable ID (FR-001, FR-002, ...).
> **Why**: A short list the reader can scan. FRs answer "what must the system do?"; ACs answer "how do I check it?"
> **How**:
> - Each starts with "System MUST" and describes a single capability.
> - One sentence each. Use semantic concept names with `[V#]` markers on first use.
> - Number sequentially: FR-001, FR-002, etc.
> - Every FR should map to one or more ACs below.
> - Aim for 10-20 FRs. More suggests the scope is too broad.
> **Separation check**: Describe observable behavior only, using semantic names with `[V#]` markers on first use — apply the Quick Reference lists in `.claude/rules/behavioral-separation.md`.

- **FR-001**: System MUST [capability using semantic names with [V#] markers].
- **FR-002**: System MUST [capability].

#### Key Entities

> **GUIDE**
> **What**: Core domain objects this initiative introduces or depends on.
> **Why**: Names domain concepts explicitly. Helps devs name types consistently.
> **How**: One bullet per entity. Include: what it is, format/constraints, how it's used. Reference the vocabulary table for field-level details.
> **Business-level only**: NO language-specific types, NO file paths, NO enum names, NO API field names. Use semantic concept names.

- **[Entity Name]**: [What it is, format, how it's used in this initiative. See the Semantic Vocabulary table for the concept's definition.]

---

### Product Constants

> **GUIDE**
> **What**: Every number the user can notice that the requirements depend on — deadlines, how long data stays fresh, timeouts the user waits through, retry limits, cooldowns, list size limits, thresholds that change behavior. One row each.
> **Why**: This makes the placement rule part of the document's structure. A value that lives only in a technical table is gone when the technical contract goes to the team — and the requirement that depends on it can no longer be built. The value lives here, in the behavioral layer, once.
> **How**:
> - Give every constant a stable ID (PC-001, PC-002, ...) and a semantic name.
> - **Every FR/AC that depends on a bound cites the constant by ID** — `PC-001` — instead of restating the bare number inline. The value appears in this table and nowhere else.
> - Every row must be referenced by at least one FR, AC, or Edge Case. An unreferenced constant is dead spec — delete it (Quality Standard #9).
> - Values the user cannot notice (connection pool sizes, buffer lengths, internal batch sizes) do NOT belong here — they are dev-owned.
> - **Every call to the server has a time limit** — loading data and saving data alike. When one action makes several calls (a save, then a load to check it), say whether the constant limits each call or the whole chain (e.g., "PC-001 limits each call").
> **Both modes**: this section is Tier 1 in `slim` and `full` alike. In `full` mode the Technical Contract may repeat a value; it must never be its only home.

| ID | Constant | Value | What it bounds | Referenced by |
|----|----------|-------|----------------|---------------|
| PC-001 | [semantic name of the bound] | [value with unit] | [which behavior this bounds, and what happens at the limit] | [FR/AC IDs] |

---

### Semantic Vocabulary

> **GUIDE**
> **What**: The concept dictionary for this PRD. One row per semantic concept name used in the behavioral layer with a `[V#]` marker.
> **Why**: The PRD names each idea; the team connects that name to the real API field using the canonical API reference. Naming the idea is the PM's job; connecting it to the API is the team's.
> **How**:
> - V-numbers run in order through the whole PRD and are given only to ideas that come from the API. Never give a V-number to a routing destination, a configuration URL, or client-side state.
> - Copy semantic names from `semantic-vocabulary/` files when they exist; propose new entries in the handoff rather than inventing a competing name.
> - Every `[V#]` marker in the behavioral layer resolves to a row here; every row is used by at least one FR/AC/Edge Case.
> - **Type column (`slim` mode): semantic types only** — `money amount`, `instant`, `string`, `boolean`, `enumeration`, `list of <entity>`, `error signal`. No units, no epoch bases, no encodings: "number (minor units)", "number (epoch milliseconds)", "ISO-8601 string" are facts about the wire format — exactly what the `[V#]` link exists to keep dev-owned. (`full` mode may keep encoded types in the per-endpoint tables.)
> - **Notes hold product meaning** — what a missing value means, which button or action uses it — and point to the Display Rule that owns how it is shown. Facts about the raw format the team must not miss (a unit mismatch, a time value counted differently than the rest of the product) are recorded in the canonical API reference entry for the endpoint, which the row may cite — they are developer warnings, not product vocabulary.
> - **`API Field` is an optional, dev-owned column.** Omit it in `slim` mode. Add it only when the project keeps a PRD-owned technical contract (`Mode: full`) and wants the binding in one place — in that case do not also duplicate the V-numbers in a per-endpoint table.

| V# | Semantic Name | Type | Required | Notes |
|----|---------------|------|----------|-------|
| V1 | [concept name] | [type] | [yes/no] | [what the value means; which distinction the behavior branches on] |

---

### Display Rules

> **GUIDE**
> **What**: One row per value the user sees, stating what decides how it is shown, with a worked example.
> **Why**: A format the user reads is a product decision, not a detail of how the screen is drawn. Timezone, currency and minor-unit handling, symbol-vs-code, ordering, and truncation change what the user believes — they must not live only in a technical table or be left for the developer to guess.
> **How**: For every value the user sees, state the determinant — the fact that decides how it is shown: which clock/timezone a time is shown in, which currency and how minor units are handled, whether the symbol or the ISO code is shown, what the sort key and direction are, where and how text is cut off — then give one concrete worked example (input → what the user sees).
> **Worked examples show the raw format**: use raw wire values as the example input. An example shows the mapping ("`2550` + `usd` → `$25.50`") without owning the contract — it stays true even if the backend later documents the field differently; a rule-style claim ("minor units, divide by 100") does not. This is the one approved home for encoding facts in `slim` mode; the Semantic Vocabulary Type column stays semantic.
> **Coverage**: every value named in an FR or AC that is displayed to a user needs a row. Mark `N/A — no rendered values` for services with no user-facing output.

| ID | Rendered Value | Presentation Determinant | Worked Example |
|----|----------------|--------------------------|----------------|
| DR-001 | [value as the user sees it] | [timezone / currency + minor units / symbol vs code / sort key + direction / truncation rule] | [input → rendered output] |

---

### Acceptance Criteria

> **GUIDE**
> **What**: Checkboxes that a reviewer can verify by using the running application.
> **Why**: The detailed verification spec. If it's not here, it doesn't get built.
> **How**:
> - Every criterion gets a stable ID: AC-001, AC-002, ...
> - Every criterion starts with a user-visible action or state.
> - Must include sub-sections for: Loading States, Error States, Empty States (when applicable).
> **Separation check**: Describe what the user sees and does, using semantic concept names with `[V#]` markers on first use — apply the Quick Reference lists in `.claude/rules/behavioral-separation.md`.

#### [Screen / Flow Area]

- [ ] **AC-001**: [Specific, testable criterion using semantic names with [V#] markers on first use]
- [ ] **AC-002**: [Another criterion]

#### Loading States

> **GUIDE**: What the user/caller sees while processing. Cover three distinct cases:
> - **Initial load**: the screen has no data yet — say that a loading state shows until the data the screen needs has loaded, referencing the shared loading requirement where one exists. What the placeholder looks like is design-owned — no "shaped like the code block and list" instructions.
> - **Background reload with old data on screen**: the saved data is old and a fresh read is running, but the old data is still showing — does the screen keep showing it unchanged (no skeleton, no spinner), or add a loading sign on top?
> - **Background reload fails**: wherever the screen reloads data in the background, include a dedicated AC for the reload failing. Default: keep the old data on screen, fire a `<feature>_refetch_failed` analytics event, do NOT switch to the error state. Make the choice explicit in an AC — do not assume.
> - **While a write is running**: what is disabled, what shows progress?
> For backend services: cover async processing indicators, queue states, or in-flight request states if applicable. Mark `N/A` if the service is purely synchronous with no user-visible wait states.

- [ ] **AC-NNN**: [Loading behavior].

#### Error States

> **GUIDE**: What happens when something fails. Cover: API errors, auth errors, network failures, validation errors.
> Applies to all project types — every system has ways to fail. Describe what each error tells the user; do not write the exact error text.
> - **Transient vs persistent**: When an error state can come both from a passing failure (the service unreachable, rate-limited, or failing) and from a lasting one (an unusable response, a content bug), either (a) state that each class gets its own message intent, OR (b) say explicitly in the PRD body that one generic message is intentional, and why. Relying on a generic message silently is a defect.

- [ ] **AC-NNN**: [Error behavior].

#### Empty States

> **GUIDE**: What happens when there's no data. Only include if the feature has data lists or query results that can be empty.
> For backend services with no user-facing data display: mark `N/A` and remove this sub-section. Do not write the exact empty-state text.

- [ ] **AC-NNN**: [Empty state behavior].

---

<!-- Section packs: Behavioral Contract — after Acceptance Criteria [position: 1] (e.g., analytics-events) -->

### Edge Cases

> **GUIDE**
> **What**: Boundary conditions, nullable fields, concurrent actions, ways to fail.
> **Why**: Edge cases are where bugs live. The #1 complaint about AI-generated PRDs is missing edge cases.
> **How**: Generate them mechanically, not from gut feeling. For each Key Entity, run through: missing, empty, smallest allowed, largest allowed, just past the limit, wrong format, old data, and how it is shown (timezone, currency, order, cut-off text). For each API endpoint: network failure, timeout, session expiry, rate limit, partial response, two changes at once. For each conditional FR: the condition cannot be decided, the condition changes mid-flow. Then merge duplicates and remove impossible cases.
> **Separation check**: Use semantic names with `[V#]` markers where applicable. Edge cases can be slightly more specific than FRs/ACs (they describe concrete data scenarios), but the same separation rule applies — see the Quick Reference lists in `.claude/rules/behavioral-separation.md`.

| # | Condition | Expected Behavior |
|---|-----------|-------------------|
| 1 | [condition] | [behavior] |

---

### Feature Flags / Remote Config

> **GUIDE**: Feature flags, remote config, rollout settings. If the feature ships with no flag and no remote config, OMIT this section and record it in the handoff's `consideredNA` list instead (see the prd-writer spec) — a table saying "None" is dead text.

| Field | Value |
|-------|-------|
| **Flag name** | [name or "None"] |
| **Fallback** | [behavior when flag is off] |

---

<!-- Section packs: Behavioral Contract — after Edge Cases [position: 1] (e.g., accessibility, compliance, platform-considerations); in `slim` mode also [position: 4] screen-flow + navigation (responsive-layout and design-prototype are `full`-mode only) -->

## Technical Contract

> **Tier 2 — condition**: the project keeps a PRD-owned technical contract (`Technical Contract → Mode: full` in `project-context.md`, or a `--tc full` run override). This ENTIRE section — heading included — exists **only** in `full` mode; in `slim` mode DELETE it completely.
>
> In `slim` mode every piece of content still has a home: Dependencies lives in Boundaries (both modes), the user-facing section packs (screen-flow, navigation) insert into the Behavioral Contract per their `slim` insertion tags, and the implementation packs (component-mapping, database-changes, service-integration, monitoring) are `full`-mode only — as are responsive-layout (the responsive shared requirement owns the works-at-every-breakpoint baseline, arrangement is design-owned, and a width-specific product difference is an ordinary FR/AC) and design-prototype (the PRD says nothing about design readiness — whether a design exists yet is workflow state the pipeline and the team own, and a design gap lives as a `ds-gap` issue on GitHub, not as a PRD row). Content that is *purely* implementation reference is **dev-owned by default**: component paths, configuration attributes, mock data, error-code-to-class mappings, query/cache configuration, route constants, and API request/response shapes live in the team's technical design, not in the PRD. A PRD is not incomplete for leaving them out.
>
> The behavioral anchors stay in the Behavioral Contract in both modes: **Product Constants**, **Semantic Vocabulary**, **Display Rules**. Never move a number, format, ordering, or policy the user can notice down here — this section may repeat one, but it may never be its only home.
>
> **Organization (`full` mode)**:
> 1. Cross-cutting tables — Data Sources, Query Configuration, Error Classification, Route Mapping
> 2. Per-endpoint blocks — Vocabulary table (V-numbered rows binding semantic names to API fields) + Error Handling
> 3. UI/config sections — Component Mapping, Visual References, etc. (the exact user-facing words, localization keys, and translations are design-owned — not a PRD section)
>
> In `full` mode the per-endpoint Vocabulary tables hold the API-field binding for the same V-numbers defined in the Semantic Vocabulary table. Repeating a V-number across the two layers is expected; splitting the set across them is not — every marker must resolve in both places or in the Semantic Vocabulary table alone.

<!-- PRD-owned technical content — `full` mode only. In `slim` mode delete every sub-section from here through Configuration Attributes, keeping the section packs and Dependencies. -->

### Data Sources

> **GUIDE**
> **What**: Every API endpoint this initiative consumes or exposes, with full URL patterns, methods, auth, and canonical reference links.

| ID | Semantic Name | Endpoint | Method | Full URL Pattern | Canonical Ref | Auth |
|---|---|---|---|---|---|---|
| DS-001 | [name] | `METHOD /path` | [METHOD] | `<BASE_URL>/path` | [link] | [auth method] |

---

### Query Configuration

> **GUIDE**
> **What**: Cache/query settings for each data source. One row per data source.

| Data Source | Query Key | staleTime | retry | Invalidation Trigger | Owner |
|---|---|---|---|---|---|
| DS-001 | `['key']` | [value] | [value] | [trigger] | [owner] |

---

### Error Classification

> **GUIDE**
> **What**: How errors are categorized for analytics and UI behavior. Defined once, referenced by all error-handling ACs.

| Error Class | Condition | error_status_code | failure_reason | UI Behavior |
|---|---|---|---|---|
| Transport error | [when] | 0 | `transport_failure` | [behavior] |
| HTTP error | [when] | [real HTTP code] | [specific reason] | [behavior] |
| Schema validation failure | [when] | 200 | `malformed_json` | [behavior] |
| Content-incomplete | [when] | 200 | `required_field_missing` | [behavior] |

> **Distinctness rule**: Every `(error_status_code, failure_reason)` tuple in this table MUST be unique. If two error classes share the same HTTP status, they MUST have distinct `failure_reason` values. Specifically:
> - Guard-triggered failures (duplicate cursor, loop detection, client-side validation) must NOT reuse a `failure_reason` already assigned to a server-returned error class.
> - "Structurally valid but content-incomplete" (HTTP 200, required field empty/null) is distinct from "schema validation failure" (malformed JSON). Never collapse both into a single `parse_error`.
> - For numeric `error_status_code`: `0` for transport failures, real HTTP codes for HTTP responses. Use `failure_reason` to disambiguate within a status code.

---

### Route Mapping

> **GUIDE**
> **What**: Maps semantic destination names (used in behavioral layer) to actual URLs and code constants.

| Behavioral Description | URL | Code Constant |
|---|---|---|
| [semantic name used in FRs/ACs] | `/path` | `code.constant()` |

---

### [Endpoint Name]

> **GUIDE**
> **What**: Per-endpoint detail block. Create one of these for each data source.

#### Vocabulary

> **GUIDE**: `full` mode only. Binds the semantic concept names defined in the [Semantic Vocabulary](#semantic-vocabulary) table to actual API fields, per endpoint. Reuse the same V-numbers — this table repeats them with their field binding, it does not define a second set. Copy entries from vocabulary files (`semantic-vocabulary/`) when they exist; add new rows for fields not yet mapped.

| V# | Semantic Name | API Field | Type | Required | Notes |
|----|---------------|-----------|------|----------|-------|
| V1 | [concept name] | `field_name` | [type] | [yes/no] | [optional clarification] |

#### Error Handling

| HTTP Status | Behavior |
|-------------|----------|
| 401 | [behavior] |
| 4xx / 5xx / network | [behavior] |
| 200 with malformed body | [behavior] |

---

### Configuration Attributes

> **GUIDE**: Environment-specific config (base URLs, API prefixes, application IDs, timeout values, etc.).
> PRDs MUST NOT hardcode base URLs or environment-specific hostnames in endpoint specifications. Endpoint paths in the Technical section MUST be specified relative to a named configuration attribute (e.g., "`<ORDERS_API_BASE_URL>/v1/orders`" rather than "`/v1/orders`" or "`api-dev.example.com/orders-service/v1/orders`"). This makes it explicit which client/prefix each endpoint belongs to and eliminates environment-switching guesswork.

| Attribute | Description | Example value (dev) |
|-----------|-------------|---------------------|
| `<BASE_URL>` | [description] | [example] |

---

<!-- Section packs (`full` mode): Technical Contract [position: 1] — UI structure (component-mapping, responsive-layout) -->
<!-- Section packs (`full` mode): Technical Contract [position: 2] — content & visuals (design-prototype) -->
<!-- Section packs (`full` mode): Technical Contract [position: 3] — navigation & flow (screen-flow, navigation) -->
<!-- Section packs (`full` mode): Technical Contract [position: 4] — infrastructure (database-changes, service-integration, monitoring) -->

## Boundaries

> **Sub-section order**: Always use this order: Dependencies → Out of Scope → Assumptions → [section packs: position 1] → Open Questions.
> Section packs inserted into Boundaries go between Assumptions and Open Questions, in position order.
> The PRD body has no list of omitted sections — no reader builds from a list of absences. Conditional sections whose trigger is absent are LEFT OUT of the document and recorded in the writer handoff's `consideredNA` field instead (see the prd-writer spec); the reviewer checks that record, not a PRD section.

### Dependencies

> **GUIDE**
> **What**: Product-level blockers the reader must know about — another initiative that must ship first, a backend capability that must exist, a deliverable that must arrive (for example, the final wording from the content team).
> **Not here**: Developer and pipeline work items — an entry to add to the canonical API reference, package or route work, and the status of any tracked issue. Design readiness is not tracked here either: whether a design exists yet is workflow state the pipeline and the team own, and a design gap lives as a `ds-gap` issue on GitHub — the pipeline files it, and the PRD does not track or restate its status. One home per fact: a dependency already recorded as an Assumption (an unverified fact) is not repeated as a row here.
> **Both modes**: Dependencies is a product fact (a blocked initiative), not implementation reference — it lives here in `slim` and `full` mode alike.

| Dependency | Source | Status |
|-----------|--------|--------|
| [what] | [where it comes from] | [Merged / In Progress / Blocked] |

---

### Out of Scope

> **GUIDE**
> **What**: Things explicitly NOT part of this initiative. AI agents cannot infer boundaries from omission.

- **OS-001**: **[Feature/behavior]** — [reason]

---

### Assumptions

> **GUIDE**
> **What**: Conditions that must be true for this PRD to be valid but are not verified by the system. If an assumption breaks, the PRD is silently wrong.
> **Why**: Open Questions capture "what we don't know." Assumptions capture "what we think we know that could be wrong." A broken assumption doesn't cause a build error — it causes wrong behavior that passes all tests.
> **How**: For each assumption, state: (1) what you're assuming, (2) where the assumption came from (code observation, API docs, verbal confirmation, convention), (3) what breaks if the assumption is wrong. If you can verify an assumption during research, do so and remove it. Only assumptions that cannot be verified at spec-writing time belong here.
>
> **Examples across stacks**:
> - Frontend: "API always returns ISO 4217 currency codes — if it returns free-text, the currency formatter throws"
> - Backend stateless: "Upstream service responds within 2s — if slower, our 5s timeout fires and the client retries"
> - Backend stateful: "Table row count stays under 10M for year 1 — if exceeded, the unindexed query in the reporting endpoint degrades"

| ID | Assumption | Source | Impact if Wrong |
|----|-----------|--------|-----------------|
| ASM-001 | [what we're assuming] | [code / API docs / verbal / convention] | [what breaks] |

---

<!-- Section packs: Boundaries [position: 1] (e.g., cross-initiative-alignment) -->

### Open Questions

> **GUIDE**
> **What**: Must be EMPTY before approval. During drafting, list questions here with a resolution method tag so reviewers know HOW to get the answer. Resolve each by researching or asking the user, then move the decision into the relevant section.
>
> **Resolution method tags:**
> - `ASK:role` — needs a human answer (PM, design, backend, legal, etc.)
> - `CHECK:source` — answer exists somewhere, go look (analytics, docs, code, competitor)
> - `TEST:env` — requires running/testing something (staging, prod)
>
> **Format**: `- OQ-N [METHOD:target]: question`

None — all questions resolved.

<!-- Section packs: Evidence appendices — end of document, after Boundaries [position: 1] (e.g., a custom mobile-baseline pack). An evidence appendix holds at most: a pinned source-repo SHA line, a summary of at most 3 sentences, and ONE match/diverge/skip decision table whose rows hold the discrepancy IDs (e.g., MA-###), with source-code citations only in its Source column — never in prose. There is no separate flagged-discrepancies section: the appendix table holds those decisions, and the project's central discrepancy catalog stays the mirror authority for the IDs (registry lockstep). Everything longer lives in the research document. Decision-row IDs are position-independent, so FR/AC references to them are unaffected by the appendix placement. -->

## Tier 2 — Include When Applicable

> Include these when conditions apply. Each has an **Insert into** tag.
> **How to use**: When the condition applies, MOVE the section to its insertion point (specified by the `Insert into` tag) — do not leave it here at the bottom. When the condition does not apply, DELETE the section entirely and record it in the writer handoff's `consideredNA` list — never leave an N/A prose block in its place.

---

### Test Coverage

> **Insert into**: Behavioral Contract — after Acceptance Criteria [position: 2]

> **GUIDE**
> **When**: `full` mode only — any PRD whose ACs will be handed to an implementer (omit only for exploratory drafts nobody will build from).
> **What**: How each acceptance criterion gets verified, and how states that cannot occur naturally in a test environment are produced.
> **Slim mode**: leave this section out entirely, and do not list it in the handoff's `consideredNA` — the test plan is the QA lead's document, not a product section this PRD considered and dropped. What the PM still owes in slim mode: every AC is phrased so a tester can check it by using the running app.
> **How**: Bind every AC (or AC group) to a verification approach — unit / integration / E2E where a UI exists; unit / integration / contract for backend services (E2E is not required where no UI exists) — or designate it `manual` with its trigger described. An AC that no test type claims and no manual designation covers will silently not be verified. Add an environment-override row for every state a test must be able to force but that cannot occur naturally (a denied permission, an absent platform capability, a dismissed native sheet).

| AC / AC group | Verification | Notes |
|---|---|---|
| AC-001..AC-004 | integration | |
| AC-012 | manual | native share sheet cannot be automated; tester dismisses it by hand |

**Environment overrides** — states a test must be able to force:

| State | How the test produces it |
|---|---|
| clipboard write denied | deny the permission in the test context |
| share unavailable | run in a context where the platform share entry point is absent |

---

### Success Criteria

> **Insert into**: Behavioral Contract — after Edge Cases [position: 1]

> **GUIDE**
> **When**: Features with user-facing flows where quality bar matters.
> **What**: Measurable outcomes that define how *well* the feature should work.

- **SC-001**: [Measurable outcome]

---

### Security Constraints

> **Insert into**: Behavioral Contract — after Edge Cases [position: 1]

> **GUIDE**
> **When**: Any feature that reads, displays, transmits, or stores auth tokens, PII (names, phone numbers, emails, avatars, account numbers), payment data, or sensitive state. "Touching" includes read-only display — a dashboard showing user names and passing customer data via router state triggers this section.
> **What**: Security requirements specific to this initiative — what must NOT be logged, exposed in URLs, persisted in browser storage, or sent in analytics.

---

### Support / Observability

> **Insert into**: Behavioral Contract — after Edge Cases [position: 1]

> **GUIDE**
> **When**: Features with failure states the user sees no sign of (e.g., silent background failures), OR features that show one identical message for several different underlying problems.
> **What**: Symptom-to-query mappings for support engineers. This section is MANDATORY when any of these conditions hold.
>
> **Required sub-sections**:
>
> 1. **Silent-state workflows**: For every FR/AC with "fail silently" / "silently suppress" / "no visible change" behavior, include: (a) the analytics event that is the SOLE signal of this state, (b) the user-reported symptom that should trigger a proactive support query, (c) explicit note: "this state has no UI signal — query [event] using user_id + timestamp window."
>
> 2. **One message, several causes**: For every page state where several different problems produce the same user-facing message, include: (a) the phrase a user would use when reporting it, (b) the analytics query to find the user + time window, (c) for each underlying problem, what support does about it, (d) either something visible in the UI that tells the causes apart (error code, correlation ID) OR explicit documentation of the analytics-based support workflow.
>
> 3. **Multi-gated suppression**: When a UI element has multiple gates that can suppress it, include a single internal analytics event with a discriminator (`reason` enum) covering every suppression path.
>
> 4. **Cross-initiative hand-offs**: When a silent state's analytics is delegated to another initiative, name (a) the specific event name, (b) the specific property/sentinel, (c) the symptom-to-query mapping. Soft hand-offs without a named event are insufficient — log as an Open Question if the owning initiative hasn't defined the event yet.
>
> **Name failures by what they mean, not by HTTP code (`slim` mode)**: support workflows use the failure classes on the analytics events (`unreachable | rejected | unusable_response | incomplete_record`, or the initiative's equivalents) and say what support DOES for each class. Never build a workflow on reading HTTP codes ("`error_status_code: 200` + `parse_error` → escalate") — turning a wire observation into a class is the developers' job, and finer detail lives in the dev-owned diagnostic properties documented in the analytics catalog.

---

### Cross-Initiative Alignment Notes

> **Insert into**: Boundaries [position: 1]

> **GUIDE**
> **When**: Feature overlaps with or depends on other initiatives.
> **What**: What's shared, what to be careful about, sequencing notes.
