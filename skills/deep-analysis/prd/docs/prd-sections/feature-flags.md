# Section Pack: Feature Flags

> **Insert into**: Behavioral Contract — after Edge Cases [position: 1]
> **When**: Any new feature that should be gated behind a feature flag or remote config.

### Feature Flags / Remote Config

> **GUIDE**
> **What**: Feature flag definition — name, fallback, and behavior when off.
> **Why**: Feature flags allow toggling without a release. Safety net for rollouts and incidents.
> **How**:
> 1. Audit existing flags first — check if one already covers this feature
> 2. Follow the codebase's naming convention for flag names
> 3. Fallback should typically be `false` (feature hidden until deliberately enabled)
> 4. Describe the user experience when the flag is off — not just "feature is off" but what the user actually sees

| Field | Value |
|-------|-------|
| **Flag name** | `[flag_name following codebase convention]` |
| **Reuse check** | [Confirmed no existing flag covers this / Reusing `EXISTING_FLAG` because ...] |
| **Fallback** | `false` |
| **Behavior when off** | [Exactly what the user sees — hidden, disabled, fallback, etc.] |
