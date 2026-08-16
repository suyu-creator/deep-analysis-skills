# Section Pack: Component Mapping

> **Insert into**: Technical Contract [position: 1]
> **When**: Any frontend/mobile feature using a design system or component library.
> **Slim mode**: not included — this content is dev-owned; the pack is available only in `full` Technical Contract mode.

### Component Mapping

> **GUIDE**
> **What**: Table mapping every UI element to a specific design system component, file path, and key props.
> **Why**: Makes the PRD implementation-ready. Without this, devs pick components by guessing, leading to inconsistent UI.
> **How**:
> 1. One row per distinct UI element. If a needed component doesn't exist, flag it as a gap — don't include it here.
> 2. **Verify every Source File path on disk** (or on the reference branch). Do not infer file names from component naming conventions — open the path and paste the verified file name back into the table.
> 3. **Verify every cited prop against the component's own prop definitions** (its props interface / documented API). Do not copy prop names from research docs, other platforms, or memory. If the component achieves the behavior with differently named props, use the real prop names and note the mapping.
> 4. **If the feature builds on an existing composed page/template component**, read it and compare its rendered elements against the FRs. Any UI element the PRD adds that the existing template lacks must be flagged — either as a component gap or as a deliberate divergence with justification. Never silently assume the template will be updated to match.

| UI Element | Component | Source File |
|-----------|-----------|-------------|
| [what the user sees] | `<ComponentName prop="value" />` | `path/to/component` |

**Component mapping confirmation**:
- [ ] Every Source File path opened and verified (not inferred from naming conventions)
- [ ] Every cited prop verified against the component's prop definitions
- [ ] Existing composed page/template components compared against FRs; additions flagged as gaps or justified divergences
