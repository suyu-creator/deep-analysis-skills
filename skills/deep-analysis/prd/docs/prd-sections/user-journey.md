# Section Pack: User Journey

> **Insert into**: Context [position: 1]
> **When**: Any feature with a user-facing flow — shows designers and developers where the feature sits in the app.

### User Journey

> **GUIDE**
> **What**: The full navigation path showing how the user reaches this feature and where they go after.
> **Why**: Designers need to know where this feature lives in the app and what surrounds it.
> **How**:
> - **Entry path** (required content — all three): (1) the concrete screen(s) the user is on immediately before this feature — always answer "how do we end up here?" by naming the screen one step before; (2) the interaction on that screen that brings them here (tap, link, menu item); (3) any non-UI entries — deep link, redirect, notification — each going through the same gates (auth, flags, eligibility) as in-app navigation, or an explicit "none". "User navigates to the screen" with no named origin is not an entry path.
> - **Trigger**: What prompted the user to enter this flow
> - **Current behavior**: One sentence on what exists today
> - **Exit**: Where the user lands after completing or cancelling
> - Keep it factual and navigational — no metrics or business KPIs.

**Entry path**: [App launch → Screen → Screen → ... → This Feature — the last named screen is the one immediately before, with the interaction that leads here]

**Non-UI entries**: [Deep link / redirect / notification entries, each with the gates that apply — or "None"]

**Trigger**: [What prompts the user to enter this flow]

**Current behavior**: [One sentence on what exists today]

**Exit**: [Where the user goes after completing or cancelling]
