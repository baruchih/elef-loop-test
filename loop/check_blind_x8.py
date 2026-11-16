"""The mechanical check of the blind view for experiment X8: every text a session can be shown, in each
condition, against every string of the database that must not occur. Usage: python -m loop.check_blind_x8 [--sessions]"""
import json
import sys

from . import views_x8 as v, log_x8 as lg
from . import check_blind_x1 as c1
from .check_blind import scan
from .review_x7 import named_answer
from .x1 import APPROVALS
from .x7 import LIBRARY, PLACES, NAMED
from .x8 import RUNS_X8, RESULTS_X8, CUTS, CONDITIONS, stage

WORDS = ["condition", "control", "pilot", "experiment", "script", "x8", "x7", "measured", "the duty", "planted"]


def forbidden(run):
    c1.RUNS_X1 = RUNS_X8                # the same scan of every table, on X8's runs
    return c1.forbidden(run)


def corpus(run, cond):
    took = CONDITIONS[cond]["took"]
    c = {"instructions": v.system_prompt(cond), "plan prompt": v.prompt_plan() + v.prompt_plan_returned(["x"]),
         "the tools": lg.describe(took) + lg.LOG_DESC}
    for a in APPROVALS:
        md = RUNS_X8 / run / "moments" / a
        kept = json.loads((md / "answers.json").read_text())
        every = [v.show_answer(kept[i], "your plan") for i in LIBRARY if a in PLACES[i]]
        lines = json.loads((md / "named_lines.json").read_text())["lines"]
        named = [named_answer(run, a, i, [int(n) for n in lines[i]]) for i in NAMED if a in NAMED[i] and lines[i]]
        h = lg.holds([], RUNS_X8 / run, took, stage(run, a))
        c[f"wake {a}, every answer, every line that can be named, and both returns"] = (
            v.prompt_wake(cond, run, a, every, 50) + v.prompt_form(cond, a, every + named, [])
            + (v.prompt_returned_1(a, h) + v.prompt_returned_2(cond, a, h) if CONDITIONS[cond]["duty"] else ""))
        db = md / ("record_took.sqlite" if took else "record.sqlite")
        c[f"record at {a}: every line"] = lg.ask_record(db, took, {"show_lines": True, "limit": 200})[0] + \
            lg.ask_record(db, took, {"show_lines": True, "limit": 200, "offset": 200})[0]
    return c


def check(run, cond, sessions):
    bad = forbidden(run)
    c = corpus(run, cond)
    hits = scan(c, bad)
    planted = next(s for s, k in bad.items() if k == "customer id")
    self_test = bool(scan({"planted": c["plan prompt"] + " " + planted}, bad))
    words = sorted({w for w in WORDS for t in c.values() if w in t.lower()})
    rep = {"run": run, "condition": cond, "strings_that_must_not_occur": len(bad), "texts_checked": len(c),
           "characters_checked": sum(len(t) for t in c.values()), "hits": hits,
           "words_of_the_design_found": words,
           "check_catches_a_planted_customer_id": self_test, "passed": not hits and self_test and not words}
    if sessions:
        sent = {}
        for sdir in sorted(RESULTS_X8.glob(f"*/*/{cond}/{run}/*")):
            for f in ("steps.jsonl", "tool_log.jsonl"):
                p = sdir / f
                if p.exists():
                    for i, ln in enumerate(p.read_text().splitlines()):
                        o = json.loads(ln)
                        sent[f"{sdir.relative_to(RESULTS_X8)} {f} {i}"] = o.get("prompt", "") + (
                            o.get("reply", "") if f == "tool_log.jsonl" else "")
            if (sdir / "system_prompt.txt").exists():
                sent[f"{sdir.relative_to(RESULTS_X8)} instructions"] = (sdir / "system_prompt.txt").read_text()
        sh = scan(sent, bad)
        sw = sorted({w for w in WORDS for t in sent.values() if w in t.lower()})
        rep["sessions"] = {"texts_checked": len(sent), "hits": sh, "words_of_the_design_found": sw}
        rep["passed"] = rep["passed"] and not sh and not sw
    return rep


if __name__ == "__main__":
    out = {f"{r} {cond}": check(r, cond, "--sessions" in sys.argv) for r in CUTS for cond in CONDITIONS}
    RESULTS_X8.mkdir(exist_ok=True)
    (RESULTS_X8 / "blind_check.json").write_text(json.dumps(out, indent=1))
    for k, rep in out.items():
        print(k, {x: val for x, val in rep.items() if x in ("texts_checked", "characters_checked", "words_of_the_design_found", "passed")},
              "hits:", rep["hits"][:4], "sessions:", {x: (len(y) if isinstance(y, list) else y) for x, y in rep.get("sessions", {}).items()})
    print("ALL PASSED" if all(r["passed"] for r in out.values()) else "NOT PASSED")
