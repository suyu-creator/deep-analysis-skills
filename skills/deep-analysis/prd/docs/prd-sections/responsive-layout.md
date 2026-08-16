# Section Pack: Responsive Layout

> **Insert into**: Technical Contract [position: 1] (`full` mode only)
> **When**: Web applications that must work across viewport sizes, in `full` mode only.
> **Slim mode — omit the section**: in `slim` mode this section does not exist. Leave it out entirely, and do not list it in the handoff's `consideredNA` — the project's responsive shared requirement already promises the baseline (the feature works at every breakpoint the SR defines, and nothing needs sideways scrolling), and how content is arranged at each width is the designer's decision. When the product really differs by width — something is shown, hidden, or unreachable at one width — write that as an ordinary FR or AC ("the list is hidden at phone width"), not as a section. In every mode, any screen width named anywhere in the PRD must be one of the responsive SR's breakpoints, or have a written override in Shared Requirements → Feature-specific overrides.

#### Responsive Layout

> **GUIDE** (`full` mode)
> **What**: How the page/feature behaves at each breakpoint the project's responsive shared requirement defines.
> **Why**: The breakpoint set is a project-level product decision, not a per-PRD choice. A hand-picked viewport list drifts from the project's actual breakpoints and silently skips whole device classes.
> **How**: Before writing, open the project's responsive shared requirement (the SR named in project-context.md / `docs/shared-requirements.md`) and enumerate its breakpoints. Write **one checklist row per breakpoint in that SR, using the SR's pixel values** — never example viewports, and never a subset. Each row states only the behavioral facts at that breakpoint: what is present, what is reachable. Reference layout components from the design system; only specify breakpoint-specific behavior that the layout system doesn't handle automatically. Reference a shared layout baseline (page shell, loading state) by its SR id, never by component class name — the SR alias is the stable product name; the class is dev-owned wiring.
> **Row-set discipline**: a row set that differs from the SR's breakpoint set — a missing breakpoint, or a viewport the SR does not define — requires an explicit override in Shared Requirements → Feature-specific overrides with justification; without one the reviewer FAILs the section. If the project has no responsive SR, state that on the section's first line and list the viewports agreed with design.

- [ ] [First breakpoint per the responsive SR, with its pixel value: behavioral facts at this breakpoint]
- [ ] [Second breakpoint per the responsive SR: behavioral facts]
- [ ] [...one row for every remaining breakpoint the SR defines]
