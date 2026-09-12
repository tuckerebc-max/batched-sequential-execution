#!/usr/bin/env python3
"""
bse.py — command-line tooling for batched-sequential-execution (BSE).

THE MODEL IN ONE SCREEN
-----------------------
A deliverable that is too large for one reliable pass is split into an ordered
series of small, budgeted, independently verified *units* (B001, B002, ...).
Every unit is executed in fresh context from a self-contained *brief*, its
output artifact is checked against *external mechanical predicates* (`check`)
and, where the unit declares judgement predicates (`source:` / `charter:`),
against a reviewer's verdict (`review`); only work that passes BOTH gates is
recorded into a durable file *ledger*. At the end the verified artifacts are
*stitched* in plan order into draft.md; the human seam pass then writes
front-matter.md, back-matter.md and final.md (the tool never writes final.md).

All state lives in a run directory, never in a conversation:

    .bse/<run-id>/
      CHARTER.md       the contract (read by every batch)
      PLAN.md          unit table + one spec block per unit
      LEDGER.md        append-only human log; first line is the identity header
      ledger.json      machine mirror — AUTHORITATIVE for tooling
      carry.md         the baton: <= 400 words of rolling carry-forward
      briefs/ID.md     generated self-contained brief per unit
      batches/ID.md    the unit's output artifact (written by the executor)
      reports/ID.md    verification report per unit; reports/stitch.md
      front-matter.md  introduction / executive summary — written in the seam pass
      back-matter.md   conclusion — written in the seam pass
      draft.md         machine output of `stitch` (regenerated, never hand-edited)
      final.md         the seam-passed deliverable; NEVER written by this tool

The seven-move loop:  CHARTER -> PLAN -> [BRIEF -> EXECUTE -> VERIFY -> RECORD]*N -> STITCH -> SEAM

Exit codes: 0 success, 1 validation/verification failure, 2 usage error.
Every command accepts --run-dir PATH and --json.

Python 3.9+, standard library only, POSIX and Windows (pathlib everywhere,
explicit UTF-8, atomic writes via temp-file + os.replace).

ADDING A MECHANICAL VERIFIER (5 lines)
--------------------------------------
    @verifier("my_check")
    def v_my_check(text, args, ctx):
        # text: artifact text; args: everything after the name in the plan's
        # "- mechanical: my_check <args>" line; ctx: dict with unit/run/etc.
        return (passed: bool, detail: str)

The registry is the VERIFIERS dict; the decorator inserts into it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UNIT_TYPES = ("research", "compose", "revise", "transform", "verify", "assemble")
ID_PATTERN = r"B\d{3}[a-z]?"          # B003, plus B003a/B003b for split units
CARRY_WORD_CAP = 400
MAX_FIX_ROUNDS = 3
BUDGET_DRIFT_PCT = 20                 # plan sum vs charter total, and audit
DEFAULT_BUDGET_TOL_PCT = 15
SEAM_WORDS = 30
DUP_MIN_WORDS = 12

CARRY_SECTIONS = [
    "Established facts",
    "Interfaces/terms now defined",
    "Open threads for later units",
    "Do not repeat",
    "Tone calibration note",
]
CHARTER_SECTIONS = [
    "Deliverable", "Through-line", "Audience", "Voice & register", "Non-negotiables",
    "Terminology lock", "Sources of truth", "Acceptance criteria", "Out of scope",
]

# Placeholder strings forbidden in PLAN.md (DESIGN §2.2)
PLAN_PLACEHOLDER_RE = re.compile(
    r"\bTBD\b|\betc\.|\bsimilar to\b|\bas above\b|\.\.\.|…", re.IGNORECASE)

# Placeholder regexes for artifacts (DESIGN §6.1 no_placeholders)
ARTIFACT_PLACEHOLDERS = [
    ("TBD", re.compile(r"\bTBD\b")),
    ("TODO", re.compile(r"\bTODO\b")),
    ("[insert", re.compile(r"\[insert", re.IGNORECASE)),
    ("Lorem", re.compile(r"\bLorem\b")),
    ("etc. (line-final)", re.compile(r"\betc\.\s*$")),
    ("as described/above", re.compile(r"\bas (?:described|above)\b", re.IGNORECASE)),
    ("XXX", re.compile(r"XXX")),
]

# Angle-bracket placeholders (<insert name>, <your title>, <DATE>) are handled
# by angle_placeholders() rather than a bare regex, so that real HTML tags,
# closing tags and autolinks (<https://...>, <user@host>) are not flagged.
ANGLE_SPAN_RE = re.compile(r"<([A-Za-z][^<>\n]*?)>")
PLACEHOLDER_VOCAB = ("insert", "your", "name", "title", "date", "tbd", "todo",
                     "xxx", "placeholder", "description")
PLACEHOLDER_VOCAB_RE = re.compile(r"\b(?:" + "|".join(PLACEHOLDER_VOCAB) + r")\b", re.IGNORECASE)
HTML_TAGS = frozenset("""
    a abbr address article aside audio b bdi bdo blockquote br caption cite code col
    colgroup data dd del details dfn div dl dt em figcaption figure footer h1 h2 h3 h4 h5 h6
    header hr i iframe img ins kbd li main mark nav ol p picture pre q rp rt ruby s samp
    section small source span strong sub summary sup table tbody td template tfoot th thead
    time tr u ul var video wbr
""".split())

# What each numeric verifier counts, in budget denominations (DESIGN §2.2)
VERIFIER_COUNTS = {"word_count": "w", "slide_count": "slides", "item_count": "items"}

# Predicate-adequacy rules enforced by `plan --validate` (DESIGN §2.2). Each may
# be waived per unit with 'waive: <rule> — <reason>' in the spec block.
ADEQUACY_RULES = ("word_count", "citation_tags", "no_conclusion")
WAIVE_RE = re.compile(r"^(?P<rule>[A-Za-z_]+)\s*(?:—|–|--|-|:)\s*(?P<reason>.+)$")
# inputs that are part of every brief anyway and therefore never count as a source
BRIEF_INPUTS = ("charter.md", "carry.md")
REVIEW_VERDICTS = ("pass", "fail")

CONCLUSION_ANYWHERE_RE = re.compile(
    r"\b(?:in conclusion|to summarize|to summarise|in summary|to sum up)\b", re.IGNORECASE)
CONCLUSION_FINAL_PARA_RE = re.compile(r"\boverall,", re.IGNORECASE)

YEAR_RE = re.compile(r"\b(?:1[5-9]\d{2}|20\d{2})\b")
DIGIT_UNIT_RE = re.compile(
    r"(?:[$€£]\s?\d)|(?:\b\d[\d,]*(?:\.\d+)?\s?(?:%|percent|w\b|words?\b|k\b|m\b|bn\b|"
    r"million|billion|thousand|kg|km|cm|mm|ms\b|s\b|h\b|hrs?\b|hours?|days?|weeks?|"
    r"months?|years?|x\b|pp\b|pts?\b|usd|eur|gbp|slides?|items?|files?|pages?))",
    re.IGNORECASE)
SOURCE_TAG_RE = re.compile(r"\[S\d+\]")

TABLE_LINE_RE = re.compile(
    r"^\s*[-*]\s*\[(?P<done>[ xX])\]\s*(?P<id>" + ID_PATTERN + r")\s+"
    r"\[(?P<type>[A-Za-z]+)\]\s*(?P<rest>.*)$")
TABLE_CANDIDATE_RE = re.compile(r"^\s*[-*]\s*\[[ xX]\]\s*B\d")
SPEC_HEADING_RE = re.compile(
    r"^###\s+(?P<id>" + ID_PATTERN + r")\b\s*(?:[—–:-]+\s*)?(?P<title>.*?)\s*$")
BUDGET_RE = re.compile(r"(?P<n>\d[\d,]*)\s*(?P<unit>[A-Za-z]+)(?:\s*\(\s*[±+/-]*\s*(?P<pct>\d+)\s*%\s*\))?")
KEY_LINE_RE = re.compile(r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?P<val>.*)$")
LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+(?P<item>.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


class BseError(Exception):
    """Raised for user-facing failures. `code` is the process exit code."""

    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def atomic_write(path: Path, text: str) -> None:
    """Write text to path atomically: temp file in the same dir, then os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".bse-tmp-", suffix=".part", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strip_comment(value: str) -> str:
    """Strip a trailing '  # comment' (only when the # is preceded by whitespace)."""
    return re.sub(r"\s+#.*$", "", value).strip()


def masked_lines(text: str) -> List[str]:
    """Same-length copy of text.splitlines() with every line inside a fenced
    code block or an HTML comment blanked (and inline comments removed)."""
    out: List[str] = []
    in_fence = in_comment = False
    for line in text.splitlines():
        if in_comment:
            if "-->" not in line:
                out.append("")
                continue
            in_comment, line = False, line.split("-->", 1)[1]
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            out.append("")
            continue
        while "<!--" in line:
            before, after = line.split("<!--", 1)
            if "-->" in after:
                line = before + after.split("-->", 1)[1]
            else:
                in_comment, line = True, before
        out.append(line)
    return out


def prose_lines(text: str) -> List[Tuple[int, str]]:
    """(1-based lineno, line) for every line outside fences and HTML comments.
    This is the definition of 'prose' used by every verifier."""
    return list(enumerate(masked_lines(text), 1))


def count_words(text: str) -> int:
    """Word-count rule: a word is a whitespace-delimited token containing at
    least one letter or digit, counted over all prose lines (headings and list
    text included; fenced code blocks and HTML comments excluded)."""
    n = 0
    for _, line in prose_lines(text):
        n += sum(1 for tok in line.split() if re.search(r"\w", tok))
    return n


def headings_of(text: str) -> List[Tuple[int, int, str]]:
    """(lineno, depth, heading text) for every ATX heading in prose."""
    res = []
    for ln, line in prose_lines(text):
        m = HEADING_RE.match(line)
        if m:
            res.append((ln, len(m.group(1)), m.group(2).strip()))
    return res


def angle_placeholders(line: str) -> List[str]:
    """Angle-bracket spans in `line` that look like placeholders: the span
    contains whitespace or a placeholder-vocabulary word, and is not a known
    HTML tag, a closing tag, or an autolink (contains '://' or '@')."""
    hits: List[str] = []
    for m in ANGLE_SPAN_RE.finditer(line):
        inner = m.group(1)
        if "://" in inner or "@" in inner:
            continue                                   # autolink / email
        tag = re.match(r"^([A-Za-z][A-Za-z0-9]*)", inner)
        if tag and tag.group(1).lower() in HTML_TAGS:
            continue                                   # <br>, <sub>, <a href="...">, <br/>
        if re.search(r"\s", inner) or PLACEHOLDER_VOCAB_RE.search(inner):
            hits.append(m.group(0))
    return hits


NUMERIC_SPEC_BUDGET_RE = re.compile(r"^within\s+\d+\s*%(?:\s+of\s+budget)?$", re.IGNORECASE)


def spec_uses_budget(spec: str) -> bool:
    """True when a numeric verifier spec compares against the unit budget
    implicitly ('', 'within N%', 'within N% of budget') rather than a literal."""
    s = spec.strip()
    return s == "" or bool(NUMERIC_SPEC_BUDGET_RE.match(s))


def parse_number_spec(spec: str, actual: int, default_base: Optional[int],
                      default_pct: int) -> Tuple[bool, str]:
    """Generic numeric comparator shared by word_count/slide_count/item_count.

    Accepted forms:  'within N% of B' | 'within N%' | '>= N' | '<= N' | '> N'
    | '< N' | '== N' | 'N' | 'N-M' | '' (= within default_pct of default_base).
    'B' may be the word 'budget'."""
    s = spec.strip()
    m = re.match(r"^within\s+(\d+)\s*%(?:\s+of\s+(\d+|budget))?$", s, re.IGNORECASE)
    if m or s == "":
        pct = int(m.group(1)) if m else default_pct
        base_txt = (m.group(2) if m else None) or "budget"
        base = default_base if base_txt.lower() == "budget" else int(base_txt)
        if base is None:
            return False, "no budget available to compare against"
        lo, hi = base * (100 - pct) / 100.0, base * (100 + pct) / 100.0
        ok = lo <= actual <= hi
        return ok, f"{actual} {'within' if ok else 'outside'} {pct}% of {base} [{lo:.0f}-{hi:.0f}]"
    m = re.match(r"^(>=|<=|==|=|>|<)\s*(\d+)$", s)
    if m:
        op, n = m.group(1), int(m.group(2))
        ok = {">=": actual >= n, "<=": actual <= n, "==": actual == n, "=": actual == n,
              ">": actual > n, "<": actual < n}[op]
        return ok, f"{actual} {op} {n}: {'ok' if ok else 'violated'}"
    m = re.match(r"^(\d+)\s*[-–]\s*(\d+)$", s)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        ok = lo <= actual <= hi
        return ok, f"{actual} {'in' if ok else 'outside'} range {lo}-{hi}"
    if re.match(r"^\d+$", s):
        ok = actual == int(s)
        return ok, f"{actual} {'==' if ok else '!='} {s}"
    return False, f"cannot parse numeric spec {spec!r}"


def parse_string_list(args: str) -> List[str]:
    """Parse ["a", "b"] (JSON) or a, b (comma-separated) into a list of strings."""
    s = args.strip()
    if s.startswith("["):
        try:
            val = json.loads(s)
            if isinstance(val, list):
                return [str(v) for v in val]
        except json.JSONDecodeError:
            s = s.strip("[]")
    return [p.strip().strip("\"'") for p in s.split(",") if p.strip().strip("\"'")]


def sections_of(text: str) -> Dict[str, List[str]]:
    """Split a markdown document into {lowercased heading: body lines}.
    Also recognises '**Heading**' and 'Heading:' lines as section starts."""
    sections: Dict[str, List[str]] = {}
    current = "_preamble"
    sections[current] = []
    for _, line in prose_lines(text):
        m = HEADING_RE.match(line)
        if not m:
            m2 = re.match(r"^\*\*(.+?)\*\*:?\s*$", line.strip()) or \
                re.match(r"^([A-Z][A-Za-z/&' -]{2,40}):\s*$", line.strip())
            if m2:
                current = m2.group(1).strip().lower()
                sections.setdefault(current, [])
                continue
        else:
            current = m.group(2).strip().lower()
            sections.setdefault(current, [])
            continue
        sections[current].append(line)
    return sections


def find_section(sections: Dict[str, List[str]], name: str) -> Optional[List[str]]:
    key = name.lower()
    for k, v in sections.items():
        if k == key or k.startswith(key) or key in k:
            return v
    return None


def bullets_of(lines: List[str]) -> List[str]:
    return [strip_comment(re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", ln))
            for ln in lines if re.match(r"^\s*(?:[-*]|\d+[.)])\s+", ln)]


# ---------------------------------------------------------------------------
# Run directory, ledger, charter, carry
# ---------------------------------------------------------------------------

class Run:
    """Paths and ledger access for one run directory."""

    def __init__(self, root: Path):
        self.root = root
        self.charter_path = root / "CHARTER.md"
        self.plan_path = root / "PLAN.md"
        self.ledger_md = root / "LEDGER.md"
        self.ledger_json = root / "ledger.json"
        self.carry_path = root / "carry.md"
        self.briefs = root / "briefs"
        self.batches = root / "batches"
        self.reports = root / "reports"
        self.draft_path = root / "draft.md"
        self.front_matter_path = root / "front-matter.md"
        self.back_matter_path = root / "back-matter.md"
        self.final_path = root / "final.md"          # read by audit only; never written

    # -- ledger -------------------------------------------------------------
    def load_ledger(self) -> dict:
        if not self.ledger_json.exists():
            raise BseError(f"no ledger.json in {self.root} (run `bse.py init`)", 2)
        try:
            data = json.loads(read_text(self.ledger_json))
        except json.JSONDecodeError as e:
            raise BseError(f"ledger.json is corrupt: {e}")
        data.setdefault("units", {})
        data.setdefault("events", [])
        return data

    def save_ledger(self, data: dict) -> None:
        atomic_write(self.ledger_json, json.dumps(data, indent=1, sort_keys=True) + "\n")

    def identity_header(self, data: dict) -> str:
        return (f"# BSE ledger — run: {data['run_id']} — charter: {data['charter']}"
                f" — created: {data['created']}")

    def append_event(self, data: dict, line: str, **fields) -> None:
        """Append one event to ledger.json AND to LEDGER.md (append-only)."""
        ts = now_iso()
        data["events"].append({"ts": ts, "line": line, **fields})
        if self.ledger_md.exists():
            existing = read_text(self.ledger_md)
        else:
            existing = self.identity_header(data) + "\n"
        if not existing.endswith("\n"):
            existing += "\n"
        atomic_write(self.ledger_md, existing + line + "\n")
        self.save_ledger(data)

    def unit_state(self, data: dict, uid: str) -> dict:
        st = data["units"].setdefault(uid, {
            "status": "pending", "artifact": None, "sha256": None, "words": None,
            "verify": None, "attempts": 0, "fix_rounds": 0, "updated": None, "history": [],
            "reviews": []})
        st.setdefault("history", [])          # ledgers written before history existed
        st.setdefault("reviews", [])          # ledgers written before `review` existed
        return st

    # -- seam-pass files -----------------------------------------------------
    def matter_text(self, path: Path) -> Optional[str]:
        """front-matter.md / back-matter.md content, or None when the file is
        absent or carries no prose (the commented `init` scaffold counts as empty)."""
        if not path.exists():
            return None
        text = read_text(path)
        return text if count_words(text) > 0 else None

    def carry_is_stale(self) -> bool:
        """True when carry.md is empty or still byte-identical to the `init`
        scaffold (line endings normalised, so a CRLF checkout is not exempt)."""
        text = self.carry_text().replace("\r\n", "\n")
        return not text.strip() or text == CARRY_TEMPLATE

    @staticmethod
    def set_status(st: dict, status: str, ts: str, note: Optional[str] = None) -> None:
        """Change a unit's status and append to its history so ledger.json alone
        shows every state the unit passed through (blocked, fix, done ...)."""
        st["status"] = status
        st["updated"] = ts
        st.setdefault("history", []).append({"status": status, "timestamp": ts, "note": note})

    # -- charter / carry ----------------------------------------------------
    def charter_text(self) -> str:
        return read_text(self.charter_path) if self.charter_path.exists() else ""

    def carry_text(self) -> str:
        return read_text(self.carry_path) if self.carry_path.exists() else ""

    def charter_totals(self, data: Optional[dict] = None) -> List[Tuple[int, str]]:
        """Every charter total, one per denomination, e.g. [(20000, 'w'), (40, 'slides')]
        from 'Total size: 20000w, 40slides' in CHARTER.md (pieces separated by
        ',', ';', '+', '/' or 'and'; the first count in each piece is used).
        Falls back to ledger.json['total']. Empty list when nothing is declared."""
        text = self.charter_text()
        m = re.search(r"total[ \t]*size[ \t]*[:=]?[ \t]*(~?\d.*)$", text, re.IGNORECASE | re.MULTILINE)
        src = m.group(1) if m else (str(data["total"]) if data and data.get("total") else "")
        totals: List[Tuple[int, str]] = []
        # split on , ; + / and — but not on the thousands comma in 20,000
        for piece in re.split(r"\s*(?:,(?!\d{3}(?!\d))|[;+/]|\band\b)\s*", src, flags=re.IGNORECASE):
            b = parse_budget(piece.strip().lstrip("~"))
            if b and b[1] not in [t[1] for t in totals]:
                totals.append((b[0], b[1]))
        return totals

    def charter_total(self, data: Optional[dict] = None) -> Optional[Tuple[int, str]]:
        """The charter's word total if it declares one, else its first total
        (used by stitch for the prose-size comparison). None when undeclared."""
        totals = self.charter_totals(data)
        for t in totals:
            if t[1] == "w":
                return t
        return totals[0] if totals else None

    def terminology_lock(self) -> List[Tuple[str, str]]:
        """[(wrong_form, approved_form)] from the charter's Terminology lock
        section. Lines look like '- wrong form -> approved form' (several wrong
        forms may be separated by '|' or ','); table rows '| wrong | right |'
        are also accepted. A line whose two sides are identical is ignored."""
        sec = find_section(sections_of(self.charter_text()), "terminology lock")
        pairs: List[Tuple[str, str]] = []
        if not sec:
            return pairs
        for line in sec:
            s = line.strip()
            if s.startswith("|"):
                cells = [c.strip() for c in s.strip("|").split("|")]
                if len(cells) >= 2 and not set(cells[0]) <= set("-: "):
                    left, right = cells[0], cells[1]
                else:
                    continue
            elif "->" in s or "→" in s:
                left, right = re.split(r"\s*(?:->|→)\s*", re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", s), 1)
            else:
                continue
            right = right.strip().strip("\"'`")
            for w in re.split(r"\s*[|,]\s*", left):
                w = w.strip().strip("\"'`")
                if w and right and w.lower() != right.lower() and w.lower() not in ("term", "wrong form"):
                    pairs.append((w, right))
        return pairs

    def do_not_repeat(self) -> List[str]:
        sec = find_section(sections_of(self.carry_text()), "do not repeat")
        return bullets_of(sec) if sec else []


def normalize_unit(u: str) -> str:
    u = u.lower().rstrip(".")
    return {"words": "w", "word": "w", "slide": "slides", "file": "files",
            "item": "items", "wds": "w"}.get(u, u)


def parse_budget(s: str) -> Optional[Tuple[int, str, int]]:
    """'1200w (±15%)' -> (1200, 'w', 15). Tolerance defaults to 15."""
    m = BUDGET_RE.search(s or "")
    if not m:
        return None
    return (int(m.group("n").replace(",", "")), normalize_unit(m.group("unit")),
            int(m.group("pct")) if m.group("pct") else DEFAULT_BUDGET_TOL_PCT)


def most_recent_run(base: Path) -> Optional[Path]:
    if not base.is_dir():
        return None
    candidates = [p for p in base.iterdir() if (p / "ledger.json").exists()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: (p / "ledger.json").stat().st_mtime)


def resolve_run(args, must_exist: bool = True) -> Run:
    if args.run_dir:
        root = Path(args.run_dir)
    else:
        root = most_recent_run(Path.cwd() / ".bse")
        if root is None:
            if must_exist:
                raise BseError("no run directory found under ./.bse — use `init` or --run-dir", 2)
            root = Path.cwd() / ".bse"
    if must_exist and not (root / "ledger.json").exists():
        raise BseError(f"{root} is not a BSE run directory (no ledger.json)", 2)
    return Run(root)


# ---------------------------------------------------------------------------
# PLAN.md parsing and validation
# ---------------------------------------------------------------------------

@dataclass
class Unit:
    id: str
    title: str = ""
    type: str = ""
    parallel: bool = False
    depends_on: List[str] = field(default_factory=list)
    budget: Optional[Tuple[int, str, int]] = None     # (n, unit, tolerance %)
    done_in_plan: bool = False
    table_line: int = 0
    spec_line: int = 0
    spec_text: str = ""                                 # verbatim block, for briefs
    fields: Dict[str, object] = field(default_factory=dict)

    # convenience accessors over parsed spec fields
    def list_field(self, key: str) -> List[str]:
        v = self.fields.get(key)
        if isinstance(v, list):
            return [str(x) for x in v]
        if isinstance(v, str) and v.strip():
            return [v.strip()]
        return []

    def scalar_field(self, key: str) -> str:
        v = self.fields.get(key)
        return v.strip() if isinstance(v, str) else ""

    def verifiers(self) -> List[Tuple[str, str]]:
        """[(kind, expression)] e.g. ('mechanical', 'word_count within 15% of 1200')."""
        out = []
        for item in self.list_field("verify"):
            m = re.match(r"^(\w+)\s*:\s*(.*)$", item)
            out.append((m.group(1).lower(), m.group(2).strip()) if m else ("mechanical", item))
        return out

    def mechanical(self) -> List[str]:
        return [expr for kind, expr in self.verifiers() if kind == "mechanical"]

    def mechanical_names(self) -> List[str]:
        return [expr.split(None, 1)[0] for expr in self.mechanical() if expr.strip()]

    def judgement(self) -> List[str]:
        """Judgement predicates ('source: ...', 'charter: ...') — anything that is
        not mechanical. These are decided by a reviewer pass, not by `check`."""
        return [f"{k}: {e}" for k, e in self.verifiers() if k != "mechanical"]

    def source_inputs(self) -> List[str]:
        """Inputs that are SOURCES: everything except the files every brief carries
        anyway (CHARTER.md, carry.md) and the run's own verified artifacts
        (batches/<ID>.md), which were already checked when they were recorded."""
        out = []
        for raw in self.list_field("inputs"):
            name = raw.strip().strip("\"'").partition("#")[0].strip().replace("\\", "/")
            low = re.sub(r"^(?:\./)+", "", name.lower())
            if low in BRIEF_INPUTS or low.startswith("batches/"):
                continue
            out.append(raw.strip())
        return out

    def waivers(self) -> Tuple[Dict[str, str], List[str]]:
        """({rule: reason}, errors) from 'waive: <rule> — <reason>' (scalar or list)."""
        out: Dict[str, str] = {}
        errors: List[str] = []
        for item in self.list_field("waive"):
            m = WAIVE_RE.match(item.strip())
            if not m:
                errors.append(f"waiver {item!r} must look like 'waive: word_count — <reason>'")
                continue
            rule = m.group("rule").lower()
            if rule not in ADEQUACY_RULES:
                errors.append(f"waiver names unknown rule '{rule}' (waivable: {', '.join(ADEQUACY_RULES)})")
                continue
            out[rule] = m.group("reason").strip()
        return out, errors


def parse_table_line(line: str, lineno: int, errors: List[str]) -> Optional[Unit]:
    m = TABLE_LINE_RE.match(line)
    if not m:
        errors.append(f"L{lineno}: unparsable table line: {line.strip()!r}")
        return None
    u = Unit(id=m.group("id"), type=m.group("type").lower(), table_line=lineno,
             done_in_plan=m.group("done").lower() == "x")
    rest = m.group("rest")
    while True:                       # consume [P] and [dep:...] in either order
        rest = rest.lstrip()
        if rest.startswith("[P]"):
            u.parallel = True
            rest = rest[3:]
        elif rest.lower().startswith("[dep:"):
            end = rest.find("]")
            if end < 0:
                errors.append(f"L{lineno}: unterminated [dep: ...]")
                return None
            u.depends_on = [d.strip() for d in rest[5:end].split(",") if d.strip()]
            rest = rest[end + 1:]
        else:
            break
    parts = list(re.finditer(r"\s*[—–-]+\s*budget\s*:\s*", rest, re.IGNORECASE))
    if not parts:
        errors.append(f"L{lineno}: {u.id} table line has no '— budget: <n><unit>'")
        return None
    last = parts[-1]
    u.title = rest[:last.start()].strip()
    u.budget = parse_budget(rest[last.end():])
    if not u.budget:
        errors.append(f"L{lineno}: {u.id} budget must look like 1200w / 6slides / 3files / 10items")
    return u


def parse_spec_block(lines: List[str], start: int) -> Tuple[Dict[str, object], int]:
    """Parse YAML-ish fields from lines[start:] until the next heading.
    Supports 'key: value', 'key: [a, b]', 'key:' + '  - item' lists, and
    'key: |' block scalars. Returns (fields, index_after_block)."""
    fields: Dict[str, object] = {}
    i = start
    n = len(lines)
    while i < n:
        line = lines[i]
        if re.match(r"^#{1,6}\s", line):
            break
        m = KEY_LINE_RE.match(line)
        if not m:
            i += 1
            continue
        key, val = m.group("key").lower(), m.group("val").rstrip()
        i += 1
        if val.strip() in ("|", ">", "|-", ">-"):
            body: List[str] = []
            while i < n and (lines[i].strip() == "" or lines[i][:1] in (" ", "\t")):
                body.append(lines[i])
                i += 1
            while body and body[-1].strip() == "":
                body.pop()
            indents = [len(b) - len(b.lstrip()) for b in body if b.strip()]
            cut = min(indents) if indents else 0
            fields[key] = "\n".join(b[cut:] if b.strip() else "" for b in body).strip()
        elif val.strip() == "" or val.strip() == "[]":
            items: List[str] = []
            while i < n and (lines[i].strip() == "" or LIST_ITEM_RE.match(lines[i])):
                lm = LIST_ITEM_RE.match(lines[i])
                if lm:
                    items.append(strip_comment(lm.group("item")))
                i += 1
            fields[key] = items
        elif val.strip().startswith("[") and val.strip().endswith("]"):
            fields[key] = parse_string_list(strip_comment(val))
        else:
            fields[key] = strip_comment(val)
    return fields, i


def parse_plan(text: str) -> Tuple[List[Unit], List[str]]:
    """Parse PLAN.md into units (in table order) and a list of hard errors."""
    raw_lines = text.splitlines()
    lines = masked_lines(text)
    errors: List[str] = []
    units: List[Unit] = []
    by_id: Dict[str, Unit] = {}
    for idx, line in enumerate(lines):
        if TABLE_CANDIDATE_RE.match(line):
            u = parse_table_line(line, idx + 1, errors)
            if u is None:
                continue
            if u.id in by_id:
                errors.append(f"L{idx + 1}: duplicate unit id {u.id} in table (first at L{by_id[u.id].table_line})")
                continue
            by_id[u.id] = u
            units.append(u)
    seen_specs: Dict[str, int] = {}
    i = 0
    while i < len(lines):
        m = SPEC_HEADING_RE.match(lines[i])
        if not m:
            i += 1
            continue
        uid = m.group("id")
        fields, end = parse_spec_block(lines, i + 1)
        if uid in seen_specs:
            errors.append(f"L{i + 1}: duplicate spec block for {uid} (first at L{seen_specs[uid]})")
        seen_specs[uid] = i + 1
        u = by_id.get(uid)
        if u is None:
            errors.append(f"L{i + 1}: spec block for {uid} has no table entry")
        else:
            u.spec_line = i + 1
            u.spec_text = "\n".join(raw_lines[i:end]).rstrip() + "\n"
            u.fields = fields
            if not u.title:
                u.title = m.group("title").strip()
            sb = parse_budget(str(fields.get("budget", "")))   # spec supplies the tolerance
            if sb and u.budget:
                u.budget = (u.budget[0], u.budget[1], sb[2])
            elif sb:
                u.budget = sb
        i = end if end > i else i + 1
    for u in units:
        if u.spec_line == 0:
            errors.append(f"L{u.table_line}: {u.id} has no '### {u.id} — title' spec block")
    return units, errors


def load_units(run: Run) -> List[Unit]:
    if not run.plan_path.exists():
        raise BseError(f"no PLAN.md in {run.root}")
    units, errors = parse_plan(read_text(run.plan_path))
    if errors:
        raise BseError("PLAN.md parse errors:\n  " + "\n  ".join(errors))
    return units


def find_cycle(units: List[Unit]) -> Optional[List[str]]:
    graph = {u.id: [d for d in u.depends_on] for u in units}
    WHITE, GREY, BLACK = 0, 1, 2
    color = {k: WHITE for k in graph}
    stack: List[str] = []

    def dfs(node: str) -> Optional[List[str]]:
        color[node] = GREY
        stack.append(node)
        for dep in graph.get(node, []):
            if dep not in color:
                continue
            if color[dep] == GREY:
                return stack[stack.index(dep):] + [dep]
            if color[dep] == WHITE:
                found = dfs(dep)
                if found:
                    return found
        stack.pop()
        color[node] = BLACK
        return None

    for k in graph:
        if color[k] == WHITE:
            c = dfs(k)
            if c:
                return c
    return None


def adequacy_errors(u: Unit, is_final: bool) -> Tuple[List[str], List[dict]]:
    """Predicate-adequacy rules (DESIGN §2.2). Returns (errors, waivers_used).
    Each error names the unit, the rule and the one-line fix."""
    errors: List[str] = []
    waived, werrs = u.waivers()
    where = f"L{u.spec_line or u.table_line}: {u.id}"
    errors += [f"{where} {e}" for e in werrs]
    names = set(u.mechanical_names())
    used: List[dict] = [{"unit": u.id, "rule": r, "reason": waived[r]} for r in ADEQUACY_RULES if r in waived]

    def fix(rule: str, line: str) -> str:
        return f"{where} [{rule}] {line} (or add 'waive: {rule} — <reason>' to the spec block)"

    if u.budget and u.budget[1] == "w" and "word_count" not in names and "word_count" not in waived:
        errors.append(fix("word_count", f"budget is in words ({u.budget[0]}w) but no word_count verifier is declared: "
                          f"add '- mechanical: word_count within {u.budget[2]}% of budget'"))
    srcs = u.source_inputs()
    if srcs and "citation_tags" not in names and not any(k == "source" for k, _ in u.verifiers()) \
            and "citation_tags" not in waived:
        errors.append(fix("citation_tags", f"reads {len(srcs)} input(s) beyond the charter ({srcs[0]}"
                          f"{', ...' if len(srcs) > 1 else ''}) but declares neither citation_tags nor a source predicate: "
                          "add '- mechanical: citation_tags' or '- source: <what must trace to which [S#]>'"))
    if u.type == "compose" and not is_final and "no_conclusion" not in names and "no_conclusion" not in waived:
        errors.append(fix("no_conclusion", "non-final compose unit does not declare no_conclusion: "
                          "add '- mechanical: no_conclusion'"))
    return errors, used


def validate_plan(run: Run, units: List[Unit], parse_errors: List[str],
                  ledger: Optional[dict] = None) -> Tuple[List[str], List[str], List[dict]]:
    """Return (errors, warnings, waivers). Empty errors == gate passed."""
    errors = list(parse_errors)
    warnings: List[str] = []
    waivers: List[dict] = []
    ids = {u.id for u in units}
    if not units:
        errors.append("PLAN EMPTY: no units found (expected '- [ ] B001 [type] title — budget: 1200w' lines)")
        return errors, warnings, waivers
    for u in units:
        where = f"L{u.spec_line or u.table_line}: {u.id}"
        aerrs, used = adequacy_errors(u, is_final=(u is units[-1]))
        errors += aerrs
        waivers += used
        if SAMPLE_MARKER in u.title or SAMPLE_MARKER in u.spec_text:
            warnings.append(f"{u.id} is the `init` sample unit — replace it with a real unit before executing")
        if u.type not in UNIT_TYPES:
            errors.append(f"L{u.table_line}: {u.id} unknown type '{u.type}' (expected one of {', '.join(UNIT_TYPES)})")
        spec_type = u.scalar_field("type").lower()
        if spec_type and spec_type != u.type:
            errors.append(f"{where} type mismatch: table says {u.type}, spec says {spec_type}")
        spec_budget = parse_budget(u.scalar_field("budget"))
        if not u.budget and not spec_budget:
            errors.append(f"{where} missing budget")
        elif u.budget and spec_budget and (u.budget[0], u.budget[1]) != (spec_budget[0], spec_budget[1]):
            errors.append(f"{where} budget mismatch: table {u.budget[0]}{u.budget[1]} vs spec {spec_budget[0]}{spec_budget[1]}")
        if not u.scalar_field("intent"):
            errors.append(f"{where} missing intent")
        if not u.scalar_field("done_when"):
            errors.append(f"{where} missing done_when")
        if not u.list_field("inputs"):
            errors.append(f"{where} missing inputs")
        if not u.list_field("produces"):
            errors.append(f"{where} missing produces")
        mech = u.mechanical()
        if not mech:
            errors.append(f"{where} needs at least one '- mechanical: ...' verifier")
        for expr in mech:
            parts = expr.split(None, 1)
            name, vargs = (parts[0] if parts else ""), (parts[1] if len(parts) > 1 else "")
            if name not in VERIFIERS:
                errors.append(f"{where} unknown mechanical verifier '{name}' (known: {', '.join(sorted(VERIFIERS))})")
            # a numeric verifier whose implicit base is the unit budget must count
            # the same denomination the budget is expressed in (else `check` can
            # never resolve the base) — an explicit literal base is always legal
            counts = VERIFIER_COUNTS.get(name)
            if counts and u.budget and spec_uses_budget(vargs) and u.budget[1] != counts:
                errors.append(f"{where} verifier '{expr}' compares against the unit budget, but the budget "
                              f"is in '{u.budget[1]}' ({u.budget[0]}{u.budget[1]}) and {name} counts '{counts}': "
                              f"give an explicit base (e.g. '{name} within 15% of <n>') or change the budget denomination")
        spec_deps = u.list_field("depends_on")
        for d in set(u.depends_on) | set(spec_deps):
            if d not in ids:
                errors.append(f"{where} depends on unknown unit {d}")
            if d == u.id:
                errors.append(f"{where} depends on itself")
        if spec_deps and set(spec_deps) != set(u.depends_on):
            errors.append(f"{where} depends_on mismatch: table {u.depends_on or '[]'} vs spec {spec_deps}")
        pm = PLAN_PLACEHOLDER_RE.search(u.spec_text)
        if pm:
            ln = u.spec_line + u.spec_text[:pm.start()].count("\n")
            errors.append(f"L{ln}: {u.id} placeholder string {pm.group(0)!r} in spec block")
    cyc = find_cycle(units)
    if cyc:
        errors.append("dependency cycle: " + " -> ".join(cyc))
    # [P] units must not share produces targets with any other unit
    produces: Dict[str, List[str]] = {}
    for u in units:
        for p in u.list_field("produces"):
            produces.setdefault(re.sub(r"\s+", " ", p.strip().lower()), []).append(u.id)
    for target, owners in produces.items():
        if len(owners) > 1 and any(next(x for x in units if x.id == o).parallel for o in owners):
            errors.append(f"[P] unit shares produces target {target!r}: {', '.join(owners)}")
    # budget sum vs charter total, per denomination
    totals = run.charter_totals(ledger)
    if not totals:
        errors.append("charter total size not found (add 'Total size: 20000w' to CHARTER.md Deliverable)")
    else:
        for d in budget_drift(units, totals):
            if d["total"] is None:
                warnings.append(f"budget denomination '{d['unit']}' (sum {d['sum']}{d['unit']} across "
                                f"{', '.join(d['units'])}) has no charter total; drift not checked")
            elif d["drift_pct"] > BUDGET_DRIFT_PCT:
                errors.append(f"budget sum {d['sum']}{d['unit']} drifts {d['drift_pct']:.0f}% from charter total "
                              f"{d['total']}{d['unit']} (limit ±{BUDGET_DRIFT_PCT}%)")
    if len(units) < 5:
        warnings.append(f"only {len(units)} units: BSE is overhead below 5 units (DESIGN §4)")
    return errors, warnings, waivers


def budget_drift(units: List[Unit], totals: List[Tuple[int, str]]) -> List[dict]:
    """Per-denomination plan-budget sums vs charter totals. One row per
    denomination that appears in the charter or the plan: {unit, sum, units,
    total, drift_pct}; total/drift_pct are None for a denomination the charter
    does not declare."""
    sums: Dict[str, int] = {}
    owners: Dict[str, List[str]] = {}
    for u in units:
        if u.budget:
            sums[u.budget[1]] = sums.get(u.budget[1], 0) + u.budget[0]
            owners.setdefault(u.budget[1], []).append(u.id)
    rows: List[dict] = []
    declared = {t[1]: t[0] for t in totals}
    for denom in list(declared) + [d for d in sums if d not in declared]:
        s = sums.get(denom, 0)
        total = declared.get(denom)
        drift = (abs(s - total) * 100.0 / total if total else 0.0) if total is not None else None
        rows.append({"unit": denom, "sum": s, "units": owners.get(denom, []), "total": total, "drift_pct": drift})
    return rows


def mark_done_in_plan(run: Run, uid: str) -> None:
    """Flip '- [ ] B00X' to '- [x] B00X' on the unit's table line (tooling only)."""
    lines = read_text(run.plan_path).splitlines()
    out = []
    for line in lines:
        m = TABLE_LINE_RE.match(line)
        if m and m.group("id") == uid:
            line = re.sub(r"\[[ ]\]", "[x]", line, count=1)
        out.append(line)
    atomic_write(run.plan_path, "\n".join(out) + "\n")


# ---------------------------------------------------------------------------
# Mechanical verifiers (registry)
# ---------------------------------------------------------------------------

Verifier = Callable[[str, str, dict], Tuple[bool, str]]
VERIFIERS: Dict[str, Verifier] = {}


def verifier(name: str) -> Callable[[Verifier], Verifier]:
    def register(fn: Verifier) -> Verifier:
        VERIFIERS[name] = fn
        return fn
    return register


def _budget_n(ctx: dict, unit_kind: Optional[str] = None) -> Optional[int]:
    b = ctx["unit"].budget if ctx.get("unit") else None
    if b and (unit_kind is None or b[1] == unit_kind):
        return b[0]
    return None


def _tol(ctx: dict) -> int:
    b = ctx["unit"].budget if ctx.get("unit") else None
    return b[2] if b else DEFAULT_BUDGET_TOL_PCT


@verifier("word_count")
def v_word_count(text: str, args: str, ctx: dict) -> Tuple[bool, str]:
    """word_count within 15% of 1200 | within 15% | >= 800 | 800-1400 | 1200"""
    ok, detail = parse_number_spec(args, count_words(text), _budget_n(ctx, "w"), _tol(ctx))
    return ok, "word_count " + detail


@verifier("no_placeholders")
def v_no_placeholders(text: str, args: str, ctx: dict) -> Tuple[bool, str]:
    """Flags TBD, TODO, [insert, Lorem, line-final 'etc.', 'as described/above',
    XXX and <angle-bracket> placeholders in prose (code spans excluded).
    An angle span counts as a placeholder only when it contains whitespace or
    placeholder vocabulary (insert, your, name, title, date, tbd, todo, xxx,
    placeholder, description); HTML tags, closing tags and autolinks pass."""
    hits = []
    for ln, line in prose_lines(text):
        bare = re.sub(r"`[^`]*`", "", line)
        for label, rx in ARTIFACT_PLACEHOLDERS:
            m = rx.search(bare)
            if m:
                hits.append(f"{label} {m.group(0)!r} L{ln}")
        for span in angle_placeholders(bare)[:1]:
            hits.append(f"<angle placeholder> {span!r} L{ln}")
    return (not hits), ("no placeholders" if not hits else "placeholders: " + "; ".join(hits[:8]))


@verifier("contains_headings")
def v_contains_headings(text: str, args: str, ctx: dict) -> Tuple[bool, str]:
    """contains_headings ["3.2 Method", "Results"] — exact heading text required."""
    wanted = parse_string_list(args)
    have = {h for _, _, h in headings_of(text)}
    missing = [w for w in wanted if w not in have]
    return (not missing), ("all headings present" if not missing else "missing headings: " + ", ".join(repr(m) for m in missing))


@verifier("max_heading_depth")
def v_max_heading_depth(text: str, args: str, ctx: dict) -> Tuple[bool, str]:
    """max_heading_depth 3"""
    try:
        limit = int(args.strip())
    except ValueError:
        return False, f"max_heading_depth needs an integer, got {args!r}"
    deep = [(ln, d) for ln, d, _ in headings_of(text) if d > limit]
    return (not deep), (f"max heading depth <= {limit}" if not deep
                        else "too deep: " + ", ".join(f"H{d} at L{ln}" for ln, d in deep[:6]))


@verifier("citation_tags")
def v_citation_tags(text: str, args: str, ctx: dict) -> Tuple[bool, str]:
    """Every prose SENTENCE with a digit-with-unit (12%, 3 million, $4, 1200w ...)
    or a year (1500-2099) must carry an [S#] tag. Physical lines of a paragraph
    are joined first, so hard-wrapped prose whose tag falls on the next line
    counts as tagged. Headings and fenced code are exempt."""
    bad = []
    for ln_of, joined in prose_sentence_chunks(text):
        # a tag written after the terminal punctuation ('...12%. [S1]') belongs
        # to the sentence it follows: move it inside before splitting
        joined = re.sub(r"([.!?])((?:\s*\[S\d+\])+)", r"\2\1", joined)
        pos = 0
        for sent in re.split(r"(?<=[.!?])\s+", joined):
            if not sent.strip():
                continue
            start = joined.find(sent, pos)
            start = pos if start < 0 else start
            pos = start + len(sent)
            if (DIGIT_UNIT_RE.search(sent) or YEAR_RE.search(sent)) and not SOURCE_TAG_RE.search(sent):
                a, b = ln_of(start), ln_of(max(start, pos - 1))
                bad.append(f"L{a}" if a == b else f"L{a}-{b}")
    return (not bad), ("all numeric claims tagged" if not bad
                       else "untagged numeric/year sentences: " + ", ".join(bad[:10]))


def prose_sentence_chunks(text: str):
    """Yield (line_of, joined_text) per prose chunk. A chunk is a paragraph
    (consecutive non-blank lines) or one block item (list item, table row,
    blockquote line, plus its indented continuation lines); headings are
    skipped. `line_of(offset)` maps an offset in joined_text back to the
    1-based source line number."""
    block_re = re.compile(r"^(?:[-*+]\s+|\d+[.)]\s+|>\s*|\|)")
    chunk: List[Tuple[int, str]] = []

    def flush():
        if not chunk:
            return None
        offsets: List[Tuple[int, int]] = []
        parts: List[str] = []
        pos = 0
        for ln, s in chunk:
            offsets.append((pos, ln))
            parts.append(s)
            pos += len(s) + 1
        joined = " ".join(parts)

        def line_of(off: int) -> int:
            ln = offsets[0][1]
            for start, l in offsets:
                if start <= off:
                    ln = l
            return ln
        return line_of, joined

    for ln, line in prose_lines(text):
        s = line.strip()
        if not s or HEADING_RE.match(line):
            r = flush()
            chunk = []
            if r:
                yield r
            continue
        if block_re.match(s):                  # a new block item starts a new chunk
            r = flush()
            chunk = []
            if r:
                yield r
            s = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+|>\s*)", "", s)
        chunk.append((ln, s))
    r = flush()
    if r:
        yield r


@verifier("forbidden_phrases")
def v_forbidden_phrases(text: str, args: str, ctx: dict) -> Tuple[bool, str]:
    """forbidden_phrases ["x", "y"]; with no list, uses the charter terminology
    lock (wrong forms) plus carry.md 'Do not repeat' bullets."""
    phrases = parse_string_list(args) if args.strip() else []
    if not phrases:
        run: Optional[Run] = ctx.get("run")
        if run:
            phrases = [w for w, _ in run.terminology_lock()] + run.do_not_repeat()
    hits = []
    for ln, line in prose_lines(text):
        low = line.lower()
        for p in phrases:
            if p and re.search(r"(?<!\w)" + re.escape(p.lower()) + r"(?!\w)", low):
                hits.append(f"{p!r} L{ln}")
    return (not hits), ("no forbidden phrases" if not hits else "forbidden: " + "; ".join(hits[:8]))


def _count_slides(text: str) -> int:
    """A slide is an H1/H2 heading; if there are none, '---' separators + 1."""
    hs = [h for h in headings_of(text) if h[1] <= 2]
    if hs:
        return len(hs)
    seps = sum(1 for _, l in prose_lines(text) if re.match(r"^\s*(?:---|\*\*\*)\s*$", l))
    return seps + 1 if seps else 0


@verifier("slide_count")
def v_slide_count(text: str, args: str, ctx: dict) -> Tuple[bool, str]:
    """slide_count 6 | within 20% of 6 | 4-8 (slides = H1/H2 headings, else '---' sections)"""
    ok, d = parse_number_spec(args, _count_slides(text), _budget_n(ctx, "slides"), _tol(ctx))
    return ok, "slide_count " + d


@verifier("item_count")
def v_item_count(text: str, args: str, ctx: dict) -> Tuple[bool, str]:
    """item_count 10 | >= 5 (items = top-level '-', '*' or '1.' list lines)"""
    n = sum(1 for _, l in prose_lines(text) if re.match(r"^(?:[-*]|\d+[.)])\s+\S", l))
    ok, d = parse_number_spec(args, n, _budget_n(ctx, "items"), _tol(ctx))
    return ok, "item_count " + d


def _resolve_path(ctx: dict, p: str) -> Path:
    cand = Path(p)
    run = ctx.get("run")
    if not cand.is_absolute() and run and (run.root / cand).exists():
        return run.root / cand
    return cand


@verifier("file_exists")
def v_file_exists(text: str, args: str, ctx: dict) -> Tuple[bool, str]:
    """file_exists path (relative to the run dir, then the cwd)"""
    p = _resolve_path(ctx, args.strip().strip("\"'"))
    return p.exists(), f"{p} {'exists' if p.exists() else 'missing'}"


def _json_validate(obj, schema: dict, path: str = "$") -> List[str]:
    """Tiny JSON-schema subset: type, properties, required, items, enum,
    minimum, maximum, minLength, maxLength, additionalProperties."""
    errs: List[str] = []
    t = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "number": (int, float),
             "integer": int, "boolean": bool, "null": type(None)}
    if t:
        allowed = t if isinstance(t, list) else [t]
        if not any(isinstance(obj, types[a]) and not (a in ("number", "integer") and isinstance(obj, bool))
                   for a in allowed if a in types):
            return [f"{path}: expected {t}, got {type(obj).__name__}"]
    if "enum" in schema and obj not in schema["enum"]:
        errs.append(f"{path}: {obj!r} not in enum")
    if isinstance(obj, dict):
        for r in schema.get("required", []):
            if r not in obj:
                errs.append(f"{path}: missing required '{r}'")
        for k, sub in schema.get("properties", {}).items():
            if k in obj:
                errs += _json_validate(obj[k], sub, f"{path}.{k}")
        if schema.get("additionalProperties") is False:
            for k in obj:
                if k not in schema.get("properties", {}):
                    errs.append(f"{path}: unexpected property '{k}'")
    if isinstance(obj, list) and isinstance(schema.get("items"), dict):
        for i, it in enumerate(obj):
            errs += _json_validate(it, schema["items"], f"{path}[{i}]")
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        if "minimum" in schema and obj < schema["minimum"]:
            errs.append(f"{path}: {obj} < minimum {schema['minimum']}")
        if "maximum" in schema and obj > schema["maximum"]:
            errs.append(f"{path}: {obj} > maximum {schema['maximum']}")
    if isinstance(obj, str):
        if "minLength" in schema and len(obj) < schema["minLength"]:
            errs.append(f"{path}: shorter than {schema['minLength']}")
        if "maxLength" in schema and len(obj) > schema["maxLength"]:
            errs.append(f"{path}: longer than {schema['maxLength']}")
    return errs


@verifier("json_schema")
def v_json_schema(text: str, args: str, ctx: dict) -> Tuple[bool, str]:
    """json_schema path/to/schema.json — artifact is JSON, or has a ```json fence."""
    sp = _resolve_path(ctx, args.strip().strip("\"'"))
    if not sp.exists():
        return False, f"schema file missing: {sp}"
    try:
        schema = json.loads(read_text(sp))
    except json.JSONDecodeError as e:
        return False, f"schema is not valid JSON: {e}"
    body = text
    m = re.search(r"```json\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if m:
        body = m.group(1)
    try:
        obj = json.loads(body)
    except json.JSONDecodeError as e:
        return False, f"artifact is not valid JSON: {e}"
    errs = _json_validate(obj, schema)
    return (not errs), ("json valid against schema" if not errs else "; ".join(errs[:8]))


@verifier("shell")
def v_shell(text: str, args: str, ctx: dict) -> Tuple[bool, str]:
    """shell <command> — runs in the run dir with $BSE_ARTIFACT set; non-zero = fail."""
    run = ctx.get("run")
    env = dict(os.environ)
    if ctx.get("artifact"):
        env["BSE_ARTIFACT"] = str(ctx["artifact"])
    try:
        cp = subprocess.run(args, shell=True, cwd=str(run.root) if run else None, env=env,
                            capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return False, "shell command timed out (300s)"
    tail = (cp.stderr or cp.stdout).strip().splitlines()[-3:]
    return cp.returncode == 0, f"exit {cp.returncode}" + (": " + " | ".join(tail) if tail else "")


@verifier("no_conclusion")
def v_no_conclusion(text: str, args: str, ctx: dict) -> Tuple[bool, str]:
    """Flags 'in conclusion' / 'to summarize' / 'in summary' anywhere and
    'overall,' in the final paragraph. Use only on non-final units."""
    hits = []
    lines = prose_lines(text)
    for ln, line in lines:
        m = CONCLUSION_ANYWHERE_RE.search(line)
        if m:
            hits.append(f"{m.group(0)!r} L{ln}")
    last_para: List[Tuple[int, str]] = []
    for ln, l in reversed(lines):          # final paragraph = after the last blank line
        if not l.strip() and last_para:
            break
        if l.strip():
            last_para.insert(0, (ln, l))
    for ln, l in last_para:
        m = CONCLUSION_FINAL_PARA_RE.search(l)
        if m:
            hits.append(f"{m.group(0)!r} in final paragraph L{ln}")
    return (not hits), ("no concluding language" if not hits else "concluding language: " + "; ".join(hits))


def run_checks(run: Run, unit: Unit, artifact: Path) -> dict:
    """Run every mechanical verifier declared by the unit. Returns the verify record."""
    exists = artifact.exists()
    text = read_text(artifact) if exists else ""
    ctx = {"unit": unit, "run": run, "artifact": artifact}
    checks = []
    for expr in unit.mechanical():
        parts = expr.split(None, 1)
        name, args = parts[0], (parts[1] if len(parts) > 1 else "")
        fn = VERIFIERS.get(name)
        if fn is None:
            checks.append({"name": name, "expr": expr, "passed": False, "detail": "unknown verifier"})
            continue
        if not exists:
            checks.append({"name": name, "expr": expr, "passed": False, "detail": "artifact missing"})
            continue
        try:
            ok, detail = fn(text, args, ctx)
        except Exception as e:  # a verifier bug must never mark a unit passed
            ok, detail = False, f"verifier error: {e}"
        checks.append({"name": name, "expr": expr, "passed": bool(ok), "detail": detail})
    judgement = [f"{k}: {e}" for k, e in unit.verifiers() if k != "mechanical"]
    return {
        "artifact": rel_to_run(run, artifact),
        "sha256": sha256_of(artifact) if exists else None,
        "words": count_words(text) if exists else 0,
        "passed": sum(1 for c in checks if c["passed"]),
        "failed": sum(1 for c in checks if not c["passed"]),
        "checks": checks,
        "judgement_pending": judgement,
        "ran_at": now_iso(),
    }


def review_for_sha(st: dict, sha: Optional[str]) -> Optional[dict]:
    """The most recent stored review whose artifact sha256 matches `sha`."""
    if not sha:
        return None
    for r in reversed(st.get("reviews") or []):
        if r.get("sha256") == sha:
            return r
    return None


def review_state(unit: Unit, st: dict, sha: Optional[str]) -> str:
    """'-' (no judgement predicates) | 'pass' | 'fail' (a review matches the
    artifact) | 'stale' (reviews exist, none match) | 'pending' (never reviewed)."""
    if not unit.judgement():
        return "-"
    r = review_for_sha(st, sha)
    if r:
        return r["verdict"]
    return "stale" if st.get("reviews") else "pending"


def judgement_summary(unit: Unit, state: str) -> str:
    n = len(unit.judgement())
    noun = f"{n} judgement predicate{'s' if n != 1 else ''}"
    return {"pass": f"{noun} reviewed: pass", "fail": f"{noun} reviewed: FAIL",
            "stale": f"{noun}: review is stale (artifact changed) — re-review",
            "pending": f"{noun} pending review"}.get(state, "")


def current_artifact_sha(run: Run, st: dict, uid: str) -> Optional[str]:
    art = run.root / (st.get("artifact") or f"batches/{uid}.md")
    return sha256_of(art) if art.exists() else None


def rel_to_run(run: Run, p: Path) -> str:
    """Portable (forward-slash) path relative to the run dir, or the path as given."""
    try:
        return p.resolve().relative_to(run.root.resolve()).as_posix()
    except ValueError:
        return str(p)


# ---------------------------------------------------------------------------
# Templates written by `init`
# ---------------------------------------------------------------------------

def charter_template(title: str, total: str) -> str:
    return f"""# CHARTER — {title}

## Deliverable
What: {title}
Format: markdown, rendered last via the format skill
Total size: {total}

## Through-line
One sentence: what this deliverable argues or establishes. Goes verbatim into
every brief. A document written in blind pieces can be locally flawless and
collectively say nothing; this is the only defense, and the seam pass cannot
repair its absence.

## Audience
Who reads this and what they already know.

## Voice & register
Two sentences on tone, person, and formality.

## Non-negotiables
1. Each item is testable.

## Terminology lock
- wrong form -> approved form

## Sources of truth
- [S1] path/or/url — what it is

## Acceptance criteria
1. Each criterion is a predicate.

## Out of scope
- Things this deliverable does not do.
"""


SAMPLE_MARKER = "SAMPLE"

# per denomination: (unit type, numeric verifier, what the sample produces)
SAMPLE_BY_DENOM = {
    "w": ("compose", "word_count within 15% of budget", 'section: "Sample section"'),
    "slides": ("transform", "slide_count within 15% of budget", 'section: "Sample slides"'),
    "items": ("research", "item_count within 15% of budget", 'section: "Sample list"'),
    "files": ("transform", "file_exists CHARTER.md", 'section: "Sample files"'),
}


def plan_template(totals: List[Tuple[int, str]]) -> str:
    """PLAN.md scaffold with ONE real, uncommented sample unit per charter
    denomination (normally one), sized to the charter total so that the very
    first `plan --validate` passes. The unit is marked SAMPLE and must be
    replaced; the validator warns while it is still there."""
    totals = totals or [(1200, "w")]
    table, specs = [], []
    for i, (n, denom) in enumerate(totals, 1):
        utype, verifier, produces = SAMPLE_BY_DENOM.get(denom, ("transform", "no_placeholders", 'section: "Sample"'))
        uid = f"B{i:03d}"
        verify = [f"  - mechanical: {verifier}"]
        if verifier != "no_placeholders":
            verify.append("  - mechanical: no_placeholders")
        if utype == "compose":
            verify.append("  - mechanical: no_conclusion")
        table.append(f"- [ ] {uid} [{utype}] {SAMPLE_MARKER} unit — replace with your first real unit — budget: {n}{denom}")
        specs.append(f"""### {uid} — {SAMPLE_MARKER} unit — replace with your first real unit
type: {utype}
budget: {n}{denom} (±15%)
depends_on: []
inputs:
  - CHARTER.md
intent: |
  This is the scaffold's sample unit. It exists so that `bse.py plan --validate`
  passes on a fresh run. Replace it with the real first unit: one paragraph a
  stranger could act on, a real budget in the band, and the input slices it needs.
produces:
  - {produces}
verify:
{chr(10).join(verify)}
done_when: |
  The sample unit has been replaced by real units and this block is gone.
""")
    return ("# PLAN\n\n## Units\n"
            "<!-- one line per unit, in execution order; [x] is set only by `bse.py record`.\n"
            "     Format: - [ ] B002 [compose] [P] [dep:B001] Section 1 — budget: 1200w -->\n"
            + "\n".join(table) + "\n\n## Specs\n\n" + "\n".join(specs))


FRONT_MATTER_TEMPLATE = """<!-- front-matter.md — introduction / executive summary.
     Written BY HAND in the seam pass (SKILL.md move 7, step 5), only after every
     unit is done and draft.md has been read against the through-line.
     `bse.py stitch` prepends this file to draft.md once it contains prose.
     Delete this comment when you write the real front matter. -->
"""

BACK_MATTER_TEMPLATE = """<!-- back-matter.md — conclusion.
     Written BY HAND in the seam pass (SKILL.md move 7, step 5), only after every
     unit is done and draft.md has been read against the through-line.
     `bse.py stitch` appends this file to draft.md once it contains prose.
     Delete this comment when you write the real back matter. -->
"""


CARRY_TEMPLATE = """# carry.md — the baton (max 400 words; each unit REPLACES this file)

## Established facts
- (none yet)

## Interfaces/terms now defined
- (none yet)

## Open threads for later units
- (none yet)

## Do not repeat
- (none yet)

## Tone calibration note
(none yet)
"""


# ---------------------------------------------------------------------------
# Output helper
# ---------------------------------------------------------------------------

def emit(args, data: dict, text: str) -> None:
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2, sort_keys=True))
    elif text:
        print(text)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(args) -> int:
    root = Path(args.run_dir) if args.run_dir else Path.cwd() / ".bse" / args.run_id
    run = Run(root)
    if run.ledger_json.exists():
        raise BseError(f"run already exists: {root}")
    for d in (run.briefs, run.batches, run.reports):
        d.mkdir(parents=True, exist_ok=True)
    title = args.title or args.run_id
    data = {"run_id": args.run_id, "title": title, "charter": str(run.charter_path.resolve()),
            "created": now_iso(), "total": args.total, "units": {}, "events": []}
    if not run.charter_path.exists():
        atomic_write(run.charter_path, charter_template(title, args.total))
    if not run.plan_path.exists():
        atomic_write(run.plan_path, plan_template(run.charter_totals(data)))
    if not run.carry_path.exists():
        atomic_write(run.carry_path, CARRY_TEMPLATE)
    if not run.front_matter_path.exists():
        atomic_write(run.front_matter_path, FRONT_MATTER_TEMPLATE)
    if not run.back_matter_path.exists():
        atomic_write(run.back_matter_path, BACK_MATTER_TEMPLATE)
    atomic_write(run.ledger_md, run.identity_header(data) + "\n")
    run.save_ledger(data)
    emit(args, {"run_dir": str(root), "run_id": args.run_id, "charter": data["charter"]},
         f"initialised run {args.run_id} at {root}\n  edit CHARTER.md and PLAN.md (replace the SAMPLE unit), "
         f"then: bse.py plan --validate")
    return 0


def cmd_plan(args) -> int:
    run = resolve_run(args)
    ledger = run.load_ledger()
    if not run.plan_path.exists():
        raise BseError(f"no PLAN.md in {run.root}")
    units, perrs = parse_plan(read_text(run.plan_path))
    if not args.validate:
        rows = [f"{u.id:<6} [{u.type}]{' [P]' if u.parallel else ''} deps={','.join(u.depends_on) or '-'} "
                f"budget={f'{u.budget[0]}{u.budget[1]}' if u.budget else '?'} {u.title}" for u in units]
        emit(args, {"units": [u.id for u in units], "parse_errors": perrs}, "\n".join(rows + perrs))
        return 1 if perrs else 0
    errors, warnings, waivers = validate_plan(run, units, perrs, ledger)
    totals = run.charter_totals(ledger)
    total = run.charter_total(ledger)
    drift = budget_drift(units, totals)
    if not errors:                       # `next` refuses to run on a never-validated plan
        ledger["plan_validated"] = {"ts": now_iso(), "units": [u.id for u in units]}
        run.save_ledger(ledger)
    data = {"ok": not errors, "errors": errors, "warnings": warnings, "waivers": waivers, "units": len(units),
            "budget_sum": sum(u.budget[0] for u in units if u.budget and total and u.budget[1] == total[1]),
            "charter_total": f"{total[0]}{total[1]}" if total else None,
            "charter_totals": [f"{n}{d}" for n, d in totals],
            "budget_sums": {d["unit"]: d["sum"] for d in drift},
            "budget_drift": drift}
    if not re.search(r"^#{1,3}\s*Through-?line\b", run.charter_text(), re.IGNORECASE | re.MULTILINE):
        warnings.append("CHARTER.md has no `## Through-line` section — every brief carries it, and a "
                        "missing through-line is the one failure the seam pass cannot repair")
    lines = [f"PLAN {'VALID' if not errors else 'INVALID'}: {len(units)} units"]
    lines += [f"  error: {e}" for e in errors] + [f"  warning: {w}" for w in warnings]
    lines += [f"  waiver: {w['unit']} {w['rule']} — {w['reason']}" for w in waivers]
    emit(args, data, "\n".join(lines))
    return 0 if not errors else 1


def unit_status(ledger: dict, uid: str) -> str:
    return ledger["units"].get(uid, {}).get("status", "pending")


def cmd_status(args) -> int:
    run = resolve_run(args)
    ledger = run.load_ledger()
    units = load_units(run)
    rows, data = [], []
    done = awaiting = 0
    for u in units:
        st = ledger["units"].get(u.id, {})
        status = st.get("status", "pending")
        done += status == "done"
        budget = f"{u.budget[0]}{u.budget[1]}" if u.budget else "?"
        words = st.get("words")
        sha = current_artifact_sha(run, st, u.id)
        review = review_state(u, st, sha)
        awaiting += sha is not None and review in ("pending", "stale") and status != "done"
        rows.append(f"{u.id:<6} {u.type:<10} {status:<8} {st.get('attempts', 0):>3}   {budget:<9} "
                    f"{words if words is not None else '-':>6}  {review:<8} {u.title}")
        data.append({"id": u.id, "type": u.type, "status": status, "attempts": st.get("attempts", 0),
                     "budget": budget, "words": words, "review": review, "title": u.title,
                     "parallel": u.parallel, "depends_on": u.depends_on})
    header = run.identity_header(ledger)
    table = f"{'id':<6} {'type':<10} {'status':<8} att   {'budget':<9} {'words':>6}  {'review':<8} title"
    foot = [f"{done} of {len(units)} units done"]
    if awaiting:
        foot.append(f"{awaiting} unit(s) awaiting review (review column: pending/stale)")
    if not units:
        foot = ["PLAN EMPTY: PLAN.md declares no units"]
    if not ledger.get("plan_validated"):
        foot.append("PLAN NOT VALIDATED: run `bse.py plan --validate`")
    emit(args, {"run_id": ledger["run_id"], "done": done, "total": len(units), "awaiting_review": awaiting,
                "plan_empty": not units, "plan_validated": bool(ledger.get("plan_validated")), "units": data},
         "\n".join([header, table] + rows + foot))
    return 0


def unblocked_units(units: List[Unit], ledger: dict) -> List[Unit]:
    """Units not done/blocked whose dependencies are all done, in plan order."""
    out = []
    for u in units:
        status = unit_status(ledger, u.id)
        if status in ("done", "blocked"):
            continue
        if all(unit_status(ledger, d) == "done" for d in u.depends_on):
            out.append(u)
    return out


def cmd_next(args) -> int:
    run = resolve_run(args)
    ledger = run.load_ledger()
    units = load_units(run)
    if not units:
        raise BseError("PLAN EMPTY: PLAN.md declares no units — add units, then `bse.py plan --validate`")
    if not ledger.get("plan_validated"):
        raise BseError("PLAN NOT VALIDATED: run `bse.py plan --validate` before executing (the plan gate)")
    remaining = [u for u in units if unit_status(ledger, u.id) != "done"]
    ready = unblocked_units(units, ledger)
    if args.all:
        emit(args, {"units": [u.id for u in ready], "remaining": len(remaining)},
             "\n".join(f"{u.id}{' [P]' if u.parallel else ''}" for u in ready))
        return 0
    nxt = ready[0] if ready else None
    if nxt is None and remaining and not args.json:
        blocked = [u.id for u in remaining if unit_status(ledger, u.id) == "blocked"]
        print(f"no unblocked unit; {len(remaining)} remaining" +
              (f" (blocked: {', '.join(blocked)})" if blocked else ""), file=sys.stderr)
    emit(args, {"unit": nxt.id if nxt else None, "remaining": len(remaining)}, nxt.id if nxt else "")
    return 0


def _read_slice(path: Path, spec: str) -> str:
    """spec like '#L40-120' or '#L40' selects lines; empty = whole file."""
    text = read_text(path)
    m = re.match(r"^#?L(\d+)(?:-L?(\d+))?$", spec.strip()) if spec else None
    if not m:
        return text
    lines = text.splitlines()
    a = int(m.group(1))
    b = int(m.group(2)) if m.group(2) else a
    return "\n".join(lines[a - 1:b]) + "\n"


def cmd_brief(args) -> int:
    run = resolve_run(args)
    units = load_units(run)
    unit = next((u for u in units if u.id == args.id), None)
    if unit is None:
        raise BseError(f"unknown unit {args.id}", 2)
    ledger = run.load_ledger()
    parts = [f"# Brief — {unit.id} — {unit.title}",
             f"<!-- generated by bse.py for run {ledger['run_id']}; do not edit. "
             f"Write your output to batches/{unit.id}.md. -->", "",
             "## Charter", "", run.charter_text().strip(), "",
             "## Unit spec", "", unit.spec_text.strip(), "",
             "## Carry (the baton)", "", run.carry_text().strip(), ""]
    missing = []
    inputs = [i for i in unit.list_field("inputs") if i.strip().lower() not in ("charter.md", "./charter.md")]
    if inputs:
        parts += ["## Inputs", ""]
    for inp in inputs:
        raw = inp.strip().strip("\"'")
        path_part, _, slice_part = raw.partition("#")
        p = _resolve_path({"run": run}, path_part)
        if not p.exists():
            missing.append(raw)
            parts += [f"### {raw}", "", f"<!-- INPUT NOT FOUND: {raw} -->", ""]
            continue
        parts += [f"### {raw}", "", _read_slice(p, "#" + slice_part if slice_part else "").rstrip(), ""]
    out = Path(args.out) if args.out else run.briefs / f"{unit.id}.md"
    atomic_write(out, "\n".join(parts).rstrip() + "\n")
    emit(args, {"unit": unit.id, "brief": str(out), "words": count_words("\n".join(parts)), "missing_inputs": missing},
         f"brief written: {out} ({count_words(' '.join(parts))} words)" +
         ("\n  MISSING INPUTS: " + ", ".join(missing) if missing else ""))
    return 1 if missing else 0


def cmd_check(args) -> int:
    run = resolve_run(args)
    units = load_units(run)
    unit = next((u for u in units if u.id == args.id), None)
    if unit is None:
        raise BseError(f"unknown unit {args.id}", 2)
    ledger = run.load_ledger()
    artifact = Path(args.artifact) if args.artifact else run.batches / f"{unit.id}.md"
    if not artifact.is_absolute() and not artifact.exists() and (run.root / artifact).exists():
        artifact = run.root / artifact
    rec = run_checks(run, unit, artifact)
    st = run.unit_state(ledger, unit.id)
    ts = now_iso()
    # --- fix-round accounting (I2): re-running check on a CHANGED artifact after
    # a FAILING check is a fix round, whether or not `record --status fix` said so.
    # An explicit `record --status fix` answering that same failing sha has already
    # counted it (st["fix_recorded_for"]), so it is not counted twice.
    prev = st.get("verify")
    auto_round = None
    changed_after_fail = bool(prev and prev.get("failed", 0) > 0 and prev.get("sha256") and rec["sha256"]
                              and prev["sha256"] != rec["sha256"])
    if changed_after_fail and st.get("fix_recorded_for") == prev["sha256"]:
        st["fix_recorded_for"] = None          # the explicit round covered this transition: consume it
    elif changed_after_fail:
        if st.get("fix_rounds", 0) >= MAX_FIX_ROUNDS and not args.force:
            raise BseError(f"{unit.id} already had {MAX_FIX_ROUNDS} fix rounds: split the unit or record --status blocked "
                           f"(or check --force, stamped FORCED)")
        st["fix_rounds"] = st.get("fix_rounds", 0) + 1
        st["attempts"] = 1 + st["fix_rounds"]
        auto_round = st["fix_rounds"]
        forced = "  FORCED" if st["fix_rounds"] > MAX_FIX_ROUNDS else ""
        failing = "; ".join(c["detail"] for c in prev["checks"] if not c["passed"])
        run.append_event(ledger, f"{unit.id} fix {auto_round}/{MAX_FIX_ROUNDS}  {ts}  "
                         f"verify=fail({prev['failed']}/{prev['passed'] + prev['failed']}): {failing}  "
                         f"auto=check (artifact changed after a failing check){forced}",
                         unit=unit.id, kind="fix", round=auto_round, note=None, auto=True, forced=bool(forced))
    st["verify"] = rec
    st["updated"] = ts
    run.save_ledger(ledger)
    ok = rec["failed"] == 0 and rec["passed"] > 0
    rstate = review_state(unit, st, rec["sha256"])
    n_mech = rec["passed"] + rec["failed"]
    halves = f"{rec['passed']}/{n_mech} mechanical"
    if unit.judgement():
        halves += "; " + judgement_summary(unit, rstate)
    lines = [f"# Verification report — {unit.id} — {unit.title}", "",
             f"- artifact: {rec['artifact']}", f"- sha256: {rec['sha256']}", f"- words: {rec['words']}",
             f"- ran: {rec['ran_at']}", f"- result: {'PASS' if ok else 'FAIL'} ({halves})", ""]
    if auto_round:
        lines += [f"- fix round {auto_round}/{MAX_FIX_ROUNDS} counted: artifact changed after a failing check", ""]
    lines += ["## Mechanical checks", ""]
    lines += [f"- [{'x' if c['passed'] else ' '}] {c['expr']} — {c['detail']}" for c in rec["checks"]]
    if rec["judgement_pending"]:
        lines += ["", f"## Judgement predicates (reviewer pass required; not counted above) — {rstate}", ""]
        lines += [f"- [{'x' if rstate == 'pass' else ' '}] {j}" for j in rec["judgement_pending"]]
        lines += ["", f"Record the verdict with: bse.py review {unit.id} --verdict pass|fail --report <path>"]
    run.reports.mkdir(parents=True, exist_ok=True)
    atomic_write(run.reports / f"{unit.id}.md", "\n".join(lines) + "\n")
    summary = f"{unit.id} check {'PASS' if ok else 'FAIL'} ({halves})"
    out_lines = [summary]
    if auto_round:
        out_lines.append(f"  fix round {auto_round}/{MAX_FIX_ROUNDS} counted (artifact changed after a failing check)")
    out_lines += [f"  {'ok  ' if c['passed'] else 'FAIL'} {c['expr']}: {c['detail']}" for c in rec["checks"]]
    out_lines.append(f"  report: {run.reports / (unit.id + '.md')}")
    emit(args, {"unit": unit.id, "ok": ok, "review": rstate, "judgement": unit.judgement(),
                "fix_round": auto_round, "fix_rounds": st.get("fix_rounds", 0), **rec}, "\n".join(out_lines))
    return 0 if ok else 1


def cmd_review(args) -> int:
    """Store a reviewer's verdict on the unit's judgement predicates, keyed to
    the artifact's sha256 so a later edit invalidates it exactly as it
    invalidates `check`. Exit 0 on a pass verdict, 1 on fail (like `check`)."""
    run = resolve_run(args)
    units = load_units(run)
    unit = next((u for u in units if u.id == args.id), None)
    if unit is None:
        raise BseError(f"unknown unit {args.id}", 2)
    judgement = unit.judgement()
    if not judgement:
        raise BseError(f"{unit.id} declares no judgement predicates (source:/charter:) — nothing to review; "
                       f"`bse.py check {unit.id}` is its only gate", 2)
    if args.verdict not in REVIEW_VERDICTS:
        raise BseError(f"--verdict must be one of {', '.join(REVIEW_VERDICTS)}", 2)
    report = Path(args.report)
    if not report.is_absolute() and not report.exists() and (run.root / report).exists():
        report = run.root / report
    if not report.exists() or report.stat().st_size == 0:
        raise BseError(f"--report must name the reviewer's written report (missing or empty): {report}", 2)
    ledger = run.load_ledger()
    artifact = Path(args.artifact) if args.artifact else run.batches / f"{unit.id}.md"
    if not artifact.is_absolute() and not artifact.exists() and (run.root / artifact).exists():
        artifact = run.root / artifact
    if not artifact.exists() or artifact.stat().st_size == 0:
        raise BseError(f"cannot review: artifact missing or empty: {artifact}")
    sha = sha256_of(artifact)
    st = run.unit_state(ledger, unit.id)
    ts = now_iso()
    rec = {"verdict": args.verdict, "sha256": sha, "artifact": rel_to_run(run, artifact),
           "report": rel_to_run(run, report), "predicates": judgement, "note": args.note, "ts": ts}
    st["reviews"].append(rec)
    st["updated"] = ts
    note = f"  note={args.note}" if args.note else ""
    run.append_event(ledger, f"{unit.id} review {args.verdict}  {ts}  predicates={len(judgement)}  "
                     f"report={rec['report']}  sha={sha[:7]}{note}",
                     unit=unit.id, kind="review", verdict=args.verdict, sha256=sha, report=rec["report"], note=args.note)
    emit(args, {"unit": unit.id, "verdict": args.verdict, "sha256": sha, "report": rec["report"],
                "predicates": judgement},
         f"{unit.id} review {args.verdict.upper()} ({len(judgement)} judgement predicate"
         f"{'s' if len(judgement) != 1 else ''}, sha={sha[:7]})" +
         ("" if args.verdict == "pass" else f"\n  fix the artifact, re-run `bse.py check {unit.id}`, then re-review"))
    return 0 if args.verdict == "pass" else 1


def cmd_record(args) -> int:
    run = resolve_run(args)
    ledger = run.load_ledger()
    if args.id.upper() == "RULING":
        if not args.note:
            raise BseError("RULING needs --note", 2)
        ruled_unit = getattr(args, "unit", None)
        if ruled_unit and ruled_unit not in {u.id for u in load_units(run)}:
            raise BseError(f"unknown unit {ruled_unit}", 2)
        tag = f"unit={ruled_unit}  " if ruled_unit else ""
        run.append_event(ledger, f"RULING        {now_iso()}  {tag}{args.note}",
                         kind="ruling", unit=ruled_unit, note=args.note)
        emit(args, {"recorded": "RULING", "unit": ruled_unit},
             "RULING recorded" + (f" for {ruled_unit}" if ruled_unit else ""))
        return 0
    if getattr(args, "unit", None):
        raise BseError("--unit is only valid with `record RULING`", 2)
    units = load_units(run)
    unit = next((u for u in units if u.id == args.id), None)
    if unit is None:
        raise BseError(f"unknown unit {args.id}", 2)
    st = run.unit_state(ledger, unit.id)
    ts = now_iso()
    status = args.status
    if status == "blocked":
        if not args.note:
            raise BseError("--status blocked requires --note <reason>", 2)
        run.set_status(st, "blocked", ts, args.note)
        run.append_event(ledger, f"{unit.id} blocked  {ts}  reason={args.note}",
                         unit=unit.id, kind="blocked", note=args.note)
        emit(args, {"unit": unit.id, "status": "blocked"}, f"{unit.id} blocked: {args.note}")
        return 0
    if status == "fix":
        if st.get("fix_rounds", 0) >= MAX_FIX_ROUNDS and not args.force:
            raise BseError(f"{unit.id} already had {MAX_FIX_ROUNDS} fix rounds: split the unit or record --status blocked (or --force)")
        st["fix_rounds"] = st.get("fix_rounds", 0) + 1
        st["attempts"] = 1 + st["fix_rounds"]
        run.set_status(st, "fix", ts, args.note)
        v = st.get("verify")
        # this explicit round answers the currently stored failing check, so a
        # later `check` on the repaired artifact must not count it again
        st["fix_recorded_for"] = v.get("sha256") if v and v.get("failed", 0) > 0 else None
        vtxt = (f"verify=fail({v['failed']}/{v['passed'] + v['failed']}): " +
                "; ".join(c["detail"] for c in v["checks"] if not c["passed"])) if v else "verify=none"
        note = f"  note={args.note}" if args.note else ""
        run.append_event(ledger, f"{unit.id} fix {st['fix_rounds']}/{MAX_FIX_ROUNDS}  {ts}  {vtxt}{note}",
                         unit=unit.id, kind="fix", round=st["fix_rounds"], note=args.note)
        emit(args, {"unit": unit.id, "status": "fix", "round": st["fix_rounds"]},
             f"{unit.id} fix round {st['fix_rounds']}/{MAX_FIX_ROUNDS} recorded")
        return 0
    # status == done
    artifact = Path(args.artifact) if args.artifact else run.batches / f"{unit.id}.md"
    if not artifact.is_absolute() and not artifact.exists() and (run.root / artifact).exists():
        artifact = run.root / artifact
    if not artifact.exists() or artifact.stat().st_size == 0:
        raise BseError(f"cannot record done: artifact missing or empty: {artifact}")
    sha = sha256_of(artifact)
    v = st.get("verify")
    problems = []
    if v is None:
        problems.append("no check has been run for this unit (run `bse.py check`)")
    else:
        if v["failed"] > 0:
            problems.append(f"stored check shows {v['failed']} failing predicate(s): " +
                            "; ".join(c["detail"] for c in v["checks"] if not c["passed"]))
        if v["passed"] == 0:
            problems.append("stored check has zero passing predicates")
        if v.get("sha256") != sha:
            problems.append("artifact changed since last check (sha mismatch) — re-run `bse.py check`")
    # judgement gate (C1): declared source:/charter: predicates need a stored
    # passing review whose sha matches the artifact as it is NOW
    judgement = unit.judgement()
    review = review_for_sha(st, sha) if judgement else None
    if judgement:
        if review is None:
            how = "no review recorded" if not st.get("reviews") else "stored review(s) are for an earlier artifact (sha mismatch)"
            problems.append(f"declares {len(judgement)} judgement predicate(s) but {how} — run the reviewer pass, then "
                            f"`bse.py review {unit.id} --verdict pass --report <path>`")
        elif review["verdict"] != "pass":
            problems.append(f"latest review of this artifact is a FAIL ({review.get('report')}) — fix, re-check, re-review")
    if problems and not args.force:
        raise BseError(f"REFUSED: {unit.id} cannot be recorded done:\n  " + "\n  ".join(problems) +
                       "\n  (use --force to override; the ledger line will be stamped FORCED)")
    words = count_words(read_text(artifact))
    rel = rel_to_run(run, artifact)
    st.update({"artifact": rel, "sha256": sha, "words": words,
               "attempts": max(1, 1 + st.get("fix_rounds", 0))})
    run.set_status(st, "done", ts, args.note)
    if args.carry:
        set_carry(run, Path(args.carry))
    mech_ok = v is not None and v["failed"] == 0 and v["passed"] > 0 and v.get("sha256") == sha
    vtxt = f"verify=pass({v['passed']}/{v['passed'] + v['failed']})" if mech_ok else \
        (f"verify=fail({v['failed']}/{v['passed'] + v['failed']})" if v else "verify=none")
    rtxt = ""
    if judgement:
        rtxt = "review=" + (review["verdict"] if review else "none")
    forced = "  FORCED" if args.force and problems else ""
    note = f"  note={args.note}" if args.note else ""
    line = (f"{unit.id} done     {ts}  artifact={rel}  words={words}  {vtxt}  "
            + (rtxt + "  " if rtxt else "") + f"sha={sha[:7]}{forced}{note}")
    run.append_event(ledger, line, unit=unit.id, kind="done", forced=bool(forced), note=args.note,
                     review=(review["verdict"] if review else None) if judgement else None)
    mark_done_in_plan(run, unit.id)
    done = sum(1 for u in units if unit_status(ledger, u.id) == "done")
    emit(args, {"unit": unit.id, "status": "done", "words": words, "sha256": sha, "forced": bool(forced),
                "review": (review["verdict"] if review else None) if judgement else None,
                "done": done, "total": len(units)},
         f"{unit.id} done ({words:,}w, {vtxt}{', ' + rtxt if rtxt else ''}){forced} — {done} of {len(units)} units")
    return 0


def set_carry(run: Run, src: Path) -> Tuple[int, List[str]]:
    if not src.exists():
        raise BseError(f"carry file not found: {src}", 2)
    text = read_text(src)
    n = count_words(text)
    if n > CARRY_WORD_CAP:
        raise BseError(f"REFUSED: carry.md would be {n} words; hard cap is {CARRY_WORD_CAP}")
    secs = sections_of(text)
    missing = [s for s in CARRY_SECTIONS if find_section(secs, s) is None]
    atomic_write(run.carry_path, text if text.endswith("\n") else text + "\n")
    return n, missing


def stale_carry_state(run: Run, ledger: dict, units: List[Unit]) -> Tuple[bool, int]:
    """(stale, done_count): stale when >= 2 units are done and carry.md is still
    the `init` scaffold or empty — the classic silent failure (SKILL.md move 6)."""
    done = sum(1 for u in units if unit_status(ledger, u.id) == "done")
    return (done >= 2 and run.carry_is_stale()), done


def cmd_carry(args) -> int:
    run = resolve_run(args)
    if args.check:
        ledger = run.load_ledger()
        units = load_units(run)
        stale, done = stale_carry_state(run, ledger, units)
        scaffold = run.carry_is_stale()
        msg = (f"CARRY STALE: {done} units done but carry.md is still the init scaffold or empty — "
               f"write the baton (references/prompts.md carry-update prompt) before the next record" if stale else
               f"carry.md ok ({count_words(run.carry_text())} words; {done} units done"
               + ("; still the init scaffold — fine until the second unit is done" if scaffold else "") + ")")
        emit(args, {"stale": stale, "scaffold": scaffold, "done": done, "words": count_words(run.carry_text())}, msg)
        return 1 if stale else 0
    if args.set:
        n, missing = set_carry(run, Path(args.set))
        emit(args, {"words": n, "missing_sections": missing},
             f"carry.md replaced ({n}/{CARRY_WORD_CAP} words)" +
             (f"\n  warning: missing sections: {', '.join(missing)}" if missing else ""))
        return 0
    text = run.carry_text()
    emit(args, {"words": count_words(text), "text": text}, text.rstrip())
    return 0


def _normalize_sentence(s: str) -> str:
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def sentences_of(text: str) -> List[str]:
    """Split prose into sentences. Paragraph breaks, headings and list items are
    hard boundaries; inside a chunk we split after . ! ? followed by space."""
    chunks: List[str] = []
    cur: List[str] = []
    for _, line in prose_lines(text):
        s = line.strip()
        is_block = bool(re.match(r"^(?:#{1,6}\s+|[-*]\s+|\d+[.)]\s+|>\s*|\|)", s))
        if not s or is_block:
            if cur:
                chunks.append(" ".join(cur))
                cur = []
            if is_block:
                chunks.append(re.sub(r"^(?:#{1,6}\s+|[-*]\s+|\d+[.)]\s+|>\s*)", "", s))
            continue
        cur.append(s)
    if cur:
        chunks.append(" ".join(cur))
    out: List[str] = []
    for c in chunks:
        c = re.sub(r"[*_`]", "", c)
        out += [x.strip() for x in re.split(r"(?<=[.!?])\s+", c) if x.strip()]
    return out


def duplicate_report(texts: Dict[str, str]) -> List[dict]:
    """Sentences of >= DUP_MIN_WORDS words (normalized) appearing in 2+ units."""
    seen: Dict[str, dict] = {}
    for uid, text in texts.items():
        for s in sentences_of(text):
            norm = _normalize_sentence(s)
            if len(norm.split()) < DUP_MIN_WORDS:
                continue
            h = hashlib.sha1(norm.encode("utf-8")).hexdigest()
            e = seen.setdefault(h, {"sentence": s, "units": []})
            if uid not in e["units"]:
                e["units"].append(uid)
    return [e for e in seen.values() if len(e["units"]) >= 2]


def cmd_stitch(args) -> int:
    run = resolve_run(args)
    ledger = run.load_ledger()
    units = load_units(run)
    incomplete = [u for u in units if unit_status(ledger, u.id) != "done"
                  or not (run.root / (ledger["units"][u.id].get("artifact") or f"batches/{u.id}.md")).exists()]
    if incomplete and not args.partial:
        raise BseError("REFUSED: incomplete units: " + ", ".join(u.id for u in incomplete)
                       + " (every unit, [P] or not, must be done; use --partial to stitch with <!-- MISSING --> markers)")
    out = Path(args.out) if args.out else run.draft_path
    if out.name.lower() == "final.md":
        raise BseError("REFUSED: stitch writes draft.md (machine output); final.md is written by hand in the seam "
                       "pass and never generated by stitch", 2)
    if getattr(args, "include_front_matter", False):
        print("note: --include-front-matter is deprecated and a no-op — front-matter.md/back-matter.md are "
              "included by default when they contain prose (use --no-front-matter to suppress)", file=sys.stderr)
    with_matter = not args.no_front_matter
    fm_text = run.matter_text(run.front_matter_path) if with_matter else None
    bm_text = run.matter_text(run.back_matter_path) if with_matter else None
    texts: Dict[str, str] = {}
    pieces: List[str] = []
    per_unit: List[dict] = []
    if with_matter:
        pieces.append(fm_text.rstrip() if fm_text else
                      "<!-- FRONT MATTER: front-matter.md not yet written — the seam pass writes it LAST -->")
    for u in units:
        st = ledger["units"].get(u.id, {})
        art = run.root / (st.get("artifact") or f"batches/{u.id}.md")
        if st.get("status") != "done" or not art.exists():
            pieces.append(f"<!-- MISSING {u.id} -->")
            per_unit.append({"id": u.id, "words": 0, "budget": u.budget[0] if u.budget else None, "missing": True})
            continue
        t = read_text(art)
        texts[u.id] = t
        pieces.append(f"<!-- BSE {u.id} — {u.title} -->\n" + t.rstrip())
        per_unit.append({"id": u.id, "words": count_words(t), "budget": u.budget[0] if u.budget else None, "missing": False})
    if with_matter:
        pieces.append(bm_text.rstrip() if bm_text else
                      "<!-- BACK MATTER: back-matter.md not yet written — the seam pass writes it LAST -->")
    atomic_write(out, "\n\n".join(pieces) + "\n")
    # --- report -----------------------------------------------------------
    total_words = sum(p["words"] for p in per_unit)
    target = run.charter_total(ledger)
    dups = duplicate_report(texts)
    lock = run.terminology_lock()
    term_viol = []
    for uid, t in texts.items():
        for ln, line in prose_lines(t):
            for wrong, right in lock:
                if re.search(r"(?<!\w)" + re.escape(wrong.lower()) + r"(?!\w)", line.lower()):
                    term_viol.append({"unit": uid, "line": ln, "wrong": wrong, "approved": right})
    seams = []
    done_ids = [u.id for u in units if u.id in texts]
    for a, b in zip(done_ids, done_ids[1:]):
        wa, wb = texts[a].split(), texts[b].split()
        seams.append({"from": a, "to": b, "last": " ".join(wa[-SEAM_WORDS:]), "first": " ".join(wb[:SEAM_WORDS])})
    rep = [f"# Stitch report — {ledger['run_id']} — {now_iso()}", "", "## Per-unit word counts", ""]
    rep += [f"- {p['id']}: {'MISSING' if p['missing'] else p['words']} (budget {p['budget']})" for p in per_unit]
    missing_ids = [p["id"] for p in per_unit if p["missing"]]
    if missing_ids:
        rep += ["", f"## Missing units ({len(missing_ids)}) — PARTIAL stitch, draft.md is not complete", ""]
        rep += [f"- {u.id}: status={unit_status(ledger, u.id)}{' [P]' if u.parallel else ''} — <!-- MISSING {u.id} --> inserted"
                for u in units if u.id in missing_ids]
    if target:
        drift = abs(total_words - target[0]) * 100.0 / target[0] if target[0] else 0
        rep += ["", f"## Total: {total_words} words vs charter target {target[0]}{target[1]} (drift {drift:.0f}%)"]
    else:
        drift = None
        rep += ["", f"## Total: {total_words} words (charter target unknown)"]
    rep += ["", "## Seam-pass files", "",
            f"- front-matter.md: {'included' if fm_text else ('suppressed (--no-front-matter)' if not with_matter else 'not yet written')}",
            f"- back-matter.md: {'included' if bm_text else ('suppressed (--no-front-matter)' if not with_matter else 'not yet written')}",
            "- final.md: written by hand in the seam pass; never generated by stitch"]
    rep += ["", f"## Duplicate content ({len(dups)} sentences of >= {DUP_MIN_WORDS} words in 2+ units)", ""]
    rep += [f"- [{', '.join(d['units'])}] {d['sentence']}" for d in dups] or ["- none"]
    rep += ["", f"## Terminology violations ({len(term_viol)})", ""]
    rep += [f"- {v['unit']} L{v['line']}: '{v['wrong']}' -> use '{v['approved']}'" for v in term_viol] or ["- none"]
    rep += ["", "## Seams (inspect each boundary)", ""]
    for s in seams:
        rep += [f"### {s['from']} -> {s['to']}", f"- last: ...{s['last']}", f"- first: {s['first']}...", ""]
    run.reports.mkdir(parents=True, exist_ok=True)
    atomic_write(run.reports / "stitch.md", "\n".join(rep).rstrip() + "\n")
    span = f"{units[0].id}-{units[-1].id}" if units else "-"
    run.append_event(ledger, f"SEAM  {span} {now_iso()}  dedup={len(dups)} found; terminology drift={len(term_viol)}"
                     + (f"; PARTIAL missing={len(missing_ids)} ({', '.join(missing_ids)})" if missing_ids else ""),
                     kind="seam", dedup=len(dups), terminology=len(term_viol), missing=missing_ids,
                     partial=bool(missing_ids))
    # budget gate (M8): a complete stitch outside the ±20% band is a failure
    # unless --allow-drift; partial stitches are under budget by construction
    drift_exceeded = bool(target) and not missing_ids and drift is not None and drift > BUDGET_DRIFT_PCT
    seam_missing = with_matter and not missing_ids and (fm_text is None or bm_text is None)
    data = {"draft": str(out), "report": str(run.reports / "stitch.md"), "words": total_words,
            "target": f"{target[0]}{target[1]}" if target else None, "drift_pct": drift,
            "drift_exceeded": drift_exceeded, "front_matter": bool(fm_text), "back_matter": bool(bm_text),
            "seam_pass_pending": seam_missing,
            "duplicates": dups, "terminology_violations": term_viol, "seams": seams,
            "missing": missing_ids, "partial": bool(missing_ids)}
    warnings = []
    if missing_ids:
        warnings.append(f"WARNING: PARTIAL stitch — {len(missing_ids)} unit(s) missing: {', '.join(missing_ids)}"
                        f" (<!-- MISSING --> markers inserted; draft.md is not the final deliverable)")
    if drift_exceeded:
        warnings.append(f"WARNING: BUDGET DRIFT — {total_words} words is {drift:.0f}% off the charter target "
                        f"{target[0]}{target[1]} (band ±{BUDGET_DRIFT_PCT}%); the deliverable is the wrong size. "
                        + ("continuing because --allow-drift was given" if args.allow_drift else
                           "re-plan or pass --allow-drift to accept it (exit 1)"))
    if seam_missing:
        absent = [n for n, t in (("front-matter.md", fm_text), ("back-matter.md", bm_text)) if t is None]
        warnings.append(f"reminder: every unit is done but the seam pass has not run — {' and '.join(absent)} "
                        f"contain no prose yet; write them (and final.md) by hand after reading draft.md")
    emit(args, data, f"stitched {len(texts)} units -> {out} ({total_words} words"
         + (f", target {target[0]}{target[1]}, drift {drift:.0f}%" if target else "") + ")\n"
         f"  duplicates={len(dups)} terminology_violations={len(term_viol)} missing={len(missing_ids)}"
         f" front_matter={'yes' if fm_text else 'no'} back_matter={'yes' if bm_text else 'no'}\n"
         f"  report: {run.reports / 'stitch.md'}")
    for w in warnings:                           # stderr, so --json consumers and humans both see it
        print(w, file=sys.stderr)
    return 1 if drift_exceeded and not args.allow_drift else 0


def cmd_audit(args) -> int:
    run = resolve_run(args)
    ledger = run.load_ledger()
    units = load_units(run)
    findings: List[dict] = []

    def add(code: str, uid: Optional[str], msg: str, level: str = "error") -> None:
        findings.append({"code": code, "unit": uid, "message": msg, "level": level})

    ids = {u.id for u in units}
    if run.ledger_md.exists():
        first = read_text(run.ledger_md).splitlines()[0] if read_text(run.ledger_md).strip() else ""
        if first != run.identity_header(ledger):
            add("LEDGER_HEADER_MISMATCH", None, "LEDGER.md identity header does not match ledger.json")
    else:
        add("LEDGER_MD_MISSING", None, "LEDGER.md missing")
    for u in units:
        st = ledger["units"].get(u.id)
        if st is None:
            if u.done_in_plan:
                add("PHANTOM_COMPLETE", u.id, "marked [x] in PLAN.md but has no ledger record")
            continue
        if st.get("status") == "done":
            art = run.root / (st.get("artifact") or f"batches/{u.id}.md")
            if not art.exists():
                add("ARTIFACT_MISSING", u.id, f"done but artifact missing: {art}")
            elif art.stat().st_size == 0:
                add("ARTIFACT_EMPTY", u.id, f"done but artifact empty: {art}")
            elif st.get("sha256") and sha256_of(art) != st["sha256"]:
                add("HASH_MISMATCH", u.id, "artifact changed since it was recorded done")
            v = st.get("verify")
            if v is None:
                add("DONE_WITHOUT_VERIFY", u.id, "done with no stored verification record")
            elif v.get("failed", 0) > 0:
                add("DONE_WITH_FAILING_VERIFY", u.id, f"done but stored verify has {v['failed']} failure(s)")
            if u.judgement():
                r = review_for_sha(st, st.get("sha256"))
                if r is None:
                    add("DONE_WITHOUT_REVIEW", u.id, f"done with {len(u.judgement())} judgement predicate(s) but no "
                        f"review stored for the recorded artifact (run `bse.py review {u.id} ...`)")
                elif r.get("verdict") != "pass":
                    add("DONE_WITH_FAILING_REVIEW", u.id, f"done but the stored review of this artifact is a FAIL ({r.get('report')})")
            if not u.done_in_plan:
                add("PLAN_NOT_MARKED", u.id, "ledger says done but PLAN.md line is still [ ]")
            if u.budget and u.budget[1] == "w" and st.get("words") is not None and u.budget[0]:
                d = abs(st["words"] - u.budget[0]) * 100.0 / u.budget[0]
                if d > BUDGET_DRIFT_PCT:
                    add("BUDGET_DRIFT", u.id, f"{st['words']} words vs budget {u.budget[0]} ({d:.0f}%)")
        elif u.done_in_plan:
            add("PHANTOM_COMPLETE", u.id, f"marked [x] in PLAN.md but ledger status is {st.get('status')}")
    for uid in ledger["units"]:
        if uid not in ids:
            add("UNKNOWN_UNIT", uid, "ledger entry for a unit not in PLAN.md")
    for ev in ledger["events"]:
        if ev.get("unit") and ev["unit"] not in ids:
            add("UNKNOWN_UNIT_EVENT", ev["unit"], f"ledger event for unknown unit: {ev.get('line', '')[:60]}")
    # a unit that was blocked and later moved on should have a RULING in between
    # (unit-linked via --unit, or unit-less) — informational, not a failure
    for u in units:
        for b in blocks_without_ruling(ledger, u.id):
            add("BLOCK_WITHOUT_RULING", u.id,
                f"blocked at {b['blocked']} (reason={b['reason']}) then '{b['resolved_to']}' at {b['resolved']} "
                f"with no RULING recorded in between", level="info")
    cw = count_words(run.carry_text())
    if cw > CARRY_WORD_CAP:
        add("CARRY_OVER_CAP", None, f"carry.md is {cw} words (cap {CARRY_WORD_CAP})")
    stale, done_count = stale_carry_state(run, ledger, units)
    if stale:
        add("CARRY_STALE", None, f"{done_count} units done but carry.md is still the init scaffold or empty — "
            "the baton was never written (SKILL.md move 6)")
    # seam pass (C2/C3): final.md is the deliverable and is written by hand
    all_done = bool(units) and done_count == len(units)
    if not run.final_path.exists():
        if all_done:
            add("SEAM_PASS_MISSING", None, "every unit is done but final.md does not exist — run the seam pass "
                "(read draft.md, write front-matter.md, back-matter.md and final.md by hand)")
        elif run.draft_path.exists():
            add("SEAM_PASS_MISSING", None, f"draft.md exists but final.md does not ({done_count}/{len(units)} units done; "
                "the seam pass runs once every unit is done)", level="info")
    elif run.draft_path.exists() and run.final_path.stat().st_mtime < run.draft_path.stat().st_mtime:
        add("FINAL_STALE", None, "final.md is older than draft.md — draft.md was re-stitched after the seam pass; "
            "redo the seam pass on the new draft", level="error" if all_done else "info")
    if all_done and run.final_path.exists():
        for name, path in (("front-matter.md", run.front_matter_path), ("back-matter.md", run.back_matter_path)):
            if run.matter_text(path) is None:
                add("SEAM_PASS_INCOMPLETE", None, f"final.md exists but {name} contains no prose — the seam pass "
                    "writes it (SKILL.md move 7, step 5)", level="info")
    for d in budget_drift(units, run.charter_totals(ledger)):
        if d["total"] is None:
            add("PLAN_BUDGET_UNCHECKED", None, f"plan budgets sum {d['sum']}{d['unit']} ({', '.join(d['units'])}) "
                f"but the charter declares no '{d['unit']}' total; drift not checked", level="info")
        elif d["drift_pct"] > BUDGET_DRIFT_PCT:
            add("PLAN_BUDGET_DRIFT", None, f"plan budgets sum {d['sum']}{d['unit']} vs charter {d['total']}{d['unit']} ({d['drift_pct']:.0f}%)")
    problems = [f for f in findings if f["level"] != "info"]
    infos = [f for f in findings if f["level"] == "info"]
    head = "audit: " + ("clean" if not problems else f"{len(problems)} finding(s)") + \
        (f" ({len(infos)} informational)" if infos else "")
    emit(args, {"ok": not problems, "findings": findings},
         "\n".join([head] + [f"  {f['code']:<24} {f['unit'] or '-':<6} {'info: ' if f['level'] == 'info' else ''}{f['message']}"
                            for f in findings]))
    return 0 if not problems else 1


def blocks_without_ruling(ledger: dict, uid: str) -> List[dict]:
    """Every block of `uid` that was later resolved (a fix/done event for the
    unit) with no RULING event — linked to this unit via --unit, or unit-less —
    recorded between the two. Ordering follows the append-only event list
    (timestamps have one-second resolution and can tie); the unit's history
    in ledger.json mirrors the same status changes."""
    out: List[dict] = []
    pending: Optional[dict] = None
    for ev in ledger.get("events", []):
        kind, unit = ev.get("kind"), ev.get("unit")
        if kind == "blocked" and unit == uid:
            pending = {"blocked": ev.get("ts"), "reason": ev.get("note"), "ruled": False}
        elif kind == "ruling" and pending and unit in (None, uid):
            pending["ruled"] = True
        elif kind in ("done", "fix") and unit == uid and pending:
            if not pending["ruled"]:
                out.append({"blocked": pending["blocked"], "reason": pending["reason"],
                            "resolved": ev.get("ts"), "resolved_to": kind})
            pending = None
    return out


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

LOOP_HELP = """The seven-move loop:
  CHARTER -> PLAN -> [ BRIEF -> EXECUTE -> VERIFY -> RECORD ] * N -> STITCH -> SEAM
  init/plan --validate  |  next -> brief -> (executor) -> check [-> review] -> record  |  stitch -> seam pass -> audit
VERIFY has two gates: `check` (mechanical predicates) and `review` (judgement predicates, source:/charter:).
`stitch` writes draft.md only; the seam pass writes front-matter.md, back-matter.md and final.md by hand."""


def build_parser() -> argparse.ArgumentParser:
    # --run-dir/--json are accepted before or after the command. The subcommand
    # copies use SUPPRESS defaults so they never overwrite a value parsed at top level.
    top = argparse.ArgumentParser(add_help=False)
    common = argparse.ArgumentParser(add_help=False)
    for parent, default in ((top, None), (common, argparse.SUPPRESS)):
        parent.add_argument("--run-dir", default=default, help="run directory (default: ./.bse/<most recent>)")
        parent.add_argument("--json", action="store_true", default=default if default else False,
                            help="machine-readable output")
    p = argparse.ArgumentParser(prog="bse.py", description=LOOP_HELP, parents=[top],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", metavar="COMMAND")

    s = sub.add_parser("init", parents=[common], help="scaffold a run dir with templates")
    s.add_argument("--run-id", required=True)
    s.add_argument("--title", default=None)
    s.add_argument("--total", default="20000w", help="charter total size, e.g. 20000w / 80slides")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("plan", parents=[common], help="parse PLAN.md; --validate runs the plan gate")
    s.add_argument("--validate", action="store_true",
                   help="schema + placeholder + dependency + budget + predicate-adequacy checks "
                        "(word-budgeted units need word_count; units reading sources need citation_tags or a "
                        "source: predicate; non-final compose units need no_conclusion — each waivable with "
                        "'waive: <rule> — <reason>' in the spec block; waivers are listed in the output)")
    s.set_defaults(func=cmd_plan)

    s = sub.add_parser("status", parents=[common],
                       help="table: id, type, status, attempts, budget, words, review (pending/stale/pass/fail)")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("next", parents=[common],
                       help="print the next unblocked unit ID (empty when all done; exit 1 on an empty or never-validated plan)")
    s.add_argument("--all", action="store_true", help="print every currently unblocked unit (wave mode)")
    s.set_defaults(func=cmd_next)

    s = sub.add_parser("brief", parents=[common], help="assemble briefs/ID.md = charter + spec + carry + input slices")
    s.add_argument("id")
    s.add_argument("--out", help="write the brief here instead of briefs/ID.md")
    s.set_defaults(func=cmd_brief)

    s = sub.add_parser("check", parents=[common],
                       help="run the unit's mechanical verifiers; write reports/ID.md. Re-running on a changed "
                            "artifact after a failing check counts a fix round (cap 3)")
    s.add_argument("id")
    s.add_argument("--artifact", help="artifact path (default batches/ID.md)")
    s.add_argument("--force", action="store_true",
                   help="run even after 3 fix rounds (the extra round is recorded and stamped FORCED)")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("review", parents=[common],
                       help="store a reviewer's verdict on the unit's judgement predicates (source:/charter:), "
                            "keyed to the artifact's sha256; required before `record --status done` for such units")
    s.add_argument("id")
    s.add_argument("--verdict", required=True, choices=list(REVIEW_VERDICTS))
    s.add_argument("--report", required=True, metavar="PATH", help="the reviewer's written report (must exist)")
    s.add_argument("--artifact", help="artifact path (default batches/ID.md)")
    s.add_argument("--note", help="free text, e.g. reviewer identity or a one-line finding")
    s.set_defaults(func=cmd_review)

    s = sub.add_parser("record", parents=[common], help="append a ledger event: done | blocked | fix (or RULING --note)")
    s.add_argument("id", help="unit ID, or RULING")
    s.add_argument("--status", choices=["done", "blocked", "fix"], default="done")
    s.add_argument("--artifact", help="artifact path (default batches/ID.md)")
    s.add_argument("--note", help="reason (blocked) / free text")
    s.add_argument("--unit", metavar="ID", help="RULING only: the unit this ruling resolves (must exist in PLAN.md)")
    s.add_argument("--carry", help="file whose content replaces carry.md on done (cap enforced)")
    s.add_argument("--force", action="store_true",
                   help="record done despite failed/missing checks or a missing/failing review (stamped FORCED)")
    s.set_defaults(func=cmd_record)

    s = sub.add_parser("carry", parents=[common],
                       help="replace (--set FILE), print (--show) or test (--check) the baton; 400-word cap")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--set", metavar="FILE")
    g.add_argument("--show", action="store_true")
    g.add_argument("--check", action="store_true",
                   help="exit 1 when >= 2 units are done and carry.md is still the init scaffold or empty")
    s.set_defaults(func=cmd_carry)

    s = sub.add_parser("stitch", parents=[common],
                       help="assemble draft.md in plan order + reports/stitch.md; never writes final.md")
    s.add_argument("--out", help="output path (default draft.md in the run dir; final.md is refused)")
    s.add_argument("--no-front-matter", action="store_true",
                   help="do not prepend front-matter.md / append back-matter.md (included by default when they contain prose)")
    s.add_argument("--include-front-matter", action="store_true",
                   help="DEPRECATED no-op alias (front/back matter are now included by default); will be removed next version")
    s.add_argument("--partial", action="store_true", help="allow incomplete units (inserts <!-- MISSING B00X -->)")
    s.add_argument("--allow-drift", action="store_true",
                   help=f"exit 0 even when the stitched total drifts more than ±{BUDGET_DRIFT_PCT}%% from the charter "
                        "target (default: prominent warning and exit 1)")
    s.set_defaults(func=cmd_stitch)

    s = sub.add_parser("audit", parents=[common],
                       help="ledger vs filesystem consistency: phantom-complete, hash/review mismatches, stale carry, "
                            "missing/stale seam pass (final.md)")
    s.set_defaults(func=cmd_audit)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "cmd", None):
        parser.print_help()
        return 2
    try:
        return args.func(args)
    except BseError as e:
        if getattr(args, "json", False):
            print(json.dumps({"error": str(e), "code": e.code}))
        else:
            print(f"error: {e}", file=sys.stderr)
        return e.code
    except KeyboardInterrupt:
        return 2


if __name__ == "__main__":
    sys.exit(main())
