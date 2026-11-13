"""Experiment X1: one reviewer session. The plan, then up to three wakes; a refusal ends it.

Usage: python -m loop.review_x1 <model> <priced|free> <run> <n> [<n> ...] [--pilot]
       python -m loop.review_x1 all [workers]        (the 90 sessions)
"""
import json
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor

from . import views_x1 as v
from .agent import turn
from .common import SCRATCH
from .fixes import MODELS
from .review import parse_json
from .review_fx import norm_fx, split
from .x1 import RUNS_X1, RESULTS_X1, PLACES, BASELINE, APPROVALS, CAP, ALLOWANCE


def session(model, cond, run, n, pilot=False):
    out = RESULTS_X1 / ("pilot" if pilot else "sessions") / model / cond / run / str(n)
    if (out / "session.json").exists():
        return f"{model}/{cond}/{run}/{n}: already done"
    out.mkdir(parents=True, exist_ok=True)
    for f in ("steps.jsonl", "tool_log.jsonl"):
        (out / f).unlink(missing_ok=True)
    sid = str(uuid.uuid4())
    cwd = SCRATCH / "rev" / sid[:13]
    system = v.system_prompt(cond)
    (out / "system_prompt.txt").write_text(system)
    state = {"first": True}
    steps, models = [], set()

    def ask(step, act, moment, prompt):
        tries = []
        for attempt in (1, 2):
            p = prompt if attempt == 1 else (
                "Your last reply could not be read as one JSON object. Send the same answers "
                "again, as one JSON object in a ```json block and nothing else.")
            try:
                r = turn(p, system, "reviewer_server_x1.py", [RUNS_X1 / moment, out / "tool_log.jsonl"],
                         ["ask_record"], cwd, sid, state["first"], timeout=1800, model=MODELS[model])
            except Exception as e:
                r = {"text": "", "is_error": True, "wall_s": 1800.0, "turns": 0, "cost_usd": 0,
                     "tokens": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}, "models": []}
            state["first"] = False
            models.update(r.get("models") or [])
            parsed = parse_json(r["text"])
            tries.append({"step": step, "act": act, "attempt": attempt, "prompt": p, "reply": r["text"],
                          "parsed": parsed, "is_error": r["is_error"], "wall_s": r["wall_s"], "turns": r["turns"],
                          "cost_usd": r["cost_usd"], "tokens": r["tokens"]})
            if parsed is not None:
                break
        with open(out / "steps.jsonl", "a") as f:
            for t in tries:
                f.write(json.dumps(t) + "\n")
        steps.extend(tries)
        return parsed

    # ---------- the plan ----------
    P = v.prices()
    plan, returns, plan_raw, ended = None, [], None, None
    prompt = v.prompt_plan(cond)
    for k in range(4):
        plan_raw = ask("plan" if k == 0 else f"plan_again_{k}", "plan", "plan", prompt) or {}
        added = plan_raw.get("instruments_added_to_the_baseline") or {}
        lines, reasons = {a: [] for a in APPROVALS}, []
        for a in APPROVALS:
            wanted, unknown = split(added.get(a) or [], norm_fx)
            for u in unknown:
                reasons.append(f'There is no instrument "{u}".')
            for i in wanted:
                if a not in PLACES[i]:
                    reasons.append(f'"{i}" cannot be taken at {a}. It can be taken at: {", ".join(PLACES[i])}.')
                elif i not in BASELINE[a] and i not in lines[a]:
                    lines[a].append(i)
        price = 100 + sum(P[f"{i} @ {a}"]["price"] for a in APPROVALS for i in lines[a])
        if cond == "priced" and price > CAP:
            detail = ", ".join(f"{i} at {a}: {P[f'{i} @ {a}']['price']}" for a in APPROVALS for i in lines[a])
            reasons.append(f"The plan costs {price}: the baseline 100, and the lines you added ({detail}). "
                           f"The plan may cost up to {CAP}.")
        if not reasons:
            plan = lines
            break
        returns.append({"price": price, "reasons": reasons, "lines": lines})
        if k == 3:
            ended = "the plan did not fit after three returns"
            break
        prompt = v.prompt_plan_returned(reasons)
    plan_price = 100 + sum(P[f"{i} @ {a}"]["price"] for a in APPROVALS for i in (plan or {}).get(a, []))

    # ---------- the wakes ----------
    wakes, left = {}, ALLOWANCE
    for a in APPROVALS if plan is not None else []:
        kept = json.loads((RUNS_X1 / run / "moments" / a / "answers.json").read_text())
        hand = [("the baseline", i) for i in BASELINE[a]] + [("your plan", i) for i in plan[a]]
        shown = [v.show_answer(kept[i], src, cond) for src, i in hand]
        moment = f"{run}/moments/{a}"
        req = ask(a + "_ask", a, moment, v.prompt_wake(run, a, shown, cond, left)) or {}
        wanted, unknown = split(req.get("take"), norm_fx)
        taken, notes, asked = [], [], []
        for u in unknown:
            notes.append(f'There is no instrument "{u}". It does not exist, so nothing was taken.')
        for i in wanted:
            if a not in PLACES[i]:
                notes.append(f'"{i}" cannot be taken at {a}, so nothing was taken.')
            elif i in [x for _, x in hand] or i in asked:
                notes.append(f'"{i}" is already in hand for this approval and was not taken again.')
            else:
                pr = P[f"{i} @ {a}"]["price"]
                if cond == "priced" and pr > left:
                    notes.append(f'"{i}" costs {pr} and the allowance has {left} left, so it was not taken.')
                    asked.append(i + " (not paid)")
                    continue
                if cond == "priced":
                    left -= pr
                asked.append(i)
                taken.append(v.show_answer(kept[i], "asked for now", cond))
        form = ask(a, a, moment, v.prompt_form(a, taken, notes))
        wakes[a] = {"asked_raw": req.get("take"), "ask_reason": req.get("reason"), "notes": notes,
                    "answers": [{"answer": s["answer"], "instrument": s["instrument"], "result": s["result"],
                                 "by": s["named_by"], "price": P[f"{s['instrument']} @ {a}"]} for s in shown + taken],
                    "form": form, "allowance_left": left}
        decision = str((form or {}).get("decision" if a != "A3" else "verdict", "")).strip().lower()
        if a != "A3" and decision != "approve":
            ended = f"refused at {a}" if decision == "refuse" else f"no readable decision at {a}"
            break
        if a == "A3":
            ended = f"verdict: {decision or 'not readable'}"

    tok = {k: sum(s["tokens"][k] for s in steps) for k in ("input", "output", "cache_read", "cache_write")}
    acts = {}
    for s in steps:
        d = acts.setdefault(s["act"], {"cost_usd": 0, "wall_s": 0, "tokens": 0})
        d["cost_usd"] = round(d["cost_usd"] + (s["cost_usd"] or 0), 4)
        d["wall_s"] = round(d["wall_s"] + s["wall_s"], 1)
        d["tokens"] += sum(s["tokens"].values())
    summary = {"model": model, "model_id": MODELS[model], "models_reported": sorted(models), "cond": cond,
               "run": run, "n": n, "session": sid, "plan": plan, "plan_form": plan_raw, "plan_price": plan_price,
               "plan_returns": returns, "wakes": wakes, "ended": ended, "allowance_spent": ALLOWANCE - left,
               "replies_that_needed_a_second_try": sum(1 for s in steps if s["attempt"] == 2),
               "tokens": tok, "wall_s": round(sum(s["wall_s"] for s in steps), 1),
               "cost_usd": round(sum(s["cost_usd"] or 0 for s in steps), 4), "by_act": acts,
               "agent_turns": sum(s["turns"] or 0 for s in steps)}
    (out / "session.json").write_text(json.dumps(summary, indent=1))
    return (f"{model}/{cond}/{run}/{n}: {summary['wall_s']}s, ${summary['cost_usd']}, plan {plan} at {plan_price} "
            f"({len(returns)} returns), {ended}, second tries {summary['replies_that_needed_a_second_try']}")


def safe(job):
    try:
        return session(*job)
    except Exception as e:
        return f"{job}: FAILED {e!r}"


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "all":
        jobs = [(m, c, r, n) for m in MODELS for c, runs in (("priced", "0123"), ("free", "03"))
                for r in runs for n in range(1, 6)]
        workers = int(a[1]) if len(a) > 1 else 8
    else:
        pilot = "--pilot" in a
        a = [x for x in a if x != "--pilot"]
        jobs = [(a[0], a[1], a[2], int(n), pilot) for n in a[3:]]
        workers = 5
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for msg in ex.map(safe, jobs):
            print(msg, flush=True)
