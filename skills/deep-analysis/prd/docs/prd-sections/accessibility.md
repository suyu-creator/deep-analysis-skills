# Section Pack: Accessibility

> **Insert into**: Behavioral Contract — after Edge Cases [position: 1]
> **When**: Features with forms, modals/dialogs/sheets, or complex interactions. Recommended for all user-facing features.

### Accessibility

> **GUIDE**
> **What**: Screen reader, focus management, and accessibility requirements.
> **Why**: Accessibility is a quality baseline. Specifying it in the PRD ensures it's built in, not bolted on.
> **How**: Cover:
> - Semantic labels for non-text elements (icons, images, badges)
> - Focus order in forms
> - Focus management after modal/sheet open and close, step transitions
> - Keyboard navigation (Tab order, Enter/Space activation) — for web
> - Screen reader behavior (VoiceOver/TalkBack) — for mobile
> **Slim mode — outcomes, not mechanisms**: feature-specific rows state what the user must be able to perceive and operate — a message is announced to assistive technology (for example, screen readers) when it appears, a control is reachable by keyboard, a state is shown with more than color alone, a control's name says where it leads. Mechanisms — live-region politeness levels ("announce politely/assertively"), focus targets, announcement wording — are design/dev-owned under the project's accessibility shared-requirement baseline. A focus rule is allowed only as an outcome: "an ignored repeat activation must not trap or move keyboard focus" passes; "focus stays on the retry button" does not.
