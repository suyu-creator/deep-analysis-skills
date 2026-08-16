# Section Pack: Service Integration

> **Insert into**: Technical Contract [position: 4]
> **When**: Any feature that calls or is called by other services, message queues, or external APIs.
> **Slim mode**: not included — this content is dev-owned; the pack is available only in `full` Technical Contract mode.

### Service Integration Points

> **GUIDE**
> **What**: Every upstream (services this feature calls) and downstream (services that call this feature) dependency.
> **Why**: Integration points are the most common source of production incidents. Making them explicit surfaces retry logic, timeout, auth, and failure mode requirements.
> **How**:
> - List each service with: what it provides, the endpoint/contract, auth method, error handling
> - Specify retry/circuit-breaker behavior
> - Specify timeout values

#### Upstream Dependencies (services this feature calls)

| Service | Endpoint | Auth | Timeout | Retry | On Failure |
|---------|----------|------|---------|-------|------------|
| [service name] | `METHOD /path` | [API key / OAuth / mTLS] | [ms] | [count + backoff] | [fallback behavior] |

#### Downstream Consumers (services that call this feature)

| Service | What It Consumes | Contract Notes |
|---------|-----------------|----------------|
| [service name] | [endpoint or event] | [backwards-compatibility constraints] |
