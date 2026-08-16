# Section Pack: Monitoring

> **Insert into**: Technical Contract [position: 4]
> **Slim mode**: not included — this content is dev-owned; the pack is available only in `full` Technical Contract mode.
> **When**: Backend services or critical features that need observability, alerting, or SLA targets.

### Monitoring & Alerting

> **GUIDE**
> **What**: Key metrics, SLA targets, alerting thresholds, and logging/dashboard requirements.
> **Why**: Features that ship without monitoring become invisible in production. Defining expectations in the PRD ensures observability ships with the feature.
> **How**:
> - Define the key metrics (latency, error rate, throughput)
> - Set SLA targets (p50, p99 latency, uptime %)
> - Specify alerting thresholds (when to page, when to warn)
> - Note any new dashboards or log queries needed

#### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| [e.g., p99 latency] | [e.g., < 200ms] | [e.g., > 500ms for 5 min → page] |
| [e.g., error rate] | [e.g., < 0.1%] | [e.g., > 1% for 5 min → warn] |

#### Logging

- [What events should be logged and at what level]
- [Any structured fields required for log queries]

#### Rollback Criteria

- [What metric thresholds trigger a rollback decision]
