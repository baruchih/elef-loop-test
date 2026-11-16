"""Experiment X7: how each run differs from run 0 in what a blind reviewer can be shown, fingerprints
masked; and whether every instrument passes on run 0. Usage: python -m loop.diff_x7"""
import json
import sqlite3

from .common import R_PASS
from .diff_x1 import mask
from .x1 import APPROVALS
from .x7 import RUNS_X7, RESULTS_X7, CUTS


def load(run, a, f):
    return json.loads((RUNS_X7 / run / "moments" / a / f).read_text())


def record(run):
    db = sqlite3.connect(RUNS_X7 / run / "moments" / "A3" / "record.sqlite")
    return [c[1] for c in db.execute("PRAGMA table_info(record)")], db.execute("SELECT * FROM record ORDER BY seq").fetchall()


def main():
    out = {"on_run_0": {}, "differences_from_run_0": {}}
    a0 = {a: load("0", a, "answers.json") for a in APPROVALS}
    n0 = {a: load("0", a, "named_lines.json")["lines"] for a in APPROVALS}
    out["on_run_0"] = {
        "answers_at_the_eleven_places_that_passed": f"{sum(1 for a in a0 for x in a0[a].values() if x['answer']['result'] == R_PASS)} of {sum(len(a0[a]) for a in a0)}",
        "named_lines_that_passed": {f"{i} @ {a}": f"{sum(1 for p in n0[a][i].values() if p['result'] == R_PASS)} of {len(n0[a][i])}"
                                    for a in APPROVALS for i in n0[a] if n0[a][i]}}
    cols, r0 = record("0")
    for run in CUTS:
        if run == "0":
            continue
        d = {"answers": [], "named_lines": {}, "record_lines": {}, "bills": [], "time_of_the_moment": []}
        for a in APPROVALS:
            a1, n1 = load(run, a, "answers.json"), load(run, a, "named_lines.json")["lines"]
            for i in a0[a]:
                x, y = a0[a][i]["answer"], a1[i]["answer"]
                if mask(x) != mask(y):
                    d["answers"].append({"answer": f"{i} @ {a}", "result": y["result"],
                                         "fields": [k for k in x if mask(x[k]) != mask(y[k])],
                                         "returns": [k for k in x["returns"] if mask(x["returns"][k]) != mask(y["returns"].get(k))]})
            for i in n0[a]:
                ls = [int(s) for s in n0[a][i] if mask(n0[a][i][s]) != mask(n1[i][s])]
                if ls:
                    d["named_lines"][f"{i} @ {a}"] = {"lines": ls, "results": sorted({n1[i][str(s)]["result"] for s in ls})}
            for f, key in (("bill.txt", "bills"), ("now.txt", "time_of_the_moment")):
                if (RUNS_X7 / "0" / "moments" / a / f).read_text() != (RUNS_X7 / run / "moments" / a / f).read_text():
                    d[key].append(a)
        _, r1 = record(run)
        d["record_lines_count"] = [len(r0), len(r1)]
        for x, y in zip(r0, r1):
            diff = [c for c, p, q in zip(cols, x, y) if mask(p) != mask(q)]
            if diff:
                d["record_lines"].setdefault(", ".join(diff), []).append(
                    {"line": x[0], **{c: [p, q] for c, p, q in zip(cols, x, y) if c in diff}})
        out["differences_from_run_0"][run] = d
    RESULTS_X7.mkdir(exist_ok=True)
    (RESULTS_X7 / "runs_against_run_0.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out["on_run_0"]))
    for r, d in out["differences_from_run_0"].items():
        print(r, json.dumps(d))


if __name__ == "__main__":
    main()
