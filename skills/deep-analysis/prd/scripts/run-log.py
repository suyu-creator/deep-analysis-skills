#!/usr/bin/env python3
"""run-log — safe writer for the PRD pipeline run log (JSONL) and its timings.

The `/create-prd` skill used to build run-log lines by hand inside bash
heredocs — `echo '{"entryType":"writer","initiative":"'"$NAME"'",…}'`. An
initiative name containing a quote, a backslash, or `$(…)` either corrupted
the line or executed. This script builds the line with `json.dumps` instead:
values arrive as arguments, never as shell-interpolated JSON fragments.

Usage:
    python3 scripts/run-log.py append \\
        --log-file .claude/prd-run-log.jsonl \\
        --entry-type researcher|writer|reviewer|senior-pm|pipeline|terminated \\
        [--data '<json object>'] \\
        [--field key=value]... [--strict]

    python3 scripts/run-log.py timing --file <timing-file> --get <key> [--iso]
    python3 scripts/run-log.py timing --file <timing-file> --delta <start> <end>

`append` merges, in order: `--data` (parsed with json.loads), then each
`--field key=value` (the value is parsed as JSON when it parses, otherwise
kept as a literal string), then the `--entry-type` value as `entryType`. It
then checks the required fields for that entry type and appends exactly ONE
line to the log file.

Missing required fields are WARNINGS on stderr and the line is still written,
because a partially-filled entry is more useful than a lost one; `--strict`
turns them into errors (exit 1, nothing written) for callers that would rather
fail loudly.

`timing` reads the `key=value` timing file the skill writes with
`echo "key=$(date +%s)" >> "$TIMING_FILE"`, where the value is an epoch
optionally followed by an ISO timestamp (`pipeline_start=1754800000 2026-...`).
The last occurrence of a key wins. `--iso` prints the ISO8601 UTC rendering
instead of the epoch (recorded ISO if present, otherwise derived from the
epoch — no platform-specific `date -r` / `date -d @` juggling). `--delta`
prints `end - start` in seconds, which is what `durationSeconds` needs.

Shell fallback, if this script is absent: build the line with `python3 -c` +
`json.dumps`, passing the schema's fields as arguments — never with `echo`,
which reintroduces exactly the injection this script exists to prevent. Read
timings with `while IFS='=' read -r key val; do …; done < "$TIMING_FILE"`.

Exit codes:
    0 — line appended (append) / value printed (timing)
    1 — required fields missing under --strict, or timing key not found
    2 — usage error, malformed --data / --field JSON, unreadable or
        unwritable file

Required fields per entry type, derived from the JSONL Schema Reference in
`skills/deep-analysis/prd/PIPELINE.md` (that section is the contract; this table
mirrors it):

    researcher, writer, reviewer, senior-pm
        entryType runId initiative agent model cycle startedAt completedAt
        durationSeconds inputSummary outputSummary artifactPath handoffPath
        metrics
    pipeline
        the above plus profile
    terminated
        entryType runId initiative terminatedAt diedInPhase completedPhases
        reason

A key counts as present when it exists, even if its value is `null`
(`handoffPath` is legitimately null for the researcher and pipeline entries).

Stdlib only, Python 3.9+. Consumers copy this single file into their project.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

AGENT_FIELDS: Tuple[str, ...] = (
    "entryType",
    "runId",
    "initiative",
    "agent",
    "model",
    "cycle",
    "startedAt",
    "completedAt",
    "durationSeconds",
    "inputSummary",
    "outputSummary",
    "artifactPath",
    "handoffPath",
    "metrics",
)

REQUIRED_FIELDS: Dict[str, Tuple[str, ...]] = {
    "researcher": AGENT_FIELDS,
    "writer": AGENT_FIELDS,
    "reviewer": AGENT_FIELDS,
    # The senior-PM phase (Phase 3.5) logs the same envelope as the other
    # agents; its judgment counts (mode, failsJudged, dispositionCounts,
    # ticketCount, escalations, ticketsVerified) travel inside `metrics`.
    "senior-pm": AGENT_FIELDS,
    "pipeline": AGENT_FIELDS + ("profile",),
    "terminated": (
        "entryType",
        "runId",
        "initiative",
        "terminatedAt",
        "diedInPhase",
        "completedPhases",
        "reason",
    ),
}

ENTRY_TYPES: Tuple[str, ...] = tuple(REQUIRED_FIELDS)


# --------------------------------------------------------------------------
# append
# --------------------------------------------------------------------------


def parse_value(raw: str) -> Any:
    """JSON when it parses, otherwise the literal string.

    This is what makes `--field 'initiative=has "quotes" and $(dollar)'` safe:
    it is not valid JSON, so it stays a string and `json.dumps` escapes it.
    """
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def build_entry(
    entry_type: str, data: str, fields: Sequence[str]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        parsed = json.loads(data)
    except ValueError as exc:
        return None, "--data is not valid JSON: %s" % exc
    if not isinstance(parsed, dict):
        return None, "--data must be a JSON object, got %s" % type(parsed).__name__

    entry: Dict[str, Any] = dict(parsed)
    for pair in fields:
        if "=" not in pair:
            return None, "--field expects key=value, got %r" % pair
        key, raw = pair.split("=", 1)
        key = key.strip()
        if not key:
            return None, "--field has an empty key: %r" % pair
        entry[key] = parse_value(raw)

    entry["entryType"] = entry_type
    return entry, None


def missing_fields(entry: Dict[str, Any], entry_type: str) -> List[str]:
    return [name for name in REQUIRED_FIELDS[entry_type] if name not in entry]


def append(args: argparse.Namespace) -> int:
    entry, error = build_entry(args.entry_type, args.data, args.field)
    if entry is None:
        sys.stderr.write("run-log: %s\n" % error)
        return 2

    missing = missing_fields(entry, args.entry_type)
    if missing:
        label = "error" if args.strict else "warning"
        for name in missing:
            sys.stderr.write(
                "run-log: %s: %s entry is missing required field '%s'\n"
                % (label, args.entry_type, name)
            )
        if args.strict:
            sys.stderr.write("run-log: nothing appended (--strict)\n")
            return 1

    line = json.dumps(entry, ensure_ascii=False, sort_keys=False)
    directory = os.path.dirname(os.path.abspath(args.log_file))
    try:
        if directory and not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        with open(args.log_file, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError as exc:
        sys.stderr.write(
            "run-log: cannot append to %s: %s\n" % (args.log_file, exc)
        )
        return 2
    return 0


# --------------------------------------------------------------------------
# timing
# --------------------------------------------------------------------------


def read_timings(path: str) -> Dict[str, str]:
    """Parse `key=value` lines; the last occurrence of a key wins."""
    values: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def split_timing(value: str) -> Tuple[Optional[int], Optional[str]]:
    """`"1754800000 2026-08-10T12:00:00Z"` → (1754800000, "2026-08-10T…")."""
    parts = value.split()
    if not parts:
        return None, None
    epoch: Optional[int]
    try:
        epoch = int(parts[0])
    except ValueError:
        epoch = None
    iso = parts[1] if len(parts) > 1 else None
    return epoch, iso


def timing(args: argparse.Namespace) -> int:
    try:
        values = read_timings(args.file)
    except OSError as exc:
        sys.stderr.write("run-log: cannot read %s: %s\n" % (args.file, exc))
        return 2

    if args.delta:
        start_key, end_key = args.delta
        epochs = []
        for key in (start_key, end_key):
            if key not in values:
                sys.stderr.write(
                    "run-log: timing key '%s' not found in %s\n"
                    % (key, args.file)
                )
                return 1
            epoch, _ = split_timing(values[key])
            if epoch is None:
                sys.stderr.write(
                    "run-log: timing key '%s' has no epoch value (%r)\n"
                    % (key, values[key])
                )
                return 1
            epochs.append(epoch)
        print(epochs[1] - epochs[0])
        return 0

    key = args.get
    if key not in values:
        sys.stderr.write(
            "run-log: timing key '%s' not found in %s\n" % (key, args.file)
        )
        return 1
    epoch, iso = split_timing(values[key])
    if not args.iso:
        if epoch is None:
            sys.stderr.write(
                "run-log: timing key '%s' has no epoch value (%r)\n"
                % (key, values[key])
            )
            return 1
        print(epoch)
        return 0
    if iso:
        print(iso)
        return 0
    if epoch is None:
        sys.stderr.write(
            "run-log: timing key '%s' has neither epoch nor ISO value (%r)\n"
            % (key, values[key])
        )
        return 1
    print(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch)))
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run-log",
        description=(
            "Append validated JSONL entries to the PRD pipeline run log and "
            "read epoch values out of the pipeline timing file."
        ),
    )
    sub = parser.add_subparsers(dest="command")

    appender = sub.add_parser(
        "append", help="append one JSONL entry to the run log"
    )
    appender.add_argument("--log-file", required=True, help="target .jsonl file")
    appender.add_argument(
        "--entry-type", required=True, choices=ENTRY_TYPES,
        help="entry type; written as the entry's `entryType`",
    )
    appender.add_argument(
        "--data", default="{}",
        help="JSON object of entry fields (default: {})",
    )
    appender.add_argument(
        "--field", action="append", default=[], metavar="KEY=VALUE",
        help=(
            "override or add one field; VALUE is parsed as JSON when possible, "
            "otherwise kept as a literal string. Repeatable."
        ),
    )
    appender.add_argument(
        "--strict", action="store_true",
        help="fail (exit 1, write nothing) when a required field is missing",
    )

    timer = sub.add_parser(
        "timing", help="read a value out of the pipeline timing file"
    )
    timer.add_argument("--file", required=True, help="timing file to read")
    selector = timer.add_mutually_exclusive_group(required=True)
    selector.add_argument("--get", metavar="KEY", help="print this key's epoch")
    selector.add_argument(
        "--delta", nargs=2, metavar=("START", "END"),
        help="print END - START in seconds",
    )
    timer.add_argument(
        "--iso", action="store_true",
        help="with --get, print ISO8601 UTC instead of the epoch",
    )

    args = parser.parse_args(argv)
    if args.command == "append":
        return append(args)
    if args.command == "timing":
        return timing(args)
    parser.print_usage(sys.stderr)
    sys.stderr.write("run-log: a subcommand is required (append | timing)\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
