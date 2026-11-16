"""Experiment X7: the 120 sessions, in ten rounds of twelve: one session for each run and model in a round.
Within a round the order is by run (0, U, R1, R2) and within a run by model, six sessions at a time.
A session that the runtime cut off is moved to results_x7/discarded/ and run again, and is not counted.
If a session is still cut off after three tries, ten minutes apart, the rounds stop there.

Usage: python -m loop.rounds_x7 [first round] [last round]
"""
import json
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from .fixes import MODELS
from .review_x7 import session
from .x7 import RESULTS_X7, CUTS


def one(job):
    who, run, n = job
    for attempt in (1, 2, 3):
        try:
            msg = session(who, run, n)
        except Exception as e:
            msg = f"{who}/{run}/{n}: FAILED {e!r}"
        d = RESULTS_X7 / "sessions" / who / run / str(n)
        s = json.loads((d / "session.json").read_text()) if (d / "session.json").exists() else None
        if s is not None and not s["cut_off_by_the_runtime"]:
            return True, msg
        if d.exists():
            to = RESULTS_X7 / "discarded" / who / run / f"{n}_try_{attempt}_{int(time.time())}"
            to.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(d), str(to))
        print(f"{who}/{run}/{n}: cut off by the runtime, try {attempt}; discarded. {msg[:200]}", flush=True)
        if attempt < 3:
            time.sleep(600)
    return False, f"{who}/{run}/{n}: cut off three times"


if __name__ == "__main__":
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    last = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    for rnd in range(first, last + 1):
        jobs = [(m, r, rnd) for r in CUTS for m in MODELS]
        with ThreadPoolExecutor(max_workers=6) as ex:
            res = list(ex.map(one, jobs))
        for ok, msg in res:
            print(msg, flush=True)
        if not all(ok for ok, _ in res):
            print(f"ROUND {rnd} NOT FINISHED. Stopped.", flush=True)
            sys.exit(1)
        print(f"ROUND {rnd} FINISHED: {sum(1 for ok, _ in res if ok)} sessions.", flush=True)
