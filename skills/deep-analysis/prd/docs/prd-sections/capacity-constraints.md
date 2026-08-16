# Section Pack: Capacity Constraints

> **Insert into**: Behavioral Contract — after Edge Cases [position: 1]
> **When**: Features that render lists, process batches, store growing data, or handle variable load. If the answer to "how many?" affects a design decision (pagination, virtualization, sharding, retention), this section applies.

### Capacity Constraints

> **GUIDE**
> **What**: Data volume ceilings and growth expectations that inform design decisions. Each constraint must state the current expected volume, the growth trajectory, and what happens when the ceiling is hit.
> **Why**: "It works with 10 items" and "it works with 10,000 items" are different architectures. Without explicit volume targets, devs guess — and either over-engineer or ship something that breaks at scale.
> **How**: For each data dimension the feature handles, state the expected volume and the design implication. Use the table below.
>
> **Frontend / Mobile examples**:
> - List size: "Max 200 list rows — no virtualization needed"
> - Payload size: "Response ≤ 50KB — no streaming/pagination needed"
> - Items at the same time: "Max 3 requests running at once — queue the rest"
>
> **Backend stateless examples**:
> - Request rate: "Peak 500 req/s — single instance sufficient"
> - Payload size: "Request body ≤ 1MB — reject larger"
> - Batch size: "Max 100 items per batch endpoint call"
>
> **Backend stateful examples**:
> - Table size: "Expect 10M rows year 1, 50M year 3"
> - Message rate: "Peak 1,000 msg/s — partition by tenant"
> - Storage growth: "~500MB/month — set retention to 90 days"
> - Connection pool: "Max 50 concurrent DB connections per instance"

| ID | Dimension | Current Expected Volume | Growth | Ceiling Behavior |
|----|-----------|------------------------|--------|-----------------|
| CAP-001 | [what — list size, row count, message rate, etc.] | [number] | [static / linear / exponential + rate] | [what happens at limit — paginate, reject, archive, alert] |
