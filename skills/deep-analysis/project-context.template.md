# Project Context

> Fill this file once per project. The PRD agents read it before every run.
> Delete the `> GUIDE` blocks after filling each section.

---

## Project Identity

> GUIDE: One paragraph. What this project is, who uses it, what problem it solves.

- **Name**: [project name]
- **Description**: [one sentence — what it does and for whom]
- **Tech stack**: [language, framework, build tool — e.g., "Java 17, Spring Boot 3.2, Gradle"]
- **Repo**: [GitHub URL]
- **Repo structure**: [monorepo with multiple apps / single service / multi-repo system]

---

## Repo Layout

> GUIDE: Map the key directories so agents know where to look.
> Adapt the entries below to match your project — delete rows that don't apply, add rows that do.

| Path | Contains |
|------|----------|
| `src/main/java/...` | Application source code |
| `src/test/java/...` | Unit and integration tests |
| `docs/` | Documentation, API specs |
| `src/main/resources/` | Configuration files |

---

## API Documentation

> GUIDE: The project-setup agent creates `docs/api-sources.md` during setup — a consolidated index
> of every API documentation source (Swagger files, registries, code annotations, external URLs).
> The researcher reads this file to find API contracts and refuses to proceed if it doesn't exist.

- **Location**: `docs/api-sources.md`

---

## Domain Glossary

> GUIDE: Business terms that agents must understand to write correct PRDs.
> Only include terms that aren't obvious from the code — things a new team member would need explained.
> **Adding terms**: prd-writer and prd-reviewer propose new terms; the user must approve before they are added. See `rules/domain-glossary.md`.

| Term | Definition |
|------|-----------|
| [term] | [what it means in this project's context] |

---

## Conventions

> GUIDE: Naming, structure, and patterns that PRDs and research docs should follow.

- **File naming**: [snake_case / kebab-case / PascalCase]
- **Branch naming**: [pattern — e.g., "feature/JIRA-123-description"]
- **Commit style**: [conventional commits / free-form / etc.]
- **Test location**: [co-located / separate tree / both]

---

## PRD Configuration

### Output Paths

> GUIDE: Where agents save their output files and find templates.
> **Directory convention**: Each initiative gets a folder. Only the PRD lives at the root of that folder.
> All other artifacts (research docs, reviews, handoff JSONs, Q&A logs, run state) go into an `_artifacts/` subdirectory.
> This keeps the initiative folder clean — a quick `ls` shows only the deliverable.

- **PRD template**: [e.g., `docs/prd-template.md`]
- **Section packs directory**: [e.g., `docs/prd-sections/`]
- **Research docs**: [e.g., `docs/initiatives/{initiative}/_artifacts/{initiative}-research.md`]
- **PRDs**: [e.g., `docs/initiatives/{initiative}/{initiative}-prd.md`]
- **Reviews**: [e.g., `docs/initiatives/{initiative}/_artifacts/{initiative}-prd-review.md`]
- **Handoff files**: [`_artifacts/` subdirectory of the initiative folder, `.json` extension]
- **Lessons**: `.claude/prd-lessons.md` (reviewer proposes in review doc, user must explicitly approve before any lesson is written)
- **Glossary**: Domain Glossary table in `project-context.md` (writer and reviewer propose terms, user must explicitly approve before any term is added — see `rules/domain-glossary.md`)
- **Semantic vocabulary**: `semantic-vocabulary/` (per-endpoint vocabulary files mapping API fields to semantic names — see `rules/semantic-vocabulary.md`). Writer and reviewer propose entries; user must explicitly approve before any entry is written.
- **Shared requirements**: `docs/shared-requirements.md` (cross-cutting requirements every PRD inherits — see `rules/shared-requirements.md`). Set to "none" if not used.

### Technical Contract

> GUIDE: "slim" (default) — the PRD keeps Product Constants, Semantic Vocabulary and Display
> Rules in the behavioral layer; API tables, error-code mappings, component paths and config
> attributes are dev-owned and live in the team's technical design.
> "full" — the PRD also includes the Technical Contract sections (legacy behavior).
>
> Pick by who owns the technical design. Working solo end-to-end? "full" — the technical
> contract is your own build plan and one document beats two. Handing specs to developers?
> "slim" — the team owns the technical design, and a PM-authored API table is a guess the
> team has to re-verify.
>
> The mode is resolved per run, not only per project: `/create-prd <initiative> --tc full`
> overrides this setting for a single initiative (a solo spike inside a team project, or one
> initiative handed to devs inside a personal project). Precedence: run override >
> this setting > `slim` default. The writer records the resolved mode in its handoff so the
> reviewer and senior PM judge the PRD in the mode it was written in.

- **Mode**: slim

### PRD Versioning

> GUIDE: How PRD versions are tracked. Set to "none" if you don't need versioning.

- **Style**: [versioned filenames (`-v1`, `-v2`) / single file with changelog / none]

### Run Logs

> GUIDE: Captures timing, model assignments, and quality metrics for each `/create-prd` run.
> Useful for comparing model profiles on the same initiative (e.g., reliable vs cost-optimized).
> Each run appends JSONL entries (one per phase, plus a pipeline summary) to the log file. Set to "no" to skip.

- **Enabled**: yes
- **Log file**: `.claude/prd-run-log.jsonl`

### Included Section Packs

> GUIDE: List which section packs from `templates/sections/` apply to this project.
> The prd-writer will include these sections in every PRD. The prd-reviewer will validate them.

Check the sections that apply to your project. Uncheck the rest.

- [x] screen-flow — Mermaid screen flow diagrams
- [x] navigation — Entry points, back behavior, deep links
- [x] analytics-events — Analytics event definitions
- [ ] localization — (removed: copy, localization keys, and translations are design-owned, not PRD content)
- [x] component-mapping — UI component to design system mapping
- [x] feature-flags — Feature flags / remote config
- [x] accessibility — Accessibility requirements
- [ ] design-prototype — Screen-to-visual-authority mapping (projects with DS/Storybook/Figma prototypes)
- [ ] user-journey — Tap-by-tap navigation path (frontend/mobile)
- [ ] responsive-layout — Responsive breakpoint behavior (web)
- [ ] database-changes — DB schema changes and migrations (backend)
- [ ] service-integration — Upstream/downstream service contracts (backend)
- [ ] monitoring — Monitoring, alerting, SLA targets (backend)
- [ ] compliance — Compliance / KYC triggers (fintech)
- [ ] platform-considerations — iOS/Android differences (mobile)
- [ ] performance — Latency/throughput budgets with measurement methods
- [ ] capacity-constraints — Data volume ceilings, growth, ceiling behavior
- [ ] rollback-degradation — Kill switch, data orphans, mid-session revert
- [ ] state-migration — Migrating existing persistent state to a new shape

### Custom Section Packs

> GUIDE: If your project needs sections not covered by the built-in packs, add them here.
> Each custom pack is a markdown file following the same format as the built-in packs
> (frontmatter with "Insert into" tag, a GUIDE block, and the section template).
> The prd-writer includes them, the prd-reviewer validates they are filled in.

Custom section pack files (one path per line, or "none"):

- none

### Registry-Mirrored Catalogs

> GUIDE: Central catalogs that PRD tables mirror — e.g., an analytics event catalog, a
> platform-discrepancy log, an error-code registry, a decision log. When a PRD table row
> mirrors a row in one of these files, additions, changes, AND removals must land in the
> catalog in the same PRD edit (see the registry-lockstep rules in prd-writer and prd-reviewer).
> List one catalog per line with its path and what it tracks, or "none".

- none

### Project-Specific Review Checks

> GUIDE: Additional review checks beyond the universal ones.
> The prd-reviewer runs these ON TOP OF its universal check matrices, as Matrix P rows.
> Write each as a checklist the reviewer can verify against the codebase.

Add one table per custom check, or leave this section empty if none apply.

<!-- EXAMPLE — DELETE EVERYTHING BETWEEN THESE MARKERS AFTER COPYING
#### Example: Spring Security
| # | Check Item |
|---|-----------|
| 1 | Every new endpoint specifies required roles via @PreAuthorize |
| 2 | No endpoint is unintentionally public |

#### Example: Remote Config Naming
| # | Check Item |
|---|-----------|
| 1 | Firebase console key uses SCREAMING_SNAKE_CASE with domain prefix |
| 2 | Dart enum member uses camelCase |
| 3 | Code fallback is false |
END EXAMPLE — DELETE -->

---

## Model Profile

> GUIDE: Controls which LLM model each agent uses. Two presets are available:
> - **reliable**: All agents use Opus, except prd-senior-pm which uses Sonnet. Best quality, highest cost.
> - **cost-optimized**: Only the mechanical agents switch to Sonnet (researcher, review-api,
>   review-structure). Every other agent in the profile table stays on Opus because they need
>   deeper judgment:
>   - **prd-writer** (Opus) — synthesizes research into requirements, asks clarifying questions
>   - **prd-reviewer** (Opus) — cross-matrix analysis, spot-checks, verdict
>   - **review-flow** (Opus) — dead-end detection, discoverability, error recovery require judgment
>   - **review-requirements** (Opus) — requirements quality (atomicity, feasibility, contradictions) needs judgment
>   - **review-smells** (Opus) — smell detection (vague verbs, loopholes, ambiguous pronouns) needs nuanced language analysis
>   - **prd-senior-pm** (Sonnet) — judges the review and makes the product decisions. It works
>     against a structured review and a decision framework, so Sonnet is enough; it stays on
>     Sonnet even here rather than dropping to Haiku, which would let invented product behavior
>     back into the spec.
>   Saves ~40-50% on token costs per PRD run.
>
> Pick a preset, then optionally override individual agents in the table below.
> The create-prd skill and prd-reviewer read this table when spawning agents.
> Valid models: `opus`, `sonnet`, `haiku`
>
> Model values are tier names resolved by Claude Code (`opus`, `sonnet`, `haiku`), not
> pinned model IDs — they track the current generation automatically.
>
> `haiku` is accepted for custom profiles. It is only appropriate for strictly mechanical work
> (e.g., review-structure checklist verification on small PRDs). Judgment-heavy agents
> (prd-writer, prd-reviewer, review-flow, review-requirements, review-smells) should stay on
> opus. Quality degradation on review agents shows up as false PASSes, which are invisible —
> prefer over-provisioning reviewers.
>
> `sonnet` — judgment floor for prd-senior-pm; anything weaker risks letting invented product behavior back into the spec.

- **Profile**: reliable

| Agent | Model | What it does |
|-------|-------|-------------|
| researcher | opus | Codebase research and fact extraction |
| prd-writer | opus | PRD drafting and synthesis |
| prd-reviewer | opus | Review orchestration, cross-checks, verdict |
| prd-senior-pm | sonnet | Judges the review, makes the product decisions, writes the writer's tickets |
| review-api | opus | Sub-reviewer: API endpoint verification |
| review-structure | opus | Sub-reviewer: structure checklist |
| review-flow | opus | Sub-reviewer: flow and edge case analysis |
| review-requirements | opus | Sub-reviewer: requirements quality (atomicity, feasibility, contradictions) |
| review-smells | opus | Sub-reviewer: smell detection (Matrix S — the only per-item smell scanner) |

---

## Research Configuration

### Codebase Research Strategy

> GUIDE: How the researcher agent should navigate the codebase.

- **Knowledge base**: [path to .ai-docs/ if it exists, or "none"]
- **Entry points for research**: [where to start looking — e.g., "controllers in src/main/java/**/controller/", "screens in lib/presentation/"]
- **API tracing method**: [e.g., "follow @RestController → @Service → @Repository", "follow Widget → Cubit → Repository → ApiService"]
- **Permalink format**: [e.g., `https://github.com/{org}/{repo}/blob/{COMMIT_SHA}/{path}` for GitHub, `https://gitlab.com/{org}/{repo}/-/blob/{COMMIT_SHA}/{path}` for GitLab, or "none" for local-only repos]

### Custom Research Steps

> GUIDE: Additional research steps the researcher executes after the standard codebase scan.
> Each step is a markdown file in `docs/research-steps/` describing what to do, where to look, and what section to add to the research output.
> Use this for cross-repo checks, external API lookups, compliance database queries, or any project-specific research needs.
> Keep research steps separate from section packs (`docs/prd-sections/`) — they serve different agents at different pipeline stages.

Check the steps that apply. Each file must define: **When** (always, or condition), **What To Do** (numbered instructions), **Where To Look** (paths/URLs), and **Output Section** (section name and what to include).

- none

### Research Scope

> GUIDE: What directories to search and what to skip.

- **Include**: [list of paths the researcher should search]
- **Exclude**: [list of paths to skip — e.g., test fixtures, generated code, other apps in a monorepo]
