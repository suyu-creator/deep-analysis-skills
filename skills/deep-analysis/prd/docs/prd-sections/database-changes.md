# Section Pack: Database Changes

> **Insert into**: Technical Contract [position: 4]
> **When**: Any feature that requires database schema changes, new tables, or data migrations.
> **Slim mode**: not included — this content is dev-owned; the pack is available only in `full` Technical Contract mode.

### Database Changes

> **GUIDE**
> **What**: Schema changes, new tables/columns, indexes, and migration strategy.
> **Why**: DB changes are the hardest to roll back. Specifying them in the PRD surfaces risks early.
> **How**:
> - List every table/collection affected (new or modified)
> - Specify columns/fields with types, constraints, and defaults
> - Describe the migration strategy: is it backwards-compatible? Does it need a data backfill?
> - Specify rollback approach

#### Schema Changes

| Table/Collection | Change | Details |
|-----------------|--------|---------|
| `[table_name]` | New table / Add column / Modify column | [columns, types, constraints] |

#### Migration Strategy

- **Backwards-compatible**: [Yes/No — can old code work with the new schema?]
- **Data backfill**: [Required / Not required — description if needed]
- **Rollback**: [How to undo the migration safely]
