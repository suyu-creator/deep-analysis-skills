---
name: create-prd
description: Full PRD creation pipeline — research, draft, review, and senior-PM judgment with human gates between phases. Chains researcher → prd-writer → prd-reviewer → prd-senior-pm agents.
argument-hint: <initiative-name> [--tc slim|full]
---

# PRD Creation Pipeline

> **路径适配**:本文件内所有 `~/.claude/skills/deep-analysis/` 路径对应**手动安装**位置(把 `skills/deep-analysis` 复制到 `~/.claude/skills/deep-analysis`)。若通过 marketplace / 插件缓存安装,skill 位于其他目录——把所有 `~/.claude/skills/deep-analysis/` 替换为 skill 实际安装路径再执行。run-log.py / prd-lint.py / validate-handoff.py 是真实 shell 命令,路径必须可执行。

Run the full PRD workflow for `{argument}`.

## Arguments

`{argument}` is the initiative name, optionally followed by flags. Strip every flag before using `{argument}` as the initiative name — the initiative name is what remains, and it is what every file path, handoff name, and agent prompt uses.

| Flag | Values | Effect |
|---|---|---|
| `--tc` | `slim` \| `full` | Technical Contract mode for **this run only**. Overrides the project-context setting. |

Anything else after the initiative name is initiative brief text, not a flag — pass it through to Phase 0.

## 集成模式(从 deep-analysis 调用时)

本流水线可被 `/deep-analysis` 技能调用。此时 deep-analysis 已完成 3 闸门(+ 可选对抗),跳过本流水线重复的研究阶段:

| 本流水线阶段 | 集成模式下 | 处理 |
|---|---|---|
| Phase 0 范围澄清 | **跳过** | deep-analysis 闸门 1 已锁定范围,直接传 phase0 JSON |
| Phase 1 研究 | **跳过** | deep-analysis 闸门 2 的 researcher 已产出调研,直接传给 prd-researcher 复用 |
| Gate 1 研究审查 | **跳过** | deep-analysis 闸门 2 已确认方向 |
| Phase 2 PRD 起草 | 执行 | 给 prd-writer 额外传:phase0 JSON + 调研结果 + 可行性裁决 + 复用候选清单 + 红队攻击面 |
| Phase 3.5 资深PM | 执行 | 给 prd-senior-pm 额外传可行性裁决与红队未答复攻击,避免它重做判断 |

集成模式判断:编排层传入 `contextHandoff`(含 `phase0Json` / `research` / `feasibilityVerdict` / `reuseCandidates` / `redTeamAttacks`)时进入集成模式,跳过上表标记的阶段,并把 contextHandoff 作为附加上下文传给 writer 与 senior PM。未传入 contextHandoff 则按完整流水线运行。

## Pre-flight

0. **Resolve the Technical Contract mode** and store it as `TC_MODE`, with `TC_MODE_SOURCE` recording where it came from. Precedence, highest first:
   1. `--tc slim` / `--tc full` on this invocation → `TC_MODE_SOURCE = run-override`
   2. `.claude/project-context.md` → PRD Configuration → Technical Contract → **Mode** → `TC_MODE_SOURCE = project-context`
   3. `slim` → `TC_MODE_SOURCE = default` (also the answer for an older project-context.md that predates the setting)

   Reject any `--tc` value other than `slim` or `full`: STOP and tell the user the two valid values. Announce the resolution once, before Phase 0 — e.g. "Technical Contract mode: **full** (run override; project-context says slim)" — so the user can correct it before research burns tokens. Then pass `TC_MODE` explicitly to the writer, the reviewer, and the senior PM: the mode a document was written in is not re-derivable from the document, and an agent that re-resolves it from project-context.md silently loses the override.

1. Read `.claude/project-context.md` — confirm it exists and is filled in. If it doesn't exist, STOP and tell the user: "You need to set up `.claude/project-context.md` first. Copy `~/.claude/skills/deep-analysis/project-context.template.md` to `.claude/project-context.md` and fill it in for your project."
2. Confirm the initiative directory exists or create it at the output path specified in project-context.md. Also create the `_artifacts/` subdirectory:
   ```bash
   mkdir -p "{initiative_dir}/_artifacts"
   ```
3. Read the **Model Profile** table from project-context.md. Extract the `Model` column for each agent row. Store as `MODEL_MAP` — a lookup from agent name to model (e.g., `researcher → sonnet`, `prd-writer → opus`, `prd-senior-pm → sonnet`). If the Model Profile section is missing, default all agents to `opus` — except `prd-senior-pm`, which defaults to `sonnet`. Pass every value through to the Agent spawn **as-is**: `opus`, `sonnet`, `haiku` are the valid tier names.
4. Check if **Run Logs** are enabled in project-context.md. If enabled:
   ```bash
   RUN_ID=$(date -u +%Y%m%d-%H%M%S)
   LOG_FILE=".claude/prd-run-log.jsonl"
   STATE_FILE="{initiative_dir}/_artifacts/.run-state.json"
   TIMING_FILE="{initiative_dir}/_artifacts/.run-timing.tmp"
   echo "pipeline_start=$(date +%s) $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$TIMING_FILE"
   ```
   Record the profile name (from the `Profile` field in Model Profile) for the run log.

5. **Stale state recovery**: Check for an abandoned previous run:
   ```bash
   [ -f "$STATE_FILE" ] && cat "$STATE_FILE"
   ```
   If `$STATE_FILE` exists, a previous pipeline run was interrupted (user closed laptop, connection dropped, etc.). Recover it:
   1. Read the state file — extract `runId`, `initiative`, `currentPhase`, `startedAt`, `completedPhases`
   2. Append a `"terminated"` JSONL entry to `$LOG_FILE` capturing all completed phases and the phase that was in progress when it died:
      ```bash
      python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py append --log-file "$LOG_FILE" --entry-type terminated \
        --field "runId=<runId from state>" \
        --field "initiative=<initiative from state>" \
        --field "terminatedAt=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --field "diedInPhase=<currentPhase from state>" \
        --field 'completedPhases=<completedPhases array from state, verbatim JSON>' \
        --field "reason=abandoned"
      ```
      Never interpolate values into a JSON string yourself — pass each one through `--field` so the script escapes it. If `~/.claude/skills/deep-analysis/prd/scripts/run-log.py` is missing, build the line with `python3 -c` + `json.dumps`, passing the schema's fields as arguments (never with `echo` — that reintroduces the injection run-log.py exists to prevent), following the [JSONL Schema Reference](#jsonl-schema-reference).
   3. Delete the stale state file: `rm -f "$STATE_FILE"`
   4. Log a message: "Recovered abandoned run {runId} for {initiative} — terminated in {currentPhase} phase."

6. **Create state file** for the current run. Never build it with shell `echo` — an initiative name containing a quote or `$(…)` would break the JSON or execute. Write it through Python's `json.dumps`, passing every value as an argument (the same rule run-log.py documents):

   ```bash
   python3 - "$STATE_FILE" "$RUN_ID" "{argument}" "<profile>" "<TC_MODE>" "<TC_MODE_SOURCE>" '<MODEL_MAP as JSON>' <<'EOF'
   import json, sys, datetime
   state_file, run_id, initiative, profile, tc_mode, tc_mode_source, model_map = sys.argv[1:]
   state = {
       "runId": run_id,
       "initiative": initiative,
       "status": "in_progress",
       "currentPhase": "preflight",
       "cycle": 1,
       "startedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
       "profile": profile,
       "technicalContractMode": tc_mode,
       "technicalContractModeSource": tc_mode_source,
       "modelMap": json.loads(model_map),
       "completedPhases": [],
   }
   with open(state_file, "w", encoding="utf-8") as f:
       json.dump(state, f)
   EOF
   ```

   The quoted delimiter `<<'EOF'` keeps the shell from touching the Python source; `modelMap` is `json.loads`-parsed; the initiative name is written verbatim via `json.dump`. `python3` is already required by run-log.py, so this adds no new dependency. If `python3` is unavailable, stop and surface the error — do not fall back to `echo` (that is exactly the injection this step exists to avoid).

### Handoff file naming convention

All agents use this naming pattern — files go in the `_artifacts/` subdirectory of the initiative folder:
- Writer handoff: `_artifacts/{initiative}-prd-handoff.json`
- Reviewer handoff: `_artifacts/{initiative}-prd-review-handoff.json` (or `_artifacts/{initiative}-prd-review-v{N}-handoff.json` if versioned)
- Senior-PM decision sheet: `_artifacts/{initiative}-senior-pm-review.md`
- Senior-PM handoff: `_artifacts/{initiative}-senior-pm-handoff.json`

These names are stable across revision cycles. The reviewer reads the writer's handoff by this name. The senior PM reads the reviewer's handoff and, on later passes, its own previous handoff — that is how it knows the run is a delta pass. No agent overwrites another's file.

## Phase 0: Scope Clarification

Before spending time on research, analyze the initiative brief (`{argument}`) for ambiguity. Ask the user **2-4 framing questions** to lock down scope before the researcher starts. This prevents misdirected research.

Focus on:
- **Ambiguous terms**: Does the initiative name map to one specific feature, or could it mean multiple things? (e.g., "notifications" could mean adding push notifications, building the notification preferences page, or adding an in-app notification center)
- **Scope boundaries**: Is this a full feature or a slice? New build or extension of existing behavior?
- **Target users/systems**: Who or what is this for? (e.g., end users, internal ops, another service)

**Format**: Present each question with your best guess based on the initiative name and what you know about the project from project-context.md:
> "Before I research, a few quick scope questions:
> 1. 'Notifications' — does this mean (a) adding push notifications to existing flows, (b) building the notification preferences page, or (c) both? I'm guessing (a) based on the project type.
> 2. Is this for all users or a specific segment?

If the user provides a detailed brief (more than 2 sentences with clear scope), you may skip this phase — the brief itself answers the framing questions. Say: **"Your brief is clear on scope — moving straight to research."**

Pass the clarified scope to the researcher so it knows exactly what to focus on.

## Phase 1: Research

If run logging is enabled: `echo "research_start=$(date +%s)" >> "$TIMING_FILE"`

Spawn an Agent using the prompt from `~/.claude/skills/deep-analysis/prd/agents/researcher.md`, with `model: MODEL_MAP[researcher]`:
- Pass `{argument}` as the INITIATIVE
- Pass the clarified scope from Phase 0 (if any) as additional context
- Let it scan the codebase (or docs/specs for greenfield) and produce a research document

The researcher will detect whether this is a greenfield project (no source code) or an existing codebase and adjust its approach automatically.

If run logging is enabled:
```bash
echo "research_end=$(date +%s)" >> "$TIMING_FILE"
```
Update state file — mark research complete and append researcher JSONL entry:
1. Extract metrics from the research document (grep-based counts):
   ```bash
   ENDPOINTS=$(grep -c '| [0-9]' {research_path_endpoints_table} 2>/dev/null || echo 0)
   FILES_READ=$(grep -c '| \`' {research_path_files_table} 2>/dev/null || echo 0)
   AMBIGUITIES=$(grep -c '| [0-9]' {research_path_ambiguities_table} 2>/dev/null || echo 0)
   ```
2. Append researcher JSONL entry:
   ```bash
   python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py append --log-file "$LOG_FILE" --entry-type researcher \
     --field "runId=$RUN_ID" \
     --field "initiative={argument}" \
     --field "agent=researcher" \
     --field "model=$MODEL_MAP_RESEARCHER" \
     --field "cycle=1" \
     --field "startedAt=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --get research_start --iso)" \
     --field "completedAt=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --get research_end --iso)" \
     --field "durationSeconds=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --delta research_start research_end)" \
     --field "inputSummary=Initiative brief: {argument}" \
     --field "outputSummary=Research doc with $ENDPOINTS endpoints, $FILES_READ files, $AMBIGUITIES ambiguities" \
     --field "artifactPath=<research doc path>" \
     --field "handoffPath=null" \
     --field "metrics={\"endpointsFound\":$ENDPOINTS,\"filesRead\":$FILES_READ,\"ambiguitiesFlagged\":$AMBIGUITIES}"
   ```
   The script escapes every value, so an initiative name containing quotes or `$(…)` is safe. If `~/.claude/skills/deep-analysis/prd/scripts/run-log.py` is missing, build the line with `python3 -c` + `json.dumps`, passing the schema's fields as arguments (never with `echo` — that reintroduces the injection run-log.py exists to prevent), following the [JSONL Schema Reference](#jsonl-schema-reference), and read the timing file with a `while IFS='=' read -r key val` loop.
3. Update state file — set `currentPhase: "gate1"`, push researcher phase into `completedPhases`

### Gate 1: Research Review

If run logging is enabled:
```bash
echo "gate1_prompt=$(date +%s)" >> "$TIMING_FILE"
```
Update state file — set `currentPhase: "gate1"`.

**Validate ambiguity table**: Read the Inconsistencies & Ambiguities table. If any `ASK:role` items have been marked `RESOLVED` by the researcher, this is a violation — the researcher must not self-resolve product/scope/rule decisions. Send the research back for correction before presenting to the user.

Present the research findings to the user as a summary:
- Modules/packages involved (or "greenfield — no code yet")
- Key API endpoints found
- Business logic discovered
- All flagged inconsistencies and ambiguities — list every `ASK:role` item with the researcher's recommended answer so the user can decide

Ask: **"Review the research above. Say 'continue' to proceed to PRD drafting, or provide feedback to adjust the research."**

For greenfield projects, also ask: **"Since there's no existing code, do you have requirements, specs, or design docs you'd like me to reference during PRD drafting?"**

If feedback is given, send it back to the researcher agent for revision. Repeat until the user says "continue."

If run logging is enabled:
```bash
echo "gate1_resume=$(date +%s)" >> "$TIMING_FILE"
```
Update state file — set `currentPhase: "writing"`.

## Phase 2: PRD Drafting (max 3 revision cycles)

If run logging is enabled: `echo "writing_start=$(date +%s)" >> "$TIMING_FILE"`

Spawn an Agent using the prompt from `~/.claude/skills/deep-analysis/prd/agents/prd-writer.md`, with `model: MODEL_MAP[prd-writer]`:
- Pass `{argument}` as the initiative name
- Pass the research document path as context
- Pass the resolved mode explicitly: "Technical Contract mode: **{TC_MODE}** (source: {TC_MODE_SOURCE}) — this is a run-level instruction; record it in your handoff as `technicalContractMode` and do not re-resolve it from project-context.md."

The prd-writer will:
1. Read the research
2. Ask clarifying questions (this is a human gate — wait for answers)
3. Draft the PRD
4. Write the handoff file

If run logging is enabled:
```bash
echo "writing_end=$(date +%s)" >> "$TIMING_FILE"
```
Append writer JSONL entry:
1. Read the writer's handoff JSON — extract `prdMetrics` (frCount, acCount, edgeCaseCount, keyEntityCount, version, isFreshDraft, failsAddressed, sectionPacksUsed) and `apiEndpoints` count
2. Append:
   ```bash
   python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py append --log-file "$LOG_FILE" --entry-type writer \
     --field "runId=$RUN_ID" \
     --field "initiative={argument}" \
     --field "agent=prd-writer" \
     --field "model=$MODEL_MAP_WRITER" \
     --field "cycle=<current_cycle>" \
     --field "startedAt=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --get writing_start --iso)" \
     --field "completedAt=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --get writing_end --iso)" \
     --field "durationSeconds=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --delta writing_start writing_end)" \
     --field "inputSummary=<research doc or revision of N FAILs>" \
     --field "outputSummary=PRD <version> with <frCount> FRs, <acCount> ACs, <edgeCaseCount> edge cases" \
     --field "artifactPath=<prd path>" \
     --field "handoffPath=<handoff path>" \
     --field 'metrics=<prdMetrics object from the handoff, verbatim JSON>'
   ```
   Pass `metrics` as the handoff's `prdMetrics` object verbatim — `--field` values that parse as JSON stay JSON, so the object is preserved rather than stringified. If `~/.claude/skills/deep-analysis/prd/scripts/run-log.py` is missing, build the line with `python3 -c` + `json.dumps`, passing the schema's fields as arguments (never with `echo` — that reintroduces the injection run-log.py exists to prevent), following the [JSONL Schema Reference](#jsonl-schema-reference).
3. Update state file — set `currentPhase: "gate2"`, push writer phase into `completedPhases`

### Gate 2: PRD Draft Review

If run logging is enabled:
```bash
echo "gate2_prompt=$(date +%s)" >> "$TIMING_FILE"
```
Update state file — set `currentPhase: "gate2"`.

**Lint the draft first.** If `~/.claude/skills/deep-analysis/prd/scripts/prd-lint.py` exists in the project, run it on the drafted PRD before prompting the user:

```bash
python3 ~/.claude/skills/deep-analysis/prd/scripts/prd-lint.py "{prd_path}" --mode prd
```

Exit 0 means clean. Any violations are mechanical facts, not opinions — surface them verbatim to the user alongside the draft notice below (one line per violation: check ID, line number, message) and note that the writer will fix them in the next revision. If the script is absent, skip this step silently.

**Cycle 1 (first draft)**: Tell the user: **"PRD draft is ready at `{prd_path}`. Review it, then say 'continue' to run the reviewer, or provide feedback for revisions."** If the lint run reported violations, append: **"prd-lint found N violation(s):"** followed by the violation lines. If feedback is given, send it back to the prd-writer for revision. Repeat until the user says "continue."

**Cycle 2+ (revision)**: Skip the human gate — the writer just applied a senior-PM ticket list the user already approved at Gate 3, so no second draft review is needed. Tell the user: **"Writer revised the PRD — running reviewer automatically."** Proceed directly to Phase 3.

If run logging is enabled:
```bash
echo "gate2_resume=$(date +%s)" >> "$TIMING_FILE"
```
Update state file — set `currentPhase: "review"`.

## Phase 3: PRD Review (max 3 revision cycles)

If run logging is enabled:
```bash
echo "review_start=$(date +%s)" >> "$TIMING_FILE"
```
Update state file — set `currentPhase: "review"`.

Track the revision count starting at 0.

### Step 3.1: Scaffold (reviewer Phase 1)

If run logging is enabled: `echo "review_scaffold_start=$(date +%s)" >> "$TIMING_FILE"`

Spawn an Agent using `~/.claude/skills/deep-analysis/prd/agents/prd-reviewer.md`, with `model: MODEL_MAP[prd-reviewer]`, and the prompt:

> "Run Phase 1 only for initiative '{argument}'. Technical Contract mode: **{TC_MODE}** (source: {TC_MODE_SOURCE}) — prefer the writer handoff's `technicalContractMode` if it disagrees, and record the resolved mode in the scaffold, the dispatch JSON, and every sub-agent prompt. Write the scaffold, determine review mode. If single mode (< 20 items), fill all matrices yourself and complete the full review (Steps 0-11). If parallel mode (>= 20 items), write the scaffold, construct sub-agent prompt files, write the dispatch JSON, then STOP."

If run logging is enabled: `echo "review_scaffold_end=$(date +%s)" >> "$TIMING_FILE"`

### Step 3.2: Check review mode

After the reviewer returns, check if a dispatch file exists:
```bash
cat {initiative_dir}/_artifacts/{argument}-review-dispatch.json 2>/dev/null
```

- **If no dispatch file**: the reviewer completed in single-agent mode. The review file and handoff are done. Skip to Gate 3.
- **If dispatch file exists**: validate it before consuming it. If `~/.claude/skills/deep-analysis/prd/scripts/validate-handoff.py` exists, run it on the dispatch file and treat any reported problem as a Phase 1 failure:
  ```bash
  python3 ~/.claude/skills/deep-analysis/prd/scripts/validate-handoff.py --type dispatch \
    "{initiative_dir}/_artifacts/{argument}-review-dispatch.json"
  ```
  Exit 0 means the dispatch is complete and consistent. On exit 1, STOP and tell the user: "Reviewer Phase 1 wrote an invalid dispatch file: [paste the reported problems]. Re-run the review." Do not dispatch sub-agents against a dispatch file with missing prompt paths or mismatched cell counts — a missing key here silently drops a whole sub-reviewer. If the script is absent, skip this check and rely on the prompt-file existence check in Step 3.3.

  Then read it. The dispatch JSON includes a `models` object with per-agent model assignments — use these for sub-agent dispatch (they match `MODEL_MAP` but are authoritative for this review run). Proceed to Step 3.3.

### Step 3.3: Dispatch sub-reviewers (parallel)

First, verify all five prompt files from the dispatch JSON exist:
```bash
for f in "{promptFiles.api}" "{promptFiles.structure}" "{promptFiles.flow}" "{promptFiles.requirements}" "{promptFiles.smells}"; do
  [ -f "$f" ] || echo "MISSING: $f"
done
```
If any are missing, STOP and tell the user: "Reviewer Phase 1 failed to write all prompt files. Missing: [list]. Re-run the review."

Read each prompt file. Paths in the dispatch JSON are absolute — use them directly, do not join with the initiative directory.

If run logging is enabled: `echo "review_dispatch_start=$(date +%s)" >> "$TIMING_FILE"`

Spawn **every sub-reviewer listed below in parallel**, using the model from `MODEL_MAP` for each:

- Agent 1 (API): read `{promptFiles.api}`, use its content as the agent prompt, `model: MODEL_MAP[review-api]`
- Agent 2 (Structure): read `{promptFiles.structure}`, use its content as the agent prompt, `model: MODEL_MAP[review-structure]`
- Agent 3 (Flow): read `{promptFiles.flow}`, use its content as the agent prompt, `model: MODEL_MAP[review-flow]`
- Agent 4 (Requirements): read `{promptFiles.requirements}`, use its content as the agent prompt, `model: MODEL_MAP[review-requirements]`
- Agent 5 (Smells): read `{promptFiles.smells}`, use its content as the agent prompt, `model: MODEL_MAP[review-smells]`

Wait for all five to complete.

If run logging is enabled: `echo "review_dispatch_end=$(date +%s)" >> "$TIMING_FILE"`

If run logging is enabled, read each sub-agent's timing file before cleanup:
```bash
for agent in api structure flow requirements smells; do
  TFILE="{initiative_dir}/_artifacts/{argument}-review-${agent}.md.timing"
  if [ -f "$TFILE" ]; then
    while IFS='=' read -r key val; do
      echo "subagent_${agent}_${key}=${val}" >> "$TIMING_FILE"
    done < "$TFILE"
  fi
done
```

### Step 3.4: Assembly (reviewer Phase 3)

If run logging is enabled: `echo "review_assembly_start=$(date +%s)" >> "$TIMING_FILE"`

Spawn an Agent using `~/.claude/skills/deep-analysis/prd/agents/prd-reviewer.md`, with `model: MODEL_MAP[prd-reviewer]`, and the prompt:

> "Run Phase 3 only for initiative '{argument}'. Sub-agents have completed. The dispatch file is at {absolute_path_to_dispatch_json}; take the Technical Contract mode from its `technicalContractMode` field rather than re-resolving it. Re-read project context, lessons, PRD, and scaffold. Assemble sub-agent outputs, fill Matrix H, run completeness verification, spot-check, dynamic findings, defect taxonomy, verdict, and commit."

If run logging is enabled:
```bash
echo "review_assembly_end=$(date +%s)" >> "$TIMING_FILE"
```
Append reviewer JSONL entry:
1. Read the reviewer's handoff JSON — extract all metrics (totalCells, failCount, failsByMatrix, smellDetection, spotCheckOverrides, defectTaxonomy, reviewMode, isReReview, previousFailsVerified, prdSize)
2. Read sub-agent timing files (if parallel mode) for per-sub-agent durations
3. Append:
   ```bash
   python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py append --log-file "$LOG_FILE" --entry-type reviewer \
     --field "runId=$RUN_ID" \
     --field "initiative={argument}" \
     --field "agent=prd-reviewer" \
     --field "model=$MODEL_MAP_REVIEWER" \
     --field "cycle=<current_cycle>" \
     --field "startedAt=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --get review_start --iso)" \
     --field "completedAt=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --get review_assembly_end --iso)" \
     --field "durationSeconds=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --delta review_start review_assembly_end)" \
     --field "inputSummary=PRD <version> at <path>, <frCount> FRs, <acCount> ACs" \
     --field "outputSummary=<verdict>: <failCount> FAILs, <totalCells> cells filled, <spotCheckOverrides> spot-check overrides" \
     --field "artifactPath=<review path>" \
     --field "handoffPath=<review handoff path>" \
     --field 'metrics=<all metrics from the handoff, verbatim JSON object>' \
     --field 'subAgentDurations={"scaffold":<delta>,"api":<delta|null>,"structure":<delta|null>,"flow":<delta|null>,"requirements":<delta|null>,"smells":<delta|null>,"assembly":<delta>}'
   ```
   Per-sub-agent deltas come from the same helper: `python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --delta subagent_api_start subagent_api_end` (and likewise for structure/flow/requirements/smells, using whatever key names the sub-agent timing files used). If `~/.claude/skills/deep-analysis/prd/scripts/run-log.py` is missing, build the line with `python3 -c` + `json.dumps`, passing the schema's fields as arguments (never with `echo` — that reintroduces the injection run-log.py exists to prevent), following the [JSONL Schema Reference](#jsonl-schema-reference).
4. Update state file — set `currentPhase: "gate3"`, push reviewer phase into `completedPhases`

### Step 3.6: Defensive cleanup

After the reviewer returns from Phase 3, verify the commit succeeded before deleting temporary files. If the commit failed, the reviewer preserves these files as evidence — do not delete them. In a non-git project the reviewer skips its commit by design, so clean up directly — there is no commit to protect.

```bash
# Clean up unless a git repo exists AND the reviewer's commit did NOT land.
# Single-quoted pattern: {argument} can never be shell-interpreted.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1 && ! git log --oneline -1 | grep -q '{argument}.*PRD review'; then
  echo "WARNING: Review commit not found — keeping sub-agent files for debugging."
else
  rm -f {initiative_dir}/_artifacts/*-review-prompt-*.md {initiative_dir}/_artifacts/*-review-dispatch.json
  rm -f {initiative_dir}/_artifacts/*-review-api.md {initiative_dir}/_artifacts/*-review-structure.md {initiative_dir}/_artifacts/*-review-flow.md {initiative_dir}/_artifacts/*-review-requirements.md {initiative_dir}/_artifacts/*-review-smells.md
  rm -f {initiative_dir}/_artifacts/*-review-*.md.timing
fi
```

The reviewer now has the review file and handoff ready.

## Phase 3.5: Senior PM Judgment

The reviewer is a mechanical checker: its FAIL list is a set of claims, and some of them are variance, overreach, duplicates of one root cause, or valid findings whose suggested fix would make the product worse. Do NOT send that list to the writer. Spawn the senior PM to judge it first.

**This phase runs on every review pass — including the pass that returns READY.** A clean technical review says the checklists are satisfied; it does not say the product is right.

If run logging is enabled: `echo "senior_pm_start=$(date +%s)" >> "$TIMING_FILE"`

Update state file — set `currentPhase: "senior-pm"`.

### Step 3.5.1: Determine the run mode

```bash
[ -f "{initiative_dir}/_artifacts/{argument}-senior-pm-handoff.json" ] && echo "delta" || echo "full"
```

- **No prior senior-PM handoff** → this is the first review pass → `full` mode. The senior PM judges every FAIL, challenges the PRD as a product, makes the decisions, and writes tickets. A **first-pass READY verdict still gets `full` mode** — there are no FAILs to judge, but the product challenge applies.
- **A prior senior-PM handoff exists** → this is a later pass → `delta` mode. The senior PM verifies its earlier tickets were applied, judges only the NEW FAILs, and does not revisit earlier dispositions. A **later-pass READY verdict gets `delta` mode**, not a skip: the tickets still need verifying.

Decide once, then enforce — re-running a full judgment every cycle produces new opinions every cycle and the PRD never stabilizes.

### Step 3.5.2: Spawn the senior PM

Spawn an Agent using `~/.claude/skills/deep-analysis/prd/agents/prd-senior-pm.md`, with `model: MODEL_MAP[prd-senior-pm]` (default `sonnet`), and the prompt:

> "Judge the review for initiative '{argument}'. Run mode: **{full|delta}** (this is review pass {N}). Technical Contract mode: **{TC_MODE}** (source: {TC_MODE_SOURCE}) — in `slim` mode a FAIL demanding Technical-Contract content is overreach; reject it citing the configured mode. The PRD is at {prd_path}. The technical review is at {review_path} and its handoff at {review_handoff_path}; the verdict was {READY|NEEDS_REVISION}. The research doc is at {research_path} and the writer's Q&A log at {qa_path} if it exists. {In delta mode: 'Your previous decision sheet is at {senior_pm_review_path} and your previous handoff at {senior_pm_handoff_path} — verify each prior ticket was applied, judge only NEW FAILs, and do not revisit earlier dispositions.'} Write the decision sheet and the handoff JSON, then commit them. Do not edit the PRD or the review."

If run logging is enabled: `echo "senior_pm_end=$(date +%s)" >> "$TIMING_FILE"`

### Step 3.5.3: Validate the senior-PM handoff

If `~/.claude/skills/deep-analysis/prd/scripts/validate-handoff.py` exists, run it before consuming the handoff:

```bash
python3 ~/.claude/skills/deep-analysis/prd/scripts/validate-handoff.py --type senior-pm \
  "{initiative_dir}/_artifacts/{argument}-senior-pm-handoff.json"
```

Exit 0 means the decision sheet's counts, tickets, and dispositions are internally consistent. On exit 1, STOP and tell the user: "The senior PM wrote an invalid handoff: [paste the reported problems]. Re-run Phase 3.5." Do not present a Gate 3 whose disposition counts disagree with its own ticket list. If the script is absent, skip this check.

### Step 3.5.4: Log the senior-PM entry

Append the `senior-pm` JSONL entry:

```bash
python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py append --log-file "$LOG_FILE" --entry-type senior-pm \
  --field "runId=$RUN_ID" \
  --field "initiative={argument}" \
  --field "agent=prd-senior-pm" \
  --field "model=$MODEL_MAP_SENIOR_PM" \
  --field "cycle=<current_cycle>" \
  --field "startedAt=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --get senior_pm_start --iso)" \
  --field "completedAt=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --get senior_pm_end --iso)" \
  --field "durationSeconds=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --delta senior_pm_start senior_pm_end)" \
  --field "inputSummary=<mode> judgment of <failCount> FAILs in <review path>" \
  --field "outputSummary=<ticketCount> tickets, <reject count> FAILs rejected, <escalations> escalations" \
  --field "artifactPath=<senior-pm decision sheet path>" \
  --field "handoffPath=<senior-pm handoff path>" \
  --field 'metrics=<{"mode":…,"failsJudged":…,"rootCauses":…,"dispositionCounts":{…},"ticketCount":…,"escalations":…,"ticketsVerified":{…}} — built from the handoff, verbatim JSON>'
```

If `~/.claude/skills/deep-analysis/prd/scripts/run-log.py` is missing, build the line with `python3 -c` + `json.dumps`, passing the schema's fields as arguments (never with `echo` — that reintroduces the injection run-log.py exists to prevent), following the [JSONL Schema Reference](#jsonl-schema-reference).

Update state file — set `currentPhase: "gate3"`, push the senior-pm phase into `completedPhases`.

### Gate 3: Senior-PM Decisions + Proposed Lessons

If run logging is enabled:
```bash
echo "gate3_prompt=$(date +%s)" >> "$TIMING_FILE"
```
Update state file — set `currentPhase: "gate3"`.

Present the senior-PM decision sheet AND proposed lessons together in one output. **The raw reviewer FAIL list is NOT the gate content** — the senior PM has already judged it, and re-presenting 90 unjudged FAILs is exactly the noise this phase exists to remove. Read `_artifacts/{argument}-senior-pm-handoff.json` and its decision sheet and present, in this order:

**First**, the verdict and the judgment summary:
- The reviewer verdict (READY / NEEDS_REVISION), the senior-PM run mode (`full` / `delta`), and the deflation: "the reviewer raised N FAIL cells; the senior PM judged them into M root causes."
- The **disposition counts** from `dispositionCounts`: `fix-technical`, `fix-product`, `reject`, `escalate`.
- In `delta` mode, the `ticketsVerified` counts — applied / partial / not-applied — so the user can see whether the last revision actually landed.

**Then**, the **decisions made** — every `fix-product` ticket, with its decided behavior, its one-line rationale, and its evidence. These are calls the senior PM made on the user's behalf; the user sees each one before any revision starts. Also surface any "Harmful Fixes Overridden" rows: what the reviewer suggested, why it would have hurt, and what the ticket says instead.

**Then**, the **rejected FAILs** — each `rejectedFails` entry with its matrix row and reason (not real / overreach / variance / no impact / fix would harm). These will NOT be fixed. The user is seeing them precisely so an override is possible.

**Then**, the **escalations** — and these are the only questions in the gate. For each: the question, why it could not be grounded in evidence, and the senior PM's recommendation. If `escalate` is 0, say "No escalations — every finding was decided from evidence." If it is greater than 5, say so and note that the senior PM flagged itself as under-deciding.

**Then**, the **ticket list** — IDs, types, and one-line instructions, so the user knows exactly what the writer will do.

**Then**, immediately show proposed lessons (if any). For each lesson, show:
- Number, name
- What was caught
- Writer rule (prevention)
- Reviewer check (detection)

If no lessons were proposed, say "No new lessons proposed."

**Then**, show proposed glossary terms (if any). Collect proposals from BOTH the writer's handoff (`proposedGlossaryTerms`) and the reviewer's handoff/review document. Deduplicate by term name — if both proposed the same term, prefer the reviewer's definition (it has the benefit of seeing the full PRD). For each term, show:
- Number, term
- Proposed definition
- Reason

If no glossary terms were proposed, say "No new glossary terms proposed."

**Then**, show proposed vocabulary entries (if any). Collect proposals from BOTH the writer's handoff (`proposedVocabularyEntries`) and the reviewer's handoff/review document. Deduplicate by endpoint + field — if both proposed the same field mapping, prefer the reviewer's semantic name. Group entries by endpoint file. For new files, note "(new file)". For each entry, show:
- Number, endpoint
- API field
- Proposed semantic name
- Reason

If no vocabulary entries were proposed, say "No new vocabulary entries proposed."

**Then**, show Proposed Shared Requirements (if any). Collect proposals from the writer's handoff, the senior PM's handoff, and the reviewer's handoff/review document (`proposedSharedRequirements` in each). Deduplicate by rule substance — if two agents proposed the same rule, keep one entry and note both origins. For each proposal, show:
- Number, rule (stated as a rule, never a feature requirement)
- Why universal — with the recurrence cited (which initiatives decided this before)
- Origin (the question, finding, or decision that surfaced it)

If no shared requirements were proposed, say "No new shared requirements proposed."

**Then**, ask for action — one prompt covering the dispositions, lessons, glossary terms, vocabulary, and shared requirements. The user has three powers over the senior PM's work:

- **(a) Answer the escalations** — each answer becomes an additional ticket for the writer, holding the user's decision word for word.
- **(b) Veto or override any disposition** — turn a `reject` back into a ticket ("fix F-14 after all"), drop a ticket ("skip T-3"), or replace a `fix-product` decision with a different one. The senior PM's dispositions are proposals with authority, not commands. Record every override: it changes the ticket list you pass to the writer, and the writer applies the amended list.
- **(c) Say "go"** — accept the dispositions as written and start the revision.

Phrase it as:
- If there are zero tickets (READY with no findings, or a delta pass where everything landed): **"No revision needed. Approve lessons: all / specific (e.g., '1 and 3') / skip. Approve glossary terms: all / specific / skip. Approve vocabulary entries: all / specific / skip. Approve SRs: all / specific / skip. Then we're done."**
- If there are tickets: **"'go' to send the N tickets to prd-writer, or veto/override any disposition first (e.g., 'un-reject F-14', 'drop T-3', 'change T-5's decision to X'). Answer any escalations above. Or 'override' to approve the PRD as-is without revising. For lessons: all / specific / skip. For glossary terms: all / specific / skip. For vocabulary entries: all / specific / skip. Approve SRs: all / specific / skip."**

Apply every veto/override to the ticket list before spawning the writer. Do NOT ask the senior PM to re-run: the user's decision is final and does not need re-judging.

If run logging is enabled:
```bash
echo "gate3_resume=$(date +%s)" >> "$TIMING_FILE"
```

On lesson approval, spawn a new Agent using `~/.claude/skills/deep-analysis/prd/agents/prd-reviewer.md`, with `model: MODEL_MAP[prd-reviewer]`, and the prompt: "Run only Step 12. Write these approved lessons to `.claude/prd-lessons.md`: [list the approved lesson names and their content from the review file]. The review file is at {review_path}." This is a targeted callback — the agent reads the review, extracts the approved lessons, and appends them to the lessons file.

On glossary term approval, spawn a new Agent using `~/.claude/skills/deep-analysis/prd/agents/prd-reviewer.md`, with `model: MODEL_MAP[prd-reviewer]`, and the prompt: "Run only Step 13. Write these approved glossary terms to the Domain Glossary table in `.claude/project-context.md`: [list the approved terms with their definitions]. The review file is at {review_path}." This is a targeted callback — the agent reads project-context.md and appends the approved terms to the glossary table.

On vocabulary entry approval, spawn a new Agent using `~/.claude/skills/deep-analysis/prd/agents/prd-reviewer.md`, with `model: MODEL_MAP[prd-reviewer]`, and the prompt: "Run only Step 14. Write these approved vocabulary entries: [list the approved entries grouped by endpoint, with file paths and actions]. The initiative is {argument}." This is a targeted callback — the agent creates or updates vocabulary files in `semantic-vocabulary/`.

On shared-requirement approval, spawn a new Agent using `~/.claude/skills/deep-analysis/prd/agents/prd-reviewer.md`, with `model: MODEL_MAP[prd-reviewer]`, and the prompt: "Run only Step 15. Write these approved shared requirements to `docs/shared-requirements.md`: [list the approved rules with their whyUniversal and origin]. The initiative is {argument}." This is a targeted callback — the agent appends each approved rule with the next sequential `SR-NN` id and commits. "Skip" writes nothing; the write-guard in `~/.claude/skills/deep-analysis/prd/rules/shared-requirements.md` allows this write only downstream of the user's explicit approval here.

If lessons, glossary terms, vocabulary entries, and shared requirements are all approved, spawn all four callbacks in parallel — they write to different files and don't conflict.

If "go" (or "revise"): increment the revision count. If run logging is enabled, increment `cycle` in the state file and set `currentPhase: "revision"`.
  - If revision count < 3: spawn a new prd-writer agent with `model: MODEL_MAP[prd-writer]` and the prompt: "This is a revision cycle. Read the existing PRD at {prd_path} and the senior-PM ticket file at {senior_pm_review_path} (handoff: {senior_pm_handoff_path}). Follow Step 3.5 (Revision Mode) — apply each ticket exactly. `fix-product` tickets hold a decision already made: implement it as written, do not re-decide. Do not fix anything on the Rejected FAILs list — those were overridden. If something needs a product decision no ticket covers, leave it and add an Open Question tagged `ASK:PM`. Do not rewrite the entire PRD. [If the user vetoed or added anything at Gate 3: 'The user amended the ticket list: <list the amendments>.']" **Pass the ticket file, not the raw review** — the writer's Step 3.5 consumes tickets. The writer handles versioning, targeted edits, and handoff. **After the writer completes the revision, return to Step 3.1 to re-run the review**, which will be followed by Phase 3.5 in `delta` mode.
  - If revision count = 3: tell the user: **"This PRD has gone through 3 revision cycles and still has open tickets. Remaining tickets: [list]. Options: 'override' to approve as-is, 'continue' to try one more cycle, or 'stop' to pause and resolve issues manually."**
If "override": mark as approved and end.

The **cycle-2+ Gate-2 skip stays as it is** (see Gate 2): the writer just applied a ticket list the user already saw and approved at Gate 3, so there is no second draft review to hold. The senior-PM gate has already happened.

## Completion

### Write Run Log (if enabled)

If run logging is enabled in project-context.md, finalize the log before summarizing:

1. Record the end time:
   ```bash
   echo "pipeline_end=$(date +%s) $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$TIMING_FILE"
   ```

2. Compute human wait time from the gate pairs — `python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --delta gate1_prompt gate1_resume` for each of gate1/gate2/gate3, summed. A missing key exits 1 and prints nothing (e.g., the pipeline ended before Gate 3) — skip that gate. If `~/.claude/skills/deep-analysis/prd/scripts/run-log.py` is missing, read the timing file with a `while IFS='=' read -r key val` loop and subtract the epochs yourself.

3. Append the **pipeline summary** JSONL entry:
   ```bash
   python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py append --log-file "$LOG_FILE" --entry-type pipeline \
     --field "runId=$RUN_ID" \
     --field "initiative={argument}" \
     --field "agent=create-prd" \
     --field "model=opus" \
     --field "profile=<profile>" \
     --field "cycle=<final_cycle>" \
     --field "startedAt=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --get pipeline_start --iso)" \
     --field "completedAt=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --get pipeline_end --iso)" \
     --field "durationSeconds=$(python3 ~/.claude/skills/deep-analysis/prd/scripts/run-log.py timing --file "$TIMING_FILE" --delta pipeline_start pipeline_end)" \
     --field "inputSummary=Initiative: {argument}, full pipeline run" \
     --field "outputSummary=<totalCycles> cycles: <summary of each cycle verdict>" \
     --field "artifactPath=<final prd path>" \
     --field "handoffPath=null" \
     --field 'metrics={"totalCycles":<count>,"finalVerdict":"<READY|NEEDS_REVISION|OVERRIDE>","technicalContractMode":"<TC_MODE>","technicalContractModeSource":"<TC_MODE_SOURCE>","humanWaitSeconds":<sum>,"agentDurationSeconds":<total minus human>,"gateDurations":{"gate1":<delta|null>,"gate2":<delta|null>,"gate3":<delta|null>},"lessonsApproved":<count>,"glossaryTermsApproved":<count>,"sharedRequirementsApproved":<count>}'
   ```
   Gate deltas come from the helper too — `--delta gate1_prompt gate1_resume` per gate; skip a gate whose pair is missing. If `~/.claude/skills/deep-analysis/prd/scripts/run-log.py` is missing, build the line with `python3 -c` + `json.dumps`, passing the schema's fields as arguments (never with `echo` — that reintroduces the injection run-log.py exists to prevent), following the [JSONL Schema Reference](#jsonl-schema-reference).

   Individual agent entries (researcher, writer, reviewer, senior-pm) were already appended after each phase completed — the pipeline entry is the final summary that ties them together via `runId`.

4. Delete the timing file and state file:
   ```bash
   rm -f "$TIMING_FILE" "$STATE_FILE"
   ```

5. Commit the run log, if the project is a git repository (do NOT push):
   ```bash
   if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
     git add "$LOG_FILE"
     git commit -m "docs: add {initiative} run log ({profile} profile, $RUN_ID)"
   fi
   ```

> **Note on token usage and cost**: Token counts are not available programmatically during a Claude Code session. To correlate cost with run logs, check your Anthropic dashboard usage for the session's time window. The `modelMap` and phase durations in the run log provide the basis for cost estimation.

### JSONL Schema Reference

Each line in `.claude/prd-run-log.jsonl` is one of these entry types:

**Common fields** (all entries): `entryType`, `runId` (YYYYMMDD-HHMMSS, shared across pipeline), `initiative`, `agent`, `model`, `profile`, `cycle` (1 = first draft+review), `startedAt`, `completedAt`, `durationSeconds`, `inputSummary`, `outputSummary`, `artifactPath`, `handoffPath`

**`"researcher"`** metrics: `endpointsFound`, `filesRead`, `ambiguitiesFlagged`

**`"writer"`** metrics: `frCount`, `acCount`, `edgeCaseCount`, `keyEntityCount`, `version`, `sectionPacksUsed`, `productConstantCount`, `displayRuleCount`, `isFreshDraft`, `failsAddressed`

**`"reviewer"`** metrics: `totalCells`, `filledCells`, `subAgentCells`, `orchestratorCells`, `failCount`, `failsByMatrix` (A/B/C/S/D1/D2/E/F/G/H/I/P), `smellDetection` (totalChecked/linguisticSmellsFound/separationSmellsFound), `spotCheckOverrides`, `verdict`, `reviewMode`, `isReReview`, `previousFailsVerified`, `defectTaxonomy` (omission/ambiguity/inconsistency/incorrectFact/extraneousInfo/misplacedRequirement), `proposedLessons`, `proposedGlossaryTerms`. Plus `subAgentDurations` (scaffold/api/structure/flow/requirements/smells/assembly — null in single mode).

**`"senior-pm"`** metrics: `mode` ("full" | "delta"), `failsJudged` (FAIL cells read — NEW cells only in delta mode), `rootCauses` (findings after collapse), `dispositionCounts` (fixTechnical/fixProduct/reject/escalate), `ticketCount`, `escalations`, and — delta mode only — `ticketsVerified` (applied/partial/notApplied)

**`"pipeline"`** metrics: `totalCycles`, `finalVerdict`, `technicalContractMode` ("slim" | "full"), `technicalContractModeSource` ("run-override" | "project-context" | "default"), `humanWaitSeconds`, `agentDurationSeconds`, `gateDurations` (gate1/gate2/gate3), `lessonsApproved`, `glossaryTermsApproved`, `sharedRequirementsApproved`

**`"terminated"`** (abandoned runs): `diedInPhase`, `completedPhases` (array of phase summaries), `reason` ("abandoned")

**`"judge"`** (LLM-as-Judge scores, appended after evaluation runs): `judgeModel`, `prdPath`, `reviewPath`, `scores` (object with dimensions: `completeness`, `precision`, `apiAccuracy`, `edgeCaseCoverage`, `testability`, `consistency`, `implementability` — each 1-5), `totalScore` (sum), `reasoning` (object with per-dimension explanation + evidence quotes)

**Optional field — all entries**: `experiment` (object, present only during `/evaluate` runs): `experimentId` (e.g., "exp6"), `batchId` (groups all runs in one evaluation session), `swapId` (e.g., "baseline", "swap-d"), `swapAgent` (agent name that was swapped, or null for baseline), `swapFrom` (original model), `swapTo` (new model), `runNumber` (1-based, for repeated runs), `fixtureSet` (path to fixtures used)

### Summary

Summarize what was produced:
- Research document path
- Technical Contract mode used, and where it came from (run override / project-context / default)
- PRD path (with version)
- Review path
- Senior-PM decision sheet path, with the final disposition counts
- Handoff file paths
- Final verdict
- Lessons added (if any)
- Run log path (if logging enabled)
