# Section Pack: State Migration

> **Insert into**: Boundaries [position: 1]
> **When**: Replacing or modifying existing behavior that has persistent state — database schemas, localStorage/sessionStorage shapes, queue message formats, API response contracts consumed by other services, or cached data structures. Does NOT apply to greenfield features with no predecessor.

### State Migration

> **GUIDE**
> **What**: How existing persistent state transitions to the new shape. Covers the migration itself, the transition period where old and new coexist, and verification that migration is complete.
> **Why**: State migration is where "it works in dev" fails in production. Old data doesn't match new schemas. Old clients send old formats. Queues have in-flight messages in the old shape. Without an explicit migration plan, the dev either breaks existing data or invents a migration strategy that the PM hasn't approved.
> **How**: Document three phases: before (what exists), during (how old and new coexist), after (how you verify completion and clean up).
>
> **Frontend examples**:
> - localStorage shape change: "Old key `draft` is a flat object. New key `draft_v2` is nested. On mount, check for `draft` — if present, transform to `draft_v2` shape and delete `draft`. If both exist, prefer `draft_v2`."
> - Session continuity: "Users mid-session on old flow during deploy see old flow until next full page load. No forced redirect."
>
> **Backend stateless examples**:
> - API versioning: "New endpoint at `/v2/orders`. Old `/v1/orders` remains for 90 days with deprecation header. Clients consuming v1 see no change."
> - Response shape change: "New field `status_v2` added alongside `status`. Old field kept for backward compatibility. Remove after all consumers migrate (tracked in [ticket])."
>
> **Backend stateful examples**:
> - Online DDL: "Add nullable column `new_field`. Backfill from `old_field` in batches of 1,000 (off-peak). Once backfill complete and verified, make non-nullable in follow-up migration."
> - Dual-write: "During transition, write to both old and new tables. Read from new table with fallback to old. Remove old-table writes after verification period (7 days)."
> - Queue format: "New consumers handle both old and new message formats. Old format support removed after queue is fully drained (max message age: 24h)."

| Phase | What | How | Verification | Duration |
|-------|------|-----|-------------|----------|
| Before | [current state shape / format] | — | — | — |
| Migration | [transformation or dual-write strategy] | [batch size, schedule, tooling] | [how to confirm progress — row counts, queue depth, logs] | [expected duration] |
| Coexistence | [how old and new shapes coexist] | [read fallback, write-both, version header] | [how to confirm old format is fully drained] | [max transition window] |
| Cleanup | [remove old shape / old code path] | [migration, deploy, config change] | [how to confirm safe to remove] | [follow-up ticket ref] |
