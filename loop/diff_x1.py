"""Experiment X1: how each run differs from run 0 in what a blind reviewer can be shown.
Fingerprints are masked. Usage: python -m loop.diff_x1"""
import json
import re
import sqlite3

from .x1 import RUNS_X1, RESULTS_X1, APPROVALS, CUTS, LIBRARY, PLACES

FP = re.compile(r"fp:[0-9a-f]{12}")


def mask(x):
    return FP.sub("fp:*", json.dumps(x, sort_keys=True))


def record(run, a):
    db = sqlite3.connect(RUNS_X1 / run / "moments" / a / "record.sqlite")
    cols = [c[1] for c in db.execute("PRAGMA table_info(record)")]
    return cols, db.execute("SELECT * FROM record ORDER BY seq").fetchall()


def answers(run, a):
    return {i: v["answer"] for i, v in json.loads((RUNS_X1 / run / "moments" / a / "answers.json").read_text()).items()}


def main():
    out = {"results": {}, "differences_from_run_0": {}}
    for run in CUTS:
        out["results"][run] = {f"{i} @ {a}": answers(run, a)[i]["result"] for a in APPROVALS for i in LIBRARY if a in PLACES[i]}
        if run == "0":
            continue
        d = {"answers": [], "record_lines": {}, "bills": []}
        for a in APPROVALS:
            a0, a1 = answers("0", a), answers(run, a)
            for i in a0:
                if mask(a0[i]) != mask(a1[i]):
                    keys = [k for k in a0[i] if mask(a0[i][k]) != mask(a1[i][k])]
                    sub = [k for k in a0[i]["returns"] if mask(a0[i]["returns"][k]) != mask(a1[i]["returns"].get(k))]
                    d["answers"].append({"answer": f"{i} @ {a}", "fields": keys, "returns": sub})
            if (RUNS_X1 / "0" / "moments" / a / "bill.txt").read_text() != (RUNS_X1 / run / "moments" / a / "bill.txt").read_text():
                d["bills"].append(a)
        cols, r0 = record("0", "A3")
        _, r1 = record(run, "A3")
        d["record_lines_count"] = [len(r0), len(r1)]
        for x, y in zip(r0, r1):
            diff = [c for c, p, q in zip(cols, x, y) if mask(p) != mask(q)]
            if diff:
                d["record_lines"].setdefault(", ".join(diff), []).append(x[0])
        out["differences_from_run_0"][run] = d
    RESULTS_X1.mkdir(exist_ok=True)
    (RESULTS_X1 / "runs_against_run_0.json").write_text(json.dumps(out, indent=1))
    names = list(out["results"]["0"])
    print("place".ljust(30), *CUTS)
    for nm in names:
        print(nm.ljust(30), *[("B" if "breach" in out["results"][r][nm] else "p") for r in CUTS])
    for r, d in out["differences_from_run_0"].items():
        print(r, json.dumps(d))


if __name__ == "__main__":
    main()
