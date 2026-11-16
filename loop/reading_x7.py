"""Experiment X7: how much of the record a session read. From the logs of the questions; no new session.
Usage: python -m loop.reading_x7   (writes results_x7/reading_of_the_record.json)

Two things are counted for a session:
- whether one of its questions covers all the account reads: a count grouped by `rows` over lines that take in
  all hundred of them, or the hundred lines themselves, shown over one question or several;
- how many of the hundred sending lines had both their times returned to it, as lines shown or as a count
  grouped by `time` and `returned`.
"""
import json
import sqlite3

from .fixes import MODELS
from .x7 import RESULTS_X7, RUNS_X7, CUTS

READ, SEND = "read: query", "cannot be undone: send notice"


def conn(run, moment):
    c = sqlite3.connect(f"file:{RUNS_X7 / run / 'moments' / moment / 'record.sqlite'}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def the_lines(run):
    c = conn(run, "A3")
    reads = {r[0] for r in c.execute("SELECT seq FROM record WHERE tool = ? AND item IS NOT NULL", (READ,))}
    sends = {r[0] for r in c.execute("SELECT seq FROM record WHERE tool = ?", (SEND,))}
    assert len(reads) == 100 and len(sends) == 100, (run, len(reads), len(sends))
    return reads, sends


def matched(run, moment, a):
    """The line numbers a question matched: the filter of loop.reviewer_tools.ask_record, run again."""
    conds, params = [], []
    for f, v in (a.get("where") or {}).items():
        if v is None:
            conds.append(f"{f} IS NULL")
        elif isinstance(v, list):
            conds.append(f"{f} IN ({','.join('?' * len(v))})")
            params += v
        else:
            conds.append(f"{f} = ?")
            params.append(v)
    if a.get("seq_from") is not None:
        conds.append("seq >= ?")
        params.append(a["seq_from"])
    if a.get("seq_to") is not None:
        conds.append("seq <= ?")
        params.append(a["seq_to"])
    w = (" WHERE " + " AND ".join(conds)) if conds else ""
    return {r[0] for r in conn(run, moment).execute(f"SELECT seq FROM record{w}", params)}


def session(run, d, reads, sends):
    p = d / "tool_log.jsonl"
    log = [json.loads(ln) for ln in p.read_text().splitlines()] if p.exists() else []
    s = json.loads((d / "session.json").read_text())
    by_rows, shown_reads, timed = False, set(), set()
    for q in log:
        if q["error"]:
            continue
        a, rep = q["args"], json.loads(q["reply"])
        by = a.get("count_by") or []
        by = [by] if isinstance(by, str) else by
        m = matched(run, q["moment"], a) if by else set()
        if "rows" in by and reads <= m:
            by_rows = True
        if "time" in by and "returned" in by:
            timed |= m & sends
        for ln in rep.get("lines", []):
            if ln["seq"] in reads:
                shown_reads.add(ln["seq"])
            if ln["seq"] in sends and "time" in ln and "returned" in ln:
                timed.add(ln["seq"])
    return {"who": s["who"], "run": run, "n": s["n"], "questions": len(log),
            "reached_A3": "A3" in s["wakes"],
            "a_count_by_rows_over_all_the_account_reads": by_rows,
            "account_read_lines_shown": len(shown_reads),
            "all_the_account_reads_covered": by_rows or len(shown_reads) == 100,
            "sending_lines_with_their_times_returned": len(timed)}


def main():
    out = []
    for run in CUTS:
        reads, sends = the_lines(run)
        for who in MODELS:
            for d in sorted((RESULTS_X7 / "sessions" / who / run).iterdir(), key=lambda p: int(p.name)):
                out.append(session(run, d, reads, sends))
    (RESULTS_X7 / "reading_of_the_record.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    print(len(main()), "sessions")
