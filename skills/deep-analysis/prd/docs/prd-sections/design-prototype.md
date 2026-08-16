# Section Pack: Visual Design References

> **Insert into**: Technical Contract [position: 2] (`full` mode only)
> **When**: Projects with a design system (`src/components/ui/` or equivalent) and/or Figma mockups, in `full` mode only.
> **Slim mode — omit the section**: in `slim` mode this section does not exist. Leave it out entirely, and do not list it in the handoff's `consideredNA` — the PRD says nothing about design readiness. Whether a design exists yet is workflow state, owned by the pipeline and the team: designers and developers talk to each other. When the pipeline finds a screen with no design, it files a `ds-gap` issue on GitHub — that stays pipeline behavior, and the PRD does not track or restate issue status anywhere, Dependencies included.

### Visual References

> **GUIDE** (`full` mode)
> **What**: A table mapping every screen or flow step to its visual design source — a Figma URL, a DS component path, or a `BLOCKED` flag.
> **Why**: Without an explicit visual reference, what gets built drifts from the approved design. Naming the source here makes it clear which design wins, and lets reviewers check it.
> **How**:
> 1. One row per screen or flow step, in flow order.
> 2. **Visual Reference** column — fill exactly one of:
>    - **Figma** — URL to the specific frame or screen. Preferred when mockups exist.
>    - **DS component** — a shipped component that defines the layout (e.g., a shell, a card, a form pattern). This is a real, shipped design system primitive — not a prototype. Cite the repo path (`src/components/ui/...`).
>    - **BLOCKED — no visual reference** — must have a corresponding `ds-gap` GitHub issue cited (`#<issue>`). A prototype must be built from this PRD before implementation begins.
> 3. **Notes** column — either:
>    - "Matches Figma" or "Uses DS component as-is" when implementation should follow the reference exactly
>    - An explicit, itemised list of intentional deviations (e.g., "Figma shows 3 tabs; this PRD ships only the first tab in v1")
>    - Forbidden: vague notes like "minor adjustments" — be precise so reviewers can verify
> 4. **Authority order** when references conflict:
>    - DS components (shipped primitives in `src/components/ui/`) win over Figma for layout structure
>    - Figma wins over PRD prose for visual design
>    - PRD prose wins over assumptions / inference
> 5. **Prototypes are outputs, not inputs.** Files in `__prototype__/` directories are built by the prototype agent AFTER the PRD is approved. The PRD writer MUST NOT reference existing prototypes as visual authority — they were generated from a previous PRD version and may be stale or based on obsolete requirements. The prototype agent will build a new prototype from this PRD.
> 6. **Tickets must reference the visual source** (Figma URL or DS component path), not just the PRD.

| Screen / Step | Visual Reference | Notes |
|---|---|---|
| [Screen name] | [Figma URL](https://...) | [Matches Figma, or itemised deviations] |
| [Screen name] | DS component: `src/components/ui/<component>` | [Uses component as-is, or deviations] |
| [Screen name] | **BLOCKED — no visual reference** (issue #<N>) | Prototype must be built from this PRD before implementation |

**Visual reference confirmation**:
- [ ] Every row above points to a Figma frame or DS component, or cites a `ds-gap` issue
- [ ] No `__prototype__/` files are referenced as visual authority (prototypes are outputs of the pipeline, not inputs)
- [ ] Tickets generated from this PRD will reference the visual source
