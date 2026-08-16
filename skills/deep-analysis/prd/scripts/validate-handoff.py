#!/usr/bin/env python3
"""validate-handoff — schema validator for inter-agent handoff JSON files.

Inter-agent state in this framework flows through naming-convention JSON files
(`_artifacts/{initiative}-prd-handoff.json`, `…-prd-review-handoff.json`,
`…-review-dispatch.json`). Nothing validated them: a string where an integer
was documented, a cell count that does not sum, a midnight timestamp, or four
of five prompt-file paths all passed silently and broke a consumer downstream.
This script is the deterministic check — hand-rolled tables, no jsonschema.

Usage:
    python3 scripts/validate-handoff.py
        --type writer|reviewer|dispatch|senior-pm <file.json>

Exit codes:
    0 — valid
    1 — invalid (one line per problem on stdout: `<field-path>: <problem>`)
    2 — usage error, unreadable file, malformed JSON, or unsupported --type

The `retro` type is accepted by the flag but always exits 2 with "unknown
type": this framework version ships no `agents/prd-retro.md`, so there is no
documented shape to encode. When a retro agent lands, add its table here.

Spec tables are derived from the agent documents, which are authoritative:
    writer     — `agents/prd-writer.md` Step 6 (Write Handoff File)
    reviewer   — `agents/prd-reviewer.md` Step 9 (Write Handoff File)
    dispatch   — `agents/prd-reviewer.md` Phase 2, Path A (dispatch JSON)
    senior-pm  — `agents/prd-senior-pm.md` Step 7 (Write the Handoff File)

Required vs optional: a field is required when the agent document emits it
unconditionally. Fields that carry proposals or conditional context
(`proposedLessons`, `previousName`, …) are validated only when present — but
their *inner* shape is enforced strictly once they appear, because a
half-filled proposal is what actually breaks the Gate 3 presentation.

Invariants enforced beyond per-field types:
    reviewer  totalCells == subAgentCells + orchestratorCells
    reviewer  timestamp must not be midnight (the agent doc forbids it)
    reviewer  nextAgent follows status (READY → none, NEEDS_REVISION → prd-writer)
    dispatch  totalCells == subAgentCells + orchestratorCells
    dispatch  models / promptFiles / outputFiles carry EXACTLY the five
              sub-agent keys — no missing key, no extra key
    senior-pm dispositionCounts carries exactly the four disposition keys, all
              integers, and agrees with the arrays it summarizes:
              fixTechnical + fixProduct == len(tickets),
              reject == len(rejectedFails), escalate == len(escalations)
    senior-pm every ticket's `type` is technical | product, and a `product`
              ticket carries a non-empty `decision` (a decision is the whole
              point of that disposition)
    senior-pm ticketsVerified is required in `delta` mode and forbidden in
              `full` mode — the mode field is what tells a reader whether the
              earlier dispositions were re-judged or enforced
    writer    technicalContractMode is slim | full — the mode the PRD was
              actually written in, which the reviewer and senior PM consume
              instead of re-resolving it (and losing a per-run --tc override)
    writer    consideredNA (optional) lists omitted conditional sections as
              {section, reason} pairs — the Considered, N/A record that used
              to be a PRD section; reviewer F-36 and the senior PM read it
              from the handoff, so a half-filled entry breaks that check
    reviewer  technicalContractMode is slim | full, and must be the mode the
              review judged the PRD in
    dispatch  technicalContractMode is slim | full, so Phase 3 and every
              sub-reviewer prompt inherit one resolution
    senior-pm timestamp must not be midnight (the agent doc forbids it)
    senior-pm nextAgent follows the ticket count (tickets → prd-writer, no
              tickets → none)

The escalation sanity bound the agent document states — more than five
escalations means the agent is under-deciding — is deliberately NOT enforced
here. It is a judgment heuristic, not a schema rule: a handoff with six
escalations is well-formed and says something true about the evidence base.

Stdlib only, Python 3.9+. Consumers copy this single file into their project.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# Shared vocabulary
# --------------------------------------------------------------------------

ISO8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
MIDNIGHT_RE = re.compile(r"T00:00:00")
INT_STRING_RE = re.compile(r"^[+-]?\d+$")

# Matrix identifiers required in `failsByMatrix` (prd-reviewer.md Step 9).
MATRIX_KEYS: Tuple[str, ...] = (
    "A", "B", "C", "S", "D1", "D2", "E", "F", "G", "H", "I", "P",
)

# The five parallel sub-reviewers (prd-reviewer.md Phase 2).
SUB_AGENT_KEYS: Tuple[str, ...] = (
    "api", "structure", "flow", "requirements", "smells",
)

# The four dispositions every senior-PM finding gets exactly one of
# (prd-senior-pm.md Step 4), as they appear in `dispositionCounts`.
DISPOSITION_KEYS: Tuple[str, ...] = (
    "fixTechnical", "fixProduct", "reject", "escalate",
)

# Ticket types (prd-senior-pm.md Step 5).
TICKET_TYPES: Tuple[str, ...] = ("technical", "product")

# Run modes (prd-senior-pm.md "Run Mode: Full or Delta").
SENIOR_PM_MODES: Tuple[str, ...] = ("full", "delta")

# Technical Contract modes (project-context.md "PRD Configuration → Technical
# Contract → Mode", overridable per run with `/create-prd … --tc`). The mode a
# PRD was written in is not re-derivable from the document, so it travels in
# the handoffs: the writer records it, the reviewer and senior PM read it
# rather than re-resolving it from project-context.md and losing the override.
TECHNICAL_CONTRACT_MODES: Tuple[str, ...] = ("slim", "full")

# Where a resolved Technical Contract mode came from.
TECHNICAL_CONTRACT_MODE_SOURCES: Tuple[str, ...] = (
    "run-override", "project-context", "default",
)

# Delta-mode prior-ticket verification buckets (prd-senior-pm.md Step 7).
TICKETS_VERIFIED_KEYS: Tuple[str, ...] = ("applied", "partial", "notApplied")

DEFECT_CATEGORIES: Tuple[str, ...] = (
    "Omission",
    "Ambiguity",
    "Inconsistency",
    "Incorrect Fact",
    "Extraneous Info",
    "Misplaced Requirement",
)


# --------------------------------------------------------------------------
# Problem collection
# --------------------------------------------------------------------------


class Problems:
    """Ordered `<field-path>: <problem>` accumulator."""

    def __init__(self) -> None:
        self.items: List[Tuple[str, str]] = []

    def add(self, path: str, message: str) -> None:
        self.items.append((path, message))

    def __len__(self) -> int:
        return len(self.items)

    def render(self) -> str:
        return "\n".join("%s: %s" % (path, message) for path, message in self.items)


def typename(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def join(path: str, key: str) -> str:
    return key if not path else "%s.%s" % (path, key)


# --------------------------------------------------------------------------
# Field primitives
#
# Every checker takes (problems, container, path, key) and returns True only
# when the field was present AND well-formed, so callers can chain safely.
# --------------------------------------------------------------------------


def present(
    problems: Problems,
    container: Dict[str, Any],
    path: str,
    key: str,
    required: bool,
) -> Tuple[bool, Any]:
    if key not in container:
        if required:
            problems.add(join(path, key), "required field is missing")
        return False, None
    return True, container[key]


def want_string(
    problems: Problems,
    container: Dict[str, Any],
    path: str,
    key: str,
    *,
    required: bool = True,
    allow_empty: bool = False,
    equals: Optional[str] = None,
    choices: Optional[Sequence[str]] = None,
) -> bool:
    found, value = present(problems, container, path, key, required)
    if not found:
        return False
    where = join(path, key)
    if not isinstance(value, str):
        problems.add(where, "expected string, got %s" % typename(value))
        return False
    if not allow_empty and not value.strip():
        problems.add(where, "must be a non-empty string")
        return False
    if equals is not None and value != equals:
        problems.add(where, 'expected "%s", got "%s"' % (equals, value))
        return False
    if choices is not None and value not in choices:
        problems.add(
            where,
            "expected one of %s, got \"%s\"" % (" | ".join(choices), value),
        )
        return False
    return True


def want_integer(
    problems: Problems,
    container: Dict[str, Any],
    path: str,
    key: str,
    *,
    required: bool = True,
    strict: bool = True,
) -> bool:
    """`strict` — the value MUST be a JSON integer.

    Non-strict accepts an integer-valued string ("12") because the agent
    document writes those fields as `"<number of …>"` placeholders; a
    non-numeric string is a violation either way.
    """
    found, value = present(problems, container, path, key, required)
    if not found:
        return False
    where = join(path, key)
    if isinstance(value, bool):
        problems.add(where, "expected integer, got boolean")
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, str):
        if strict:
            problems.add(
                where,
                'expected integer, got string "%s" (must be a JSON number, '
                "not a quoted value)" % value,
            )
            return False
        if INT_STRING_RE.match(value.strip()):
            return True
        problems.add(
            where, 'expected integer, got non-numeric string "%s"' % value
        )
        return False
    problems.add(where, "expected integer, got %s" % typename(value))
    return False


def want_boolean(
    problems: Problems,
    container: Dict[str, Any],
    path: str,
    key: str,
    *,
    required: bool = True,
) -> bool:
    found, value = present(problems, container, path, key, required)
    if not found:
        return False
    if not isinstance(value, bool):
        problems.add(
            join(path, key), "expected boolean, got %s" % typename(value)
        )
        return False
    return True


def want_flag(
    problems: Problems,
    container: Dict[str, Any],
    path: str,
    key: str,
    *,
    required: bool = True,
) -> bool:
    """Boolean, or the string "true"/"false".

    The agent document writes `"isNewFile": "<true if …>"`, so a quoted boolean
    is what agents actually emit; anything else is a violation.
    """
    found, value = present(problems, container, path, key, required)
    if not found:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, str) and value.strip().lower() in ("true", "false"):
        return True
    problems.add(
        join(path, key),
        'expected boolean (or the string "true"/"false"), got %s'
        % (('"%s"' % value) if isinstance(value, str) else typename(value)),
    )
    return False


def want_list(
    problems: Problems,
    container: Dict[str, Any],
    path: str,
    key: str,
    *,
    required: bool = True,
    of: Optional[str] = None,
) -> Tuple[bool, List[Any]]:
    found, value = present(problems, container, path, key, required)
    if not found:
        return False, []
    where = join(path, key)
    if not isinstance(value, list):
        problems.add(where, "expected array, got %s" % typename(value))
        return False, []
    if of == "string":
        ok = True
        for index, item in enumerate(value):
            if not isinstance(item, str):
                problems.add(
                    "%s[%d]" % (where, index),
                    "expected string, got %s" % typename(item),
                )
                ok = False
            elif not item.strip():
                problems.add(
                    "%s[%d]" % (where, index), "must be a non-empty string"
                )
                ok = False
        return ok, value
    if of == "object":
        ok = True
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                problems.add(
                    "%s[%d]" % (where, index),
                    "expected object, got %s" % typename(item),
                )
                ok = False
        return ok, value
    return True, value


def want_object(
    problems: Problems,
    container: Dict[str, Any],
    path: str,
    key: str,
    *,
    required: bool = True,
) -> Tuple[bool, Dict[str, Any]]:
    found, value = present(problems, container, path, key, required)
    if not found:
        return False, {}
    where = join(path, key)
    if not isinstance(value, dict):
        problems.add(where, "expected object, got %s" % typename(value))
        return False, {}
    return True, value


def want_timestamp(
    problems: Problems,
    container: Dict[str, Any],
    path: str,
    key: str,
    *,
    reject_midnight: bool = False,
) -> bool:
    if not want_string(problems, container, path, key):
        return False
    where = join(path, key)
    value = container[key]
    if not ISO8601_RE.match(value):
        problems.add(
            where,
            'expected ISO8601 timestamp (YYYY-MM-DDTHH:MM:SS), got "%s"' % value,
        )
        return False
    if reject_midnight and MIDNIGHT_RE.search(value):
        problems.add(
            where,
            'midnight timestamp "%s" — the agent document requires the actual '
            'current time from `date -u +"%%Y-%%m-%%dT%%H:%%M:%%SZ"`' % value,
        )
        return False
    return True


def want_exact_keys(
    problems: Problems,
    container: Dict[str, Any],
    path: str,
    key: str,
    expected: Sequence[str],
    *,
    required: bool = True,
    value_kind: str = "string",
) -> bool:
    """Object must carry EXACTLY `expected` — no missing key, no extra key."""
    found, obj = want_object(problems, container, path, key, required=required)
    if not found:
        return False
    where = join(path, key)
    ok = True
    for missing in [name for name in expected if name not in obj]:
        problems.add(join(where, missing), "required key is missing")
        ok = False
    for extra in [name for name in obj if name not in expected]:
        problems.add(
            join(where, extra),
            "unexpected key (allowed keys: %s)" % ", ".join(expected),
        )
        ok = False
    for name in expected:
        if name not in obj:
            continue
        if value_kind == "string":
            ok = want_string(problems, obj, where, name) and ok
        elif value_kind == "integer":
            ok = want_integer(problems, obj, where, name, strict=True) and ok
    return ok


def sum_invariant(
    problems: Problems,
    container: Dict[str, Any],
    path: str,
    total_key: str,
    part_keys: Sequence[str],
) -> None:
    """Check total == sum(parts), only when every operand is a real integer."""
    values = []
    for key in (total_key,) + tuple(part_keys):
        value = container.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            return  # a type problem was already reported for this field
        values.append(value)
    total, parts = values[0], values[1:]
    if total != sum(parts):
        problems.add(
            join(path, total_key),
            "%s (%d) != %s = %d"
            % (
                total_key,
                total,
                " + ".join(
                    "%s (%d)" % (name, value)
                    for name, value in zip(part_keys, parts)
                ),
                sum(parts),
            ),
        )


# --------------------------------------------------------------------------
# Type: writer  (agents/prd-writer.md Step 6)
# --------------------------------------------------------------------------


def validate_writer(document: Dict[str, Any], problems: Problems) -> None:
    root = ""
    want_string(problems, document, root, "agent", equals="prd-writer")
    want_string(problems, document, root, "initiative")
    want_timestamp(problems, document, root, "timestamp")
    want_string(problems, document, root, "status")
    want_string(problems, document, root, "prdPath")
    want_string(
        problems, document, root, "technicalContractMode",
        choices=TECHNICAL_CONTRACT_MODES,
    )
    want_string(
        problems, document, root, "technicalContractModeSource",
        required=False, choices=TECHNICAL_CONTRACT_MODE_SOURCES,
    )
    want_list(problems, document, root, "apiEndpoints", of="string")
    want_list(
        problems, document, root, "existingCodeReferenced",
        required=False, of="string",
    )
    want_list(problems, document, root, "dependencies", required=False)
    validate_considered_na(document, problems, root)

    found, metrics = want_object(problems, document, root, "prdMetrics")
    if found:
        for key in ("frCount", "acCount", "edgeCaseCount", "keyEntityCount"):
            want_integer(problems, metrics, "prdMetrics", key, strict=False)
        for key in ("productConstantCount", "displayRuleCount"):
            want_integer(
                problems, metrics, "prdMetrics", key,
                required=False, strict=False,
            )
        want_string(problems, metrics, "prdMetrics", "version", required=False)
        want_integer(
            problems, metrics, "prdMetrics", "sectionPacksUsed",
            required=False, strict=False,
        )
        want_boolean(
            problems, metrics, "prdMetrics", "isFreshDraft", required=False
        )
        want_integer(
            problems, metrics, "prdMetrics", "failsAddressed",
            required=False, strict=False,
        )

    validate_glossary_proposals(document, problems, root)
    validate_vocabulary_proposals(document, problems, root)
    validate_shared_requirement_proposals(document, problems, root)

    want_string(problems, document, root, "nextAgent", equals="prd-reviewer")


def validate_considered_na(
    document: Dict[str, Any], problems: Problems, root: str
) -> None:
    """`consideredNA` is optional: absent (or empty) means "no applicable
    conditional section was omitted". When present, each entry names the
    omitted section and the reason its trigger is absent — reviewer F-36
    judges every reason against the PRD's own facts, so both fields must be
    non-empty strings."""
    ok, entries = want_list(
        problems, document, root, "consideredNA",
        required=False, of="object",
    )
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue  # the non-object item was already reported above
        path = "consideredNA[%d]" % index
        want_string(problems, entry, path, "section")
        want_string(problems, entry, path, "reason")


def validate_glossary_proposals(
    document: Dict[str, Any], problems: Problems, root: str
) -> None:
    ok, terms = want_list(
        problems, document, root, "proposedGlossaryTerms",
        required=False, of="object",
    )
    if not ok:
        return
    for index, term in enumerate(terms):
        path = "proposedGlossaryTerms[%d]" % index
        want_string(problems, term, path, "term")
        want_string(problems, term, path, "definition")
        want_string(problems, term, path, "reason")


def validate_shared_requirement_proposals(
    document: Dict[str, Any], problems: Problems, root: str
) -> None:
    """`proposedSharedRequirements` is optional in every handoff that carries
    it (writer, reviewer, senior-pm): absent means "none proposed". When
    present, each proposal needs the rule and its universality argument;
    `originQuestion` is optional because a senior-pm or reviewer proposal may
    originate from a finding rather than a Q&A entry."""
    ok, proposals = want_list(
        problems, document, root, "proposedSharedRequirements",
        required=False, of="object",
    )
    if not ok:
        return
    for index, proposal in enumerate(proposals):
        path = "proposedSharedRequirements[%d]" % index
        want_string(problems, proposal, path, "rule")
        want_string(problems, proposal, path, "whyUniversal")
        want_string(problems, proposal, path, "originQuestion", required=False)


def validate_vocabulary_proposals(
    document: Dict[str, Any], problems: Problems, root: str
) -> None:
    ok, groups = want_list(
        problems, document, root, "proposedVocabularyEntries",
        required=False, of="object",
    )
    if not ok:
        return
    for index, group in enumerate(groups):
        path = "proposedVocabularyEntries[%d]" % index
        want_string(problems, group, path, "endpoint")
        want_string(problems, group, path, "file")
        want_flag(problems, group, path, "isNewFile")
        entries_ok, entries = want_list(
            problems, group, path, "entries", of="object"
        )
        if not entries_ok:
            continue
        for position, entry in enumerate(entries):
            entry_path = "%s.entries[%d]" % (path, position)
            want_string(problems, entry, entry_path, "apiField")
            want_string(problems, entry, entry_path, "semanticName")
            action_ok = want_string(
                problems, entry, entry_path, "action",
                choices=("add", "change"),
            )
            if action_ok and entry["action"] == "change":
                want_string(problems, entry, entry_path, "previousName")
            want_string(problems, entry, entry_path, "reason")


# --------------------------------------------------------------------------
# Type: reviewer  (agents/prd-reviewer.md Step 9)
# --------------------------------------------------------------------------


def validate_reviewer(document: Dict[str, Any], problems: Problems) -> None:
    root = ""
    want_string(problems, document, root, "agent", equals="prd-reviewer")
    want_string(problems, document, root, "initiative")
    want_timestamp(problems, document, root, "timestamp", reject_midnight=True)
    status_ok = want_string(
        problems, document, root, "status",
        choices=("READY", "NEEDS_REVISION"),
    )
    want_string(problems, document, root, "prdPath")
    want_string(problems, document, root, "reviewPath")
    want_string(
        problems, document, root, "technicalContractMode",
        choices=TECHNICAL_CONTRACT_MODES,
    )

    for key in ("subAgentCells", "orchestratorCells", "totalCells", "failCount"):
        want_integer(problems, document, root, key, strict=True)
    sum_invariant(
        problems, document, root, "totalCells",
        ("subAgentCells", "orchestratorCells"),
    )

    found, size = want_object(problems, document, root, "prdSize")
    if found:
        for key in ("frCount", "acCount", "endpointCount", "entityCount"):
            want_integer(problems, size, "prdSize", key, strict=False)

    want_exact_keys(
        problems, document, root, "failsByMatrix", MATRIX_KEYS,
        value_kind="integer",
    )

    found, smells = want_object(problems, document, root, "smellDetection")
    if found:
        for key in (
            "totalChecked",
            "linguisticSmellsFound",
            "separationSmellsFound",
        ):
            want_integer(problems, smells, "smellDetection", key, strict=False)

    want_string(
        problems, document, root, "reviewMode", choices=("single", "parallel")
    )
    want_boolean(problems, document, root, "isReReview")
    want_integer(
        problems, document, root, "previousFailsVerified", strict=False
    )
    want_integer(problems, document, root, "spotCheckOverrides", strict=False)

    found, taxonomy = want_object(problems, document, root, "defectTaxonomy")
    if found:
        for key in (
            "omission",
            "ambiguity",
            "inconsistency",
            "incorrectFact",
            "extraneousInfo",
            "misplacedRequirement",
        ):
            want_integer(
                problems, taxonomy, "defectTaxonomy", key, strict=False
            )

    issues_ok, issues = want_list(
        problems, document, root, "issuesSummary", required=False, of="object"
    )
    if issues_ok:
        for index, issue in enumerate(issues):
            path = "issuesSummary[%d]" % index
            want_integer(problems, issue, path, "id", strict=False)
            want_string(problems, issue, path, "matrixRow")
            want_string(
                problems, issue, path, "category", choices=DEFECT_CATEGORIES
            )
            want_string(problems, issue, path, "title")
            want_string(problems, issue, path, "fix")

    lessons_ok, lessons = want_list(
        problems, document, root, "proposedLessons", required=False, of="object"
    )
    if lessons_ok:
        for index, lesson in enumerate(lessons):
            path = "proposedLessons[%d]" % index
            want_string(problems, lesson, path, "name")
            want_string(problems, lesson, path, "appliesWhen")
            want_string(problems, lesson, path, "issue")
            want_string(problems, lesson, path, "writerRule")
            want_string(problems, lesson, path, "reviewerCheck")

    validate_glossary_proposals(document, problems, root)
    validate_vocabulary_proposals(document, problems, root)
    validate_shared_requirement_proposals(document, problems, root)

    next_ok = want_string(
        problems, document, root, "nextAgent", choices=("none", "prd-writer")
    )
    if status_ok and next_ok:
        expected = "prd-writer" if document["status"] == "NEEDS_REVISION" else "none"
        if document["nextAgent"] != expected:
            problems.add(
                "nextAgent",
                'status "%s" requires nextAgent "%s", got "%s"'
                % (document["status"], expected, document["nextAgent"]),
            )


# --------------------------------------------------------------------------
# Type: dispatch  (agents/prd-reviewer.md Phase 2, Path A)
# --------------------------------------------------------------------------


def validate_dispatch(document: Dict[str, Any], problems: Problems) -> None:
    root = ""
    want_string(problems, document, root, "reviewMode", equals="parallel")
    want_string(problems, document, root, "scaffoldPath")
    want_string(problems, document, root, "prdPath")
    want_string(
        problems, document, root, "technicalContractMode",
        choices=TECHNICAL_CONTRACT_MODES,
    )

    for key in ("subAgentCells", "orchestratorCells", "totalCells"):
        want_integer(problems, document, root, key, strict=True)
    sum_invariant(
        problems, document, root, "totalCells",
        ("subAgentCells", "orchestratorCells"),
    )

    for key in ("models", "promptFiles", "outputFiles"):
        want_exact_keys(
            problems, document, root, key, SUB_AGENT_KEYS, value_kind="string"
        )

    found, previous = want_object(problems, document, root, "previousReview")
    if found:
        want_boolean(problems, previous, "previousReview", "exists")
        want_list(problems, previous, "previousReview", "previousFails")
        want_list(problems, previous, "previousReview", "changedSections")


# --------------------------------------------------------------------------
# Type: senior-pm  (agents/prd-senior-pm.md Step 7)
# --------------------------------------------------------------------------


def validate_senior_pm(document: Dict[str, Any], problems: Problems) -> None:
    root = ""
    want_string(problems, document, root, "agent", equals="prd-senior-pm")
    want_string(problems, document, root, "initiative")
    want_timestamp(problems, document, root, "timestamp", reject_midnight=True)
    want_string(problems, document, root, "reviewPath")
    want_string(problems, document, root, "prdPath", required=False)
    want_string(problems, document, root, "seniorPmReviewPath", required=False)

    mode_ok = want_string(
        problems, document, root, "mode", choices=SENIOR_PM_MODES
    )
    want_integer(problems, document, root, "failsJudged", strict=True)
    want_integer(
        problems, document, root, "rootCauses", required=False, strict=True
    )

    counts_ok = want_exact_keys(
        problems, document, root, "dispositionCounts", DISPOSITION_KEYS,
        value_kind="integer",
    )

    tickets_ok, tickets = want_list(
        problems, document, root, "tickets", of="object"
    )
    if tickets_ok:
        for index, ticket in enumerate(tickets):
            path = "tickets[%d]" % index
            want_string(problems, ticket, path, "id")
            type_ok = want_string(
                problems, ticket, path, "type", choices=TICKET_TYPES
            )
            want_string(problems, ticket, path, "instruction")
            want_string(problems, ticket, path, "rationale", required=False)
            want_string(problems, ticket, path, "evidence")
            # A `product` ticket without a decision is the exact failure the
            # disposition exists to prevent: the writer would have to invent
            # the behavior, which is what the senior PM was spawned to stop.
            if type_ok and ticket["type"] == "product":
                want_string(problems, ticket, path, "decision")

    escalations_ok, escalations = want_list(
        problems, document, root, "escalations", of="object"
    )
    if escalations_ok:
        for index, escalation in enumerate(escalations):
            path = "escalations[%d]" % index
            want_string(problems, escalation, path, "id")
            want_string(problems, escalation, path, "question")
            want_string(problems, escalation, path, "recommendation")
            want_string(
                problems, escalation, path, "whyUngroundable", required=False
            )

    rejected_ok, rejected = want_list(
        problems, document, root, "rejectedFails", of="object"
    )
    if rejected_ok:
        for index, entry in enumerate(rejected):
            path = "rejectedFails[%d]" % index
            want_string(problems, entry, path, "matrixRow")
            want_string(problems, entry, path, "reason")

    validate_shared_requirement_proposals(document, problems, root)

    # dispositionCounts must agree with the arrays it summarizes. A decision
    # sheet whose counts and lists disagree cannot be presented at Gate 3:
    # the user would be approving numbers that describe a different run.
    if counts_ok:
        counts = document["dispositionCounts"]
        if tickets_ok:
            ticket_total = counts["fixTechnical"] + counts["fixProduct"]
            if ticket_total != len(tickets):
                problems.add(
                    "dispositionCounts",
                    "fixTechnical (%d) + fixProduct (%d) = %d != %d ticket(s) "
                    "in `tickets`"
                    % (
                        counts["fixTechnical"],
                        counts["fixProduct"],
                        ticket_total,
                        len(tickets),
                    ),
                )
            by_type = {name: 0 for name in TICKET_TYPES}
            for ticket in tickets:
                kind = ticket.get("type")
                if kind in by_type:
                    by_type[kind] += 1
            for key, kind in (
                ("fixTechnical", "technical"),
                ("fixProduct", "product"),
            ):
                if counts[key] != by_type[kind]:
                    problems.add(
                        "dispositionCounts.%s" % key,
                        "%s (%d) != %d ticket(s) of type \"%s\""
                        % (key, counts[key], by_type[kind], kind),
                    )
        if rejected_ok and counts["reject"] != len(rejected):
            problems.add(
                "dispositionCounts.reject",
                "reject (%d) != %d entr(y|ies) in `rejectedFails`"
                % (counts["reject"], len(rejected)),
            )
        if escalations_ok and counts["escalate"] != len(escalations):
            problems.add(
                "dispositionCounts.escalate",
                "escalate (%d) != %d entr(y|ies) in `escalations`"
                % (counts["escalate"], len(escalations)),
            )

    # ticketsVerified belongs to delta mode only: in full mode there is no
    # prior ticket list to verify, so its presence means the mode field lies.
    if mode_ok:
        mode = document["mode"]
        has_verified = "ticketsVerified" in document
        if mode == "delta" and not has_verified:
            problems.add(
                "ticketsVerified",
                'required field is missing: mode "delta" must report how many '
                "prior tickets were applied / partial / not-applied",
            )
        elif mode == "full" and has_verified:
            problems.add(
                "ticketsVerified",
                'unexpected field: mode "full" is the first pass, so there are '
                "no prior tickets to verify",
            )
    if "ticketsVerified" in document:
        want_exact_keys(
            problems, document, root, "ticketsVerified",
            TICKETS_VERIFIED_KEYS, value_kind="integer",
        )

    next_ok = want_string(
        problems, document, root, "nextAgent", choices=("none", "prd-writer")
    )
    if next_ok and tickets_ok:
        expected = "prd-writer" if tickets else "none"
        if document["nextAgent"] != expected:
            problems.add(
                "nextAgent",
                '%d ticket(s) require nextAgent "%s", got "%s"'
                % (len(tickets), expected, document["nextAgent"]),
            )


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

VALIDATORS = {
    "writer": validate_writer,
    "reviewer": validate_reviewer,
    "dispatch": validate_dispatch,
    "senior-pm": validate_senior_pm,
}


def validate(document: Any, handoff_type: str) -> Problems:
    problems = Problems()
    if not isinstance(document, dict):
        problems.add(
            "<root>", "expected a JSON object, got %s" % typename(document)
        )
        return problems
    VALIDATORS[handoff_type](document, problems)
    return problems


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate-handoff",
        description=(
            "Validate an inter-agent handoff JSON file against the shape "
            "documented in the agent that writes it."
        ),
        epilog=(
            "Exit 0 valid, 1 invalid (one line per problem), 2 usage error. "
            "--type retro is reserved: it exits 2 until this framework "
            "version ships agents/prd-retro.md."
        ),
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=("writer", "reviewer", "dispatch", "senior-pm", "retro"),
        help=(
            "handoff contract to apply: writer (prd-writer Step 6), "
            "reviewer (prd-reviewer Step 9), dispatch (prd-reviewer Path A), "
            "senior-pm (prd-senior-pm Step 7). retro is reserved and always "
            "exits 2 — no retro agent exists yet."
        ),
    )
    parser.add_argument("file", help="handoff JSON file to validate")
    args = parser.parse_args(argv)

    if args.type not in VALIDATORS:
        sys.stderr.write(
            "validate-handoff: unknown type '%s': no agents/prd-%s.md exists "
            "in this framework version, so there is no documented shape to "
            "validate\n" % (args.type, args.type)
        )
        return 2

    try:
        with open(args.file, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        sys.stderr.write(
            "validate-handoff: cannot read %s: %s\n" % (args.file, exc)
        )
        return 2

    try:
        document = json.loads(text)
    except ValueError as exc:
        sys.stderr.write(
            "validate-handoff: %s is not valid JSON: %s\n" % (args.file, exc)
        )
        return 2

    problems = validate(document, args.type)
    if problems:
        print(problems.render())
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
