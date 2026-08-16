#!/usr/bin/env python3
"""Doc-consistency checker for the PRD agents framework.

The framework is documentation: agents, rules, templates and section packs are
markdown, and every enumeration in them (smell counts, matrix rows, section-pack
registries, file trees) is maintained by hand. That makes drift the dominant
defect class -- a count that says 9 while the source list holds 10, a README
tree that names a deleted file, a consuming project's vocabulary left behind in
a "generic" example. Each of those is mechanically detectable, so this script
detects them.

Run from anywhere; the repo root is inferred from this file's location and can
be overridden with --root.

Exit codes:
    0  no findings
    1  findings reported
    2  usage error

Output: one line per finding, ``<CHECK-ID> <file>:<line> <message>``.

Python 3.9+, standard library only -- no third-party imports, ever. CI runs it
on a bare ``actions/checkout`` with the runner's system Python.
"""

import argparse
import os
import re
import sys

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

# Directories that hold framework documentation. Everything here is authored
# markdown that the checks below reason about.
DOC_DIRS = ("agents", "rules", "templates", "skills")

# DOC-007: who may keep a rule alive. rules/ is deliberately excluded -- a rule
# that only other rules mention (or that mentions itself) is still unreachable
# from the pipeline, and counting rules/ as a consumer would let a cluster of
# orphans vouch for each other.
RULE_CONSUMER_DIRS = ("agents", "templates", "skills")

# Directories walked when collecting markdown to scan.
SCAN_ROOTS = ("agents", "rules", "templates", "skills", "scripts")

# Root-level markdown files that are part of the framework's documentation.
ROOT_DOCS = ("README.md", "project-context.md")

# Never walk into these.
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", ".github"}

# DOC-001: backticked repo-relative paths that must exist on disk.
#
# `docs/` is deliberately NOT in this prefix set. This repo has no docs/ tree:
# every `docs/...` reference in the framework describes the *consuming*
# project's layout (`docs/api-sources.md`, `docs/prd-sections/`,
# `docs/initiatives/{initiative}/...`), so checking it against this repo's disk
# would report ~18 findings that are all correct as written.
REF_PATH_RE = re.compile(
    r"`((?:agents|rules|templates|skills|scripts)"
    r"/[A-Za-z0-9._/-]+\.(?:md|py|sh|json|ya?ml))`"
)

# DOC-002: the source of truth for smell counts, and the files that restate them.
SMELL_PATTERNS_FILE = os.path.join("agents", "prd-smell-patterns.md")
SMELL_LINGUISTIC_HEADING = "## Linguistic Smells"
SMELL_SEPARATION_HEADING = "## Behavioral/Technical Separation Smells"
SMELL_COUNT_CONSUMERS = (os.path.join("agents", "prd-reviewer.md"), "README.md")

REVIEWER_FILE = os.path.join("agents", "prd-reviewer.md")
PROJECT_CONTEXT_FILE = "project-context.md"
README_FILE = "README.md"
SECTIONS_DIR = os.path.join("templates", "sections")
BANNED_TERMS_FILE = os.path.join("scripts", "banned-terms.txt")

# DOC-006 scan surface. The banned-terms guard protects *authored framework
# documentation*, so it scans the doc dirs plus the two root docs. It does NOT
# scan scripts/tests/fixtures/: those fixtures exist to make the linter fire and
# deliberately contain bad examples, so scanning them would couple two unrelated
# test suites. Per-term exemptions use the `term :: path` syntax instead of
# widening this surface.
BANNED_SCAN_DIRS = DOC_DIRS
BANNED_SCAN_FILES = ROOT_DOCS


# --------------------------------------------------------------------------
# Infrastructure
# --------------------------------------------------------------------------


class Finding(object):
    """One reported problem, rendered as ``<ID> <file>:<line> <message>``."""

    def __init__(self, check_id, path, line, message):
        self.check_id = check_id
        self.path = path
        self.line = line
        self.message = message

    def render(self):
        return "%s %s:%d %s" % (self.check_id, self.path, self.line, self.message)

    def sort_key(self):
        return (self.check_id, self.path, self.line, self.message)


def read_lines(root, rel_path):
    """Return the file's lines without trailing newlines, or None if unreadable."""
    try:
        with open(os.path.join(root, rel_path), "r", encoding="utf-8") as handle:
            return handle.read().splitlines()
    except (IOError, OSError, UnicodeDecodeError):
        return None


def markdown_files(root, dirs, extra_files):
    """Yield repo-relative paths of markdown files under `dirs`, plus `extra_files`."""
    seen = []
    for directory in dirs:
        abs_dir = os.path.join(root, directory)
        if not os.path.isdir(abs_dir):
            continue
        for dirpath, dirnames, filenames in os.walk(abs_dir):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                if name.endswith(".md"):
                    abs_path = os.path.join(dirpath, name)
                    seen.append(os.path.relpath(abs_path, root))
    for name in extra_files:
        if os.path.isfile(os.path.join(root, name)):
            seen.append(name)
    return seen


def all_markdown(root):
    """Every markdown file the checker considers part of the repo."""
    return markdown_files(root, SCAN_ROOTS, ROOT_DOCS)


def strip_code_fences(lines):
    """Yield (line_number, text) for lines outside ``` fenced blocks."""
    in_fence = False
    for index, text in enumerate(lines, start=1):
        stripped = text.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield index, text


def strip_inline_code(text):
    """Blank out `code span` contents.

    Markdown inside a code span is quoted, not live: a README that documents the
    ``](#anchor)`` link syntax is describing it, not linking. Replacing each
    span with spaces of the same width keeps column positions intact.
    """
    return re.sub(r"`[^`]*`", lambda match: " " * len(match.group(0)), text)


def github_slug(heading_text):
    """Approximate GitHub's heading-anchor slug algorithm."""
    text = heading_text.strip().lower()
    # GitHub strips inline markdown emphasis and links before slugging.
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # Drop everything that is not a word character, a space or a hyphen.
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


# --------------------------------------------------------------------------
# DOC-001: referenced files exist
# --------------------------------------------------------------------------


README_TREE_HEADING = "## What's Included"


def extract_readme_tree_block(lines):
    """Return [(line_no, text)] for the file tree under "## What's Included".

    The README contains three ASCII diagrams drawn with the same box-drawing
    characters: the repo file tree, the pipeline diagram, and an example output
    tree for a consuming project. Only the first is a claim about this repo's
    contents, so the parser is scoped to the first fenced block after the
    "What's Included" heading rather than to every line that happens to contain
    a tree branch.
    """
    block = []
    state = "seeking-heading"
    for line_no, text in enumerate(lines, start=1):
        if state == "seeking-heading":
            if text.strip() == README_TREE_HEADING:
                state = "seeking-fence"
        elif state == "seeking-fence":
            if text.strip().startswith("```"):
                state = "in-block"
        elif state == "in-block":
            if text.strip().startswith("```"):
                break
            block.append((line_no, text))
    return block


def parse_readme_tree(lines):
    """Parse the README's "What's Included" ASCII tree.

    Returns ``(files, dirs, first_line)`` where `files` maps a repo-relative
    path to the line it was declared on, `dirs` is the same for directories, and
    `first_line` is the line the tree starts on (used to anchor tree-level
    findings).
    """
    files = {}
    dirs = {}
    stack = []
    first_line = 0
    for line_no, text in extract_readme_tree_block(lines):
        marker = -1
        for candidate in ("├──", "└──"):  # ├── └──
            found = text.find(candidate)
            if found != -1 and (marker == -1 or found < marker):
                marker = found
        if marker == -1:
            continue
        if first_line == 0:
            first_line = line_no
        depth = marker // 4
        entry = text[marker + 3:].strip()
        if not entry:
            continue
        # Strip the trailing `# comment` column, then take the first token.
        entry = entry.split("#", 1)[0].strip()
        if not entry:
            continue
        name = entry.split()[0]
        prefix = stack[:depth]
        if name.endswith("/"):
            name = name.rstrip("/")
            del stack[depth:]
            stack.append(name)
            dirs["/".join(prefix + [name])] = line_no
        else:
            files["/".join(prefix + [name])] = line_no
    return files, dirs, first_line


def check_doc_001(root):
    findings = []

    # (a) every backticked repo-relative path in any markdown file exists
    for rel_path in all_markdown(root):
        lines = read_lines(root, rel_path)
        if lines is None:
            continue
        for line_no, text in enumerate(lines, start=1):
            for match in REF_PATH_RE.finditer(text):
                target = match.group(1)
                if not os.path.exists(os.path.join(root, target)):
                    findings.append(
                        Finding(
                            "DOC-001",
                            rel_path,
                            line_no,
                            "referenced file does not exist: %s" % target,
                        )
                    )

    readme_lines = read_lines(root, README_FILE)
    if readme_lines is None:
        findings.append(Finding("DOC-001", README_FILE, 0, "README.md is unreadable"))
        return findings

    tree_files, tree_dirs, tree_line = parse_readme_tree(readme_lines)

    # (b) every file named in the README tree exists on disk
    for path, line_no in sorted(tree_files.items()):
        if not os.path.exists(os.path.join(root, path)):
            findings.append(
                Finding(
                    "DOC-001",
                    README_FILE,
                    line_no,
                    "README tree names a file that does not exist: %s" % path,
                )
            )
    for path, line_no in sorted(tree_dirs.items()):
        if not os.path.isdir(os.path.join(root, path)):
            findings.append(
                Finding(
                    "DOC-001",
                    README_FILE,
                    line_no,
                    "README tree names a directory that does not exist: %s" % path,
                )
            )

    # (c) every markdown file under the doc dirs appears in the README tree
    for rel_path in markdown_files(root, DOC_DIRS, ()):
        normalized = rel_path.replace(os.sep, "/")
        if normalized not in tree_files:
            findings.append(
                Finding(
                    "DOC-001",
                    README_FILE,
                    tree_line,
                    "file missing from the README tree: %s" % normalized,
                )
            )

    return findings


# --------------------------------------------------------------------------
# DOC-002: smell-count consistency
# --------------------------------------------------------------------------


def count_bullets_under(lines, heading):
    """Count ``- **`` bullets between `heading` and the next ``## `` heading."""
    inside = False
    count = 0
    for text in lines:
        if text.strip() == heading:
            inside = True
            continue
        if inside and text.startswith("## "):
            break
        if inside and text.startswith("- **"):
            count += 1
    return count


def check_doc_002(root):
    findings = []
    lines = read_lines(root, SMELL_PATTERNS_FILE)
    if lines is None:
        return [
            Finding(
                "DOC-002",
                SMELL_PATTERNS_FILE,
                0,
                "smell patterns file is missing -- cannot verify counts",
            )
        ]

    linguistic = count_bullets_under(lines, SMELL_LINGUISTIC_HEADING)
    separation = count_bullets_under(lines, SMELL_SEPARATION_HEADING)
    total = linguistic + separation

    for heading, count in (
        (SMELL_LINGUISTIC_HEADING, linguistic),
        (SMELL_SEPARATION_HEADING, separation),
    ):
        if count == 0:
            findings.append(
                Finding(
                    "DOC-002",
                    SMELL_PATTERNS_FILE,
                    0,
                    'no "- **" bullets found under "%s"' % heading,
                )
            )
    if findings:
        return findings

    expectations = (
        (re.compile(r"(\d+) linguistic"), linguistic, "linguistic smell count"),
        (re.compile(r"(\d+) separation"), separation, "separation smell count"),
        (re.compile(r"(\d+) smell patterns"), total, "total smell-pattern count"),
        (re.compile(r"all (\d+) patterns"), total, "total smell-pattern count"),
    )

    for rel_path in SMELL_COUNT_CONSUMERS:
        consumer_lines = read_lines(root, rel_path)
        if consumer_lines is None:
            continue
        for line_no, text in enumerate(consumer_lines, start=1):
            for pattern, expected, label in expectations:
                for match in pattern.finditer(text):
                    stated = int(match.group(1))
                    if stated != expected:
                        findings.append(
                            Finding(
                                "DOC-002",
                                rel_path,
                                line_no,
                                "%s says %d but %s defines %d (%r)"
                                % (
                                    label,
                                    stated,
                                    SMELL_PATTERNS_FILE,
                                    expected,
                                    match.group(0),
                                ),
                            )
                        )
    return findings


# --------------------------------------------------------------------------
# DOC-003: matrix / F-row integrity
# --------------------------------------------------------------------------

F_REF_RE = re.compile(r"\bF-(\d+)\b")
F_ROW_RE = re.compile(r"^\|\s*F-(\d+)\s*\|")
MATRIX_REF_RE = re.compile(r"\bMatrix ([A-Z][0-9]?)\b")
MATRIX_DEF_RE = re.compile(r"\*\*Matrix ([A-Z][0-9]?):")


def check_doc_003(root):
    lines = read_lines(root, REVIEWER_FILE)
    if lines is None:
        return [Finding("DOC-003", REVIEWER_FILE, 0, "reviewer file is missing")]

    scaffold_rows = set()
    matrix_defs = set()
    for text in lines:
        row = F_ROW_RE.match(text)
        if row:
            scaffold_rows.add(row.group(1))
        for match in MATRIX_DEF_RE.finditer(text):
            matrix_defs.add(match.group(1))

    findings = []
    reported_f = set()
    reported_matrix = set()
    for line_no, text in enumerate(lines, start=1):
        if F_ROW_RE.match(text):
            continue
        for match in F_REF_RE.finditer(text):
            number = match.group(1)
            if number not in scaffold_rows and number not in reported_f:
                reported_f.add(number)
                findings.append(
                    Finding(
                        "DOC-003",
                        REVIEWER_FILE,
                        line_no,
                        "F-%s is referenced but has no scaffold row "
                        "`| F-%s |` in the Matrix F table" % (number, number),
                    )
                )
        for match in MATRIX_REF_RE.finditer(text):
            name = match.group(1)
            if name not in matrix_defs and name not in reported_matrix:
                reported_matrix.add(name)
                findings.append(
                    Finding(
                        "DOC-003",
                        REVIEWER_FILE,
                        line_no,
                        "Matrix %s is referenced but has no "
                        "`**Matrix %s:` definition" % (name, name),
                    )
                )
    return findings


# --------------------------------------------------------------------------
# DOC-004: README anchors resolve
# --------------------------------------------------------------------------

ANCHOR_LINK_RE = re.compile(r"\]\(#([^)]+)\)")


def check_doc_004(root):
    lines = read_lines(root, README_FILE)
    if lines is None:
        return [Finding("DOC-004", README_FILE, 0, "README.md is unreadable")]

    slugs = set()
    for _, text in strip_code_fences(lines):
        if text.startswith("#"):
            heading = text.lstrip("#").strip()
            if heading:
                slugs.add(github_slug(heading))

    findings = []
    for line_no, text in strip_code_fences(lines):
        for match in ANCHOR_LINK_RE.finditer(strip_inline_code(text)):
            anchor = match.group(1)
            if anchor not in slugs:
                findings.append(
                    Finding(
                        "DOC-004",
                        README_FILE,
                        line_no,
                        "anchor #%s does not match any README heading" % anchor,
                    )
                )
    return findings


# --------------------------------------------------------------------------
# DOC-005: section-pack integrity
# --------------------------------------------------------------------------

INSERT_TAG_RE = re.compile(r">\s*\*\*Insert into\*\*:")
POSITION_RE = re.compile(r"\[position:\s*\d+\]")
PACK_CHECKBOX_RE = re.compile(r"^-\s*\[[ xX]\]\s*([a-z0-9][a-z0-9-]*)")
PACK_LIST_HEADING = "### Included Section Packs"


def section_pack_names(root):
    abs_dir = os.path.join(root, SECTIONS_DIR)
    if not os.path.isdir(abs_dir):
        return []
    return sorted(
        name[:-3] for name in os.listdir(abs_dir) if name.endswith(".md")
    )


def check_doc_005(root):
    findings = []

    # (a) every section pack carries an Insert-into tag with a position
    for pack in section_pack_names(root):
        rel_path = "%s/%s.md" % (SECTIONS_DIR.replace(os.sep, "/"), pack)
        lines = read_lines(root, rel_path)
        if lines is None:
            continue
        tag_line = 0
        for line_no, text in enumerate(lines, start=1):
            if INSERT_TAG_RE.search(text):
                tag_line = line_no
                if not POSITION_RE.search(text):
                    findings.append(
                        Finding(
                            "DOC-005",
                            rel_path,
                            line_no,
                            "`> **Insert into**:` tag has no `[position: N]`",
                        )
                    )
                break
        if tag_line == 0:
            findings.append(
                Finding(
                    "DOC-005",
                    rel_path,
                    1,
                    "missing `> **Insert into**:` tag",
                )
            )

    # (b) every pack listed in project-context.md exists on disk
    context_lines = read_lines(root, PROJECT_CONTEXT_FILE)
    if context_lines is not None:
        inside = False
        for line_no, text in enumerate(context_lines, start=1):
            if text.strip() == PACK_LIST_HEADING:
                inside = True
                continue
            if inside and text.startswith("### "):
                break
            if not inside:
                continue
            match = PACK_CHECKBOX_RE.match(text.strip())
            if not match:
                continue
            if "removed" in text.lower():
                continue
            pack = match.group(1)
            target = os.path.join(root, SECTIONS_DIR, pack + ".md")
            if not os.path.exists(target):
                findings.append(
                    Finding(
                        "DOC-005",
                        PROJECT_CONTEXT_FILE,
                        line_no,
                        "section pack %r is listed but %s/%s.md does not exist"
                        % (pack, SECTIONS_DIR.replace(os.sep, "/"), pack),
                    )
                )

    # (c) every built-in pack has a Matrix G check-definition line
    reviewer_lines = read_lines(root, REVIEWER_FILE)
    if reviewer_lines is not None:
        reviewer_text = "\n".join(reviewer_lines)
        for pack in section_pack_names(root):
            if ("`%s`:" % pack) not in reviewer_text:
                findings.append(
                    Finding(
                        "DOC-005",
                        REVIEWER_FILE,
                        0,
                        "section pack %r has no Matrix G check definition "
                        "(expected a line starting `%s`:)" % (pack, pack),
                    )
                )

    return findings


# --------------------------------------------------------------------------
# DOC-006: banned-terms guard
# --------------------------------------------------------------------------

WORDISH_RE = re.compile(r"^\w+$")


def load_banned_terms(root):
    """Parse banned-terms.txt.

    Returns ``(terms, error)``. Each term is ``(term, compiled_regex,
    allowed_paths)``. Lines are one term each; ``#`` starts a comment; the
    inline allowlist syntax ``term :: path[, path...]`` exempts specific files.
    """
    lines = read_lines(root, BANNED_TERMS_FILE)
    if lines is None:
        return [], Finding(
            "DOC-006",
            BANNED_TERMS_FILE,
            0,
            "banned-terms file is missing -- domain-leakage guard cannot run",
        )

    terms = []
    for text in lines:
        stripped = text.split("#", 1)[0].strip()
        if not stripped:
            continue
        allowed = set()
        if "::" in stripped:
            term_part, allow_part = stripped.split("::", 1)
            stripped = term_part.strip()
            allowed = set(
                part.strip().replace(os.sep, "/")
                for part in allow_part.split(",")
                if part.strip()
            )
            if not stripped:
                continue
        # Word-ish terms get a leading word boundary so `idt` cannot match
        # inside `width`, plus a trailing `\w*` so inflections (`remittances`)
        # still trip the guard. Terms containing punctuation or spaces
        # (`money-transfer`, `/transfer/`, `bank deposit`) match literally --
        # a leading `\b` is meaningless before `/`.
        if WORDISH_RE.match(stripped):
            pattern = r"\b%s\w*" % re.escape(stripped)
        else:
            pattern = re.escape(stripped)
        terms.append((stripped, re.compile(pattern, re.IGNORECASE), allowed))
    return terms, None


def check_doc_006(root):
    terms, error = load_banned_terms(root)
    if error is not None:
        return [error]
    if not terms:
        return [
            Finding(
                "DOC-006",
                BANNED_TERMS_FILE,
                0,
                "banned-terms file defines no terms",
            )
        ]

    findings = []
    for rel_path in markdown_files(root, BANNED_SCAN_DIRS, BANNED_SCAN_FILES):
        normalized = rel_path.replace(os.sep, "/")
        lines = read_lines(root, rel_path)
        if lines is None:
            continue
        for line_no, text in enumerate(lines, start=1):
            for term, pattern, allowed in terms:
                if normalized in allowed:
                    continue
                match = pattern.search(text)
                if match:
                    findings.append(
                        Finding(
                            "DOC-006",
                            normalized,
                            line_no,
                            "banned term %r (matched %r) -- consuming-project "
                            "vocabulary must not appear in framework docs"
                            % (term, match.group(0)),
                        )
                    )
    return findings


# --------------------------------------------------------------------------
# DOC-007: rule-file cross-references
# --------------------------------------------------------------------------

RULE_REF_RE = re.compile(r"rules/([A-Za-z0-9._-]+\.md)")


def check_doc_007(root):
    findings = []
    rules_dir = os.path.join(root, "rules")
    if not os.path.isdir(rules_dir):
        return [Finding("DOC-007", "rules", 0, "rules/ directory is missing")]

    rule_files = sorted(
        name for name in os.listdir(rules_dir) if name.endswith(".md")
    )

    # (a) orphan-rule detection: consumed by at least one agent/template/skill
    consumers = markdown_files(root, RULE_CONSUMER_DIRS, ())
    referenced = set()
    for rel_path in consumers:
        lines = read_lines(root, rel_path)
        if lines is None:
            continue
        for text in lines:
            for match in RULE_REF_RE.finditer(text):
                referenced.add(match.group(1))
    for name in rule_files:
        if name not in referenced:
            findings.append(
                Finding(
                    "DOC-007",
                    "rules/%s" % name,
                    0,
                    "orphan rule -- not referenced by any file under %s"
                    % ", ".join("%s/" % d for d in RULE_CONSUMER_DIRS),
                )
            )

    # (b) every rules/ reference anywhere resolves to a file that exists
    for rel_path in all_markdown(root):
        lines = read_lines(root, rel_path)
        if lines is None:
            continue
        for line_no, text in enumerate(lines, start=1):
            for match in RULE_REF_RE.finditer(text):
                name = match.group(1)
                if name not in rule_files:
                    findings.append(
                        Finding(
                            "DOC-007",
                            rel_path.replace(os.sep, "/"),
                            line_no,
                            "reference to rules/%s but no such rule file exists"
                            % name,
                        )
                    )
    return findings


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

CHECKS = (
    ("DOC-001", check_doc_001),
    ("DOC-002", check_doc_002),
    ("DOC-003", check_doc_003),
    ("DOC-004", check_doc_004),
    ("DOC-005", check_doc_005),
    ("DOC-006", check_doc_006),
    ("DOC-007", check_doc_007),
)


def default_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    parser = argparse.ArgumentParser(
        description="Check the framework's documentation for internal drift."
    )
    parser.add_argument(
        "--root",
        default=default_root(),
        help="repo root to check (default: the parent of this script's directory)",
    )
    parser.add_argument(
        "--only",
        action="append",
        metavar="DOC-00N",
        help="run only this check (repeatable)",
    )
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        sys.stderr.write("error: not a directory: %s\n" % root)
        return 2

    selected = None
    if args.only:
        selected = set(item.strip().upper() for item in args.only)
        known = set(check_id for check_id, _ in CHECKS)
        unknown = sorted(selected - known)
        if unknown:
            sys.stderr.write(
                "error: unknown check id(s): %s\n" % ", ".join(unknown)
            )
            return 2

    findings = []
    for check_id, check in CHECKS:
        if selected is not None and check_id not in selected:
            continue
        findings.extend(check(root))

    findings.sort(key=lambda finding: finding.sort_key())
    for finding in findings:
        print(finding.render())

    if findings:
        sys.stderr.write("\n%d finding(s)\n" % len(findings))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
