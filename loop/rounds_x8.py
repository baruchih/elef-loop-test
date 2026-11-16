"""Experiment X8: the 310 sessions, in ten rounds of thirty-one. A round has one session of each cell of ten,
two of each cell of twenty, and one of Opus's (run 0 under DF in the odd rounds, run R2 under DF in the even).
Within a round the order is by run (0, R1, R2), then by condition (X, S, D, F, DF), then by model, six at a time.
A session that the runtime cut off is moved to results_x8/discarded/ and run again, and is not counted.
If a session is still cut off after three tries, ten minutes apart, the rounds stop there.

Usage: python -m loop.rounds_x8 [first round] [last round]      python -m loop.rounds_x8 --list
"""
import json
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from .review_x8 import session
from .x8 import RESULTS_X8

WEAKER = ["sonnet", "haiku"]
CELLS = {"0": {"S": 10, "D": 10, "F": 10, "DF": 10}, "R1": {"S": 10, "D": 10},
         "R2": {"X": 10, "S": 20, "D": 20, "F": 20, "DF": 20}}


def jobs(rnd):
    out = []
    for run, conds in CELLS.items():
        for cond in ("X", "S", "D", "F", "DF"):
            for who in WEAKER if cond in conds else []:
                out += [(who, cond, run, n) for n in ([rnd] if conds[cond] == 10 else [2 * rnd - 1, 2 * rnd])]
        if (run == "0" and rnd % 2) or (run == "R2" and not rnd % 2):
            out.append(("opus", "DF", run, (rnd + 1) // 2))
    return out


def one(job):
    who, cond, run, n = job
    for attempt in (1, 2, 3):
        try:
            msg = session(who, cond, run, n)
        except Exception as e:
            msg = f"{who}/{cond}/{run}/{n}: FAILED {e!r}"
        d = RESULTS_X8 / "sessions" / who / cond / run / str(n)
        s = json.loads((d / "session.json").read_text()) if (d / "session.json").exists() else None
        if s is not None and not s["cut_off_by_the_runtime"]:
            return True, msg
        if d.exists():
            to = RESULTS_X8 / "discarded" / who / cond / run / f"{n}_try_{attempt}_{int(time.time())}"
            to.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(d), str(to))
        print(f"{who}/{cond}/{run}/{n}: cut off by the runtime, try {attempt}; discarded. {msg[:200]}", flush=True)
        if attempt < 3:
            time.sleep(600)
    return False, f"{who}/{cond}/{run}/{n}: cut off three times"


if __name__ == "__main__":
    if "--list" in sys.argv:
        every = [j for r in range(1, 11) for j in jobs(r)]
        print(len(every), "sessions;", len(set(every)), "different;", len(jobs(1)), "in a round")
        sys.exit(0)
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    last = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    for rnd in range(first, last + 1):
        with ThreadPoolExecutor(max_workers=6) as ex:
            res = list(ex.map(one, jobs(rnd)))
        for ok, msg in res:
            print(msg, flush=True)
        if not all(ok for ok, _ in res):
            print(f"ROUND {rnd} NOT FINISHED. Stopped.", flush=True)
            sys.exit(1)
        print(f"ROUND {rnd} FINISHED: {sum(1 for ok, _ in res if ok)} sessions.", flush=True)
