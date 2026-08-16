# Section Pack: Performance

> **Insert into**: Behavioral Contract — after Edge Cases [position: 1]
> **When**: Features with user-facing latency (page loads, form submissions, real-time updates), high-throughput endpoints, or operations where slowness degrades user trust (payments, search). Also applies to backend services with SLA commitments or latency-sensitive consumers.

### Performance Requirements

> **GUIDE**
> **What**: Measurable performance thresholds that define "fast enough." Every requirement must have a number and a measurement method.
> **Why**: Without explicit targets, a correct but slow implementation passes all FRs and ACs. Performance is a requirement, not a polish pass.
> **How**: Define thresholds for the scenarios that matter. Not every screen needs a budget — focus on entry points, data-heavy views, and user-blocking operations. Use the table format below.
>
> **Frontend / Mobile examples**:
> - Initial render: "Skeleton visible within 200ms of navigation"
> - Data-populated render: "List items visible within 1s of mount (P95, 3G throttled)"
> - Interaction response: "Tap-to-feedback within 100ms"
> - Bundle size: "Route chunk ≤ 50KB gzipped"
>
> **Backend stateless examples**:
> - Response time: "P50 ≤ 50ms, P95 ≤ 200ms, P99 ≤ 500ms"
> - Throughput: "Sustain 1,000 req/s per instance"
> - Cold start: "First request after deploy ≤ 2s"
>
> **Backend stateful examples**:
> - Write latency: "Commit acknowledged within 100ms (P95)"
> - Read-after-write: "Written data queryable within 500ms"
> - Queue drain: "95th percentile message processing ≤ 5s"
> - Replication lag: "Replica ≤ 1s behind primary under normal load"

| ID | Scenario | Metric | Target | Measurement Method |
|----|----------|--------|--------|-------------------|
| PERF-001 | [scenario] | [what to measure] | [threshold] | [how to verify — e.g., Lighthouse, load test, APM percentile] |
