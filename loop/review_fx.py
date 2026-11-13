"""Experiment 1b: reviewer sessions, blind only, for one model and one condition.

  asis   the views, rules sheet, form and prompts of experiment 1's blind arm, unchanged
  fixes  the same with the fixes of experiment 1b

Usage: python -m loop.review_fx <model> <asis|fixes> <run> <n> [<n> ...] [--pilot]
       python -m loop.review_fx all [workers]         (the 105 sessions)
"""
import json
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor

from . import views, views_fx
from .agent import turn
from .common import RUNS, INSTRUMENTS, I_UNDO, SCRATCH
from .fixes import RESULTS_1B, I_TRACE, INSTRUMENTS_FX, MODELS
from .review import parse_json, norm_instrument


def norm_fx(name):
    n = " ".join(str(name).lower().replace("_", " ").split())
    if n in ("trace", I_TRACE, "the " + I_TRACE, "trace of action", "trace of the action", I_TRACE + " instrument"):
        return I_TRACE
    return norm_instrument(name)


def split(raw, norm):
    if isinstance(raw, str):
        raw = [raw]
    wanted, unknown = [], []
    for name in raw or []:
        i = norm(name)
        if i and i not in wanted:
            wanted.append(i)
        elif not i:
            unknown.append(str(name))
    return wanted, unknown


def session(model, cond, run, n, pilot=False):
    run_dir = RUNS / run
    out = RESULTS_1B / ("pilot" if pilot else "sessions") / model / cond / run / str(n)
    if (out / "session.json").exists():
        return f"{model}/{cond}/{run}/{n}: already done"
    out.mkdir(parents=True, exist_ok=True)
    for f in ("steps.jsonl", "tool_log.jsonl"):
        (out / f).unlink(missing_ok=True)
    sid = str(uuid.uuid4())
    cwd = SCRATCH / "rev" / sid[:13]
    system = views.system_prompt(run_dir, "blind") if cond == "asis" else views_fx.system_prompt(run_dir)
    (out / "system_prompt.txt").write_text(system)
    state = {"first": True}
    steps, models = [], set()

    def ask(step, moment, prompt):
        tries = []
        for attempt in (1, 2):
            p = prompt if attempt == 1 else (
                "Your last reply could not be read as one JSON object. Send the same answers "
                "again, as one JSON object in a ```json block and nothing else.")
            try:
                r = turn(p, system, "reviewer_server.py",
                         [run_dir / "moments" / moment, "blind", out / "tool_log.jsonl", run_dir / "salt.txt"],
                         ["ask_record"], cwd, sid, state["first"], timeout=1800, model=MODELS[model])
            except Exception as e:                       # a timeout: reported as it is
                r = {"text": "", "is_error": True, "wall_s": 1800.0, "turns": 0, "cost_usd": 0,
                     "tokens": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0},
                     "models": [], "raw": {"error": repr(e)}}
            state["first"] = False
            models.update(r.get("models") or [])
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

    forms, asks = {}, {}
    if cond == "asis":
        forms["m1"] = ask("m1", "m1", views.prompt_m1(run_dir))
        forms["m2"] = ask("m2", "m2", views.prompt_m2(run_dir))
        req = ask("m3_ask", "m3", views.prompt_m3_ask()) or {}
        wanted, unknown = split(req.get("take_again"), norm_instrument)
        forced = [I_UNDO] if run == "C" and I_UNDO not in wanted else []
        forms["m3"] = ask("m3", "m3", views.prompt_m3_form(run_dir, wanted, unknown, bool(forced)))
        asks["m3"] = {"asked_raw": req.get("take_again"), "reason": req.get("reason"), "asked": wanted,
                      "do_not_exist": unknown, "shown_unasked": forced}
        forms["m4"] = ask("m4", "m4", views.prompt_m4(run_dir, wanted + forced))
    else:
        forms["m1"] = ask("m1", "m1", views_fx.prompt_m1(run_dir))
        earlier = {}
        for m in ("m2", "m3", "m4"):
            req = ask(m + "_ask", m, views_fx.prompt_ask(run_dir, m, earlier)) or {}
            raw = req.get("take", req.get("take_again"))
            wanted, unknown = split(raw, norm_fx)
            forced = [I_TRACE] if I_TRACE not in wanted else []
            if m == "m3" and I_UNDO not in wanted:
                forced.append(I_UNDO)
            forms[m] = ask(m, m, views_fx.prompt_form(run_dir, m, wanted, unknown, forced))
            asks[m] = {"asked_raw": raw, "reason": req.get("reason"), "asked": wanted,
                       "do_not_exist": unknown, "shown_unasked": forced}
            earlier[m] = wanted + forced

    tok = {k: sum(s["tokens"][k] for s in steps) for k in ("input", "output", "cache_read", "cache_write")}
    summary = {"model": model, "model_id": MODELS[model], "models_reported": sorted(models),
               "cond": cond, "run": run, "n": n, "session": sid, "forms": forms, "asks": asks,
               "replies_that_needed_a_second_try": sum(1 for s in steps if s["attempt"] == 2),
               "tokens": tok, "wall_s": round(sum(s["wall_s"] for s in steps), 1),
               "cost_usd": round(sum(s["cost_usd"] or 0 for s in steps), 4),
               "agent_turns": sum(s["turns"] or 0 for s in steps)}
    (out / "session.json").write_text(json.dumps(summary, indent=1))
    return (f"{model}/{cond}/{run}/{n}: {summary['wall_s']}s, ${summary['cost_usd']}, "
            f"second tries {summary['replies_that_needed_a_second_try']}, "
            f"forms missing: {[m for m, f in forms.items() if f is None]}, models {sorted(models)}")


def safe(job):
    try:
        return session(*job)
    except Exception as e:
        return f"{job}: FAILED {e!r}"


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "all":
        jobs = [(m, c, r, n) for m in MODELS for c in ("asis", "fixes")
                for r in ("ABC" if c == "asis" else "ABCD") for n in range(1, 6)]
        workers = int(a[1]) if len(a) > 1 else 8
    else:
        pilot = "--pilot" in a
        a = [x for x in a if x != "--pilot"]
        jobs = [(a[0], a[1], a[2], int(n), pilot) for n in a[3:]]
        workers = 5
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for msg in ex.map(safe, jobs):
            print(msg, flush=True)
