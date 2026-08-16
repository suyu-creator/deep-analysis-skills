# Section Pack: Rollback / Degradation

> **Insert into**: Boundaries [position: 1]
> **When**: Features where a broken deploy has significant user impact — payment flows, auth changes, data-writing features, schema migrations, or any feature without a feature flag kill switch. Also relevant when a feature flag exists but turning it off leaves orphaned data or broken state.

### Rollback / Degradation Plan

> **GUIDE**
> **What**: What happens when this feature needs to be reverted after shipping. Covers both clean rollback (feature flag off) and dirty rollback (code revert after data has been written).
> **Why**: "Just revert the deploy" is not a plan when the feature has written data, changed a schema, or altered user-facing state. Without an explicit rollback strategy, incidents become improvised.
> **How**: Answer three questions:
> 1. **Kill switch**: Is there a feature flag? What does the user see when it's off? Is turning it off safe at any point, or only before certain actions?
> 2. **Data orphans**: If the feature wrote data (DB rows, localStorage, queue messages) and is then reverted, what happens to that data? Is it ignored, cleaned up, or does it cause errors?
> 3. **Mid-session users**: If a user is mid-flow when the feature is reverted (deploy or flag toggle), what do they experience?
>
> **Frontend examples**:
> - "Feature flag `send_new_flow` off → user sees old flow. localStorage key `draft_v2` is ignored by old code (no parse errors)."
> - "Mid-session: user on step 3 of new wizard, flag toggled off → next navigation loads old flow, draft is lost. Acceptable — draft is ephemeral."
>
> **Backend stateless examples**:
> - "Revert deploy → old code serves old response shape. Clients on new SDK version receive 4xx from removed endpoint — client must handle gracefully."
> - "No data written — clean rollback."
>
> **Backend stateful examples**:
> - "Schema migration is backward-compatible (additive column, nullable). Old code ignores new column — safe to revert."
> - "Schema migration is NOT backward-compatible. Rollback requires: (1) deploy old code with read-path fallback, (2) run backfill to undo transformation, (3) drop column in follow-up migration."
> - "Queue messages written in new format. Old consumer cannot parse them → dead-letter queue. Manual reprocessing required after re-deploy."

| Scenario | Mechanism | User Impact | Data Impact | Notes |
|----------|-----------|-------------|-------------|-------|
| Feature flag off | [flag name] | [what user sees] | [orphaned data?] | [safe at any point?] |
| Code revert (no data written) | Deploy rollback | [user experience] | None | [clean/dirty] |
| Code revert (data written) | Deploy rollback | [user experience] | [what happens to written data] | [manual cleanup needed?] |
| Mid-session user | [flag toggle / deploy] | [what they experience] | [draft/state lost?] | [acceptable?] |
