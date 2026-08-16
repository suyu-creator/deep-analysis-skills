# Behavioral/Technical Separation

PRDs MUST separate behavioral requirements from technical implementation details into two distinct sections: the **Behavioral Contract** and the **Technical Contract**.

## Core Principle

A requirement passes the behavioral test if a QA engineer can verify it without reading source code. QA verification includes dev tools (network, storage, console inspection) — a requirement verifiable that way is still behavioral, even if it sounds technical. CS jargon that describes testable behavior should be rephrased to how QA would actually verify it, but it stays in the Behavioral Contract.

Decide whether a phrase belongs in the behavioral layer with three generic tests. They work on any platform — web, mobile, backend — without needing a list of examples, so do NOT decide by matching a phrase against known-bad samples; apply the test:

1. **Rename test** — would the requirement break if a developer renamed an API field, endpoint, status code, header, config key, or localization key, even though the observable behavior is unchanged? If yes, it is technical → move it to the Technical Contract and reference it by semantic name.
2. **Designer-choice test** — could a designer present the same behavior with a different component, layout, emphasis, or visual treatment? If yes, the phrase is a design decision → remove it; describe what the user sees, learns, or does instead. This applies regardless of platform; see "Quick Reference: Forbidden in the Behavioral Layer" for what counts.
3. **QA-observability test** — can a tester confirm it purely by using the running app, with no knowledge of how it is built or stored? If no, it is an implementation detail → move it to the Technical Contract; do not reword it into the behavioral layer.

**Placement rule — the value axis, decided before the three tests.** *Every number, rule, and policy the user can see or feel lives in the behavioral layer. A constant, format, ordering, or policy may never live only in a technical table, a discrepancy row, or a section the reader has to reconstruct it from.* The three tests above exclude **wire vocabulary and mechanism**, never values the user perceives: a field name, endpoint path, status code, header or config key is technical; a timeout the user waits through, a money format they read, and a sort order they see are not. When a test fires on a user-perceivable value, the remedy is a **Product Constants** row (bounds), a **Display Rules** row (rendered formats, ordering, truncation) or a **Semantic Vocabulary** row (concept names) — all three in the Behavioral Contract. The Technical Contract may repeat such a value; it may never be its only home, because it is optional (see "Technical Contract" below) and goes to the team with the technical design.

**Product-requirement carve-out:** when the mechanic *is* the product requirement, it stays in the behavioral layer even if it names UI or input mechanics. The test: is this a PM decision about *what the product does*, or a designer/engineer decision about *how it is rendered or built*? Only the former belongs here. The full carve-out list is in "Quick Reference: Allowed in the Behavioral Layer" below.

## Quick Reference: Allowed in the Behavioral Layer

This is the single canonical carve-out list. Every other framework file points here instead of restating it. These items are product requirements, not design or implementation decisions — do NOT flag them.

- **Interaction patterns that *are* the requirement** — drag-to-reorder ("drag to reorder"), swipe-to-dismiss.
- **Input/output mechanics that define the product** — "accepts only a 6-digit numeric code".
- **Shipped design-system component names** — carousel, skeleton, bottom sheet — when the PM explicitly chose them because the DS ships that component.
- **Behavioral placement** — "inline beneath the input", "near the triggering element". These say where the user sees feedback and distinguish feedback strategies (field-level vs page-level). Only placement that prescribes CSS positioning is forbidden (see the Forbidden list).
- **PM-decided display formats** — "MM:SS", "0:30", "zero-padded".
- **Constants the user can notice** — deadlines, how long data may stay unrefreshed, timeouts the user waits through, retry limits, cooldowns, list ceilings, behavior thresholds. These live in **Product Constants** and are cited by ID from the FR/AC that depends on them; never relocate one to a technical table.
- **Presentation determinants for rendered values** — timezone, currency and minor-unit handling, symbol vs code, sort key and direction, truncation rule. These live in **Display Rules** with a worked example.
- **Perceivable outcomes and their priority** — "announced to assistive technology when it appears", "must not lose the keyboard user's place", "the same information is available at both breakpoints", "the no-data state is the primary state and is designed first". Outcomes and priorities are product calls; the treatment that achieves them (ordering, shape, politeness level, focus target) is design-owned — see the design-mechanism item in the Forbidden list.
- **User-visible navigation** — "new browser tab".
- **Platform concepts** — "browser's one-time-code autofill", "device identifier header", "browser's reported language".
- **Generic UI vocabulary used without a visual qualifier** — button, link, input, field, error message, page, screen, form, list, item, section, label, text, header, tab, menu, notification, dialog, alert, indicator, grid.
- **Enum values in analytics ACs** — allowed when they make the AC testable. In `slim` mode the enum members must themselves be semantic classes, not wire taxonomy (see the transport-taxonomy item in the Forbidden list).
- **Product decisions and platform concepts that sound technical** — "replacing the current history entry", "proactive refresh". Acceptable as-is; these describe what the system does, not how it is built.
- **CS jargon describing testable behavior** — "atomically replace", "first-expiry-wins", "single shared in-flight refresh", "invalidate the cached user profile". Verifiable with dev tools, so these stay in the Behavioral Contract — but rephrase them to how QA would actually verify the behavior. Flag for **rephrasing in place**, never for relocation to the Technical Contract.
- **Exact wording mandated by law, compliance, or contract** — quoted verbatim as a constraint with its source cited. This is the only place exact user-facing words are allowed in requirements.
- **Analytics event names and property values** — a data contract, not user-facing wording, so they remain in the PRD (in the Analytics Events table). ACs reference them semantically; a raw event name inline in an FR/AC is still forbidden.

## Quick Reference: Forbidden in the Behavioral Layer

This is the single canonical forbidden list. Apply the three tests above rather than matching text against these examples — the examples illustrate the tests, they do not bound them.

- **API vocabulary and wire details** (rename test) — API field names, enum wire values, endpoint paths and URL patterns, query keys, HTTP status codes, header names, analytics event names inline in FRs/ACs, constructor signatures. Replace with semantic concept names with `[V#]` markers, semantic destinations ("the order details page"), and semantic outcomes ("when the backend rate-limits further attempts"). Paths map in Route Mapping; status codes and headers map in Error Classification / per-endpoint Error Handling.
- **Code wiring in the PRD (`slim` mode)** (rename test) — literal route paths and path constants (`paths.inviteFriends`, a config-file path), repo file paths (`src/…`, `packages/…`, `.ts`/`.tsx` files), DS components cited by file path or internal props, component class names where an SR alias exists, per-endpoint path/method tables, and dead-code cleanup instructions. Route naming, constants, component wiring, and cleanup are implementation work items. A repo path or code identifier may appear only inside (a) a `ds-gap` / `api-canonical-gap` issue reference, (b) a Boundaries → Dependencies row where a product-level blocker is itself a code artifact (a backend capability that must exist first — never ordinary package or route work), or (c) a commit-pinned evidence permalink. Everywhere else name the concept: "a stable, purpose-named authenticated route", the DS component's name, the SR id for a shared shell or loading baseline, one prose sentence for a flow's reads/writes with a pointer to the canonical API reference (the endpoint inventory lives in the research document).
- **Wire encodings in Semantic Vocabulary types (`slim` mode)** (rename test) — Type cells that hold units, epoch bases, or encodings: "number (minor units)", "number (epoch milliseconds)", "ISO-8601 string". Types are semantic — `money amount`, `instant`, `string`, `boolean`, `enumeration`, `list of <entity>`, `error signal`. Notes hold product semantics and point at the Display Rule that owns the rendering; encoding facts the team must not miss (unit mismatches, epoch-base traps) are recorded in the canonical API reference entry the row may cite. Display Rules worked examples keep using raw wire values as input — an example shows the mapping without owning the contract, so it is the one approved home for encoding facts. (`full` mode may keep encoded types in the per-endpoint tables.)
- **Transport taxonomy in analytics properties (`slim` mode)** (rename test) — an `error_status_code`-style property, status-number encoding rules ("`0` for transport failure", "`200` for a success response that could not be interpreted"), and wire-level failure classes (`transport`, `http_error`, `parse_error`) in the Analytics Events or Support sections. Analytics property values are product-semantic enums: outcomes, suppression reasons, and failure classes named by what they mean to support (`unreachable | rejected | unusable_response | incomplete_record`). A class that cannot be named without HTTP vocabulary is dev-owned diagnostics, not a PRD property — teams may attach diagnostic properties (status codes, correlation identifiers) whose naming, encoding, and wire-to-class mapping are dev-owned and documented in the analytics catalog. Support workflows reference the semantic classes and say what support does per class.
- **Literal user-facing text and localization keys** — headings, body text, button labels, toasts, error/empty-state text, and any localization-key path. The exact words are design-owned; say what the message must tell the user instead. Sole exception: wording mandated by law or contract (see the Allowed list).
- **Design decisions** (designer-choice test):
  - **Emphasis/variant qualifiers** — "primary, filled button", "tonal", "outlined".
  - **Layout arrangements that prescribe CSS structure** — sticky, full-surface, grid-3-column, fixed/absolute positioning.
  - **Visual treatments** — pixel values, color variants, spacing tokens, breakpoints.
  - **Over-specified ACs (altitude)** — an AC that enumerates several visual elements or reads as a screen layout is a design spec, not a behavioral criterion. That furniture belongs to the design source (the Visual References section in `full` mode; the design itself in `slim` mode) and the Screen Flow section; the AC should assert one observable outcome.
  - **Design-mechanism prescriptions (`slim` mode — same violation class as wire leaks)** — content ordering and stacking ("renders as a single column", "stacked in that order"), skeleton/placeholder composition ("shaped like the code block, total and list"), live-region politeness levels ("confirmations announce politely, failures announce assertively"), and focus targets or choreography ("focus lands at the start of the content", "focus stays on the retry affordance"). The PRD states **outcomes the user can perceive, and their priority** — a state is the main one and is designed first, announcements happen, the keyboard user does not lose their place, nothing requires horizontal scrolling — never the **treatment** that achieves them; the treatment belongs to design/dev under the relevant shared-requirement baseline or `ds-gap` issue. A focus rule is allowed only as an outcome ("an ignored repeat activation must not trap or move keyboard focus" passes; "focus stays on the retry button" does not).
- **Framework terminology — three tiers, three different remedies**:
  1. **Library/framework-specific terms** (library names, config keys) — "query invalidation", "staleTime", "React Router state", "Zod schema validation", "Axios interceptor" → **relocate** to the Technical Contract and restate the behavior observably ("data refreshes after successful mutations").
  2. **CS jargon describing testable behavior** → **rephrase in place**; it stays in the Behavioral Contract (see the Allowed list). Never relocate it to the Technical Contract.
  3. **Product decisions that sound technical** → **allowed as-is** (see the Allowed list). Do not flag.
- **Implementation mechanism** (QA-observability test) — *where or how* a value is stored or transported: secure-storage backend, keystore/keychain, encryption scheme, caching layer, transport protocol. Move it to the Technical Contract; do NOT reword it into an FR/AC.

## Copy and Localization Are Design-Owned

The final user-facing text (the exact words the user reads), localization keys, and translations are **design deliverables**, produced with or after design — they are NOT part of the PRD. The PRD specifies copy *intent per state*: which states need a message and what each message must tell the user (e.g. "show an error explaining the entered codes did not match and prompting a retry"), never the exact string, the localization key, or the translation.

**Completeness, not wording:** the PRD must still enumerate every state that needs a message (error, empty, success, loading) so design knows what copy to produce. Drop the words, keep the coverage.

**Exception — mandated wording:** when exact wording is dictated by law, compliance, or contract (regulatory disclosures, legal terms), it stays in the PRD as a constraint, with its source cited, and design must use it verbatim. This is the only case where exact wording appears in requirements. (Analytics event names and property values are a data contract, not user-facing wording — they remain in the PRD regardless.)

## Behavioral Contract

Contains: FRs, ACs, Edge Cases, Key Entities, **Product Constants**, **Semantic Vocabulary**, **Display Rules**, Feature Flags, Success Criteria, Security, Accessibility, Compliance, Support/Observability. The three bolded sections are Tier 1 in both Technical Contract modes — they are what keeps a PRD buildable when the technical contract is not part of it.

Rules for this layer:
- Use **semantic concept names** for data attributes (e.g., "order identifier" not `order_id`)
- Add **`[V#]` markers** on first use of each semantic name, linking it to the vocabulary table in the Technical Contract
- Each semantic name maps to exactly one API field — if ambiguous, make it more specific
- **Use vocabulary files when they exist** — if `semantic-vocabulary/` contains a file for an endpoint, use the semantic names defined there. Do not invent alternatives for fields that already have vocabulary entries. See `rules/semantic-vocabulary.md`
- **Never include API vocabulary, wire details, framework terminology, or implementation mechanism**: apply the rename and QA-observability tests — see "Quick Reference: Forbidden in the Behavioral Layer" for the canonical list and the per-tier remedy (relocate / rephrase in place / allowed as-is)
- **Never make design decisions**: describe what the user sees, learns, or does — let design decide how to render it. Apply the designer-choice test; the forbidden items are in "Quick Reference: Forbidden in the Behavioral Layer" and the product-language exceptions in "Quick Reference: Allowed in the Behavioral Layer"

## Technical Contract

**Optional — `slim` (default) or `full`.** `project-context.md` → PRD Configuration → Technical Contract → **Mode** selects it, and a `/create-prd … --tc` run override wins. In `slim` mode the PRD-owned technical content is dev-owned: it lives in the team's technical design, and a PRD is not incomplete for omitting it. In `full` mode the PRD includes it (legacy behavior).

Contains (in `full` mode): Data Sources, Query Configuration, Error Classification, Route Mapping, per-endpoint Vocabulary tables + Error Handling, Component Mapping, Visual References, Screen Flow, mock-data sections, Configuration Attributes, Dependencies. In `slim` mode only Dependencies and the section packs that insert here remain. (Copy, localization keys, and translations are NOT here — they are design deliverables; see "Copy and Localization Are Design-Owned" above.)

Rules for this layer:
- **Cross-cutting concerns defined once**: Error classification, query config, route mapping each live in one table as implementation reference
- **Per-endpoint blocks** include: Vocabulary table (V-numbered rows mapping semantic names to API fields) and Error Handling (HTTP status → behavior)

## `[V#]` Vocabulary References

FRs and ACs use `[V#]` markers to link semantic names to their definitions: the **Semantic Vocabulary** table in the Behavioral Contract, which every PRD includes, and — in `full` mode — the per-endpoint vocabulary tables inside the Technical Contract that bind the same V-numbers to API fields. Repeating a V-number across the two layers is expected; splitting the set across them is not.

**Scope**: V-numbers are exclusively for API field mappings — concepts that resolve to a field in an endpoint's request or response. Non-API concepts (routing destinations, configuration URLs, client-side state) do not get V-numbers. Use a consistent semantic name; in `full` mode reference the relevant TC section on first use (e.g., "post-sign-in destination (see Route Mapping)", "configured terms URL (see Configuration Attributes)"), and in `slim` mode name it semantically and stop there — the destination and the setting are dev-owned.

**Format**: `[V1]`, `[V2]`, `[V3]`, etc. — sequential across all endpoints in the PRD.

**First-use rule**: The first time a semantic name appears in an FR or AC, it gets a `[V#]` marker. Subsequent uses of the same term do not repeat the marker.

**Example**:
```
- FR-001: System MUST display the order identifier [V1] and shipping method label [V2].
- FR-002: System MUST display the order identifier and the order status [V3].
```

Each `[V#]` resolves to exactly one row in the Semantic Vocabulary table:

```
### Semantic Vocabulary

| V# | Semantic Name | Type | Required | Notes |
|----|---------------|------|----------|-------|
| V1 | order identifier | string | yes | |
| V2 | shipping method label | string | no | |
| V3 | order status | enumeration | yes | |
```

`API Field` is an optional, dev-owned column. In `full` mode the binding lives in the per-endpoint
Vocabulary tables instead, repeating the same V-numbers:

```
### GET /v1/orders/{id}

#### Vocabulary

| V# | Semantic Name | API Field | Type | Required | Notes |
|----|---------------|-----------|------|----------|-------|
| V1 | order identifier | order_id | string | yes | |
| V2 | shipping method label | shipping_method_code | string | no | |
| V3 | order status | status | string | yes | |
```

V-numbers are local to a single PRD. Vocabulary files (`semantic-vocabulary/`) provide the cross-initiative source of truth for semantic names. The writer copies entries from vocabulary files into the PRD's Semantic Vocabulary table, assigning V-numbers. The PRD is self-contained.

## Detection

The prd-reviewer detects violations using the "Behavioral/Technical Separation Smells" in `agents/prd-smell-patterns.md`. Seven smell patterns cover: API field leaks, enum leaks, wire-detail leaks (paths, status codes, headers), user-facing text / localization keys in requirements, analytics event names inline, framework terminology / implementation mechanism, and design decisions in requirements (including emphasis variants and over-specified ACs).

## This Rule Applies To

- **prd-writer**: MUST produce separated Behavioral/Technical Contracts with `[V#]` vocabulary references
- **prd-reviewer**: MUST check for separation violations in FRs, ACs, and Edge Cases — every violation is a FAIL (there is no WARN status; edge cases may be slightly more specific, but the same rule applies)
- **All agents**: MUST NOT embed technical details in the behavioral layer when writing or revising PRDs

This rule applies to all agents, skills, and conversations in this project.
