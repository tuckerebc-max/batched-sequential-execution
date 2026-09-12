"""Tests for scripts/bse.py — stdlib unittest, no network, no leftover files.

Run:  python -m unittest discover -s tests -v
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
BSE_PATH = HERE.parent / "scripts" / "bse.py"
spec = importlib.util.spec_from_file_location("bse", BSE_PATH)
bse = importlib.util.module_from_spec(spec)
sys.modules["bse"] = bse       # dataclasses need the module registered
spec.loader.exec_module(bse)


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

CHARTER = """# CHARTER — Test report

## Deliverable
What: a test report
Format: markdown
Total size: {total}

## Audience
Testers.

## Voice & register
Plain.

## Non-negotiables
1. Numbers are tagged.

## Terminology lock
- cap ledger | capacity book -> capacity ledger

## Sources of truth
- [S1] notes/source.md

## Acceptance criteria
1. Sections exist.

## Out of scope
- Nothing.
"""

SPEC = """### {id} — {title}
type: {type}
budget: {budget} (±15%)
depends_on: [{deps}]
inputs:
{inputs}
intent: |
  Write the {title} section so a stranger could act on it.
produces:
  - section: "{produces}"
verify:
{verify}
{waive}
done_when: |
  The {title} section exists.
"""

NO_CONCLUSION_WAIVER = "waive: no_conclusion — fixture prose is a fragment with no closing paragraph"


def unit(id, title, type="compose", budget="100w", deps="", parallel=False, produces=None,
         verify=("  - mechanical: word_count within 15% of 100", "  - mechanical: no_placeholders"),
         inputs=("  - CHARTER.md",), waive=NO_CONCLUSION_WAIVER):
    return dict(id=id, title=title, type=type, budget=budget, deps=deps, parallel=parallel,
                produces=produces or title, verify="\n".join(verify), inputs="\n".join(inputs), waive=waive)


def plan_text(units, sep="—"):
    lines = ["# PLAN", "", "## Units"]
    for u in units:
        dep = f"[dep:{u['deps']}] " if u["deps"] else ""
        p = "[P] " if u["parallel"] else ""
        lines.append(f"- [ ] {u['id']} [{u['type']}] {p}{dep}{u['title']} {sep} budget: {u['budget']}")
    lines += ["", "## Specs", ""]
    for u in units:
        lines.append(SPEC.format(**u))
    return "\n".join(lines)


THREE = [unit("B001", "Alpha"), unit("B002", "Beta", deps="B001"), unit("B003", "Gamma", deps="B002")]


def prose(n, seed="alpha"):
    """n words of unique-ish prose, no numbers, no placeholders."""
    words = []
    i = 0
    while len(words) < n:
        words.append(f"{seed}{i % 7} word{i}")
        i += 1
    return " ".join(" ".join(words).split()[:n])


def subcommand_help(name):
    """The --help text of one subcommand (argparse exits, so capture around it)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.suppress(SystemExit):
        bse.main([name, "--help"])
    return out.getvalue()


def run_cli(*argv):
    """Invoke bse.main with captured stdout/stderr. Returns (exit, out, err)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = bse.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class RunCase(unittest.TestCase):
    """Base: temp dir with an initialised run, charter and 3-unit plan."""
    units = THREE
    total = "300w"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.rd = self.tmp / ".bse" / "t1"
        code, _, err = run_cli("init", "--run-id", "t1", "--run-dir", str(self.rd), "--total", self.total)
        self.assertEqual(code, 0, err)
        self.run = bse.Run(self.rd)
        self.write_charter()
        self.write_plan(self.units)
        self.cli("plan", "--validate")          # `next` refuses a never-validated plan; result not asserted here

    def tearDown(self):
        self._tmp.cleanup()

    def write_charter(self, total=None):
        (self.rd / "CHARTER.md").write_text(CHARTER.format(total=total or self.total), encoding="utf-8")

    def write_plan(self, units, sep="—"):
        (self.rd / "PLAN.md").write_text(plan_text(units, sep), encoding="utf-8")

    def cli(self, *argv):
        return run_cli(*argv, "--run-dir", str(self.rd))

    def artifact(self, uid, text):
        p = self.rd / "batches" / f"{uid}.md"
        p.write_text(text, encoding="utf-8")
        return p

    def good_artifact(self, uid, heading=None, n=100, seed=None):
        return self.artifact(uid, f"# {heading or uid}\n\n{prose(n - 1, seed or uid.lower())}\n")

    def carry_file(self, uid):
        """A real (non-scaffold) baton naming the unit, as the loop requires before every record."""
        p = self.tmp / f"carry-{uid}.md"
        p.write_text(f"## Established facts\n- {uid} landed [S1]\n\n## Interfaces/terms now defined\n- (none)\n\n"
                     f"## Open threads for later units\n- (none)\n\n## Do not repeat\n- the {uid} opening\n\n"
                     f"## Tone calibration note\nPlain.\n", encoding="utf-8")
        return p

    def complete(self, uid, carry=True, **kw):
        self.good_artifact(uid, **kw)
        code, out, err = self.cli("check", uid)
        self.assertEqual(code, 0, out + err)
        extra = ["--carry", str(self.carry_file(uid))] if carry else []
        code, out, err = self.cli("record", uid, "--status", "done", *extra)
        self.assertEqual(code, 0, out + err)

    def ledger(self):
        return json.loads((self.rd / "ledger.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

class TestInit(RunCase):
    def test_init_scaffolds_run_dir(self):
        for name in ("CHARTER.md", "PLAN.md", "LEDGER.md", "ledger.json", "carry.md", "briefs", "batches", "reports"):
            self.assertTrue((self.rd / name).exists(), name)
        first = (self.rd / "LEDGER.md").read_text(encoding="utf-8").splitlines()[0]
        self.assertRegex(first, r"^# BSE ledger — run: t1 — charter: .*CHARTER\.md — created: \d{4}-")
        data = self.ledger()
        self.assertEqual(data["run_id"], "t1")
        self.assertEqual(data["units"], {})
        self.assertEqual(data["events"], [])

    def test_init_refuses_existing_run(self):
        code, _, err = self.cli("init", "--run-id", "t1")
        self.assertEqual(code, 1)
        self.assertIn("already exists", err)

    def test_init_charter_template_has_required_sections(self):
        rd = self.tmp / ".bse" / "t2"
        run_cli("init", "--run-id", "t2", "--run-dir", str(rd), "--total", "500w")
        text = (rd / "CHARTER.md").read_text(encoding="utf-8")
        for sec in bse.CHARTER_SECTIONS:
            self.assertIn(f"## {sec}", text)
        self.assertIn("Total size: 500w", text)
        for sec in bse.CARRY_SECTIONS:
            self.assertIn(sec, (rd / "carry.md").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# plan parsing + validation
# ---------------------------------------------------------------------------

class TestPlan(RunCase):
    def test_validate_happy_path(self):
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 0, out)
        self.assertIn("PLAN VALID", out)

    def test_validate_json_output(self):
        code, out, _ = self.cli("plan", "--validate", "--json")
        data = json.loads(out)
        self.assertTrue(data["ok"])
        self.assertEqual(data["units"], 3)
        self.assertEqual(data["charter_total"], "300w")

    def test_duplicate_id_fails(self):
        self.write_plan([unit("B001", "Alpha"), unit("B001", "Alpha again"), unit("B003", "Gamma")])
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 1)
        self.assertIn("duplicate unit id B001", out)

    def test_cycle_fails(self):
        self.write_plan([unit("B001", "Alpha", deps="B003"), unit("B002", "Beta", deps="B001"),
                         unit("B003", "Gamma", deps="B002")])
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 1)
        self.assertIn("dependency cycle", out)

    def test_missing_budget_fails(self):
        text = plan_text(THREE).replace("- [ ] B002 [compose] [dep:B001] Beta — budget: 100w",
                                        "- [ ] B002 [compose] [dep:B001] Beta")
        (self.rd / "PLAN.md").write_text(text, encoding="utf-8")
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 1)
        self.assertRegex(out, r"L\d+: B002 table line has no")

    def test_placeholder_fails_with_line_number(self):
        u = THREE[:]
        u[1] = dict(u[1], produces="section like the one above, etc.")
        self.write_plan(u)
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 1)
        self.assertRegex(out, r"L\d+: B002 placeholder string 'etc\.'")

    def test_budget_drift_fails(self):
        self.write_charter(total="1000w")
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 1)
        self.assertIn("drifts", out)

    def test_unknown_dependency_and_missing_intent(self):
        text = plan_text(THREE).replace("[dep:B002]", "[dep:B009]")
        text = re.sub(r"intent: \|\n  Write the Alpha section.*\n", "intent: |\n", text)
        (self.rd / "PLAN.md").write_text(text, encoding="utf-8")
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 1)
        self.assertIn("depends on unknown unit B009", out)
        self.assertIn("B001 missing intent", out)

    def test_no_mechanical_verifier_fails(self):
        u = THREE[:]
        u[0] = unit("B001", "Alpha", verify=("  - charter: acceptance criteria 1",))
        self.write_plan(u)
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 1)
        self.assertIn("at least one '- mechanical:", out)

    def test_parallel_units_sharing_produces_fails(self):
        u = [unit("B001", "Alpha", parallel=True, produces="Shared"),
             unit("B002", "Beta", parallel=True, produces="Shared"), unit("B003", "Gamma")]
        self.write_plan(u)
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 1)
        self.assertIn("shares produces target", out)

    def test_parser_tolerates_crlf_hyphen_and_comments(self):
        text = plan_text(THREE, sep="-").replace("\n", "\r\n")
        text = "<!--\n- [ ] B099 [compose] Example — budget: 5w\n-->\r\n" + text
        (self.rd / "PLAN.md").write_bytes(text.encode("utf-8"))
        units, errors = bse.parse_plan((self.rd / "PLAN.md").read_text(encoding="utf-8"))
        self.assertEqual(errors, [])
        self.assertEqual([u.id for u in units], ["B001", "B002", "B003"])
        self.assertEqual(units[1].depends_on, ["B001"])
        self.assertEqual(units[1].budget, (100, "w", 15))
        self.assertEqual(bse.parse_plan(plan_text(THREE).replace("(±15%)", "(±5%)"))[0][0].budget, (100, "w", 5))
        self.assertEqual(units[0].scalar_field("intent"), "Write the Alpha section so a stranger could act on it.")
        self.assertEqual(units[0].list_field("produces"), ['section: "Alpha"'])
        self.assertEqual(units[0].mechanical(), ["word_count within 15% of 100", "no_placeholders"])

    def test_unparsable_line_reports_line_number(self):
        (self.rd / "PLAN.md").write_text("# P\n- [ ] B001 [compose Alpha — budget: 1w\n", encoding="utf-8")
        _, errors = bse.parse_plan((self.rd / "PLAN.md").read_text(encoding="utf-8"))
        self.assertTrue(any(e.startswith("L2:") for e in errors), errors)


# ---------------------------------------------------------------------------
# next / dependency resolution
# ---------------------------------------------------------------------------

class TestNext(RunCase):
    def test_next_is_first_unit(self):
        code, out, _ = self.cli("next")
        self.assertEqual((code, out.strip()), (0, "B001"))

    def test_next_respects_dependencies(self):
        self.complete("B001")
        code, out, _ = self.cli("next")
        self.assertEqual(out.strip(), "B002")
        code, out, _ = self.cli("next", "--json")
        self.assertEqual(json.loads(out), {"unit": "B002", "remaining": 2})

    def test_next_parallel_unit_is_eligible_and_all_lists_it(self):
        self.write_plan([unit("B001", "Alpha"), unit("B002", "Beta", deps="B001"),
                         unit("B003", "Gamma", parallel=True, produces="Other")])
        code, out, _ = self.cli("next", "--all")
        self.assertEqual(out.split(), ["B001", "B003", "[P]"])
        self.complete("B001")
        self.complete("B003")
        code, out, _ = self.cli("next")
        self.assertEqual(out.strip(), "B002")

    def test_next_empty_when_all_done(self):
        for uid in ("B001", "B002", "B003"):
            self.complete(uid)
        code, out, _ = self.cli("next")
        self.assertEqual((code, out), (0, ""))
        code, out, _ = self.cli("next", "--json")
        self.assertEqual(json.loads(out), {"unit": None, "remaining": 0})

    def test_next_skips_blocked_units(self):
        self.cli("record", "B001", "--status", "blocked", "--note", "needs ruling")
        code, out, err = self.cli("next")
        self.assertEqual((code, out), (0, ""))
        self.assertIn("blocked: B001", err)


# ---------------------------------------------------------------------------
# brief
# ---------------------------------------------------------------------------

class TestBrief(RunCase):
    def test_brief_contains_charter_spec_carry_and_nothing_else(self):
        (self.rd / "carry.md").write_text("## Do not repeat\n- the baton marker\n", encoding="utf-8")
        code, out, _ = self.cli("brief", "B002")
        self.assertEqual(code, 0, out)
        text = (self.rd / "briefs" / "B002.md").read_text(encoding="utf-8")
        self.assertIn("## Terminology lock", text)              # charter
        self.assertIn("### B002 — Beta", text)                  # this unit's spec
        self.assertIn("the baton marker", text)                 # carry
        self.assertNotIn("### B001", text)                      # no other spec blocks
        self.assertNotIn("### B003", text)
        self.assertNotIn("- [ ] B00", text)                     # no plan table
        self.assertNotIn("BSE ledger", text)                    # no ledger

    def test_brief_includes_input_slice_and_flags_missing(self):
        src = self.rd / "notes.md"
        src.write_text("\n".join(f"line{i}" for i in range(1, 11)) + "\n", encoding="utf-8")
        text = plan_text(THREE).replace("inputs:\n  - CHARTER.md", "inputs:\n  - notes.md#L3-5\n  - missing.md", 1)
        (self.rd / "PLAN.md").write_text(text, encoding="utf-8")
        code, out, _ = self.cli("brief", "B001", "--out", str(self.tmp / "b.md"))
        self.assertEqual(code, 1)
        brief = (self.tmp / "b.md").read_text(encoding="utf-8")
        self.assertIn("line3\nline4\nline5", brief)
        self.assertNotIn("line2", brief)
        self.assertIn("INPUT NOT FOUND: missing.md", brief)

    def test_unknown_unit_is_usage_error(self):
        code, _, err = self.cli("brief", "B042")
        self.assertEqual(code, 2)


# ---------------------------------------------------------------------------
# mechanical verifiers (unit-level, pass + fail each)
# ---------------------------------------------------------------------------

class TestVerifiers(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.run = bse.Run(self.root)
        self.unit = bse.Unit(id="B001", budget=(100, "w", 15))
        self.ctx = {"unit": self.unit, "run": self.run, "artifact": self.root / "a.md"}

    def tearDown(self):
        self._tmp.cleanup()

    def v(self, name, text, args=""):
        return bse.VERIFIERS[name](text, args, self.ctx)

    def test_word_count(self):
        self.assertTrue(self.v("word_count", prose(100), "within 15% of 100")[0])
        self.assertFalse(self.v("word_count", prose(50), "within 15% of 100")[0])
        self.assertTrue(self.v("word_count", prose(90), "")[0])              # defaults to budget
        self.assertTrue(self.v("word_count", prose(90), ">= 80")[0])
        self.assertFalse(self.v("word_count", prose(90), "80-85")[0])
        self.assertFalse(self.v("word_count", prose(90), "nonsense spec")[0])

    def test_count_words_excludes_fences_and_comments(self):
        text = "# Title\n\none two three\n\n```\ncode words here\n```\n<!-- hidden words -->\nfour\n"
        self.assertEqual(bse.count_words(text), 5)

    def test_no_placeholders(self):
        self.assertTrue(self.v("no_placeholders", "Clean prose here. `<code>` is fine etc. not final\n")[0])
        for bad in ("TBD", "TODO", "[insert name]", "Lorem ipsum", "and so on etc.", "as described", "XXX", "<fill me>"):
            ok, detail = self.v("no_placeholders", f"line one\n{bad}\n")
            self.assertFalse(ok, bad)
            self.assertIn("L2", detail)

    def test_contains_headings(self):
        text = "## 3.2 Method\n\ntext\n\n### Results ###\n"
        self.assertTrue(self.v("contains_headings", text, '["3.2 Method", "Results"]')[0])
        self.assertFalse(self.v("contains_headings", text, '["Discussion"]')[0])

    def test_max_heading_depth(self):
        text = "# A\n## B\n### C\n"
        self.assertTrue(self.v("max_heading_depth", text, "3")[0])
        ok, detail = self.v("max_heading_depth", text, "2")
        self.assertFalse(ok)
        self.assertIn("H3 at L3", detail)

    def test_citation_tags(self):
        self.assertTrue(self.v("citation_tags", "Growth was 12% in 2025 [S1].\nNo numbers here.\n")[0])
        ok, detail = self.v("citation_tags", "## 2025 review\nGrowth was 12% year on year.\n")
        self.assertFalse(ok)
        self.assertIn("L2", detail)

    def test_forbidden_phrases_explicit_and_from_charter(self):
        self.assertFalse(self.v("forbidden_phrases", "the cap ledger grew", '["cap ledger"]')[0])
        self.assertTrue(self.v("forbidden_phrases", "the capacity ledger grew", '["cap ledger"]')[0])
        (self.root / "CHARTER.md").write_text(CHARTER.format(total="1w"), encoding="utf-8")
        (self.root / "carry.md").write_text("## Do not repeat\n- history of widgets\n", encoding="utf-8")
        self.assertFalse(self.v("forbidden_phrases", "The capacity book is old.")[0])
        self.assertFalse(self.v("forbidden_phrases", "the History of Widgets again")[0])
        self.assertTrue(self.v("forbidden_phrases", "the capacity ledger is fine")[0])

    def test_slide_count(self):
        deck = "# Title\n\n## One\n\n## Two\n"
        self.assertTrue(self.v("slide_count", deck, "3")[0])
        self.assertFalse(self.v("slide_count", deck, "within 10% of 6")[0])
        self.assertTrue(self.v("slide_count", "a\n\n---\n\nb\n\n---\n\nc\n", "3")[0])

    def test_item_count(self):
        items = "\n".join(f"- item {i}" for i in range(10)) + "\n  - nested\n"
        self.assertTrue(self.v("item_count", items, "10")[0])
        self.assertFalse(self.v("item_count", items, ">= 11")[0])

    def test_file_exists(self):
        (self.root / "present.txt").write_text("x", encoding="utf-8")
        self.assertTrue(self.v("file_exists", "", "present.txt")[0])
        self.assertFalse(self.v("file_exists", "", "absent.txt")[0])

    def test_json_schema(self):
        (self.root / "schema.json").write_text(json.dumps({
            "type": "object", "required": ["name", "n"],
            "properties": {"name": {"type": "string"}, "n": {"type": "integer", "minimum": 1},
                           "tags": {"type": "array", "items": {"type": "string"}}}}), encoding="utf-8")
        good = '```json\n{"name": "a", "n": 2, "tags": ["x"]}\n```\n'
        self.assertTrue(self.v("json_schema", good, "schema.json")[0])
        ok, detail = self.v("json_schema", '{"name": "a", "n": 0, "tags": [1]}', "schema.json")
        self.assertFalse(ok)
        self.assertIn("minimum", detail)
        self.assertFalse(self.v("json_schema", "not json", "schema.json")[0])

    def test_shell(self):
        py = sys.executable
        self.assertTrue(self.v("shell", "", f'"{py}" -c "import sys; sys.exit(0)"')[0])
        ok, detail = self.v("shell", "", f'"{py}" -c "import sys; sys.exit(3)"')
        self.assertFalse(ok)
        self.assertIn("exit 3", detail)

    def test_no_conclusion(self):
        self.assertTrue(self.v("no_conclusion", "Overall, this paragraph is early.\n\nMore work follows here.\n")[0])
        self.assertFalse(self.v("no_conclusion", "Body text.\n\nOverall, that is it.\n")[0])
        self.assertFalse(self.v("no_conclusion", "In conclusion, stop.\n\nMore.\n")[0])

    def test_registry_extension_is_a_decorator(self):
        @bse.verifier("always_true_test")
        def v(text, args, ctx):
            return True, "ok"
        try:
            self.assertIs(bse.VERIFIERS["always_true_test"], v)
        finally:
            del bse.VERIFIERS["always_true_test"]


# ---------------------------------------------------------------------------
# check / record / resume
# ---------------------------------------------------------------------------

class TestCheckRecord(RunCase):
    def test_check_writes_report_and_stores_results(self):
        self.artifact("B001", "# B001\n\nshort TBD\n")
        code, out, _ = self.cli("check", "B001")
        self.assertEqual(code, 1)
        report = (self.rd / "reports" / "B001.md").read_text(encoding="utf-8")
        self.assertIn("FAIL (0/2 mechanical)", report)
        v = self.ledger()["units"]["B001"]["verify"]
        self.assertEqual((v["passed"], v["failed"]), (0, 2))
        self.assertEqual(len(v["checks"]), 2)
        self.assertTrue(v["sha256"])

    def test_check_missing_artifact_fails_every_check(self):
        code, out, _ = self.cli("check", "B001", "--json")
        self.assertEqual(code, 1)
        self.assertTrue(all(c["detail"] == "artifact missing" for c in json.loads(out)["checks"]))

    def test_record_done_refused_when_checks_failed(self):
        self.artifact("B001", "# B001\n\nshort TBD\n")
        self.cli("check", "B001")
        code, _, err = self.cli("record", "B001", "--status", "done")
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", err)
        self.assertEqual(self.ledger()["units"]["B001"]["status"], "pending")
        self.assertNotIn("B001 done", (self.rd / "LEDGER.md").read_text(encoding="utf-8"))

    def test_record_done_refused_without_check(self):
        self.good_artifact("B001")
        code, _, err = self.cli("record", "B001", "--status", "done")
        self.assertEqual(code, 1)
        self.assertIn("no check has been run", err)

    def test_record_done_refused_when_artifact_changed_after_check(self):
        self.good_artifact("B001")
        self.cli("check", "B001")
        self.good_artifact("B001", seed="changed")
        code, _, err = self.cli("record", "B001", "--status", "done")
        self.assertEqual(code, 1)
        self.assertIn("sha mismatch", err)

    def test_record_force_stamps_forced(self):
        self.artifact("B001", "# B001\n\nshort TBD\n")
        self.cli("check", "B001")
        code, out, _ = self.cli("record", "B001", "--status", "done", "--force")
        self.assertEqual(code, 0)
        line = [l for l in (self.rd / "LEDGER.md").read_text(encoding="utf-8").splitlines() if l.startswith("B001 done")][0]
        self.assertIn("FORCED", line)
        self.assertIn("verify=fail(2/2)", line)
        self.assertTrue(self.ledger()["events"][-1]["forced"])

    def test_record_done_marks_plan_and_ledger(self):
        self.complete("B001")
        self.assertIn("- [x] B001", (self.rd / "PLAN.md").read_text(encoding="utf-8"))
        st = self.ledger()["units"]["B001"]
        self.assertEqual(st["status"], "done")
        self.assertEqual(st["artifact"], "batches/B001.md")
        self.assertEqual(st["attempts"], 1)
        line = (self.rd / "LEDGER.md").read_text(encoding="utf-8").splitlines()[-1]
        self.assertRegex(line, r"^B001 done\s+\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\s+artifact=batches/B001\.md\s+words=\d+\s+verify=pass\(2/2\)\s+sha=[0-9a-f]{7}$")

    def test_record_fix_rounds_are_capped(self):
        for i in range(3):
            code, out, _ = self.cli("record", "B001", "--status", "fix")
            self.assertEqual(code, 0)
        code, _, err = self.cli("record", "B001", "--status", "fix")
        self.assertEqual(code, 1)
        self.assertIn("split the unit", err)
        self.assertIn("B001 fix 3/3", (self.rd / "LEDGER.md").read_text(encoding="utf-8"))
        self.assertEqual(self.ledger()["units"]["B001"]["attempts"], 4)

    def test_record_blocked_requires_note(self):
        code, _, _ = self.cli("record", "B001", "--status", "blocked")
        self.assertEqual(code, 2)
        code, _, _ = self.cli("record", "B001", "--status", "blocked", "--note", "source contradicts NN-1")
        self.assertEqual(code, 0)
        self.assertIn("B001 blocked", (self.rd / "LEDGER.md").read_text(encoding="utf-8"))
        self.assertIn("reason=source contradicts NN-1", (self.rd / "LEDGER.md").read_text(encoding="utf-8"))

    def test_record_ruling_and_ledger_is_append_only(self):
        before = (self.rd / "LEDGER.md").read_text(encoding="utf-8")
        self.cli("record", "RULING", "--note", "use 2025 figures")
        self.complete("B001")
        after = (self.rd / "LEDGER.md").read_text(encoding="utf-8")
        self.assertTrue(after.startswith(before))
        self.assertIn("RULING", after)
        self.assertEqual(len(self.ledger()["events"]), 2)

    def test_record_done_can_replace_carry(self):
        new = self.tmp / "carry-new.md"
        new.write_text("## Established facts\n- fact one\n", encoding="utf-8")
        self.good_artifact("B001")
        self.cli("check", "B001")
        code, _, _ = self.cli("record", "B001", "--status", "done", "--carry", str(new))
        self.assertEqual(code, 0)
        self.assertIn("fact one", (self.rd / "carry.md").read_text(encoding="utf-8"))

    def test_resume_after_simulated_context_loss(self):
        self.complete("B001")
        self.complete("B002")
        # "context loss": a brand-new Run object built only from the identity header on disk
        header = (self.rd / "LEDGER.md").read_text(encoding="utf-8").splitlines()[0]
        m = re.match(r"^# BSE ledger — run: (\S+) — charter: (.*) — created: (\S+)$", header)
        self.assertIsNotNone(m)
        fresh = bse.Run(Path(m.group(2)).parent)
        data = fresh.load_ledger()
        self.assertEqual(data["run_id"], "t1")
        done = {u for u, s in data["units"].items() if s["status"] == "done"}
        self.assertEqual(done, {"B001", "B002"})
        code, out, _ = run_cli("next", "--run-dir", str(fresh.root))
        self.assertEqual(out.strip(), "B003")
        code, out, _ = run_cli("status", "--run-dir", str(fresh.root))
        self.assertIn("2 of 3 units done", out)


# ---------------------------------------------------------------------------
# stitch
# ---------------------------------------------------------------------------

class TestStitch(RunCase):
    def test_stitch_orders_by_plan_and_writes_report(self):
        for uid in ("B001", "B002", "B003"):
            self.complete(uid)
        code, out, _ = self.cli("stitch")
        self.assertEqual(code, 0, out)
        draft = (self.rd / "draft.md").read_text(encoding="utf-8")
        self.assertLess(draft.index("# B001"), draft.index("# B002"))
        self.assertLess(draft.index("# B002"), draft.index("# B003"))
        report = (self.rd / "reports" / "stitch.md").read_text(encoding="utf-8")
        self.assertIn("- B001: 100 (budget 100)", report)
        self.assertIn("vs charter target 300w", report)
        self.assertIn("### B001 -> B002", report)
        self.assertIn("SEAM  B001-B003", (self.rd / "LEDGER.md").read_text(encoding="utf-8"))

    def test_stitch_duplicate_detection(self):
        dup = "This exact sentence of more than twelve words is repeated in two different units by design."
        self.complete("B001")
        self.artifact("B002", f"# B002\n\n{prose(80, 'b')}.\n\n{dup}\n")
        self.cli("check", "B002"); self.cli("record", "B002", "--status", "done")
        self.artifact("B003", f"# B003\n\n{dup}   this EXACT sentence, of more than twelve words is repeated in two different units by design!\n{prose(70, 'c')}\n")
        self.cli("check", "B003"); self.cli("record", "B003", "--status", "done")
        code, out, _ = self.cli("stitch", "--json")
        data = json.loads(out)
        self.assertEqual(len(data["duplicates"]), 1)
        self.assertEqual(data["duplicates"][0]["units"], ["B002", "B003"])
        self.assertIn("[B002, B003]", (self.rd / "reports" / "stitch.md").read_text(encoding="utf-8"))

    def test_stitch_refuses_incomplete_unless_partial(self):
        self.complete("B001")
        code, _, err = self.cli("stitch")
        self.assertEqual(code, 1)
        self.assertIn("B002, B003", err)
        self.assertFalse((self.rd / "draft.md").exists())
        code, out, _ = self.cli("stitch", "--partial")
        self.assertEqual(code, 0)
        draft = (self.rd / "draft.md").read_text(encoding="utf-8")
        self.assertIn("<!-- MISSING B002 -->", draft)
        self.assertIn("<!-- MISSING B003 -->", draft)

    def test_stitch_never_modifies_batches_and_reports_terminology(self):
        self.artifact("B001", f"# B001\n\nThe cap ledger grew. {prose(95, 'a')}\n")
        self.cli("check", "B001"); self.cli("record", "B001", "--status", "done")
        self.complete("B002"); self.complete("B003")
        before = {p.name: p.read_bytes() for p in (self.rd / "batches").iterdir()}
        code, out, _ = self.cli("stitch", "--json", "--include-front-matter")
        data = json.loads(out)
        self.assertEqual(data["terminology_violations"][0]["wrong"], "cap ledger")
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.rd / "batches").iterdir()})
        self.assertIn("FRONT MATTER", (self.rd / "draft.md").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# audit
# ---------------------------------------------------------------------------

class TestAudit(RunCase):
    def codes(self):
        code, out, _ = self.cli("audit", "--json")
        return code, {f["code"] for f in json.loads(out)["findings"]}

    def test_audit_clean(self):
        self.complete("B001")
        self.assertEqual(self.codes(), (0, set()))

    def test_audit_phantom_complete(self):
        text = (self.rd / "PLAN.md").read_text(encoding="utf-8").replace("- [ ] B002", "- [x] B002")
        (self.rd / "PLAN.md").write_text(text, encoding="utf-8")
        code, codes = self.codes()
        self.assertEqual(code, 1)
        self.assertIn("PHANTOM_COMPLETE", codes)

    def test_audit_hash_mismatch_and_missing_artifact(self):
        self.complete("B001"); self.complete("B002")
        self.good_artifact("B001", seed="tampered")
        (self.rd / "batches" / "B002.md").unlink()
        code, codes = self.codes()
        self.assertEqual(code, 1)
        self.assertIn("HASH_MISMATCH", codes)
        self.assertIn("ARTIFACT_MISSING", codes)

    def test_audit_done_with_failing_verify_and_unknown_unit(self):
        self.artifact("B001", "# B001\n\nshort TBD\n")
        self.cli("check", "B001")
        self.cli("record", "B001", "--status", "done", "--force")
        data = self.ledger()
        data["units"]["B777"] = {"status": "done"}
        (self.rd / "ledger.json").write_text(json.dumps(data), encoding="utf-8")
        code, codes = self.codes()
        self.assertIn("DONE_WITH_FAILING_VERIFY", codes)
        self.assertIn("UNKNOWN_UNIT", codes)
        self.assertIn("BUDGET_DRIFT", codes)

    def test_audit_carry_over_cap_and_plan_budget_drift(self):
        (self.rd / "carry.md").write_text(prose(450), encoding="utf-8")
        self.write_charter(total="1000w")
        code, codes = self.codes()
        self.assertIn("CARRY_OVER_CAP", codes)
        self.assertIn("PLAN_BUDGET_DRIFT", codes)


# ---------------------------------------------------------------------------
# carry, atomic writes, paths, help
# ---------------------------------------------------------------------------

class TestCarryAndInfra(RunCase):
    def test_carry_cap_enforced(self):
        big = self.tmp / "big.md"
        big.write_text("## Established facts\n" + prose(401), encoding="utf-8")
        before = (self.rd / "carry.md").read_text(encoding="utf-8")
        code, _, err = self.cli("carry", "--set", str(big))
        self.assertEqual(code, 1)
        self.assertRegex(err, r"would be 40[1-9] words; hard cap is 400")
        self.assertEqual((self.rd / "carry.md").read_text(encoding="utf-8"), before)

    def test_carry_set_and_show(self):
        ok = self.tmp / "ok.md"
        ok.write_text("## Established facts\n- one [S1]\n\n## Do not repeat\n- widgets\n", encoding="utf-8")
        code, out, _ = self.cli("carry", "--set", str(ok))
        self.assertEqual(code, 0)
        self.assertIn("missing sections", out)          # warned, not refused
        code, out, _ = self.cli("carry", "--show")
        self.assertIn("- widgets", out)

    def test_atomic_write_leaves_no_temp_files(self):
        target = self.rd / "atomic.txt"
        bse.atomic_write(target, "hello")
        bse.atomic_write(target, "world")
        self.assertEqual(target.read_text(encoding="utf-8"), "world")
        self.assertEqual([p.name for p in self.rd.iterdir() if p.name.startswith(".bse-tmp")], [])
        self.complete("B001")
        stray = [p.name for p in self.rd.rglob("*") if ".part" in p.name or ".bse-tmp" in p.name]
        self.assertEqual(stray, [])

    def test_atomic_write_failure_keeps_old_content(self):
        target = self.rd / "keep.txt"
        bse.atomic_write(target, "old")
        with self.assertRaises(TypeError):
            bse.atomic_write(target, None)          # write() rejects None -> temp is removed
        self.assertEqual(target.read_text(encoding="utf-8"), "old")
        self.assertEqual([p.name for p in self.rd.iterdir() if p.name.startswith(".bse-tmp")], [])

    def test_paths_use_pathlib_and_posix_relatives(self):
        self.complete("B001")
        rel = self.ledger()["units"]["B001"]["artifact"]
        self.assertEqual(rel, "batches/B001.md")                      # portable form in the ledger
        self.assertTrue((self.rd / rel).exists())                     # joins correctly on any OS
        src = BSE_PATH.read_text(encoding="utf-8")
        self.assertNotRegex(src, r"\"[A-Za-z_]+/[A-Za-z_]+\.md\"\s*\)?\s*$")  # no os-path string building
        self.assertNotIn("os.path.join", src)
        self.assertIn("os.replace", src)
        for call in re.findall(r"(?:(?<!def )\bopen|\.read_text|\.write_text)\(([^)]*)\)", src):
            self.assertIn("encoding=", call, call)                   # every file open names UTF-8

    def test_run_dir_defaults_to_most_recent(self):
        old = os.getcwd()
        os.chdir(self.tmp)
        try:
            run_cli("init", "--run-id", "t0", "--run-dir", str(self.tmp / ".bse" / "t0"))
            now = (self.rd / "ledger.json").stat().st_mtime + 60      # make t1 unambiguously the most recent
            os.utime(self.rd / "ledger.json", (now, now))
            code, out, _ = run_cli("status")
            self.assertEqual(code, 0, out)
            self.assertIn("run: t1", out)
        finally:
            os.chdir(old)

    def test_no_run_dir_is_usage_error(self):
        code, _, err = run_cli("status", "--run-dir", str(self.tmp / "nowhere"))
        self.assertEqual(code, 2)

    def test_help_shows_loop_and_every_command(self):
        parser = bse.build_parser()
        text = parser.format_help()
        self.assertIn("CHARTER -> PLAN -> [ BRIEF -> EXECUTE -> VERIFY -> RECORD ] * N -> STITCH", text)
        for cmd in ("init", "plan", "status", "next", "brief", "check", "review", "record", "carry", "stitch", "audit"):
            self.assertIn(cmd, text)
        code, out, _ = run_cli("record", "--help") if False else (0, "", "")
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                bse.main(["record", "--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_global_flags_accepted_before_the_command(self):
        code, out, _ = run_cli("--json", "--run-dir", str(self.rd), "next")
        self.assertEqual(json.loads(out), {"unit": "B001", "remaining": 3})
        code, _, err = run_cli("--run-dir", str(self.tmp / "nowhere"), "next")
        self.assertEqual(code, 2)

    def test_absolute_artifact_path_is_stored_relative(self):
        art = self.good_artifact("B001")
        code, out, _ = self.cli("check", "B001", "--artifact", str(art.resolve()))
        self.assertEqual(code, 0, out)
        self.assertEqual(self.ledger()["units"]["B001"]["verify"]["artifact"], "batches/B001.md")

    def test_json_error_output(self):
        code, out, _ = self.cli("brief", "B042", "--json")
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)["code"], 2)


# ---------------------------------------------------------------------------
# review defects 1-7 (regression tests)
# ---------------------------------------------------------------------------

class TestStitchPartialUniform(RunCase):
    """Defect 1: ANY incomplete unit (including [P]) needs --partial."""
    units = [unit("B001", "Alpha"), unit("B002", "Beta", deps="B001"),
             unit("B003", "Gamma", parallel=True, produces="Other")]

    def test_incomplete_parallel_unit_refused_without_partial(self):
        self.complete("B001"); self.complete("B002")
        code, _, err = self.cli("stitch")
        self.assertEqual(code, 1)
        self.assertIn("B003", err)
        self.assertIn("--partial", err)
        self.assertFalse((self.rd / "draft.md").exists())

    def test_partial_lists_missing_and_warns(self):
        self.complete("B001"); self.complete("B002")
        code, out, err = self.cli("stitch", "--partial")
        self.assertEqual(code, 0)
        self.assertIn("<!-- MISSING B003 -->", (self.rd / "draft.md").read_text(encoding="utf-8"))
        self.assertIn("WARNING: PARTIAL", out + err)
        report = (self.rd / "reports" / "stitch.md").read_text(encoding="utf-8")
        self.assertIn("## Missing units (1)", report)
        self.assertRegex(report, r"- B003: status=pending \[P\]")
        ev = self.ledger()["events"][-1]
        self.assertEqual((ev["kind"], ev["missing"], ev["partial"]), ("seam", ["B003"], True))
        self.assertIn("PARTIAL missing=1 (B003)", (self.rd / "LEDGER.md").read_text(encoding="utf-8"))
        code, out, _ = self.cli("stitch", "--partial", "--json")
        self.assertEqual(json.loads(out)["missing"], ["B003"])

    def test_done_unit_with_deleted_artifact_counts_as_incomplete(self):
        for uid in ("B001", "B002", "B003"):
            self.complete(uid)
        (self.rd / "batches" / "B002.md").unlink()
        code, _, err = self.cli("stitch")
        self.assertEqual(code, 1)
        self.assertIn("B002", err)


class TestNoPlaceholdersAngleRule(unittest.TestCase):
    """Defect 2: angle-bracket rule flags placeholders, not HTML or autolinks."""

    def v(self, text):
        return bse.VERIFIERS["no_placeholders"](text, "", {"unit": None})

    def test_html_tags_and_autolinks_pass(self):
        for ok in ("line<br>break", "line<br/>break", "H<sub>2</sub>O", "E = mc<sup>2</sup>",
                   "see <https://example.com> now", "mail <user@example.com> now", "</div>",
                   '<a href="https://x.y">x</a>', "<img src=x.png>", "<details><summary>More</summary>",
                   "if x < 5 and y > 3 then"):
                passed, detail = self.v(f"prose\n{ok}\n")
                self.assertTrue(passed, f"{ok!r} -> {detail}")

    def test_placeholder_spans_fail(self):
        for bad in ("<insert name>", "<your title>", "<name>", "<Title>", "<DATE>", "<tbd>", "<TODO>",
                    "<xxx>", "<placeholder>", "<description>", "<fill me>", "<company name here>"):
            passed, detail = self.v(f"prose\nthe {bad} goes here\n")
            self.assertFalse(passed, bad)
            self.assertIn("<angle placeholder>", detail)
            self.assertIn("L2", detail)

    def test_other_placeholder_patterns_still_flagged(self):
        for bad in ("TBD", "TODO", "[insert name]", "Lorem ipsum", "and so on etc.", "as described", "XXX"):
            self.assertFalse(self.v(f"line one\n{bad}\n")[0], bad)
        self.assertTrue(self.v("Clean prose. `<insert x>` in code is fine etc. not final\n")[0])
        self.assertTrue(self.v("<!-- <insert x> in a comment is fine -->\nclean\n")[0])


class TestVerifierBaseAtValidate(RunCase):
    """Defect 3: an implicit budget base must match the verifier's denomination."""
    total = "200w, 3files"
    units = [unit("B001", "Alpha"), unit("B002", "Beta", deps="B001"),
             unit("B003", "Gamma", budget="3files", deps="B002",
                  verify=("  - mechanical: word_count within 15%", "  - mechanical: no_placeholders"))]

    def test_implicit_base_with_mismatched_denomination_fails_validation(self):
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"B003 verifier 'word_count within 15%' .*budget is in 'files' \(3files\) and word_count counts 'w'")
        for spec in ("word_count", "word_count within 15% of budget", "slide_count within 10%", "item_count"):
            u = self.units[:]
            u[2] = unit("B003", "Gamma", budget="3files", deps="B002",
                        verify=(f"  - mechanical: {spec}", "  - mechanical: no_placeholders"))
            self.write_plan(u)
            code, out, _ = self.cli("plan", "--validate")
            self.assertEqual(code, 1, spec)
            self.assertIn(f"verifier '{spec}'", out)

    def test_explicit_literal_base_is_legal(self):
        u = self.units[:]
        u[2] = unit("B003", "Gamma", budget="3files", deps="B002",
                    verify=("  - mechanical: word_count within 15% of 100", "  - mechanical: no_placeholders"))
        self.write_plan(u)
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 0, out)
        u[2] = unit("B003", "Gamma", budget="3files", deps="B002",
                    verify=("  - mechanical: word_count >= 50", "  - mechanical: file_exists CHARTER.md"))
        self.write_plan(u)
        self.assertEqual(self.cli("plan", "--validate")[0], 0)

    def test_matching_denomination_is_legal(self):
        u = self.units[:]
        u[2] = unit("B003", "Gamma", budget="3files", deps="B002", verify=("  - mechanical: no_placeholders",))
        u[0] = unit("B001", "Alpha", verify=("  - mechanical: word_count within 15%",))
        self.write_plan(u)
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 0, out)


class TestCitationTagsSentenceAware(unittest.TestCase):
    """Defect 4: citation_tags evaluates sentences, joining hard-wrapped lines."""

    def v(self, text):
        return bse.VERIFIERS["citation_tags"](text, "", {"unit": None})

    def test_hard_wrapped_sentence_with_tag_on_next_line_passes(self):
        wrapped = ("Deployment of distributed resources grew by 12% across the\n"
                   "region between 2023 and 2025, according to the state survey [S1].\n"
                   "A second, untagged sentence has no numbers in it at all.\n")
        self.assertFalse(bse.SOURCE_TAG_RE.search(wrapped.splitlines()[0]))   # would fail line-by-line
        passed, detail = self.v(wrapped)
        self.assertTrue(passed, detail)

    def test_genuinely_untagged_sentence_still_fails(self):
        text = ("Deployment grew by 12% across the\n"
                "region between 2023 and 2025.\n"
                "This sentence is fine [S2].\n")
        passed, detail = self.v(text)
        self.assertFalse(passed)
        self.assertIn("L1-2", detail)

    def test_tag_after_period_covers_only_its_own_sentence(self):
        passed, detail = self.v("Growth was 12%. [S1] The next has 2025 in it.\n")
        self.assertFalse(passed)
        self.assertIn("L1", detail)
        self.assertTrue(self.v("Growth was 12%. [S1] Next has 2025 [S2].\n")[0])

    def test_headings_fences_and_list_items_are_handled(self):
        self.assertTrue(self.v("## 2025 review\n\n```\nvalue = 12%\n```\n\nText with 3 items [S1].\n")[0])
        passed, detail = self.v("- first bullet 12% [S1]\n- second bullet 2025\n")
        self.assertFalse(passed)
        self.assertIn("L2", detail)
        passed, detail = self.v("- bullet 12% wraps onto the\n  next line here [S1]\n")
        self.assertTrue(passed, detail)


class TestRulingUnit(RunCase):
    """Defect 5: record RULING --unit ID."""

    def test_ruling_with_unit_is_linked_in_both_ledgers(self):
        code, out, _ = self.cli("record", "RULING", "--unit", "B002", "--note", "use 2025 figures")
        self.assertEqual(code, 0)
        self.assertIn("for B002", out)
        line = (self.rd / "LEDGER.md").read_text(encoding="utf-8").splitlines()[-1]
        self.assertRegex(line, r"^RULING\s+\d{4}-\S+\s+unit=B002\s+use 2025 figures$")
        ev = self.ledger()["events"][-1]
        self.assertEqual((ev["kind"], ev["unit"], ev["note"]), ("ruling", "B002", "use 2025 figures"))
        self.assertEqual(self.cli("audit")[0], 0)

    def test_ruling_unknown_unit_is_usage_error(self):
        code, _, err = self.cli("record", "RULING", "--unit", "B042", "--note", "x")
        self.assertEqual(code, 2)
        self.assertIn("unknown unit B042", err)
        self.assertEqual(self.ledger()["events"], [])

    def test_unitless_ruling_still_legal_and_unit_flag_rejected_elsewhere(self):
        code, _, _ = self.cli("record", "RULING", "--note", "global ruling")
        self.assertEqual(code, 0)
        ev = self.ledger()["events"][-1]
        self.assertEqual((ev["kind"], ev["unit"]), ("ruling", None))
        self.assertNotIn("unit=", (self.rd / "LEDGER.md").read_text(encoding="utf-8").splitlines()[-1])
        code, _, err = self.cli("record", "B001", "--status", "fix", "--unit", "B001")
        self.assertEqual(code, 2)


class TestUnitHistory(RunCase):
    """Defect 6: per-unit history in ledger.json; audit surfaces unruled blocks."""

    def audit(self):
        code, out, _ = self.cli("audit", "--json")
        return code, json.loads(out)

    def test_history_records_every_status_change(self):
        self.cli("record", "B001", "--status", "fix", "--note", "tighten")
        self.cli("record", "B001", "--status", "blocked", "--note", "source contradicts NN-1")
        self.complete("B001")
        st = self.ledger()["units"]["B001"]
        self.assertEqual(st["status"], "done")
        self.assertEqual([h["status"] for h in st["history"]], ["fix", "blocked", "done"])
        self.assertEqual(st["history"][1]["note"], "source contradicts NN-1")
        self.assertEqual(st["history"][0]["note"], "tighten")
        for h in st["history"]:
            self.assertRegex(h["timestamp"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_audit_reports_block_resolved_without_ruling_as_info(self):
        self.cli("record", "B001", "--status", "blocked", "--note", "needs ruling")
        self.complete("B001")
        code, data = self.audit()
        self.assertEqual(code, 0)                       # informational, not a failure
        self.assertTrue(data["ok"])
        f = [f for f in data["findings"] if f["code"] == "BLOCK_WITHOUT_RULING"]
        self.assertEqual(len(f), 1)
        self.assertEqual((f[0]["unit"], f[0]["level"]), ("B001", "info"))
        self.assertIn("needs ruling", f[0]["message"])
        code, out, _ = self.cli("audit")
        self.assertIn("clean (1 informational)", out)
        self.assertIn("info:", out)

    def test_audit_silent_when_ruling_recorded(self):
        self.cli("record", "B001", "--status", "blocked", "--note", "needs ruling")
        self.cli("record", "RULING", "--unit", "B001", "--note", "use 2025 figures")
        self.complete("B001")
        code, data = self.audit()
        self.assertEqual([f["code"] for f in data["findings"]], [])
        # a unit-less ruling between block and resolution also counts
        self.cli("record", "B002", "--status", "blocked", "--note", "x")
        self.cli("record", "RULING", "--note", "global")
        self.complete("B002")
        self.assertEqual([f["code"] for f in self.audit()[1]["findings"]], [])
        # a ruling for a different unit does not
        self.cli("record", "B003", "--status", "blocked", "--note", "y")
        self.cli("record", "RULING", "--unit", "B001", "--note", "unrelated")
        self.complete("B003")
        findings = self.audit()[1]["findings"]
        self.assertEqual([f["unit"] for f in findings if f["unit"]], ["B003"])
        # every unit is now done and no final.md exists: the seam-pass gate fires (run-level, not unit-level)
        self.assertEqual([f["code"] for f in findings if not f["unit"]], ["SEAM_PASS_MISSING"])

    def test_old_ledger_without_history_still_loads(self):
        data = self.ledger()
        data["units"]["B001"] = {"status": "pending", "attempts": 0, "fix_rounds": 0, "verify": None}
        (self.rd / "ledger.json").write_text(json.dumps(data), encoding="utf-8")
        self.complete("B001")
        self.assertEqual([h["status"] for h in self.ledger()["units"]["B001"]["history"]], ["done"])
        self.assertEqual(self.audit()[0], 0)


class TestMultiDenominationBudgets(RunCase):
    """Defect 7: per-denomination charter totals and drift."""
    units = [unit("B001", "Alpha"), unit("B002", "Beta", deps="B001"),
             unit("B003", "Deck", type="transform", budget="5slides", deps="B002",
                  verify=("  - mechanical: slide_count within 20%",))]

    def test_charter_totals_parse_several_forms(self):
        for line in ("20000w, 40slides", "20000 words + 40 slides", "20,000w; 40slides", "~20000w and 40 slides"):
            self.write_charter(total=line)
            self.assertEqual(self.run.charter_totals(), [(20000, "w"), (40, "slides")], line)
        self.write_charter(total="~20,000 words (about 40 pages)")
        self.assertEqual(self.run.charter_totals(), [(20000, "w")])
        self.assertEqual(self.run.charter_total(), (20000, "w"))

    def test_drift_is_checked_per_denomination(self):
        self.write_charter(total="200w, 10slides")
        code, out, _ = self.cli("plan", "--validate", "--json")
        data = json.loads(out)
        self.assertFalse(data["ok"])
        self.assertEqual(data["errors"], ["budget sum 5slides drifts 50% from charter total 10slides (limit ±20%)"])
        self.assertEqual(data["charter_totals"], ["200w", "10slides"])
        self.assertEqual(data["budget_sums"], {"w": 200, "slides": 5})
        self.write_charter(total="200w, 5slides")
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 0, out)
        self.write_charter(total="100w, 5slides")
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 1)
        self.assertIn("budget sum 200w drifts 100%", out)
        code, out, _ = self.cli("audit", "--json")
        self.assertEqual([f["code"] for f in json.loads(out)["findings"]], ["PLAN_BUDGET_DRIFT"])

    def test_undeclared_denomination_is_informational(self):
        self.write_charter(total="200w")
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 0, out)
        self.assertIn("warning: budget denomination 'slides' (sum 5slides across B003) has no charter total", out)
        code, out, _ = self.cli("plan", "--validate", "--json")
        rows = {r["unit"]: r for r in json.loads(out)["budget_drift"]}
        self.assertIsNone(rows["slides"]["total"])
        self.assertEqual(rows["w"]["drift_pct"], 0)
        code, out, _ = self.cli("audit", "--json")
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertTrue(data["ok"])
        self.assertEqual([(f["code"], f["level"]) for f in data["findings"]], [("PLAN_BUDGET_UNCHECKED", "info")])
        self.assertIn("5slides (B003)", data["findings"][0]["message"])


# ---------------------------------------------------------------------------
# ship-blocking defects C1-C4, I1, I2, I7, I10, M8 (regression tests)
# ---------------------------------------------------------------------------

JUDGED = ("  - mechanical: word_count within 15% of 100", "  - mechanical: no_placeholders",
          "  - source: every claim traces to [S1]", "  - charter: acceptance criteria 1")


class TestReviewGate(RunCase):
    """C1: judgement predicates are a gate — `review` records the verdict keyed
    to the artifact sha; `record done` refuses without a matching pass."""
    units = [unit("B001", "Alpha", verify=JUDGED), unit("B002", "Beta", deps="B001"),
             unit("B003", "Gamma", deps="B002")]

    def report(self, name="B001-review.md", text="# Review B001\n\nverdict: pass\n"):
        p = self.rd / "reports" / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_review_is_usage_error_without_judgement_predicates(self):
        self.good_artifact("B002")
        code, _, err = self.cli("review", "B002", "--verdict", "pass", "--report", str(self.report()))
        self.assertEqual(code, 2)
        self.assertIn("declares no judgement predicates", err)
        self.assertEqual(self.ledger()["events"], [])

    def test_review_requires_existing_report_and_artifact(self):
        self.good_artifact("B001")
        code, _, err = self.cli("review", "B001", "--verdict", "pass", "--report", str(self.rd / "missing.md"))
        self.assertEqual(code, 2)
        self.assertIn("--report", err)
        (self.rd / "batches" / "B001.md").unlink()
        code, _, err = self.cli("review", "B001", "--verdict", "pass", "--report", str(self.report()))
        self.assertEqual(code, 1)
        self.assertIn("artifact missing", err)

    def test_review_pass_is_stored_keyed_to_sha_in_both_ledgers(self):
        art = self.good_artifact("B001")
        self.report()
        code, out, _ = self.cli("review", "B001", "--verdict", "pass", "--report", "reports/B001-review.md",
                                "--note", "reviewer: R2")
        self.assertEqual(code, 0, out)
        self.assertIn("B001 review PASS (2 judgement predicates", out)
        st = self.ledger()["units"]["B001"]
        self.assertEqual(len(st["reviews"]), 1)
        r = st["reviews"][0]
        self.assertEqual((r["verdict"], r["sha256"], r["report"], r["note"]),
                         ("pass", bse.sha256_of(art), "reports/B001-review.md", "reviewer: R2"))
        self.assertEqual(r["predicates"], ["source: every claim traces to [S1]", "charter: acceptance criteria 1"])
        line = (self.rd / "LEDGER.md").read_text(encoding="utf-8").splitlines()[-1]
        self.assertRegex(line, r"^B001 review pass\s+\d{4}-\S+\s+predicates=2\s+report=reports/B001-review\.md\s+sha=[0-9a-f]{7}\s+note=reviewer: R2$")
        ev = self.ledger()["events"][-1]
        self.assertEqual((ev["kind"], ev["unit"], ev["verdict"]), ("review", "B001", "pass"))

    def test_record_done_refused_without_review_then_allowed_after_pass(self):
        self.good_artifact("B001")
        code, out, _ = self.cli("check", "B001")
        self.assertEqual(code, 0, out)                     # mechanical half passes
        code, _, err = self.cli("record", "B001", "--status", "done")
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", err)
        self.assertIn("2 judgement predicate(s) but no review recorded", err)
        self.assertEqual(self.ledger()["units"]["B001"]["status"], "pending")
        self.report()
        self.cli("review", "B001", "--verdict", "pass", "--report", "reports/B001-review.md")
        code, out, _ = self.cli("record", "B001", "--status", "done")
        self.assertEqual(code, 0, out)
        self.assertIn("review=pass", out)
        line = [l for l in (self.rd / "LEDGER.md").read_text(encoding="utf-8").splitlines() if l.startswith("B001 done")][0]
        self.assertRegex(line, r"verify=pass\(2/2\)\s+review=pass\s+sha=[0-9a-f]{7}$")
        self.assertEqual(self.ledger()["events"][-1]["review"], "pass")

    def test_record_done_refused_on_fail_verdict(self):
        self.good_artifact("B001")
        self.cli("check", "B001")
        self.report()
        code, out, _ = self.cli("review", "B001", "--verdict", "fail", "--report", "reports/B001-review.md")
        self.assertEqual(code, 1)                          # like `check`, a FAIL verdict exits 1
        self.assertIn("review FAIL", out)
        code, _, err = self.cli("record", "B001", "--status", "done")
        self.assertEqual(code, 1)
        self.assertIn("latest review of this artifact is a FAIL", err)
        # a later pass on the same artifact wins
        self.cli("review", "B001", "--verdict", "pass", "--report", "reports/B001-review.md")
        self.assertEqual(self.cli("record", "B001", "--status", "done")[0], 0)

    def test_artifact_edit_after_review_invalidates_it(self):
        self.good_artifact("B001")
        self.cli("check", "B001")
        self.report()
        self.cli("review", "B001", "--verdict", "pass", "--report", "reports/B001-review.md")
        self.good_artifact("B001", seed="edited")
        self.cli("check", "B001")                          # mechanical half is current again
        code, _, err = self.cli("record", "B001", "--status", "done")
        self.assertEqual(code, 1)
        self.assertIn("stored review(s) are for an earlier artifact (sha mismatch)", err)
        code, out, _ = self.cli("status", "--json")
        self.assertEqual(json.loads(out)["units"][0]["review"], "stale")
        self.cli("review", "B001", "--verdict", "pass", "--report", "reports/B001-review.md")
        self.assertEqual(self.cli("record", "B001", "--status", "done")[0], 0)

    def test_force_overrides_missing_review_and_stamps_forced(self):
        self.good_artifact("B001")
        self.cli("check", "B001")
        code, out, _ = self.cli("record", "B001", "--status", "done", "--force")
        self.assertEqual(code, 0, out)
        line = [l for l in (self.rd / "LEDGER.md").read_text(encoding="utf-8").splitlines() if l.startswith("B001 done")][0]
        self.assertIn("review=none", line)
        self.assertIn("FORCED", line)
        self.assertIn("verify=pass(2/2)", line)            # the mechanical half really did pass
        code, out, _ = self.cli("audit", "--json")
        self.assertIn("DONE_WITHOUT_REVIEW", {f["code"] for f in json.loads(out)["findings"]})

    def test_check_summary_distinguishes_the_halves(self):
        self.good_artifact("B001")
        code, out, _ = self.cli("check", "B001")
        self.assertIn("B001 check PASS (2/2 mechanical; 2 judgement predicates pending review)", out)
        report = (self.rd / "reports" / "B001.md").read_text(encoding="utf-8")
        self.assertIn("- result: PASS (2/2 mechanical; 2 judgement predicates pending review)", report)
        self.assertIn("bse.py review B001 --verdict pass|fail", report)
        self.report()
        self.cli("review", "B001", "--verdict", "pass", "--report", "reports/B001-review.md")
        code, out, _ = self.cli("check", "B001", "--json")
        data = json.loads(out)
        self.assertEqual((data["review"], data["ok"]), ("pass", True))
        code, out, _ = self.cli("check", "B001")
        self.assertIn("(2/2 mechanical; 2 judgement predicates reviewed: pass)", out)
        code, out, _ = self.cli("check", "B002")
        self.good_artifact("B002")
        code, out, _ = self.cli("check", "B002")
        self.assertIn("B002 check PASS (2/2 mechanical)", out)  # no judgement half for this unit

    def test_status_shows_review_column(self):
        self.good_artifact("B001")
        self.cli("check", "B001")
        code, out, _ = self.cli("status")
        self.assertIn("review", out.splitlines()[1])
        row = [l for l in out.splitlines() if l.startswith("B001")][0]
        self.assertIn("pending", row)
        self.assertIn("1 unit(s) awaiting review", out)
        code, out, _ = self.cli("status", "--json")
        data = json.loads(out)
        self.assertEqual([u["review"] for u in data["units"]], ["pending", "-", "-"])
        self.assertEqual(data["awaiting_review"], 1)
        self.report()
        self.cli("review", "B001", "--verdict", "pass", "--report", "reports/B001-review.md")
        code, out, _ = self.cli("status", "--json")
        self.assertEqual(json.loads(out)["units"][0]["review"], "pass")

    def test_audit_catches_done_without_matching_review(self):
        self.good_artifact("B001")
        self.cli("check", "B001")
        self.report()
        self.cli("review", "B001", "--verdict", "pass", "--report", "reports/B001-review.md")
        self.cli("record", "B001", "--status", "done")
        code, out, _ = self.cli("audit", "--json")
        self.assertEqual(code, 0, out)
        data = self.ledger()
        data["units"]["B001"]["reviews"][0]["verdict"] = "fail"    # tampered
        (self.rd / "ledger.json").write_text(json.dumps(data), encoding="utf-8")
        code, out, _ = self.cli("audit", "--json")
        self.assertIn("DONE_WITH_FAILING_REVIEW", {f["code"] for f in json.loads(out)["findings"]})
        data["units"]["B001"]["reviews"] = []
        (self.rd / "ledger.json").write_text(json.dumps(data), encoding="utf-8")
        code, out, _ = self.cli("audit", "--json")
        self.assertEqual(code, 1)
        self.assertIn("DONE_WITHOUT_REVIEW", {f["code"] for f in json.loads(out)["findings"]})


class TestSeamPassFiles(RunCase):
    """C2/C3: draft.md is stitch output; front-/back-matter.md and final.md are
    written by hand in the seam pass; the tool never writes final.md."""

    def finish_all(self):
        for uid in ("B001", "B002", "B003"):
            self.complete(uid)

    def test_init_scaffolds_commented_front_and_back_matter(self):
        for name in ("front-matter.md", "back-matter.md"):
            text = (self.rd / name).read_text(encoding="utf-8")
            self.assertTrue(text.startswith("<!--"), name)
            self.assertEqual(bse.count_words(text), 0, name)      # comment only: no prose
            self.assertIn("seam pass", text)
        self.assertFalse((self.rd / "final.md").exists())

    def test_stitch_includes_matter_by_default_when_it_has_prose(self):
        self.finish_all()
        (self.rd / "front-matter.md").write_text("# Introduction\n\nThe opening.\n", encoding="utf-8")
        (self.rd / "back-matter.md").write_text("# Conclusion\n\nThe close.\n", encoding="utf-8")
        code, out, err = self.cli("stitch", "--json")
        self.assertEqual(code, 0, out + err)
        draft = (self.rd / "draft.md").read_text(encoding="utf-8")
        self.assertTrue(draft.startswith("# Introduction"))
        self.assertTrue(draft.rstrip().endswith("The close."))
        self.assertLess(draft.index("# B001"), draft.index("# Conclusion"))
        data = json.loads(out)
        self.assertEqual((data["front_matter"], data["back_matter"], data["seam_pass_pending"]), (True, True, False))
        self.assertNotIn("seam pass has not run", err)
        self.assertIn("- front-matter.md: included", (self.rd / "reports" / "stitch.md").read_text(encoding="utf-8"))

    def test_stitch_skips_commented_scaffold_and_reminds_when_all_done(self):
        self.finish_all()
        code, out, err = self.cli("stitch")
        self.assertEqual(code, 0)
        draft = (self.rd / "draft.md").read_text(encoding="utf-8")
        self.assertNotIn("Written BY HAND", draft)                  # scaffold comment not pasted in
        self.assertIn("FRONT MATTER: front-matter.md not yet written", draft)
        self.assertIn("seam pass has not run", err)
        self.assertIn("front-matter.md and back-matter.md", err)
        # a partial stitch is not nagged about the seam pass
        self.write_plan(self.units)
        (self.rd / "batches" / "B003.md").unlink()
        code, out, err = self.cli("stitch", "--partial")
        self.assertNotIn("seam pass has not run", err)

    def test_no_front_matter_flag_and_deprecated_alias(self):
        self.finish_all()
        (self.rd / "front-matter.md").write_text("# Introduction\n\nThe opening.\n", encoding="utf-8")
        code, out, err = self.cli("stitch", "--no-front-matter")
        self.assertEqual(code, 0)
        draft = (self.rd / "draft.md").read_text(encoding="utf-8")
        self.assertNotIn("Introduction", draft)
        self.assertNotIn("FRONT MATTER", draft)
        code, out, err = self.cli("stitch", "--include-front-matter")
        self.assertEqual(code, 0)
        self.assertIn("deprecated", err)
        self.assertTrue((self.rd / "draft.md").read_text(encoding="utf-8").startswith("# Introduction"))
        self.assertIn("DEPRECATED", subcommand_help("stitch"))
        self.assertIn("--no-front-matter", subcommand_help("stitch"))

    def test_stitch_refuses_to_write_final_md(self):
        self.finish_all()
        code, _, err = self.cli("stitch", "--out", str(self.rd / "final.md"))
        self.assertEqual(code, 2)
        self.assertIn("never generated by stitch", err)
        self.assertFalse((self.rd / "final.md").exists())

    def test_audit_seam_pass_missing_levels(self):
        self.complete("B001")
        code, out, _ = self.cli("audit", "--json")
        self.assertEqual([f["code"] for f in json.loads(out)["findings"]], [])   # nothing stitched yet: silent
        self.cli("stitch", "--partial")
        code, out, _ = self.cli("audit", "--json")
        f = [f for f in json.loads(out)["findings"] if f["code"] == "SEAM_PASS_MISSING"]
        self.assertEqual((code, f[0]["level"]), (0, "info"))
        self.complete("B002"); self.complete("B003")
        code, out, _ = self.cli("audit", "--json")
        f = [f for f in json.loads(out)["findings"] if f["code"] == "SEAM_PASS_MISSING"]
        self.assertEqual((code, f[0]["level"]), (1, "error"))
        self.assertIn("final.md", f[0]["message"])

    def test_audit_final_stale_and_clean_seam_pass(self):
        self.finish_all()
        self.cli("stitch")
        (self.rd / "front-matter.md").write_text("# Introduction\n\nThe opening.\n", encoding="utf-8")
        (self.rd / "back-matter.md").write_text("# Conclusion\n\nThe close.\n", encoding="utf-8")
        (self.rd / "final.md").write_text("# Final\n\nseam-passed by hand\n", encoding="utf-8")
        t = (self.rd / "draft.md").stat().st_mtime
        os.utime(self.rd / "final.md", (t + 5, t + 5))
        code, out, _ = self.cli("audit", "--json")
        self.assertEqual((code, json.loads(out)["findings"]), (0, []))
        os.utime(self.rd / "final.md", (t - 5, t - 5))                # draft re-stitched after the seam pass
        code, out, _ = self.cli("audit", "--json")
        f = json.loads(out)["findings"]
        self.assertEqual([(x["code"], x["level"]) for x in f], [("FINAL_STALE", "error")])
        self.assertEqual(code, 1)

    def test_tool_never_writes_final_md(self):
        self.finish_all()
        self.cli("stitch"); self.cli("stitch", "--partial"); self.cli("audit"); self.cli("status")
        self.assertFalse((self.rd / "final.md").exists())
        self.assertNotIn("final_path,", BSE_PATH.read_text(encoding="utf-8").replace("final_path.exists", "").replace("final_path.stat", ""))
        src = BSE_PATH.read_text(encoding="utf-8")
        self.assertNotRegex(src, r"atomic_write\(\s*run\.final_path")


class TestCarryStale(RunCase):
    """C4: an untouched baton after two done units is an audit error."""

    def test_audit_carry_stale_after_second_done_unit(self):
        self.complete("B001", carry=False)
        code, out, _ = self.cli("audit", "--json")
        self.assertNotIn("CARRY_STALE", {f["code"] for f in json.loads(out)["findings"]})
        self.complete("B002", carry=False)
        code, out, _ = self.cli("audit", "--json")
        f = [f for f in json.loads(out)["findings"] if f["code"] == "CARRY_STALE"]
        self.assertEqual((code, f[0]["level"]), (1, "error"))
        self.assertIn("2 units done", f[0]["message"])
        # an empty carry is just as stale; a written one is not
        (self.rd / "carry.md").write_text("\n\n", encoding="utf-8")
        code, out, _ = self.cli("audit", "--json")
        self.assertIn("CARRY_STALE", {f["code"] for f in json.loads(out)["findings"]})
        self.cli("carry", "--set", str(self.carry_file("B002")))
        code, out, _ = self.cli("audit", "--json")
        self.assertNotIn("CARRY_STALE", {f["code"] for f in json.loads(out)["findings"]})

    def test_carry_check_exit_codes(self):
        code, out, _ = self.cli("carry", "--check")
        self.assertEqual(code, 0)
        self.assertIn("still the init scaffold", out)
        self.complete("B001", carry=False); self.complete("B002", carry=False)
        code, out, _ = self.cli("carry", "--check")
        self.assertEqual(code, 1)
        self.assertIn("CARRY STALE", out)
        code, out, _ = self.cli("carry", "--check", "--json")
        self.assertEqual(json.loads(out)["stale"], True)
        # a CRLF checkout of the scaffold is still the scaffold
        (self.rd / "carry.md").write_bytes(bse.CARRY_TEMPLATE.replace("\n", "\r\n").encode("utf-8"))
        self.assertEqual(self.cli("carry", "--check")[0], 1)
        self.cli("carry", "--set", str(self.carry_file("B002")))
        code, out, _ = self.cli("carry", "--check")
        self.assertEqual((code, "ok" in out), (0, True))


class TestPredicateAdequacy(RunCase):
    """I1: plan --validate enforces predicate adequacy, with visible waivers."""

    def errors(self):
        code, out, _ = self.cli("plan", "--validate", "--json")
        data = json.loads(out)
        return code, data["errors"], data

    def test_word_budget_requires_word_count(self):
        u = THREE[:]
        u[1] = unit("B002", "Beta", deps="B001", verify=("  - mechanical: no_placeholders",))
        self.write_plan(u)
        code, errs, _ = self.errors()
        self.assertEqual(code, 1)
        self.assertEqual(len(errs), 1)
        self.assertRegex(errs[0], r"^L\d+: B002 \[word_count\] budget is in words \(100w\) but no word_count verifier is declared: add '- mechanical: word_count within 15% of budget' \(or add 'waive: word_count — <reason>'")
        u[1] = unit("B002", "Beta", deps="B001", budget="10items", verify=("  - mechanical: item_count within 15% of budget",))
        self.write_charter(total="200w, 10items")
        self.write_plan(u)
        self.assertEqual(self.errors()[0], 0)               # items budget: no word_count needed

    def test_source_inputs_require_citation_tags_or_source_predicate(self):
        u = THREE[:]
        u[1] = unit("B002", "Beta", deps="B001", inputs=("  - CHARTER.md", "  - notes/source.md#L1-9"))
        self.write_plan(u)
        code, errs, _ = self.errors()
        self.assertEqual(code, 1)
        self.assertRegex(errs[0], r"B002 \[citation_tags\] reads 1 input\(s\) beyond the charter \(notes/source\.md#L1-9\) but declares neither citation_tags nor a source predicate: add '- mechanical: citation_tags' or '- source: ")
        for fix in (("  - mechanical: word_count within 15% of 100", "  - mechanical: citation_tags"),
                    ("  - mechanical: word_count within 15% of 100", "  - source: every figure traces to [S1]")):
            u[1] = unit("B002", "Beta", deps="B001", inputs=("  - CHARTER.md", "  - notes/source.md"), verify=fix)
            self.write_plan(u)
            self.assertEqual(self.errors()[0], 0, fix)
        # the run's own files are not sources: CHARTER.md, carry.md, batches/<ID>.md
        u[1] = unit("B002", "Beta", deps="B001", inputs=("  - ./CHARTER.md", "  - carry.md", "  - batches/B001.md#L1-40"))
        self.write_plan(u)
        self.assertEqual(self.errors()[0], 0)

    def test_nonfinal_compose_requires_no_conclusion(self):
        u = [unit("B001", "Alpha", waive=""), unit("B002", "Beta", deps="B001", waive=""),
             unit("B003", "Gamma", deps="B002", waive="")]
        self.write_plan(u)
        code, errs, _ = self.errors()
        self.assertEqual(code, 1)
        self.assertEqual(len(errs), 2)                      # B003 is the final unit: exempt
        self.assertRegex(errs[0], r"^L\d+: B001 \[no_conclusion\] non-final compose unit does not declare no_conclusion: add '- mechanical: no_conclusion'")
        self.assertIn("B002 [no_conclusion]", errs[1])
        fixed = ("  - mechanical: word_count within 15% of 100", "  - mechanical: no_conclusion")
        u = [unit("B001", "Alpha", waive="", verify=fixed), unit("B002", "Beta", deps="B001", waive="", verify=fixed),
             unit("B003", "Gamma", deps="B002", waive="")]
        self.write_plan(u)
        self.assertEqual(self.errors()[0], 0)
        u[0] = unit("B001", "Alpha", type="revise", waive="")   # rule is compose-only
        self.write_plan(u)
        self.assertEqual(self.errors()[0], 0)

    def test_waivers_opt_out_and_are_listed(self):
        u = THREE[:]
        u[1] = unit("B002", "Beta", deps="B001", inputs=("  - CHARTER.md", "  - notes/source.md"),
                    verify=("  - mechanical: no_placeholders",),
                    waive="waive:\n  - word_count — budget is a ceiling, not a target\n  - citation_tags: source has no figures\n  - no_conclusion — fragment")
        self.write_plan(u)
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 0, out)
        self.assertIn("waiver: B002 word_count — budget is a ceiling, not a target", out)
        self.assertIn("waiver: B002 citation_tags — source has no figures", out)
        code, errs, data = self.errors()
        self.assertEqual({(w["unit"], w["rule"]) for w in data["waivers"]},
                         {("B001", "no_conclusion"), ("B002", "word_count"), ("B002", "citation_tags"),
                          ("B002", "no_conclusion"), ("B003", "no_conclusion")})
        # malformed or unknown waivers are errors, not silent
        u[1] = unit("B002", "Beta", deps="B001", waive="waive: word_count")
        self.write_plan(u)
        code, errs, _ = self.errors()
        self.assertEqual(code, 1)
        self.assertTrue(any("must look like 'waive: word_count — <reason>'" in e for e in errs), errs)
        u[1] = unit("B002", "Beta", deps="B001", waive="waive: budget_drift — because")
        self.write_plan(u)
        code, errs, _ = self.errors()
        self.assertTrue(any("unknown rule 'budget_drift'" in e for e in errs), errs)


class TestFixRoundsFromCheck(RunCase):
    """I2: `check` itself counts a fix round when re-run on a changed artifact
    after a failing check; `record --status fix` never double-counts."""

    def fix_rounds(self):
        return self.ledger()["units"]["B001"].get("fix_rounds", 0)

    def test_changed_artifact_after_failing_check_counts_a_round(self):
        self.artifact("B001", "# B001\n\nshort TBD\n")
        self.assertEqual(self.cli("check", "B001")[0], 1)
        self.assertEqual(self.fix_rounds(), 0)
        self.good_artifact("B001")
        code, out, _ = self.cli("check", "B001", "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual((data["fix_round"], data["fix_rounds"]), (1, 1))
        st = self.ledger()["units"]["B001"]
        self.assertEqual((st["fix_rounds"], st["attempts"]), (1, 2))
        line = [l for l in (self.rd / "LEDGER.md").read_text(encoding="utf-8").splitlines() if l.startswith("B001 fix")][0]
        self.assertRegex(line, r"^B001 fix 1/3\s+\d{4}-\S+\s+verify=fail\(2/2\): .*auto=check")
        ev = [e for e in self.ledger()["events"] if e.get("kind") == "fix"][0]
        self.assertEqual((ev["round"], ev["auto"], ev["unit"]), (1, True, "B001"))
        self.assertIn("fix round 1/3 counted", (self.rd / "reports" / "B001.md").read_text(encoding="utf-8"))

    def test_unchanged_rerun_and_rerun_after_pass_do_not_count(self):
        self.artifact("B001", "# B001\n\nshort TBD\n")
        self.cli("check", "B001"); self.cli("check", "B001"); self.cli("check", "B001")
        self.assertEqual(self.fix_rounds(), 0)              # same failing artifact re-checked: no round
        self.good_artifact("B001")
        self.cli("check", "B001")
        self.assertEqual(self.fix_rounds(), 1)
        self.good_artifact("B001", seed="polish")
        self.cli("check", "B001")
        self.assertEqual(self.fix_rounds(), 1)              # edit after a PASS is not a fix round

    def test_explicit_record_fix_is_not_double_counted(self):
        self.artifact("B001", "# B001\n\nshort TBD\n")
        self.cli("check", "B001")
        code, out, _ = self.cli("record", "B001", "--status", "fix", "--note", "remove placeholder")
        self.assertEqual(code, 0)
        self.assertEqual(self.fix_rounds(), 1)
        self.good_artifact("B001")
        self.cli("check", "B001")
        self.assertEqual(self.fix_rounds(), 1)              # the round was already recorded explicitly
        fixes = [l for l in (self.rd / "LEDGER.md").read_text(encoding="utf-8").splitlines() if l.startswith("B001 fix")]
        self.assertEqual(len(fixes), 1)
        self.assertIn("note=remove placeholder", fixes[0])
        # ...but a NEW failing check followed by another edit is a new round
        self.artifact("B001", "# B001\n\nshort TBD\n")
        self.cli("check", "B001")
        self.good_artifact("B001", seed="again")
        self.cli("check", "B001")
        self.assertEqual(self.fix_rounds(), 2)

    def test_cap_at_three_then_split_or_block_message_and_force(self):
        for i in range(3):
            self.artifact("B001", f"# B001\n\nshort TBD {i}\n")
            self.cli("check", "B001")
            self.good_artifact("B001", seed=f"fix{i}")
            self.assertEqual(self.cli("check", "B001")[0], 0)
        self.assertEqual(self.fix_rounds(), 3)
        self.artifact("B001", "# B001\n\nshort TBD again\n")
        self.cli("check", "B001")
        self.good_artifact("B001", seed="fourth")
        code, _, err = self.cli("check", "B001")
        self.assertEqual(code, 1)
        self.assertIn("already had 3 fix rounds: split the unit or record --status blocked", err)
        self.assertEqual(self.fix_rounds(), 3)
        code, out, _ = self.cli("check", "B001", "--force")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.fix_rounds(), 4)
        self.assertIn("B001 fix 4/3", (self.rd / "LEDGER.md").read_text(encoding="utf-8"))
        self.assertIn("FORCED", (self.rd / "LEDGER.md").read_text(encoding="utf-8").splitlines()[-1])
        code, _, err = self.cli("record", "B001", "--status", "fix")
        self.assertEqual(code, 1)                           # record's cap message is unchanged
        self.assertIn("split the unit", err)


class TestEmptyAndUnvalidatedPlans(RunCase):
    """I7: an empty or never-validated plan is not a finished one."""

    def test_next_and_status_on_empty_plan(self):
        (self.rd / "PLAN.md").write_text("# PLAN\n\n## Units\n\n## Specs\n", encoding="utf-8")
        code, out, err = self.cli("next")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("PLAN EMPTY", err)
        code, out, _ = self.cli("next", "--json")
        self.assertEqual(json.loads(out)["code"], 1)
        code, out, _ = self.cli("status")
        self.assertEqual(code, 0)
        self.assertIn("PLAN EMPTY", out)
        code, out, _ = self.cli("status", "--json")
        self.assertTrue(json.loads(out)["plan_empty"])
        code, out, _ = self.cli("plan", "--validate")
        self.assertEqual(code, 1)
        self.assertIn("PLAN EMPTY", out)

    def test_next_refuses_never_validated_plan(self):
        rd = self.tmp / ".bse" / "fresh"
        run_cli("init", "--run-id", "fresh", "--run-dir", str(rd), "--total", "300w")
        (rd / "CHARTER.md").write_text(CHARTER.format(total="300w"), encoding="utf-8")
        (rd / "PLAN.md").write_text(plan_text(THREE), encoding="utf-8")
        code, out, err = run_cli("next", "--run-dir", str(rd))
        self.assertEqual((code, out), (1, ""))
        self.assertIn("PLAN NOT VALIDATED", err)
        code, out, _ = run_cli("status", "--run-dir", str(rd))
        self.assertIn("PLAN NOT VALIDATED", out)
        # an INVALID plan does not count as validated
        (rd / "CHARTER.md").write_text(CHARTER.format(total="3000w"), encoding="utf-8")
        self.assertEqual(run_cli("plan", "--validate", "--run-dir", str(rd))[0], 1)
        self.assertEqual(run_cli("next", "--run-dir", str(rd))[0], 1)
        (rd / "CHARTER.md").write_text(CHARTER.format(total="300w"), encoding="utf-8")
        self.assertEqual(run_cli("plan", "--validate", "--run-dir", str(rd))[0], 0)
        code, out, _ = run_cli("next", "--run-dir", str(rd))
        self.assertEqual((code, out.strip()), (0, "B001"))
        self.assertIn("plan_validated", json.loads((rd / "ledger.json").read_text(encoding="utf-8")))
        self.assertNotIn("PLAN NOT VALIDATED", run_cli("status", "--run-dir", str(rd))[1])

    def test_init_sample_unit_validates_and_is_flagged(self):
        for total, denom, vname in (("1200w", "w", "word_count"), ("40slides", "slides", "slide_count"),
                                    ("120items", "items", "item_count"), ("3files", "files", "file_exists")):
            rd = self.tmp / ".bse" / f"sample-{denom}"
            code, out, err = run_cli("init", "--run-id", f"sample-{denom}", "--run-dir", str(rd), "--total", total)
            self.assertEqual(code, 0, err)
            self.assertIn("replace the SAMPLE unit", out)
            plan = (rd / "PLAN.md").read_text(encoding="utf-8")
            self.assertIn(f"- [ ] B001 [", plan)
            self.assertIn("SAMPLE", plan)
            self.assertIn(vname, plan)
            units, errors = bse.parse_plan(plan)
            self.assertEqual((errors, [u.id for u in units]), ([], ["B001"]))   # real, uncommented unit
            code, out, _ = run_cli("plan", "--validate", "--run-dir", str(rd))
            self.assertEqual(code, 0, out)
            self.assertIn("PLAN VALID: 1 units", out)
            self.assertIn("B001 is the `init` sample unit", out)
            code, out, _ = run_cli("next", "--run-dir", str(rd))
            self.assertEqual((code, out.strip()), (0, "B001"))
        rd = self.tmp / ".bse" / "sample-multi"
        run_cli("init", "--run-id", "sample-multi", "--run-dir", str(rd), "--total", "2000w, 10slides")
        code, out, _ = run_cli("plan", "--validate", "--run-dir", str(rd))
        self.assertEqual(code, 0, out)
        self.assertIn("PLAN VALID: 2 units", out)


class TestStitchDriftGate(RunCase):
    """M8: a complete stitch outside the ±20% band exits non-zero unless --allow-drift."""

    def test_drift_beyond_band_fails_unless_allowed(self):
        for uid in ("B001", "B002", "B003"):
            self.complete(uid)
        self.write_charter(total="600w")                       # 300 words stitched -> 50% drift
        code, out, err = self.cli("stitch")
        self.assertEqual(code, 1)
        self.assertIn("WARNING: BUDGET DRIFT", err)
        self.assertIn("50%", err)
        self.assertTrue((self.rd / "draft.md").exists())        # the draft is still written for inspection
        code, out, err = self.cli("stitch", "--allow-drift", "--json")
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["drift_exceeded"])
        self.assertIn("--allow-drift was given", err)
        self.write_charter(total="300w")
        code, out, err = self.cli("stitch", "--json")
        self.assertEqual((code, json.loads(out)["drift_exceeded"]), (0, False))
        self.assertIn("--allow-drift", subcommand_help("stitch"))

    def test_partial_stitch_is_exempt_from_the_gate(self):
        self.complete("B001")
        code, out, err = self.cli("stitch", "--partial", "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertGreater(data["drift_pct"], 20)
        self.assertFalse(data["drift_exceeded"])
        self.assertNotIn("BUDGET DRIFT", err)


class TestExamplesAndCI(unittest.TestCase):
    """I10: the item-denominated charter total parses; CI exercises the examples."""

    def test_items_total_parses_like_the_feedback_sweep_charter(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = bse.Run(Path(tmp))
            for line in ("Total size: 120items", "Total size: 120 items", "Total size: ~120 items (feedback comments)"):
                (Path(tmp) / "CHARTER.md").write_text(f"# C\n\n## Deliverable\n{line}\n", encoding="utf-8")
                self.assertEqual(run.charter_totals(), [(120, "items")], line)
            self.assertEqual(run.charter_total(), (120, "items"))
        ex = HERE.parent / "examples" / "feedback-sweep"
        if ex.exists():
            self.assertEqual(bse.Run(ex).charter_totals(), [(120, "items")])

    def test_ci_workflow_runs_examples(self):
        wf = (HERE.parent / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        self.assertIn("examples:", wf)                              # a dedicated job
        for needle in ('"plan --validate"', '"status"', '"audit"', "ledger.json", "--run-dir", "status=1", 'exit "$status"'):
            self.assertIn(needle, wf)
        self.assertIn("py_compile", wf)


class TestThroughLine(RunCase):
    """The charter's through-line is the one thing the seam pass cannot repair."""

    def test_missing_through_line_warns_but_does_not_invalidate(self):
        code, out, err = self.cli("plan", "--validate")
        self.assertEqual(code, 0, out + err)
        self.assertIn("Through-line", out + err)
        self.assertIn("VALID", out)

    def test_through_line_section_silences_the_warning(self):
        text = (self.rd / "CHARTER.md").read_text(encoding="utf-8")
        text = text.replace("\n## Audience", "\n## Through-line\nThe test report argues one thing.\n\n## Audience", 1)
        (self.rd / "CHARTER.md").write_text(text, encoding="utf-8")
        code, out, err = self.cli("plan", "--validate")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("Through-line", out + err)

    def test_init_scaffold_contains_a_through_line_section(self):
        self.assertIn("## Through-line", bse.charter_template("T", "300w"))


if __name__ == "__main__":
    unittest.main()
