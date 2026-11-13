"""Runs reviewer sessions over the frozen views of a run.

Usage: python -m loop.review <run> <arm> <n> [<n> ...]      (sessions in parallel)
"""
import json
import re
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import views
from .agent import turn
from .common import RUNS, RESULTS, INSTRUMENTS, I_UNDO, MODEL, SCRATCH


def parse_json(text):
    blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    cands = blocks[::-1]
    i, j = text.find("{"), text.rfind("}")
    if i >= 0 and j > i:
        cands.append(text[i:j + 1])
    for c in cands:
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            continue
    return None


def norm_instrument(name):
    n = re.sub(r"[^a-z ]", " ", str(name).lower())
    n = re.sub(r"\s+", " ", n).strip()
    for i in INSTRUMENTS:
        if n == i or n == i.replace(" ", "") or n in (i + " instrument", "the " + i):
            return i
    return None


def session(run, arm, n):
    run_dir = RUNS / run
    out = RESULTS / "sessions" / run / arm / str(n)
    if (out / "session.json").exists():
        return f"{run}/{arm}/{n}: already done"
    out.mkdir(parents=True, exist_ok=True)
    for f in ("steps.jsonl", "tool_log.jsonl"):
        (out / f).unlink(missing_ok=True)
    sid = str(uuid.uuid4())
    cwd = SCRATCH / "rev" / sid[:13]          # an opaque name: the session can see its directory
    system = views.system_prompt(run_dir, arm)
    (out / "system_prompt.txt").write_text(system)
    allowed = ["ask_record"] + (["read_database"] if arm == "sighted" else [])
    state = {"first": True}
    steps = []

    def ask(step, moment, prompt):
        """One prompt to the session; one more try if the reply is not a JSON object."""
        tries = []
        for attempt in (1, 2):
            p = prompt if attempt == 1 else (
                "Your last reply could not be read as one JSON object. Send the same answers "
                "again, as one JSON object in a ```json block and nothing else.")
            r = turn(p, system, "reviewer_server.py",
                     [run_dir / "moments" / moment, arm, out / "tool_log.jsonl", run_dir / "salt.txt"],
                     allowed, cwd, sid, state["first"], timeout=1800)
            state["first"] = False
            parsed = parse_json(r["text"])
            tries.append({"step": step, "moment": moment, "attempt": attempt, "prompt": p,
                          "reply": r["text"], "parsed": parsed, "is_error": r["is_error"],
                          "wall_s": r["wall_s"], "turns": r["turns"], "cost_usd": r["cost_usd"],
                          "tokens": r["tokens"]})
            if parsed is not None:
                break
        with open(out / "steps.jsonl", "a") as f:
            for t in tries:
                f.write(json.dumps(t) + "\n")
        steps.extend(tries)
        return parsed

    forms = {}
    forms["m1"] = ask("m1", "m1", views.prompt_m1(run_dir))
    forms["m2"] = ask("m2", "m2", views.prompt_m2(run_dir))
    req = ask("m3_ask", "m3", views.prompt_m3_ask()) or {}
    raw = req.get("take_again") or []
    if isinstance(raw, str):
        raw = [raw]
    wanted, unknown = [], []
    for name in raw:
        i = norm_instrument(name)
        if i and i not in wanted:
            wanted.append(i)
        elif not i:
            unknown.append(str(name))
    forced = run == "C" and I_UNDO not in wanted
    forms["m3"] = ask("m3", "m3", views.prompt_m3_form(run_dir, wanted, unknown, forced))
    shown = wanted + ([I_UNDO] if forced else [])
    forms["m4"] = ask("m4", "m4", views.prompt_m4(run_dir, shown))

    tok = {k: sum(s["tokens"][k] for s in steps) for k in ("input", "output", "cache_read", "cache_write")}
    summary = {"run": run, "arm": arm, "n": n, "model": MODEL, "session": sid,
               "forms": forms,
               "retake": {"asked_raw": raw, "reason": req.get("reason"), "taken": wanted,
                          "asked_for_instruments_that_do_not_exist": unknown,
                          "asked_for_undo_rehearsal": I_UNDO in wanted,
                          "undo_rehearsal_shown_unasked": forced},
               "replies_that_needed_a_second_try": sum(1 for s in steps if s["attempt"] == 2),
               "tokens": tok, "wall_s": round(sum(s["wall_s"] for s in steps), 1),
               "cost_usd": round(sum(s["cost_usd"] or 0 for s in steps), 4),
               "agent_turns": sum(s["turns"] or 0 for s in steps)}
    (out / "session.json").write_text(json.dumps(summary, indent=1))
    return (f"{run}/{arm}/{n}: done in {summary['wall_s']}s, "
            f"{tok['input'] + tok['output'] + tok['cache_read'] + tok['cache_write']} tokens, "
            f"forms missing: {[m for m, f in forms.items() if f is None]}")


if __name__ == "__main__":
    run, arm = sys.argv[1], sys.argv[2]
    ns = [int(x) for x in sys.argv[3:]]
    with ThreadPoolExecutor(max_workers=5) as ex:
        for msg in ex.map(lambda n: session(run, arm, n), ns):
            print(msg, flush=True)
