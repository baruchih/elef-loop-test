"""Experiment X8: X7's harness and worker, on three runs with the three lines drawn anew, and the
record with the field `took` beside the record without it.

What is new against X7 is in the rules, the forms, the log and the audit (views_x8, log_x8, review_x8).
The runs themselves differ from X7's only in which three lines carry the cut. X7's files are not
touched: the runs are made under runs_x8/. X7's modules read their folder from a module global, and
this module points those globals at runs_x8/ for any process that imports it.

Usage: python -m loop.x8        (writes the seeds, then makes runs 0, R1 and R2 under runs_x8/)
"""
import json
import random
import sqlite3
from datetime import datetime

from . import x7, views_x7, review_x7, diff_x7
from .common import ROOT, TOOL_READ, TOOL_CASE, TOOL_STATUS, TOOL_SEND
from .x1 import APPROVALS
from .x7 import H7, TOOL_TIDY

RUNS_X8 = ROOT / "runs_x8"
RESULTS_X8 = ROOT / "results_x8"
x7.RUNS_X7 = views_x7.RUNS_X7 = review_x7.RUNS_X7 = diff_x7.RUNS_X7 = RUNS_X8
diff_x7.RESULTS_X7 = RESULTS_X8

CUTS = {"0": None, "R1": "the wide reads", "R2": "the previews"}
diff_x7.CUTS = CUTS

SEEDS = {"R1": 8801, "R2": 8802}        # fixed before any session, and before the draws were looked at
CONDITIONS = {"X": {"took": False, "statement": False, "duty": False},
              "S": {"took": False, "statement": True, "duty": False},
              "D": {"took": False, "statement": True, "duty": True},
              "F": {"took": True, "statement": False, "duty": False},
              "DF": {"took": True, "statement": True, "duty": True}}
WORK_TOOLS = [TOOL_READ, TOOL_CASE, TOOL_STATUS, TOOL_TIDY, TOOL_SEND]      # the lines of a call: these carry `took`
MOMENTS = ["plan"] + APPROVALS


def draw(run):
    """Three of the hundred, by the run's seed: which account reads are wide, or which sending calls are previews."""
    return tuple(sorted(random.Random(SEEDS[run]).sample(range(1, 101), 3)))


def record_file(cond):
    return "record_took.sqlite" if CONDITIONS[cond]["took"] else "record.sqlite"


def with_took(d):
    """A second copy of a moment's record, with the field `took` after `returned` on the lines of a call."""
    src = sqlite3.connect(d / "record.sqlite")
    cols = [c[1] for c in src.execute("PRAGMA table_info(record)")]
    new = cols[:cols.index("returned") + 1] + ["took"] + cols[cols.index("returned") + 1:]
    (d / "record_took.sqlite").unlink(missing_ok=True)
    dst = sqlite3.connect(d / "record_took.sqlite")
    dst.execute(f"CREATE TABLE record({','.join(new)})")
    for row in src.execute("SELECT * FROM record ORDER BY seq"):
        r = dict(zip(cols, row))
        took = None
        if r["tool"] in WORK_TOOLS and r["time"] and r["returned"]:
            took = int((datetime.fromisoformat(r["returned"]) - datetime.fromisoformat(r["time"])).total_seconds())
        r["took"] = took
        dst.execute(f"INSERT INTO record VALUES ({','.join('?' * len(new))})", [r[c] for c in new])
    dst.commit()
    dst.close()


def stage(run, moment):
    """The lines of a wake's stage: those the record did not have at the wake before. (first, last), or None."""
    if moment == "plan":
        return None
    last = lambda m: sqlite3.connect(RUNS_X8 / run / "moments" / m / "record.sqlite").execute(      # noqa: E731
        "SELECT MAX(seq) FROM record").fetchone()[0]
    k = APPROVALS.index(moment)
    return ((last(APPROVALS[k - 1]) + 1) if k else 1, last(moment))


def the_three(run):
    """The record lines of the three, for a run with a cut."""
    info = json.loads((RUNS_X8 / run / "run_info.json").read_text())
    return info["lines_of_the_three_reads"] if run == "R1" else info["lines_of_the_three_sending_calls"]


if __name__ == "__main__":
    RUNS_X8.mkdir(exist_ok=True)
    seeds = {r: {"seed": SEEDS[r], "the draw": "sorted(random.Random(seed).sample(range(1, 101), 3))",
                 "among": "the hundred account reads" if r == "R1" else "the hundred sending calls"} for r in SEEDS}
    (RUNS_X8 / "seeds.json").write_text(json.dumps(seeds, indent=1))
    (RUNS_X8 / "plan").mkdir(exist_ok=True)
    for f in ("record.sqlite", "record_took.sqlite"):
        (RUNS_X8 / "plan" / f).unlink(missing_ok=True)
    for run, cut in CUTS.items():
        three = draw(run) if cut else ()
        x7.THE_THREE = three or x7.THE_THREE          # the worker's script reads which three from here
        h = H7.create(RUNS_X8 / run, run)
        info = {"cut": cut, "seed": SEEDS.get(run), "the_three_of_the_hundred": list(three), **x7.script(h, run)}
        if not cut:
            info["lines_of_the_three_reads"] = info["lines_of_the_three_sending_calls"] = []
        (RUNS_X8 / run / "run_info.json").write_text(json.dumps(info, indent=1))
        for a in APPROVALS:
            with_took(RUNS_X8 / run / "moments" / a)
        print(run, info)
    rec = sqlite3.connect(RUNS_X8 / "plan" / "record.sqlite")
    cols = [c[1] for c in sqlite3.connect(RUNS_X8 / "0" / "harness.sqlite").execute("PRAGMA table_info(record)")]
    rec.execute(f"CREATE TABLE record({','.join(cols)})")
    rec.commit()
    rec.close()
    with_took(RUNS_X8 / "plan")
    p = x7.prices()
    (RUNS_X8 / "prices.json").write_text(json.dumps(p, indent=1))
    old = json.loads((ROOT / "runs_x7" / "prices.json").read_text())
    print("prices as in X7:", p == old)
    for run in CUTS:
        print(run, "stages:", {a: stage(run, a) for a in APPROVALS})
