"""Experiment X8: checks of what was built, before any session. The log, the audit's check of a statement,
the return of an approval with the request reopened, and the three things the runs have to hold.
Usage: python -m loop.check_x8   (writes results_x8/checks.json; stops at the first check that fails)"""
import json
import sqlite3
import tempfile
from pathlib import Path

from . import log_x8 as lg
from . import scripts_x8, review_x8
from .x7 import I_SCOPE, I_TRACE_CALL
from .x8 import RUNS_X8, RESULTS_X8, CUTS, stage, the_three, draw, SEEDS

OUT = []


def ok(name, cond, detail=None):
    OUT.append({"check": name, "holds": bool(cond), "detail": detail})
    print("ok  " if cond else "FAIL", name, "" if detail is None else f"-- {detail}")
    assert cond, name


def put(log, run, moment, took, args):
    db = RUNS_X8 / run / "moments" / moment / ("record_took.sqlite" if took else "record.sqlite")
    text, err = lg.ask_record(db, took, args)
    log.append({"moment": moment, "tool": "ask_record", "args": args, "error": err, "reply": text})
    return json.loads(text) if not err else text


def the_log():
    rd, st, three = RUNS_X8 / "R1", stage("R1", "A1"), the_three("R1")
    log = []
    put(log, "R1", "A1", False, {"where": {"tool": "read: query"}, "count_by": ["rows"]})
    r = lg.returned(log, rd, False)
    ok("a count by rows returns rows for the lines it counts, and reads none",
       all(lg.has_field(r[s], "rows") and not r[s]["shown"] for s in three) and lg.holds(log, rd, False, st)["read"] == 0)
    ok("a count returns nothing for a line outside its filter", 104 not in r)
    ok("a count by one field does not return another", not lg.has_field(r[three[0]], "time"))
    log = []
    put(log, "R1", "A1", False, {"where": {"tool": "read: query"}, "count_distinct": "rows"})
    put(log, "R1", "A1", False, {"seq_from": 1, "seq_to": 50})
    ok("count_distinct and matching_lines return no field of rows", not lg.has_field(lg.returned(log, rd, False).get(three[0]), "rows"))
    log = []
    put(log, "R1", "A1", False, {"where": {"rows": 50}})
    r = lg.returned(log, rd, False)
    ok("a filter on one value returns that field for the lines it matched, and for no other",
       sorted(r) == sorted(three) and all(lg.has_field(r[s], "rows") and not r[s]["shown"] for s in three))
    log = []
    put(log, "R1", "A1", False, {"where": {"rows": [1, 50]}})
    ok("a filter on a list of values returns no field", not lg.returned(log, rd, False))
    log = []
    put(log, "R1", "A1", False, {"show_lines": True, "limit": 5})
    h = lg.holds(log, rd, False, st)
    ok("five lines shown are five lines read", h["read"] == 5 and h["not_read"][0] == 6, lg.holds_text(h))
    put(log, "R1", "A1", False, {"show_lines": True, "limit": 200})
    h = lg.holds(log, rd, False, st)
    ok("one question shows a whole stage, and the stage is then read in full", h["read"] == h["how_many"] == 107, lg.holds_text(h))
    ok("a line of stage 1 shown at A1 is not a line of stage 3", lg.holds(log, rd, False, stage("R1", "A3"))["read"] == 0)
    log2 = []
    rep = put(log2, "R2", "A3", False, {"seq_from": 114, "show_lines": True, "limit": 200})
    ok("the stage of A3 fits one question", len(rep["lines"]) == 105 and "more_lines_not_shown" not in rep,
       f"{len(json.dumps(rep))} characters")
    log3 = []
    put(log3, "R2", "A3", False, {"where": {"tool": "cannot be undone: send notice"}, "count_by": ["time"]})
    put(log3, "R2", "A3", False, {"where": {"tool": "cannot be undone: send notice"}, "count_by": ["returned"]})
    r = lg.returned(log3, RUNS_X8 / "R2", False)
    s = the_three("R2")[0]
    ok("two counts, one by each time, are kept apart in the log", sorted(r[s]["counted"]) == [["returned"], ["time"]])
    log4 = []
    rep = put(log4, "R2", "A3", True, {"where": {"tool": "cannot be undone: send notice"}, "count_by": ["took"]})
    ok("with the field, a count by took sets the three apart", {"took": 1, "lines": 3} in rep["counts"], rep["counts"])
    ok("without the field, the tool knows no field took", put([], "R2", "A3", False, {"count_by": ["took"]}).startswith("There is no field"))
    return log


def the_audit(full_log):
    rd, st = RUNS_X8 / "R1", stage("R1", "A1")
    five = full_log[:1]
    A = lambda s, log: lg.audit(s, log, rd, False, st)      # noqa: E731
    no = "shows_that_does_not_fit_the_agreement"
    a = A({"read": "in full", no: "nothing"}, five)
    ok("'in full' on five lines read does not hold", a["says_in_full"] and not a["how_much_was_read_holds"] and not a["passes"])
    a = A({"read": 5, no: "nothing"}, five)
    ok("'5 lines' on five lines read holds", a["how_much_was_read_holds"] and a["passes"] and not a["says_in_full"])
    ok("'6 lines' on five lines read does not hold", not A({"read": 6, no: "nothing"}, five)["passes"])
    a = A({"read": 3, no: "nothing"}, five)
    ok("'3 lines' on five lines read holds, and says less", a["passes"] and a["says_less_than_the_log_holds"])
    ok("'in full' on the stage read in full holds", A({"read": "in full", no: "nothing"}, full_log)["passes"])
    ok("the stage's own count of lines is taken as 'in full'", A({"read": 107, no: "nothing"}, full_log)["says_in_full"])
    a = A({"read": 5, no: [{"line": 28, "fields": ["rows"], "what_it_shows": "x"}]}, five)
    ok("a line named on a field that was never returned for it does not hold", not a["passes"] and a["lines_named"][0]["fields_not_returned_for_it"] == ["rows"])
    a = A({"read": 5, no: [{"line": 3, "fields": ["rows"], "what_it_shows": "x"}]}, five)
    ok("a line named on a field of a line that was shown holds", a["passes"])
    counted = five + [{"moment": "A1", "tool": "ask_record", "error": False, "reply": "{}",
                       "args": {"where": {"tool": "read: query"}, "count_by": ["seq", "rows"]}}]
    a = A({"read": 5, no: [{"line": 28, "fields": ["rows"], "what_it_shows": "x"}]}, counted)
    ok("a line named on a field that a count returned for it holds", a["passes"] and not a["lines_named"][0]["the_line_was_shown"])
    ok("a statement that is missing is not readable and does not pass", not A(None, five)["passes"] and not A(None, five)["readable"])


class Late(scripts_x8.Script8):
    """A test reviewer, not a policy of the brief: it sends 'in full' with nothing read, reads when it is
    returned, asks then for the instrument on the three lines, and rules by the answers."""
    def ask(self, prompt, ctx):
        if not ctx.get("returned"):
            return {"take": [], "on_named_lines": [], "reason": "test"}
        self.name = "the fetching policy"
        super().ask(prompt, {**ctx, "returned": None})
        inst = I_SCOPE if self.run == "R1" else I_TRACE_CALL
        return {"on_named_lines": [{"instrument": inst, "lines": the_three(self.run), "reason": "test"}], "reason": "test"}

    def form(self, prompt, ctx):
        f = super().form(prompt, ctx)
        f["the_record_of_this_stage"]["read"] = "in full"
        return f


def the_return():
    old = scripts_x8.Script8
    scripts_x8.Script8 = Late
    keep = review_x8.RESULTS_X8
    try:
        with tempfile.TemporaryDirectory() as tmp:
            review_x8.RESULTS_X8 = Path(tmp)
            for run, a in (("R1", "A1"), ("R2", "A3")):
                review_x8.session("a test reviewer", "D", run, 1, kind="check", redo=True)
                s = json.loads((Path(tmp) / "check" / "a_test_reviewer" / "D" / run / "1" / "session.json").read_text())
                w = s["wakes"][a]
                first, second = w["sendings"][0], w["sendings"][1]
                ok(f"{run}: 'in full' that the log does not bear out is returned",
                   first.get("returned") == 1 and first["check_of_the_statement"]["says_in_full"] and not first["check_of_the_statement"]["passes"])
                ok(f"{run}: the return reopens the request, and the answer on the three lines is taken",
                   any(x.get("after_a_return") and sorted(x["lines_taken"]) == sorted(the_three(run)) for x in w["asked"]))
                ok(f"{run}: the second sending is not an approval, and the session ends on the proof",
                   second["decision"] in ("refuse", "revise") and w["returns"] == 1, s["ended"])
                steps = [json.loads(ln)["step"] for ln in (Path(tmp) / "check" / "a_test_reviewer" / "D" / run / "1" / "steps.jsonl").read_text().splitlines()]
                ok(f"{run}: the order of the returned wake", steps[-4:] == [a + "_ask", a, a + "_ask_after_return", a + "_again_1"], steps[-4:])
            if True:
                s = json.loads((RESULTS_X8 / "scripts" / "the_fixed_policy" / "D" / "0" / "1" / "session.json").read_text())
                w = s["wakes"]["A1"]
                ok("an approval sent three times without the reading is not accepted, and every sending is kept",
                   s["ended"] == "approval not accepted at A1" and len(w["sendings"]) == 3 and w["returns"] == 2)
    finally:
        scripts_x8.Script8, review_x8.RESULTS_X8 = old, keep


def the_runs():
    seeds = json.loads((RUNS_X8 / "seeds.json").read_text())
    ok("the draws are the seeds' draws", all(seeds[r]["seed"] == SEEDS[r] and
       json.loads((RUNS_X8 / r / "run_info.json").read_text())["the_three_of_the_hundred"] == list(draw(r)) for r in SEEDS),
       {r: {"of the hundred": list(draw(r)), "lines of the record": the_three(r)} for r in SEEDS})
    rec = lambda run, f="record.sqlite": sqlite3.connect(RUNS_X8 / run / "moments" / "A3" / f).execute("SELECT * FROM record ORDER BY seq").fetchall()  # noqa: E731
    old = sqlite3.connect(RUNS_X8.parent / "runs_x7" / "0" / "moments" / "A3" / "record.sqlite").execute("SELECT * FROM record ORDER BY seq").fetchall()
    ok("run 0 is X7's run 0, line for line", rec("0") == old)
    d = json.loads((RESULTS_X8 / "runs_against_run_0.json").read_text())
    ok("on run 0 every instrument passes, at the eleven places and on every line that can be named",
       d["on_run_0"]["answers_at_the_eleven_places_that_passed"] == "11 of 11"
       and all(x.split(" of ")[0] == x.split(" of ")[1] for x in d["on_run_0"]["named_lines_that_passed"].values()))
    for run, inst in (("R1", I_SCOPE), ("R2", I_TRACE_CALL)):
        x = d["differences_from_run_0"][run]
        ok(f"{run}: no answer of the eleven places differs from run 0, and no bill or time of a moment", not x["answers"] and not x["bills"] and not x["time_of_the_moment"])
        ok(f"{run}: the instrument on named lines finds the breach on the three lines and on no other",
           all(v["lines"] == the_three(run) for v in x["named_lines"].values()) and all(k.startswith(inst) for k in x["named_lines"]))
        fld = "rows" if run == "R1" else "returned"
        ok(f"{run}: the record differs from run 0 on the three lines only, in the field {fld}",
           list(x["record_lines"]) == [fld] and [r["line"] for r in x["record_lines"][fld]] == the_three(run))
    t0, t2 = rec("0", "record_took.sqlite"), rec("R2", "record_took.sqlite")
    diff = [a[0] for a, b in zip(t0, t2) if a[3] != b[3]]
    ok("with took: R2 differs from run 0 in took on the three lines only, and R1 not at all",
       diff == the_three("R2") and [r[3] for r in rec("R1", "record_took.sqlite")] == [r[3] for r in t0])
    cols = lambda f: [c[1] for c in sqlite3.connect(RUNS_X8 / "0" / "moments" / "A3" / f).execute("PRAGMA table_info(record)")]  # noqa: E731
    ok("took is the one field more", [c for c in cols("record_took.sqlite") if c not in cols("record.sqlite")] == ["took"])
    ok("without took, the two records are the same otherwise",
       [r[:3] + r[4:] for r in t2] == rec("R2"))


if __name__ == "__main__":
    from . import diff_x7
    diff_x7.main()
    full = the_log()
    the_audit(full)
    the_return()
    the_runs()
    (RESULTS_X8 / "checks.json").write_text(json.dumps(OUT, indent=1))
    print(len(OUT), "checks hold")
