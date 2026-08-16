# Lesson Lifecycle

Lessons in `.claude/prd-lessons.md` are a *project's* accumulated review failures. Every active lesson costs something on every future PRD: a Writer rule the writer must hold in context, and a Matrix H row the reviewer must execute. Left alone, that cost grows without bound and the corpus fills with rules that have already been fixed elsewhere.

This document defines the lifecycle that bounds the cost: lessons are born `active`, are narrowed by an **Applies when** condition, and eventually **graduate** into the framework or are **superseded** by a broader lesson — at which point they stop generating work.

The mechanics of the fields live where the agents read them: the lesson template and the three valid `Status` values are in `agents/prd-reviewer.md` Step 12; the review-time skip and applicability gates are in reviewer Step 1 / step 8.1.1 and writer Step 0. This file is the maintenance ritual around them.

**Approval boundary.** Nothing here overrides `rules/prd-lessons.md`. No agent may add a lesson, change a lesson's Status, or delete a lesson without explicit user approval. An agent running this workflow *proposes* the graduation and the retirement; the user decides.

## When to review the corpus

Run a corpus review when any of these triggers fires:

- **Volume**: the project has **15 or more active lessons**. Beyond roughly this point the reviewer is spending more attention on lesson checks than on the PRD.
- **Time**: **quarterly**, even if the corpus is small — the framework moves underneath the lessons, and a lesson that contradicts the current framework is worse than no lesson.
- **Families**: the same **lesson family has 3+ members**. A family is a set of lessons that each patch a loophole in the previous one ("also check the empty state", "also check the empty state on mobile", "also check the empty state after a failed refresh"). Three members is proof that the *generic* rule was never written — the pattern is not "another loophole", it is a missing principle. Replace the family with one generic lesson (each old member gets `superseded-by:`), or graduate the principle into the framework.

Count only active lessons for the volume trigger; `superseded-by:*` and `graduated:*` entries are inert history.

## The genericity test

For each active lesson, ask one question:

> **Would this rule be correct in a project with a completely different domain and stack?**

- **Yes** → graduation candidate. The lesson is a general truth about writing PRDs that happened to be discovered here.
- **No** → it stays a project lesson. Genuinely project-specific rules (this project's catalog files, this team's endpoint conventions) belong in `.claude/prd-lessons.md` or `project-context.md`, not in the framework.
- **Yes, but it names project files, catalogs, endpoints, or screens** → **extract the generic kernel and rewrite.** Do not graduate the lesson verbatim. Ask what the named artifact is an *instance of* ("the `feature-catalog.ts` registry" → "a central catalog that every new entry must be registered in"), then write the rule in those terms. If the kernel cannot be stated without the project noun, it failed the test — keep it local.

A graduated rule must also survive the framework's own standards: it has to be checkable by an agent, phrased as an instruction rather than an anecdote, and it must not restate a rule that already exists (see Merge-first discipline).

## Where graduated rules land

Use this routing table to place the extracted kernel by what kind of rule it is. One home per rule — pick the single best row, do not copy it into two.

| Kind of rule | Lands in |
|---|---|
| Writer behavior — how the PRD must be drafted | `agents/prd-writer.md` (Quality Standards, or the relevant step's checklist) |
| Reviewer detection — how to catch a defect | `agents/prd-reviewer.md` (matrix column definitions, or a new/extended Matrix F row) |
| Smell-shaped — a recognizable requirements-quality defect | `agents/prd-smell-patterns.md` |
| Template obligation — a section or field every PRD must fill | `~/.claude/skills/deep-analysis/prd/docs/prd-base-template.md`, or the relevant `/docs/prd-sections/*.md` pack |
| Cross-agent principle — binds writer, reviewer, and orchestrator alike | a file under `rules/` (extend an existing rule before adding a new one) |
| Mechanically checkable — a deterministic text/structure rule | `~/.claude/skills/deep-analysis/prd/scripts/prd-lint.py` as a new check ID, plus a fixture in `scripts/tests/fixtures/` |

If a rule seems to belong in two places, it is usually two rules (one behavioral obligation and one detection method) — split it and route each half. A rule that can be enforced by the linter should be, even if it is also stated in prose: prompts forget, scripts do not.

## The retire step

Graduation is not finished until the project lesson stops generating work.

1. Land the framework change first — the rule must be merged (in `agents/`, `templates/`, `rules/`, or `scripts/`) before the lesson is retired. Never retire a lesson against an unmerged branch.
2. With user approval, set the project lesson's **Status** to `graduated: <framework commit sha or PR link>`. The ref is mandatory: it is the only trace back from the retired lesson to the rule that replaced it.
3. Alternatively, **delete** the lesson outright — also with user approval. Prefer `graduated:` when the history is useful (it explains why the framework rule exists); prefer deletion when the corpus is large and the entry adds only noise.
4. **Lessons that contradict the current framework must be deleted, not kept.** A lesson referencing a removed section, a renamed matrix, a retired template field, or a rule the framework has since reversed will actively mislead the writer and produce false FAILs in Matrix H. Marking it `graduated:` is wrong — nothing graduated. Delete it and say so in the approval request.
5. For a superseded family, set each old member to `superseded-by: L-NNN` pointing at the replacement, and make sure the replacement's **Applies when** covers every case the family covered.
6. Re-verify after retiring: the next review should show a smaller Matrix H and no `[PENDING]` or orphaned rows. A `superseded-by:` pointer must name a lesson that exists and is itself active.

## Merge-first discipline

The framework's rules budget is **one home per rule** (`agents/prd-reviewer.md`, Step 8.6, "Rules budget"): before adding a lesson or a framework rule, check whether an existing rule already covers the pattern, and if it does, extend or amend that rule instead of adding a sibling. Name the rule and quote the clause you would change.

The same discipline governs this workflow:

- **Prefer extending an existing lesson over adding a sibling lesson.** Amend the existing lesson's Writer rule / Reviewer check, or broaden its **Applies when**, rather than appending a near-duplicate — that is precisely how 3-member families form.
- **Prefer extending an existing framework rule over creating a new file.** A new file under `rules/` is justified only when the principle has no existing home.
- **Prefer narrowing over deleting.** A lesson that fires falsely on most PRDs usually needs a tighter **Applies when**, not retirement.
- Every duplicated rule is a future drift bug: two copies will disagree eventually, and the reviewer pays attention to both.
