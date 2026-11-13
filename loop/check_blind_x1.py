"""The mechanical check of the blind view for experiment X1.
Usage: python -m loop.check_blind_x1 [--sessions]"""
import json
import re
import sqlite3
import sys

from . import views_x1 as v, reviewer_tools as rt
from .check_blind import scan
from .check_blind import forbidden as forbidden_1
from .x1 import RUNS_X1, RESULTS_X1, APPROVALS, CUTS, LIBRARY, PLACES, CATEGORIES, OTHER_VALUE


def forbidden(run):
    d = RUNS_X1 / run
    out = {}
    for path in [d / "env.sqlite"] + [d / "moments" / a / "env.sqlite" for a in APPROVALS]:
        db = sqlite3.connect(path)
        for (t,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            out.setdefault(t, "table name")
            cols = [c[1] for c in db.execute(f"PRAGMA table_info({t})")]
            for c in cols:
                out.setdefault(c, "column name")
            for row in db.execute(f"SELECT * FROM {t}"):
                for c, val in zip(cols, row):
                    if val is None or str(val) == "":
                        continue
                    kind = {"cust_id": "customer id", "full_name": "customer name",
                            "email_addr": "customer email"}.get(c, "stored value")
                    out.setdefault(str(val), kind)
                    if c == "full_name":
                        for part in str(val).split():
                            out.setdefault(part, "part of a customer name")
                    if c == "email_addr":
                        for part in re.split(r"[.@]", str(val).split("@")[0]):
                            out.setdefault(part, "part of a customer email")
    for c in CATEGORIES + [OTHER_VALUE]:
        out.setdefault(c, "stored value")
    return out


def corpus(run):
    c = {}
    for cond in ("priced", "free"):
        c[f"instructions, {cond}"] = v.system_prompt(cond)
        c[f"plan prompt, {cond}"] = v.prompt_plan(cond) + v.prompt_plan_returned(["x"])
        for a in APPROVALS:
            kept = json.loads((RUNS_X1 / run / "moments" / a / "answers.json").read_text())
            every = [v.show_answer(kept[i], "your plan", cond) for i in LIBRARY if a in PLACES[i]]
            c[f"wake {a}, {cond}, every answer"] = v.prompt_wake(run, a, every, cond, 50) + v.prompt_form(a, every, [])
    for a in APPROVALS:
        md = RUNS_X1 / run / "moments" / a
        total = json.loads(rt.ask_record(md, {})[0])["matching_lines"]
        c[f"record at {a}: every line"] = "\n".join(
            rt.ask_record(md, {"show_lines": True, "limit": 200, "offset": off})[0] for off in range(0, total, 200))
    return c


def check(run, sessions):
    bad = forbidden(run)
    c = corpus(run)
    hits = scan(c, bad)
    planted = next(s for s, k in bad.items() if k == "customer id")
    self_test = bool(scan({"planted": c["plan prompt, priced"] + " " + planted}, bad))
    rep = {"run": run, "strings_that_must_not_occur": len(bad), "texts_checked": len(c),
           "characters_checked": sum(len(t) for t in c.values()), "hits": hits,
           "check_catches_a_planted_customer_id": self_test, "passed": not hits and self_test}
    if sessions:
        sent = {}
        for sdir in sorted(RESULTS_X1.glob(f"*/*/*/{run}/*")):
            for f in ("steps.jsonl", "tool_log.jsonl"):
                p = sdir / f
                if p.exists():
                    for i, ln in enumerate(p.read_text().splitlines()):
                        o = json.loads(ln)
                        sent[f"{sdir.relative_to(RESULTS_X1)} {f} {i}"] = o.get("prompt", "") + (
                            o.get("reply", "") if f == "tool_log.jsonl" else "")
            if (sdir / "system_prompt.txt").exists():
                sent[f"{sdir.relative_to(RESULTS_X1)} instructions"] = (sdir / "system_prompt.txt").read_text()
        sh = scan(sent, bad)
        rep["sessions"] = {"texts_checked": len(sent), "hits": sh}
        rep["passed"] = rep["passed"] and not sh
    return rep


if __name__ == "__main__":
    rt.FIELDS.insert(2, "returned")
    out = {r: check(r, "--sessions" in sys.argv) for r in CUTS}
    RESULTS_X1.mkdir(exist_ok=True)
    (RESULTS_X1 / "blind_check.json").write_text(json.dumps(out, indent=1))
    for r, rep in out.items():
        print(r, {k: val for k, val in rep.items() if k not in ("hits", "sessions")}, "hits:", rep["hits"][:6],
              "sessions:", {k: (len(x) if isinstance(x, list) else x) for k, x in rep.get("sessions", {}).items()})
