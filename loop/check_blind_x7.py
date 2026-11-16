"""The mechanical check of the blind view for experiment X7.
Usage: python -m loop.check_blind_x7 [--sessions]"""
import json
import sys

from . import views_x7 as v, reviewer_tools as rt
from . import check_blind_x1 as c1
from .check_blind import scan
from .review_x7 import named_answer
from .x1 import APPROVALS
from .x7 import RUNS_X7, RESULTS_X7, CUTS, LIBRARY, PLACES, NAMED


def forbidden(run):
    c1.RUNS_X1 = RUNS_X7                # the same scan of every table, on X7's runs
    return c1.forbidden(run)


def corpus(run):
    c = {"instructions": v.system_prompt(), "plan prompt": v.prompt_plan() + v.prompt_plan_returned(["x"])}
    for a in APPROVALS:
        md = RUNS_X7 / run / "moments" / a
        kept = json.loads((md / "answers.json").read_text())
        every = [v.show_answer(kept[i], "your plan") for i in LIBRARY if a in PLACES[i]]
        lines = json.loads((md / "named_lines.json").read_text())["lines"]
        named = [named_answer(run, a, i, [int(n) for n in lines[i]]) for i in NAMED if a in NAMED[i] and lines[i]]
        c[f"wake {a}, every answer, and every line that can be named"] = (
            v.prompt_wake(run, a, every, 50) + v.prompt_form(a, every + named, []))
        total = json.loads(rt.ask_record(md, {})[0])["matching_lines"]
        c[f"record at {a}: every line"] = "\n".join(
            rt.ask_record(md, {"show_lines": True, "limit": 200, "offset": off})[0] for off in range(0, total, 200))
    return c


def check(run, sessions):
    bad = forbidden(run)
    c = corpus(run)
    hits = scan(c, bad)
    planted = next(s for s, k in bad.items() if k == "customer id")
    self_test = bool(scan({"planted": c["plan prompt"] + " " + planted}, bad))
    rep = {"run": run, "strings_that_must_not_occur": len(bad), "texts_checked": len(c),
           "characters_checked": sum(len(t) for t in c.values()), "hits": hits,
           "check_catches_a_planted_customer_id": self_test, "passed": not hits and self_test}
    if sessions:
        sent = {}
        for sdir in sorted(RESULTS_X7.glob(f"*/*/{run}/*")):
            for f in ("steps.jsonl", "tool_log.jsonl"):
                p = sdir / f
                if p.exists():
                    for i, ln in enumerate(p.read_text().splitlines()):
                        o = json.loads(ln)
                        sent[f"{sdir.relative_to(RESULTS_X7)} {f} {i}"] = o.get("prompt", "") + (
                            o.get("reply", "") if f == "tool_log.jsonl" else "")
            if (sdir / "system_prompt.txt").exists():
                sent[f"{sdir.relative_to(RESULTS_X7)} instructions"] = (sdir / "system_prompt.txt").read_text()
        sh = scan(sent, bad)
        rep["sessions"] = {"texts_checked": len(sent), "hits": sh}
        rep["passed"] = rep["passed"] and not sh
    return rep


if __name__ == "__main__":
    rt.FIELDS.insert(2, "returned")
    out = {r: check(r, "--sessions" in sys.argv) for r in CUTS}
    RESULTS_X7.mkdir(exist_ok=True)
    (RESULTS_X7 / "blind_check.json").write_text(json.dumps(out, indent=1))
    for r, rep in out.items():
        print(r, {k: val for k, val in rep.items() if k not in ("hits", "sessions")}, "hits:", rep["hits"][:6],
              "sessions:", {k: (len(x) if isinstance(x, list) else x) for k, x in rep.get("sessions", {}).items()})
