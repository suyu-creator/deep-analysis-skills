# Semantic Vocabulary

Never write to vocabulary files in `semantic-vocabulary/` without explicit user approval.

The prd-writer PROPOSES vocabulary entries when it encounters API fields during research that need semantic names. The prd-reviewer PROPOSES vocabulary entries when it finds the PRD using raw API field names instead of semantic names. The create-prd orchestrator collects both sets of proposals and presents them to the user. The user decides which to accept. Only after the user explicitly approves specific entries (by name or number) may any agent write them to vocabulary files.

If the user says "skip", "none", or does not approve — write nothing.

## File format

Each API endpoint gets its own file in `semantic-vocabulary/`. The naming convention converts the endpoint to a filename: lowercase HTTP method + path with `/` replaced by `-` and `{param}` replaced by the param name.

Examples:
- `GET /v1/orders/{id}` → `semantic-vocabulary/get-v1-orders-id.md`
- `POST /v1/customers` → `semantic-vocabulary/post-v1-customers.md`

Each file contains a mapping table from API field names to semantic concept names used in the behavioral layer of PRDs.

## PRD snapshot pattern

When the writer drafts a PRD, it copies relevant vocabulary entries into the PRD's **Semantic Vocabulary** table in the Behavioral Contract, assigning V-numbers (V1, V2, V3... sequential across all endpoints). In `full` Technical Contract mode it additionally binds those same V-numbers to their API fields in per-endpoint Vocabulary tables; in `slim` mode the binding is dev-owned and the `API Field` column is omitted. The PRD is self-contained — if vocabulary files change later, the PRD retains its snapshot. New terms discovered during drafting are added to the PRD tables and proposed as vocabulary file additions.

## How agents use vocabulary files

- **prd-writer**: Reads vocabulary files for endpoints identified during research. Copies entries into the PRD's Semantic Vocabulary table with V-numbers. Uses semantic names with `[V#]` markers in FRs/ACs. Proposes new entries for unmapped fields.
- **prd-reviewer**: Verifies FRs/ACs use semantic names from vocabulary files and that `[V#]` markers resolve to Semantic Vocabulary rows (and, in `full` mode, to the per-endpoint table that binds them). Flags invented alternatives for already-mapped fields. Proposes entries for fields the writer missed.
- **create-prd orchestrator**: Collects proposals from both agents, deduplicates, presents to user for approval, and dispatches callbacks to write approved entries.

This rule applies to all agents, skills, and conversations in this project.
