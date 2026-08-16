#!/usr/bin/env python3
"""prd-lint — deterministic enforcement layer for mechanical PRD rules.

Every rule in this file is mechanically checkable: no judgment, no LLM.
It exists because prompt-level discipline ("the agent MUST grep...") is
probabilistic, while a script cannot forget.

Usage:
    python3 scripts/prd-lint.py <file.md> [--mode prd|review|shared-requirements] [--format text|json]

Exit codes:
    0 — clean
    1 — violations found
    2 — usage / parse error

Checks, mode `prd`:
    LINT-001  every [V<n>] marker in the Behavioral Contract resolves to a
              `| V<n> |` row in a Vocabulary table — the Semantic Vocabulary
              table in the Behavioral Contract (slim mode), a per-endpoint
              Vocabulary table in the Technical Contract (full mode), or both;
              duplicate V-numbers *within one layer* are violations, while the
              same V-number appearing in both layers is the repetition the
              placement rule expects
    LINT-002  unchecked writer-confirmation checkboxes
    LINT-003  branch-name (non commit-pinned) /blob/ URLs
    LINT-004  Changelog version numbers must be non-decreasing top-to-bottom
    LINT-005  Open Questions must hold no OQ- items — only a "None" line
    LINT-006  no `> **GUIDE**` blocks remain
    LINT-007  analytics binding: ACs reference AE-<n>, never raw event names;
              every AE-<n> is referenced by at least one AC
    LINT-008  wire-value leak: API Field values must not appear in
              FR / AC / Edge Case lines. `API Field` is an optional, dev-owned
              column, so a slim PRD carries no source for this scan — it then
              skips cleanly rather than reporting anything
    LINT-009  template conformance: `## Behavioral Contract` and
              `## Boundaries` present verbatim; `## Technical Contract`
              present unless the PRD is slim (no Technical Contract), in which
              case the behavioral anchors Product Constants / Semantic
              Vocabulary / Display Rules must be present instead
    LINT-010  Product Constants integrity (only runs when the PRD has a
              Product Constants section): every PC-<n> row is referenced by at
              least one FR / AC / Edge Case, and no FR / AC states a bound as a
              bare inline duration instead of citing a PC-<n> row
    LINT-011  slim shape only (no `## Technical Contract` heading): the
              Analytics Events and Support sections carry no transport
              taxonomy — no `error_status_code` / `status_code` / `http_error`
              / `parse_error` tokens and no literal status-number encoding
              rules ("0 for transport failure", "200 for ..."). Failure
              classes are product-semantic (`unreachable`, `rejected`,
              `unusable_response`, `incomplete_record`); wire encodings are
              dev-owned diagnostics. Never fires in full mode
    LINT-012  slim shape only: Semantic Vocabulary Type cells are semantic
              types (money amount, instant, string, enumeration, list of
              <entity>) — no `minor units`, `epoch`, `milliseconds`/`seconds`,
              `ISO-` bases, and no parenthesized encoding after a base type
              ("number (minor units)"). Full mode may keep encoded types in
              its per-endpoint tables, so the check never fires there
    LINT-013  slim shape only: no code wiring outside the Dependencies
              section — repo path fragments (`src/…`, `packages/…`),
              source-file references (`.ts` / `.tsx` / `.dart`), and
              backticked `paths.*` route constants. Markdown evidence links
              (text + http(s) target) and bare URLs are exempt — pinned
              citations, e.g. Mobile Baseline links into a mobile repo, are
              evidence, not web wiring; full mode is exempt entirely
    LINT-014  slim shape only, heuristic: design-mechanism phrases in the
              Behavioral Contract — "politely", "assertively", "stacked in
              that order", "single column", "shaped like". Deliberately
              narrow (wording varies); the reviewer's separation pass is the
              real net for design-mechanism prescriptions

Checks, mode `review`:
    LINT-101  zero [PENDING] cells
    LINT-102  verdict cells carry only PASS / FAIL: ... / N/A (no WARN, INFO)
    LINT-103  TOTAL_CELLS / SUB_AGENT_CELLS / ORCHESTRATOR_CELLS present,
              integers, and TOTAL == SUB + ORCH

Checks, mode `shared-requirements` (migration scan for a consuming project's
docs/shared-requirements.md — run at framework install/upgrade; findings are
migration items for the SR owner, never PRD defects):
    LINT-201  Localization-section mandate — an SR still demands a
              Localization section, localization-key tables, or listed
              translations in the PRD. Copy, localization keys, and
              translations are design-owned; the PRD no longer contains a
              Localization section
    LINT-202  Technical-Contract-mandatory language — an SR mandates the
              Technical Contract or one of its tables (Data Sources, Error
              Classification, Route Mapping, per-endpoint blocks). Slim mode
              omits the Technical Contract entirely, so the mandate is
              unsatisfiable there; the SR must defer to the project's mode or
              carry an explicit override
    LINT-203  literal-copy mandate — an SR requires exact / literal / final /
              verbatim copy or strings in the PRD. Requirements state copy
              intent; literal copy is design-owned (the sole exception is
              legally mandated wording, quoted with its source)
    Lines that state the current rule ("design-owned", "must not", "no
    longer") are exempt — the scan targets stale obligations, not the
    sentences that correct them.

Stdlib only, Python 3.9+. Consumers copy this single file into their project.
Fenced code-block interiors are excluded from every scan so that documentation
examples inside a PRD are never linted as content.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# Markdown model
# --------------------------------------------------------------------------

FENCE_RE = re.compile(r"^\s{0,3}(?:```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
TABLE_ROW_RE = re.compile(r"^\s*\|")
TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|?\s*$")


class Heading:
    """One markdown ATX heading."""

    def __init__(self, level: int, title: str, line: int) -> None:
        self.level = level
        self.title = title
        self.line = line  # 0-based index into Document.lines

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "Heading(level=%d, title=%r, line=%d)" % (
            self.level,
            self.title,
            self.line,
        )


class Table:
    """A contiguous run of markdown table rows."""

    def __init__(self, header_line: int, header_cells: List[str]) -> None:
        self.header_line = header_line
        self.header_cells = header_cells
        self.rows: List[Tuple[int, List[str]]] = []  # (0-based line, cells)

    @property
    def line_span(self) -> Tuple[int, int]:
        last = self.rows[-1][0] if self.rows else self.header_line
        return (self.header_line, last)

    def column(self, pattern: str) -> Optional[int]:
        """Index of the first header cell matching `pattern` (case-insensitive)."""
        rx = re.compile(pattern, re.IGNORECASE)
        for idx, cell in enumerate(self.header_cells):
            if rx.search(cell):
                return idx
        return None


def split_row(line: str) -> List[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [cell.strip() for cell in body.split("|")]


class Document:
    """Parsed markdown document with heading-tree and table access."""

    def __init__(self, text: str) -> None:
        self.lines = text.split("\n")
        self.in_fence = self._scan_fences()
        self.headings = self._scan_headings()

    # -- parsing ---------------------------------------------------------

    def _scan_fences(self) -> List[bool]:
        flags = [False] * len(self.lines)
        open_fence = False
        for idx, line in enumerate(self.lines):
            if FENCE_RE.match(line):
                # The fence markers themselves count as fenced content.
                flags[idx] = True
                open_fence = not open_fence
                continue
            flags[idx] = open_fence
        return flags

    def _scan_headings(self) -> List[Heading]:
        found: List[Heading] = []
        for idx, line in enumerate(self.lines):
            if self.in_fence[idx]:
                continue
            m = HEADING_RE.match(line)
            if m:
                found.append(Heading(len(m.group(1)), m.group(2).strip(), idx))
        return found

    # -- lookup ----------------------------------------------------------

    def live_lines(self, start: int = 0, end: Optional[int] = None):
        """Yield (0-based index, text) for lines outside fenced code blocks."""
        if end is None:
            end = len(self.lines)
        for idx in range(max(0, start), min(end, len(self.lines))):
            if not self.in_fence[idx]:
                yield idx, self.lines[idx]

    def heading_exact(self, title: str, level: int) -> Optional[Heading]:
        for h in self.headings:
            if h.level == level and h.title == title:
                return h
        return None

    def headings_containing(
        self, needle: str, min_level: int = 1, max_level: int = 6
    ) -> List[Heading]:
        low = needle.lower()
        return [
            h
            for h in self.headings
            if low in h.title.lower() and min_level <= h.level <= max_level
        ]

    def body(self, heading: Heading) -> Tuple[int, int]:
        """Line range (start, end) of a heading's content, end exclusive."""
        start = heading.line + 1
        for h in self.headings:
            if h.line > heading.line and h.level <= heading.level:
                return (start, h.line)
        return (start, len(self.lines))

    def section(self, title: str, level: int = 2) -> Optional[Tuple[int, int]]:
        h = self.heading_exact(title, level)
        return self.body(h) if h else None

    def subheadings(self, span: Tuple[int, int]) -> List[Heading]:
        start, end = span
        return [h for h in self.headings if start <= h.line < end]

    def enclosing_titles(self, line: int) -> List[str]:
        """Titles of every heading that encloses `line`, outermost first."""
        stack: List[Heading] = []
        for h in self.headings:
            if h.line >= line:
                break
            while stack and stack[-1].level >= h.level:
                stack.pop()
            stack.append(h)
        return [h.title for h in stack]

    def tables(self, start: int = 0, end: Optional[int] = None) -> List[Table]:
        if end is None:
            end = len(self.lines)
        tables: List[Table] = []
        current: Optional[Table] = None
        for idx in range(max(0, start), min(end, len(self.lines))):
            if self.in_fence[idx]:
                current = None
                continue
            line = self.lines[idx]
            if not TABLE_ROW_RE.match(line):
                current = None
                continue
            if TABLE_SEP_RE.match(line):
                continue  # header separator — not a data row
            cells = split_row(line)
            if current is None:
                current = Table(idx, cells)
                tables.append(current)
            else:
                current.rows.append((idx, cells))
        return tables


# --------------------------------------------------------------------------
# Violations
# --------------------------------------------------------------------------


class Violation:
    def __init__(self, check_id: str, line: int, message: str) -> None:
        self.id = check_id
        self.line = line  # 1-based, as reported
        self.message = message

    def as_dict(self) -> Dict[str, object]:
        return {"id": self.id, "line": self.line, "message": self.message}


def add(out: List[Violation], check_id: str, line_index: int, message: str) -> None:
    """Append a violation; `line_index` is 0-based and becomes 1-based."""
    out.append(Violation(check_id, line_index + 1, message))


# --------------------------------------------------------------------------
# Shared extraction helpers
# --------------------------------------------------------------------------

V_ROW_RE = re.compile(r"^\s*\|\s*\*{0,2}V(\d+)\*{0,2}\s*\|")
V_MARKER_RE = re.compile(r"\[V(\d+)\]")
PLACEHOLDER_RE = re.compile(r"^[\[<{]")


def _vocabulary_tables_under(doc: Document, section: str) -> List[Table]:
    span = doc.section(section, 2)
    if span is None:
        return []
    tables: List[Table] = []
    for heading in doc.subheadings(span):
        if "vocabulary" not in heading.title.lower():
            continue
        tables.extend(doc.tables(*doc.body(heading)))
    return tables


def behavioral_vocabulary_tables(doc: Document) -> List[Table]:
    """Tables under a `Vocabulary` heading inside the Behavioral Contract.

    This is the slim-mode home of the `[V#]` dictionary: `### Semantic
    Vocabulary`. The PRD names the concepts here; binding them to wire fields
    is dev-owned and optional.
    """
    return _vocabulary_tables_under(doc, "Behavioral Contract")


def technical_vocabulary_tables(doc: Document) -> List[Table]:
    """Tables under a `Vocabulary` heading inside the Technical Contract."""
    return _vocabulary_tables_under(doc, "Technical Contract")


def vocabulary_tables(doc: Document) -> List[Table]:
    """Every Vocabulary table, in either layer.

    A full-mode PRD repeats its V-numbers in the Technical Contract with the
    API-field binding attached; a slim-mode PRD defines them once in the
    behavioral layer. Both are valid sources for resolving a marker.
    """
    return behavioral_vocabulary_tables(doc) + technical_vocabulary_tables(doc)


def strip_cell(cell: str) -> str:
    return cell.strip().strip("`").strip("*").strip()


def is_slim(doc: Document) -> bool:
    """A PRD without a `## Technical Contract` heading is in the slim shape.

    The slim-only checks below gate on this: in full mode the Technical
    Contract legitimately carries wire taxonomy, encodings, and code wiring,
    so those checks must never fire there.
    """
    return doc.heading_exact("Technical Contract", 2) is None


def analytics_table(doc: Document) -> Optional[Table]:
    for heading in doc.headings_containing("Analytics Events"):
        for table in doc.tables(*doc.body(heading)):
            if table.column(r"event\s*name") is not None:
                return table
    return None


def fr_ac_lines(doc: Document) -> List[Tuple[int, str]]:
    """FR / AC lines plus Edge Cases table rows — the behavioral prose."""
    picked: Dict[int, str] = {}
    id_re = re.compile(r"\b(?:FR|AC)-\d+\b")
    for idx, line in doc.live_lines():
        if id_re.search(line):
            picked[idx] = line
    for heading in doc.headings_containing("Edge Cases"):
        for table in doc.tables(*doc.body(heading)):
            for idx, _cells in table.rows:
                picked[idx] = doc.lines[idx]
    return sorted(picked.items())


def word_occurrence(value: str) -> re.Pattern:
    return re.compile(
        r"(?<![A-Za-z0-9_.\-])" + re.escape(value) + r"(?![A-Za-z0-9_.\-])"
    )


# --------------------------------------------------------------------------
# Mode `prd` checks
# --------------------------------------------------------------------------


def _collect_v_rows(
    doc: Document, tables: Sequence[Table], layer: str, out: List[Violation]
) -> Dict[int, int]:
    """V-number → defining line, reporting duplicates *within this layer*."""
    defined: Dict[int, int] = {}
    for table in tables:
        for idx, _cells in table.rows:
            m = V_ROW_RE.match(doc.lines[idx])
            if not m:
                continue
            num = int(m.group(1))
            if num in defined:
                add(
                    out,
                    "LINT-001",
                    idx,
                    "duplicate vocabulary V-number V%d in the %s (first "
                    "defined on line %d)" % (num, layer, defined[num] + 1),
                )
                continue
            defined[num] = idx
    return defined


def check_001_vocabulary_markers(doc: Document, out: List[Violation]) -> None:
    # Duplicate detection is per layer on purpose: a full-mode PRD repeats each
    # V-number in the Technical Contract to attach the API-field binding, which
    # the placement rule expects. Two rows for one number *inside* a layer is
    # still a defect — that is a second definition, not a repetition.
    behavioral = _collect_v_rows(
        doc, behavioral_vocabulary_tables(doc), "Behavioral Contract", out
    )
    technical = _collect_v_rows(
        doc, technical_vocabulary_tables(doc), "Technical Contract", out
    )
    defined = set(behavioral) | set(technical)

    bc = doc.section("Behavioral Contract", 2)
    if bc is None:
        return
    for idx, line in doc.live_lines(*bc):
        for m in V_MARKER_RE.finditer(line):
            num = int(m.group(1))
            if num not in defined:
                add(
                    out,
                    "LINT-001",
                    idx,
                    "[V%d] marker does not resolve to a `| V%d |` row in the "
                    "Semantic Vocabulary table or any Vocabulary table inside "
                    "the Technical Contract" % (num, num),
                )


CONFIRMATION_RE = re.compile(r"^\s*\*\*[^*]*confirmation\*\*\s*:", re.IGNORECASE)
LIST_ITEM_RE = re.compile(r"^\s*[-*+]\s+")
UNCHECKED_RE = re.compile(r"^\s*[-*+]\s+\[\s\]")
AC_EXEMPT_TITLES = (
    "acceptance criteria",
    "loading states",
    "error states",
    "empty states",
)


def _is_ac_context(doc: Document, line_index: int) -> bool:
    titles = [t.lower() for t in doc.enclosing_titles(line_index)]
    return any(t in AC_EXEMPT_TITLES for t in titles)


def check_002_unchecked_confirmations(doc: Document, out: List[Violation]) -> None:
    total = len(doc.lines)
    for idx, line in doc.live_lines():
        if not CONFIRMATION_RE.match(line):
            continue
        label = line.strip()
        j = idx + 1
        while j < total:
            if doc.in_fence[j]:
                break
            text = doc.lines[j]
            if text.strip() == "":
                k = j + 1
                while k < total and doc.lines[k].strip() == "":
                    k += 1
                if k < total and not doc.in_fence[k] and LIST_ITEM_RE.match(doc.lines[k]):
                    j = k
                    continue
                break
            if not LIST_ITEM_RE.match(text):
                break
            if UNCHECKED_RE.match(text) and not _is_ac_context(doc, j):
                add(
                    out,
                    "LINT-002",
                    j,
                    "unchecked writer-confirmation checkbox under %s — every "
                    "confirmation box must be [x] before submission" % label,
                )
            j += 1


BRANCH_URL_RE = re.compile(
    r"https?://\S*?/blob/(main|master|dev|develop)/", re.IGNORECASE
)


def check_003_branch_urls(doc: Document, out: List[Violation]) -> None:
    for idx, line in doc.live_lines():
        for m in BRANCH_URL_RE.finditer(line):
            add(
                out,
                "LINT-003",
                idx,
                "branch-name URL `/blob/%s/` is not a permalink — pin the "
                "citation to a commit SHA (7-40 hex chars after /blob/)"
                % m.group(1),
            )


VERSION_RE = re.compile(r"\bv(\d+)\b", re.IGNORECASE)


def check_004_changelog_order(doc: Document, out: List[Violation]) -> None:
    heading = doc.heading_exact("Changelog", 2)
    if heading is None:
        candidates = doc.headings_containing("Changelog", min_level=2, max_level=2)
        if not candidates:
            return
        heading = candidates[0]
    previous: Optional[int] = None
    previous_line: Optional[int] = None
    for table in doc.tables(*doc.body(heading)):
        for idx, _cells in table.rows:
            m = VERSION_RE.search(doc.lines[idx])
            if not m:
                continue
            version = int(m.group(1))
            if previous is not None and version < previous:
                add(
                    out,
                    "LINT-004",
                    idx,
                    "changelog out of order: v%d appears after v%d (line %d) — "
                    "rows must read in ascending version order"
                    % (version, previous, (previous_line or 0) + 1),
                )
            previous = version
            previous_line = idx


OQ_RE = re.compile(r"\bOQ-\w+")
NONE_RE = re.compile(r"^\s*(?:[-*+]\s+)?(?:\*{0,2})none\b", re.IGNORECASE)


def check_005_open_questions(doc: Document, out: List[Violation]) -> None:
    headings = doc.headings_containing("Open Questions")
    if not headings:
        add(
            out,
            "LINT-005",
            0,
            "no Open Questions section found — the section is required and "
            "must state None",
        )
        return
    for heading in headings:
        start, end = doc.body(heading)
        found_oq = False
        found_none = False
        for idx, line in doc.live_lines(start, end):
            if OQ_RE.search(line):
                found_oq = True
                add(
                    out,
                    "LINT-005",
                    idx,
                    "unresolved OQ- item in Open Questions — every question "
                    "must be resolved and the decision moved into its section",
                )
            if NONE_RE.match(line):
                found_none = True
        if not found_oq and not found_none:
            add(
                out,
                "LINT-005",
                heading.line,
                "Open Questions must contain a 'None' line stating all "
                "questions are resolved",
            )


GUIDE_RE = re.compile(r"^\s*>\s*\*\*GUIDE\*\*")


def check_006_guide_blocks(doc: Document, out: List[Violation]) -> None:
    for idx, line in doc.live_lines():
        if GUIDE_RE.match(line):
            add(
                out,
                "LINT-006",
                idx,
                "`> **GUIDE**` block left in the document — guide blocks must "
                "be deleted once the section is filled",
            )


BACKTICK_RE = re.compile(r"`([^`]+)`")
# Projects may prefix event IDs per initiative (e.g., AE-CVV-001), not just AE-001.
AE_ID_RE = re.compile(r"\bAE-(?:[A-Za-z0-9]+-)*\d+\b")
AC_ID_RE = re.compile(r"\bAC-\d+\b")


def check_007_analytics_binding(doc: Document, out: List[Violation]) -> None:
    table = analytics_table(doc)
    if table is None:
        return
    event_col = table.column(r"event\s*name")
    span_start, span_end = table.line_span
    table_lines = set(range(span_start, span_end + 1))

    events: List[Tuple[str, int]] = []
    ae_rows: List[Tuple[str, int]] = []
    for idx, cells in table.rows:
        ae_match = AE_ID_RE.search(doc.lines[idx])
        if ae_match:
            ae_rows.append((ae_match.group(0), idx))
        if event_col is None or event_col >= len(cells):
            continue
        for name in BACKTICK_RE.findall(cells[event_col]):
            name = name.strip()
            if name and not PLACEHOLDER_RE.match(name):
                events.append((name, idx))

    ac_lines = [
        (idx, line)
        for idx, line in doc.live_lines()
        if AC_ID_RE.search(line) and idx not in table_lines
    ]

    for idx, line in ac_lines:
        for name, _row in events:
            if word_occurrence(name).search(line):
                add(
                    out,
                    "LINT-007",
                    idx,
                    "raw analytics event name `%s` appears in an AC — ACs must "
                    "reference the event by AE-number" % name,
                )

    for ae_id, row_idx in ae_rows:
        referenced = any(
            re.search(r"\b" + re.escape(ae_id) + r"\b", line) for _idx, line in ac_lines
        )
        if not referenced:
            add(
                out,
                "LINT-007",
                row_idx,
                "%s is referenced by zero ACs — the event has no test surface"
                % ae_id,
            )


def check_008_wire_value_leak(doc: Document, out: List[Violation]) -> None:
    values: Dict[str, int] = {}
    for table in vocabulary_tables(doc):
        col = table.column(r"api\s*field")
        if col is None:
            continue
        for idx, cells in table.rows:
            if col >= len(cells):
                continue
            for raw in re.split(r"[,/]| or ", cells[col]):
                value = strip_cell(raw)
                if len(value) < 3 or " " in value:
                    continue
                if PLACEHOLDER_RE.match(value):
                    continue
                values.setdefault(value, idx)
    if not values:
        return
    for idx, line in fr_ac_lines(doc):
        if "AE-" in line:
            continue  # analytics ACs legitimately carry the data contract
        for value, row_idx in values.items():
            if word_occurrence(value).search(line):
                add(
                    out,
                    "LINT-008",
                    idx,
                    "wire value `%s` (vocabulary row on line %d) leaked into a "
                    "behavioral line — use the semantic name instead"
                    % (value, row_idx + 1),
                )


REQUIRED_SECTIONS = ("Behavioral Contract", "Boundaries")

# The behavioral anchors a slim PRD carries in place of the Technical Contract.
# They are what keeps a slim document buildable: constants, concept names, and
# render determinants all live in the behavioral layer, by the placement rule.
SLIM_ANCHORS = ("Product Constants", "Semantic Vocabulary", "Display Rules")


def check_009_template_conformance(doc: Document, out: List[Violation]) -> None:
    for title in REQUIRED_SECTIONS:
        if doc.heading_exact(title, 2) is None:
            add(
                out,
                "LINT-009",
                0,
                "required section `## %s` is missing or renamed — top-level "
                "section names must match the template exactly" % title,
            )

    if doc.heading_exact("Technical Contract", 2) is not None:
        return  # full-mode shape: nothing further to require

    # No Technical Contract: the PRD is slim (or the section was renamed).
    # Either way the behavioral anchors must be present, because they are the
    # only remaining home for user-perceivable values.
    bc = doc.section("Behavioral Contract", 2)
    present = set()
    if bc is not None:
        present = {h.title.strip() for h in doc.subheadings(bc)}
    for anchor in SLIM_ANCHORS:
        if anchor not in present:
            add(
                out,
                "LINT-009",
                0,
                "no `## Technical Contract` section, so this PRD is slim — but "
                "the behavioral anchor `### %s` is missing from the Behavioral "
                "Contract. A slim PRD must carry Product Constants, Semantic "
                "Vocabulary and Display Rules (or restore the Technical "
                "Contract heading if the section was renamed)" % anchor,
            )


PC_ROW_RE = re.compile(r"^\s*\|\s*\*{0,2}(PC-[A-Za-z0-9]*-?\d+)\*{0,2}\s*\|")
PC_REF_RE = re.compile(r"\bPC-(?:[A-Za-z0-9]+-)*\d+\b")
FR_AC_ID_RE = re.compile(r"\b(?:FR|AC)-\d+\b")

# Durations are the bound class the placement rule was written for: a timeout
# the user waits through, a freshness window, a cooldown. Keeping the unit list
# to time units is deliberate — "a 6-digit code" and "3 columns" are product
# mechanics and design, not constants, and matching them would make the check
# noise. Other bound classes are caught by the reviewer's F-33.
DURATION_RE = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)?)\s*-?\s*"
    r"(ms|millisecond|milliseconds|s|sec|secs|second|seconds|"
    r"min|mins|minute|minutes|h|hr|hrs|hour|hours|"
    r"day|days|week|weeks|month|months|year|years)\b",
    re.IGNORECASE,
)


def product_constants_span(doc: Document) -> Optional[Tuple[int, int]]:
    for heading in doc.headings_containing("Product Constants"):
        return doc.body(heading)
    return None


def check_010_product_constants(doc: Document, out: List[Violation]) -> None:
    span = product_constants_span(doc)
    if span is None:
        return  # the PRD does not use the Product Constants discipline

    pc_start, pc_end = span
    defined: Dict[str, int] = {}
    for table in doc.tables(pc_start, pc_end):
        for idx, _cells in table.rows:
            m = PC_ROW_RE.match(doc.lines[idx])
            if m and not PLACEHOLDER_RE.match(m.group(1)):
                defined.setdefault(m.group(1), idx)

    # Reference scan deliberately excludes the Product Constants table itself:
    # its "Referenced by" column names the FRs, so counting it would let every
    # row vouch for itself.
    behavioral: List[Tuple[int, str]] = [
        (idx, line)
        for idx, line in fr_ac_lines(doc)
        if not (pc_start <= idx < pc_end)
    ]

    for pc_id, row_idx in defined.items():
        pattern = re.compile(r"\b" + re.escape(pc_id) + r"\b")
        if not any(pattern.search(line) for _idx, line in behavioral):
            add(
                out,
                "LINT-010",
                row_idx,
                "%s is referenced by zero requirements — an unused constant is "
                "dead spec: cite it from the FR/AC it bounds, or delete the row"
                % pc_id,
            )

    for idx, line in behavioral:
        if not FR_AC_ID_RE.search(line):
            continue  # edge-case rows carry scenario values, not bounds
        if PC_REF_RE.search(line):
            continue
        m = DURATION_RE.search(line)
        if m:
            add(
                out,
                "LINT-010",
                idx,
                "bare inline bound `%s` in a requirement — every bound the "
                "user perceives lives in Product Constants and is cited by ID "
                "(PC-NNN), never restated inline" % m.group(0).strip(),
            )


# Transport taxonomy the slim analytics contract must not carry: wire-level
# class names / status-code properties, and literal status-number encoding
# rules. Semantic classes (unreachable, rejected, unusable_response,
# incomplete_record) pass — they are named by what support does, not by how
# the wire failed.
WIRE_TAXONOMY_RE = re.compile(
    r"\b(error_status_code|status_code|http_error|parse_error)\b"
)
STATUS_ENCODING_RE = re.compile(
    r"`?\b(?:0|[1-5]\d{2})\b`?\s+for\s+"
    r"(?:a\s+|an\s+|the\s+)?(?:transport|timeout|success|error|failure)",
    re.IGNORECASE,
)


def check_011_analytics_wire_taxonomy(doc: Document, out: List[Violation]) -> None:
    if not is_slim(doc):
        return
    spans: List[Tuple[int, int]] = []
    for heading in doc.headings_containing("Analytics Events"):
        spans.append(doc.body(heading))
    for heading in doc.headings_containing("Support"):
        spans.append(doc.body(heading))
    seen: set = set()
    for start, end in spans:
        for idx, line in doc.live_lines(start, end):
            if idx in seen:
                continue
            m = WIRE_TAXONOMY_RE.search(line)
            if m:
                seen.add(idx)
                add(
                    out,
                    "LINT-011",
                    idx,
                    "wire failure taxonomy `%s` in the Analytics/Support "
                    "content — slim-mode failure classes are product-semantic "
                    "(unreachable / rejected / unusable_response / "
                    "incomplete_record); status codes and wire classes are "
                    "dev-owned diagnostics documented in the analytics "
                    "catalog" % m.group(1),
                )
                continue
            m = STATUS_ENCODING_RE.search(line)
            if m:
                seen.add(idx)
                add(
                    out,
                    "LINT-011",
                    idx,
                    "status-number encoding rule `%s` in the "
                    "Analytics/Support content — how a failure class is "
                    "detected and encoded on the wire is dev-owned; the PRD "
                    "names the class by its support meaning only"
                    % m.group(0).strip(),
                )


# Wire-encoding vocabulary that must not appear in a slim Semantic Vocabulary
# Type cell: unit qualifiers, epoch bases, and parenthesized encodings after a
# base type. Semantic types (money amount, instant, enumeration, list of
# <entity>) carry none of these — the Display Rules worked example fixes the
# raw-value mapping, and encoding traps live in the canonical API reference.
TYPE_ENCODING_RE = re.compile(
    r"minor[\s-]?units?|epoch|milli\s*seconds?|(?<![A-Za-z])seconds?\b"
    r"|\bISO[- ]?\d*\b|\([^)]*\)",
    re.IGNORECASE,
)


def check_012_vocabulary_type_encoding(doc: Document, out: List[Violation]) -> None:
    if not is_slim(doc):
        return
    for table in behavioral_vocabulary_tables(doc):
        col = table.column(r"type")
        if col is None:
            continue
        for idx, cells in table.rows:
            if col >= len(cells):
                continue
            cell = cells[col]
            if PLACEHOLDER_RE.match(strip_cell(cell)):
                continue
            m = TYPE_ENCODING_RE.search(cell)
            if m:
                add(
                    out,
                    "LINT-012",
                    idx,
                    "wire encoding `%s` in a Semantic Vocabulary Type cell — "
                    "slim-mode types are semantic (money amount, instant, "
                    "string, enumeration, list of <entity>); the encoding is "
                    "dev-owned, fixed implicitly by the Display Rules worked "
                    "example and documented in the canonical API reference"
                    % m.group(0).strip(),
                )


# Code wiring a slim PRD must not carry outside Dependencies: repo path
# fragments, source-file references, and route path constants. Whole markdown
# evidence links and bare URLs are stripped before matching — a commit-pinned
# permalink whose target (or link text) names a source file is a citation, not
# web wiring. This is what keeps Mobile Baseline citations to a pinned mobile
# repo legal.
MD_EVIDENCE_LINK_RE = re.compile(r"\[[^\]]*\]\(\s*https?://[^)]*\)")
URL_RE = re.compile(r"https?://\S+")
CODE_WIRING_RE = re.compile(
    r"(?<![\w./-])(?:src|packages)/[\w./-]+"
    r"|(?<![\w./-])[\w./-]+\.(?:tsx|ts|dart)\b"
    r"|`paths\.\w+"
)


def check_013_code_wiring(doc: Document, out: List[Violation]) -> None:
    if not is_slim(doc):
        return
    exempt: set = set()
    for heading in doc.headings_containing("Dependencies"):
        start, end = doc.body(heading)
        exempt.update(range(start, end))
    for idx, line in doc.live_lines():
        if idx in exempt:
            continue
        m = CODE_WIRING_RE.search(URL_RE.sub("", MD_EVIDENCE_LINK_RE.sub("", line)))
        if m:
            add(
                out,
                "LINT-013",
                idx,
                "code wiring `%s` outside the Dependencies table — in slim "
                "mode repo paths, source files and route-path constants are "
                "dev-owned: name the concept and let the implementation "
                "ticket carry the wiring (evidence permalinks and "
                "ds-gap/api-canonical-gap issue references are the allowed "
                "homes)" % m.group(0).strip("`"),
            )


# Design-mechanism phrases the behavioral layer must not prescribe in slim
# mode: live-region politeness levels, stacking/composition order, skeleton
# shape. The list is deliberately narrow — wording varies, so this check is a
# low-confidence tripwire; the reviewer's separation pass is the real net.
DESIGN_MECHANISM_RE = re.compile(
    r"\bpolitely\b|\bassertively\b|stacked in that order|single column"
    r"|shaped like",
    re.IGNORECASE,
)


def check_014_design_mechanism(doc: Document, out: List[Violation]) -> None:
    if not is_slim(doc):
        return
    bc = doc.section("Behavioral Contract", 2)
    if bc is None:
        return
    for idx, line in doc.live_lines(*bc):
        m = DESIGN_MECHANISM_RE.search(line)
        if m:
            add(
                out,
                "LINT-014",
                idx,
                "design-mechanism phrase `%s` in the behavioral layer — the "
                "PRD states perceivable outcomes and their priority; "
                "ordering, skeleton shape, live-region politeness and focus "
                "targets are design-owned (heuristic check; the reviewer's "
                "separation pass is the real net)" % m.group(0),
            )


# --------------------------------------------------------------------------
# Mode `review` checks
# --------------------------------------------------------------------------

PENDING_RE = re.compile(r"\[PENDING\]")
BAD_VERDICT_RE = re.compile(r"\b(WARN|WARNING|INFO)\b")
COUNT_KEYS = ("TOTAL_CELLS", "SUB_AGENT_CELLS", "ORCHESTRATOR_CELLS")


def check_101_pending(doc: Document, out: List[Violation]) -> None:
    for idx, line in doc.live_lines():
        count = len(PENDING_RE.findall(line))
        if count:
            add(
                out,
                "LINT-101",
                idx,
                "%d [PENDING] cell(s) remain — every verdict cell must be "
                "filled before a verdict is generated" % count,
            )


def check_102_verdict_tokens(doc: Document, out: List[Violation]) -> None:
    for table in doc.tables():
        for idx, cells in table.rows:
            for cell in cells:
                m = BAD_VERDICT_RE.search(cell)
                if m:
                    add(
                        out,
                        "LINT-102",
                        idx,
                        "invalid verdict token `%s` — only PASS, FAIL: ..., or "
                        "N/A are valid verdicts" % m.group(1),
                    )
                    break


def check_103_cell_counts(doc: Document, out: List[Violation]) -> None:
    found: Dict[str, Tuple[int, str]] = {}
    # Deliberately scans fenced lines too: the reviewer scaffold renders this
    # count header inside a plain ``` block, so skipping fences would report
    # every key as missing and mask a genuine sum mismatch.
    for idx, line in enumerate(doc.lines):
        m = re.match(r"^\s*\**(" + "|".join(COUNT_KEYS) + r")\**\s*:\s*(\S+)", line)
        if m and m.group(1) not in found:
            found[m.group(1)] = (idx, m.group(2))

    parsed: Dict[str, int] = {}
    for key in COUNT_KEYS:
        if key not in found:
            add(out, "LINT-103", 0, "%s is missing — it must be a plain integer" % key)
            continue
        idx, raw = found[key]
        token = raw.strip().strip("`").strip("*")
        if not re.match(r"^\d+$", token):
            add(
                out,
                "LINT-103",
                idx,
                "%s must be a plain integer, found `%s`" % (key, raw),
            )
            continue
        parsed[key] = int(token)

    if len(parsed) == len(COUNT_KEYS):
        total = parsed["TOTAL_CELLS"]
        expected = parsed["SUB_AGENT_CELLS"] + parsed["ORCHESTRATOR_CELLS"]
        if total != expected:
            add(
                out,
                "LINT-103",
                found["TOTAL_CELLS"][0],
                "TOTAL_CELLS (%d) != SUB_AGENT_CELLS (%d) + ORCHESTRATOR_CELLS "
                "(%d) = %d"
                % (
                    total,
                    parsed["SUB_AGENT_CELLS"],
                    parsed["ORCHESTRATOR_CELLS"],
                    expected,
                ),
            )


# --------------------------------------------------------------------------
# Mode `shared-requirements` — stale-pattern migration scan
# --------------------------------------------------------------------------
#
# Shared requirements are authored per project and outlive framework upgrades,
# so an SR can keep mandating an artifact the framework has since removed or
# forbidden. Each check below targets one known-stale pattern from a previous
# framework generation. Findings are migration items for the SR owner (fix the
# SR or record an explicit override) — never defects in any PRD.

# A line that states the *current* rule ("translations are design-owned",
# "the PRD must not contain literal copy") is a correction, not a stale
# obligation — exempt it.
SR_NEGATION_RE = re.compile(
    r"design-owned|must\s+not|do(?:es)?\s+not|don'?t\b|never\b|no\s+longer",
    re.IGNORECASE,
)
SR_MANDATE_RE = re.compile(
    r"\bmust\b|\brequired?\b|\bshall\b|\bmandat|\balways\s+include", re.IGNORECASE
)
SR_LOCALIZATION_RE = re.compile(
    r"localization\s+(?:keys?\s+)?section|localization\s+keys?\s+table"
    r"|keys?\s+and\s+translations?|translations?\s+for\s+(?:all|each|every)\b"
    r"|all\s+user-facing\s+strings",
    re.IGNORECASE,
)
SR_TECHNICAL_RE = re.compile(
    r"technical\s+contract"
    r"|data\s+sources\s+table|error\s+classification\s+table"
    r"|route\s+mapping\s+table|per-endpoint\s+(?:vocabulary|error|table|block)",
    re.IGNORECASE,
)
SR_LITERAL_COPY_RE = re.compile(
    r"(?:exact|literal|final|verbatim)\s+(?:copy|wording|strings?)",
    re.IGNORECASE,
)


def check_201_localization_mandate(doc: Document, out: List[Violation]) -> None:
    for idx, line in doc.live_lines():
        if SR_LOCALIZATION_RE.search(line) and not SR_NEGATION_RE.search(line):
            add(
                out,
                "LINT-201",
                idx,
                "stale Localization mandate — copy, localization keys, and "
                "translations are design-owned and the PRD no longer contains "
                "a Localization section; fix the SR (keep any language "
                "enumeration, drop the section mandate) or record an explicit "
                "override",
            )


def check_202_technical_contract_mandate(doc: Document, out: List[Violation]) -> None:
    for idx, line in doc.live_lines():
        if (
            SR_TECHNICAL_RE.search(line)
            and SR_MANDATE_RE.search(line)
            and not SR_NEGATION_RE.search(line)
        ):
            add(
                out,
                "LINT-202",
                idx,
                "stale Technical-Contract mandate — slim mode omits the "
                "Technical Contract and its tables entirely, so this SR is "
                "unsatisfiable for slim PRDs; make the SR defer to the "
                "project's Technical Contract mode or record an explicit "
                "override",
            )


def check_203_literal_copy_mandate(doc: Document, out: List[Violation]) -> None:
    for idx, line in doc.live_lines():
        if (
            SR_LITERAL_COPY_RE.search(line)
            and SR_MANDATE_RE.search(line)
            and not SR_NEGATION_RE.search(line)
        ):
            add(
                out,
                "LINT-203",
                idx,
                "stale literal-copy mandate — requirements state copy intent; "
                "literal copy, keys, and translations are design-owned (sole "
                "exception: legally mandated wording, quoted with its "
                "source); fix the SR or record an explicit override",
            )


PRD_CHECKS = (
    check_001_vocabulary_markers,
    check_002_unchecked_confirmations,
    check_003_branch_urls,
    check_004_changelog_order,
    check_005_open_questions,
    check_006_guide_blocks,
    check_007_analytics_binding,
    check_008_wire_value_leak,
    check_009_template_conformance,
    check_010_product_constants,
    check_011_analytics_wire_taxonomy,
    check_012_vocabulary_type_encoding,
    check_013_code_wiring,
    check_014_design_mechanism,
)

REVIEW_CHECKS = (
    check_101_pending,
    check_102_verdict_tokens,
    check_103_cell_counts,
)

SHARED_REQUIREMENTS_CHECKS = (
    check_201_localization_mandate,
    check_202_technical_contract_mandate,
    check_203_literal_copy_mandate,
)

MODE_CHECKS = {
    "prd": PRD_CHECKS,
    "review": REVIEW_CHECKS,
    "shared-requirements": SHARED_REQUIREMENTS_CHECKS,
}


def lint(text: str, mode: str) -> List[Violation]:
    doc = Document(text)
    out: List[Violation] = []
    for check in MODE_CHECKS[mode]:
        check(doc, out)
    out.sort(key=lambda v: (v.line, v.id, v.message))
    return out


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def render(violations: Sequence[Violation], fmt: str) -> str:
    if fmt == "json":
        counts: Dict[str, int] = {}
        for violation in violations:
            counts[violation.id] = counts.get(violation.id, 0) + 1
        counts["total"] = len(violations)
        return json.dumps(
            {
                "violations": [v.as_dict() for v in violations],
                "counts": counts,
            },
            indent=2,
        )
    return "\n".join(
        "%s %d %s" % (v.id, v.line, v.message) for v in violations
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="prd-lint",
        description="Deterministic linter for mechanical PRD and review rules.",
    )
    parser.add_argument("file", help="markdown file to lint")
    parser.add_argument(
        "--mode",
        choices=("prd", "review", "shared-requirements"),
        default="prd",
        help="rule set to apply (default: prd)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    args = parser.parse_args(argv)

    try:
        with open(args.file, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        sys.stderr.write("prd-lint: cannot read %s: %s\n" % (args.file, exc))
        return 2

    try:
        violations = lint(text, args.mode)
    except Exception as exc:  # noqa: BLE001 - parse failures must exit 2
        sys.stderr.write("prd-lint: failed to parse %s: %s\n" % (args.file, exc))
        return 2

    output = render(violations, args.format)
    if output:
        print(output)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
