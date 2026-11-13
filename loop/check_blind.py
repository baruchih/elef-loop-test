"""The mechanical check of the blind view.

No customer id, name, table name, column name or stored value of the database may occur in
anything the blind reviewer can be shown: the instructions, the prompt of every moment, every
answer that can be taken again, the tool's description, and every line and every field value
that the record tool can return.

Usage: python -m loop.check_blind <run> [--sessions]
  --sessions  also checks what the blind sessions of that run were actually sent.
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

from . import views, reviewer_tools as rt
from .common import RUNS, RESULTS, INSTRUMENTS

MOMENTS = ["m1", "m2", "m3", "m4"]


def forbidden(run_dir):
    """Every string that must not occur, with its kind."""
    out = {}
    dbs = [run_dir / "env.sqlite"] + [run_dir / "moments" / m / "env.sqlite" for m in MOMENTS]
    for path in dbs:
        db = sqlite3.connect(path)
        for (t,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            out.setdefault(t, "table name")
            cols = [c[1] for c in db.execute(f"PRAGMA table_info({t})")]
            for c in cols:
                out.setdefault(c, "column name")
            for row in db.execute(f"SELECT * FROM {t}"):
                for c, v in zip(cols, row):
                    if v is None or str(v) == "":
                        continue
                    kind = {"cust_id": "customer id", "full_name": "customer name",
                            "email_addr": "customer email"}.get(c, "stored value")
                    out.setdefault(str(v), kind)
                    if c == "full_name":
                        for part in str(v).split():
                            out.setdefault(part, "part of a customer name")
                    if c == "email_addr":
                        for part in re.split(r"[.@]", str(v).split("@")[0]):
                            out.setdefault(part, "part of a customer email")
    return out


def blind_corpus(run_dir):
    """Everything the blind reviewer can be shown, as named texts."""
    c = {"instructions": views.system_prompt(run_dir, "blind"),
         "prompt m1": views.prompt_m1(run_dir),
         "prompt m2": views.prompt_m2(run_dir),
         "prompt m3, asking": views.prompt_m3_ask(),
         "prompt m3, form, all answers taken again":
             views.prompt_m3_form(run_dir, INSTRUMENTS, ["an instrument that does not exist"], True),
         "prompt m3, form, none taken again": views.prompt_m3_form(run_dir, [], [], False),
         "prompt m4": views.prompt_m4(run_dir, INSTRUMENTS),
         "tool description": rt.RECORD_DESC + json.dumps(rt.RECORD_SCHEMA)}
    for m in MOMENTS:
        d = run_dir / "moments" / m
        total = json.loads(rt.ask_record(d, {})[0])["matching_lines"]
        lines = []
        for off in range(0, total, 200):
            lines.append(rt.ask_record(d, {"show_lines": True, "limit": 200, "offset": off})[0])
        c[f"record at {m}: every line"] = "\n".join(lines)
        c[f"record at {m}: every value of every field"] = "\n".join(
            rt.ask_record(d, {"count_by": [f]})[0] for f in rt.FIELDS)
        c[f"record at {m}: an error reply"] = rt.ask_record(d, {"where": {"nosuchfield": 1}})[0]
    return c


def scan(corpus, bad):
    hits = []
    for name, text in corpus.items():
        for s, kind in bad.items():
            if s in text and re.search(r"(?<![A-Za-z0-9_])" + re.escape(s) + r"(?![A-Za-z0-9_])", text):
                hits.append({"where": name, "kind": kind, "string": s})
    return hits


def check(run, sessions=False):
    run_dir = RUNS / run
    bad = forbidden(run_dir)
    corpus = blind_corpus(run_dir)
    kinds = {}
    for k in bad.values():
        kinds[k] = kinds.get(k, 0) + 1
    hits = scan(corpus, bad)
    # The check must be able to fail: plant one real customer id and see it caught.
    planted = next(s for s, k in bad.items() if k == "customer id")
    self_test = bool(scan({"planted": corpus["prompt m2"] + " " + planted}, bad))
    report = {"run": run, "strings_that_must_not_occur": len(bad), "by_kind": kinds,
              "texts_checked": len(corpus), "characters_checked": sum(len(t) for t in corpus.values()),
              "hits": hits, "check_catches_a_planted_customer_id": self_test,
              "passed": not hits and self_test}
    if sessions:
        sent = {}
        for sdir in sorted((RESULTS / "sessions" / run / "blind").glob("*")):
            for f in ("steps.jsonl", "tool_log.jsonl"):
                p = sdir / f
                if not p.exists():
                    continue
                for i, ln in enumerate(p.read_text().splitlines()):
                    o = json.loads(ln)
                    sent[f"session {sdir.name} {f} line {i}"] = o.get("prompt", "") + o.get("reply", "") \
                        if f == "tool_log.jsonl" else o.get("prompt", "")
            p = sdir / "system_prompt.txt"
            if p.exists():
                sent[f"session {sdir.name} instructions"] = p.read_text()
        shits = scan(sent, bad)
        report["sessions"] = {"texts_checked": len(sent), "hits": shits}
        report["passed"] = report["passed"] and not shits
    return report


if __name__ == "__main__":
    r = check(sys.argv[1], "--sessions" in sys.argv)
    out = RESULTS / f"blind_check_{sys.argv[1]}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(r, indent=1))
    print(json.dumps(r, indent=1))
