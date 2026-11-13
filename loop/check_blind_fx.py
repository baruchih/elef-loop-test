"""The mechanical check of the blind view, for the views with the fixes (experiment 1b).

Usage: python -m loop.check_blind_fx [--sessions]
"""
import json
import sys

from . import views_fx as vf, reviewer_tools as rt
from .check_blind import forbidden, scan, MOMENTS
from .common import RUNS, I_UNDO
from .fixes import RESULTS_1B, INSTRUMENTS_FX, I_TRACE, taken


def corpus(run):
    d = RUNS / run
    c = {"instructions": vf.system_prompt(d), "prompt m1": vf.prompt_m1(d),
         "tool description": rt.RECORD_DESC + json.dumps(rt.RECORD_SCHEMA)}
    earlier = {}
    for m in ("m2", "m3", "m4"):
        c[f"prompt {m}, asking, every earlier answer shown"] = vf.prompt_ask(d, m, earlier)
        c[f"prompt {m}, form, every answer asked for"] = vf.prompt_form(d, m, INSTRUMENTS_FX, ["no such instrument"], [])
        c[f"prompt {m}, form, none asked for"] = vf.prompt_form(d, m, [], [], [I_TRACE, I_UNDO])
        c[f"answers taken at {m}"] = json.dumps(taken(run, m))
        earlier[m] = INSTRUMENTS_FX
    for m in MOMENTS:
        md = d / "moments" / m
        total = json.loads(rt.ask_record(md, {})[0])["matching_lines"]
        c[f"record at {m}: every line"] = "\n".join(
            rt.ask_record(md, {"show_lines": True, "limit": 200, "offset": off})[0] for off in range(0, total, 200))
    return c


def check(run, sessions):
    bad = forbidden(RUNS / run)
    c = corpus(run)
    hits = scan(c, bad)
    planted = next(s for s, k in bad.items() if k == "customer id")
    self_test = bool(scan({"planted": c["prompt m1"] + " " + planted}, bad))
    rep = {"run": run, "strings_that_must_not_occur": len(bad), "texts_checked": len(c),
           "characters_checked": sum(len(t) for t in c.values()), "hits": hits,
           "check_catches_a_planted_customer_id": self_test, "passed": not hits and self_test}
    if sessions:
        sent = {}
        for sdir in sorted(RESULTS_1B.glob(f"*/*/*/{run}/*")):
            for f in ("steps.jsonl", "tool_log.jsonl"):
                p = sdir / f
                if p.exists():
                    for i, ln in enumerate(p.read_text().splitlines()):
                        o = json.loads(ln)
                        sent[f"{sdir.relative_to(RESULTS_1B)} {f} {i}"] = o.get("prompt", "") + (
                            o.get("reply", "") if f == "tool_log.jsonl" else "")
            if (sdir / "system_prompt.txt").exists():
                sent[f"{sdir.relative_to(RESULTS_1B)} instructions"] = (sdir / "system_prompt.txt").read_text()
        sh = scan(sent, bad)
        rep["sessions"] = {"texts_checked": len(sent), "hits": sh}
        rep["passed"] = rep["passed"] and not sh
    return rep


if __name__ == "__main__":
    out = {r: check(r, "--sessions" in sys.argv) for r in "ABCD"}
    RESULTS_1B.mkdir(exist_ok=True)
    (RESULTS_1B / "blind_check_fx.json").write_text(json.dumps(out, indent=1))
    for r, rep in out.items():
        print(r, {k: v for k, v in rep.items() if k != "hits"}, "hits:", rep["hits"][:5])
