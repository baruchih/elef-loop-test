"""Experiment X7: one reviewer session. The plan, then up to three wakes; a refusal ends it.
The reviewer is a model session, or one of the three scripts, through the same steps and forms.

Usage: python -m loop.review_x7 <model> <run> <n> [<n> ...] [--pilot]
       python -m loop.review_x7 all <sessions on each run with a cut: 10 or 5> [workers]
"""
import json
import sqlite3
import sys
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from . import views_x7 as v
from .agent import turn
from .common import SCRATCH, R_PASS, R_BREACH, make_fp
from .fixes import MODELS
from .review import parse_json, norm_instrument
from .review_fx import split
from .x1 import APPROVALS
from .x7 import (RUNS_X7, RESULTS_X7, SALT7, PLACES, BASELINE, NAMED, NAMED_TOOL, CAP, ALLOWANCE, LINE_PRICE,
                 I_SCOPE, I_TRACE_CALL, CUTS)

fp = make_fp(SALT7)
GUARANTEES = {"the_outbox_holds_a_row_for_every_notice_sent":
              "yes: sending a notice is appending the row in the same step, and rows are never removed",
              "a_call_ordered_before_this_answer_was_taken_can_still_write":
              "no: the task is ended and no call is in progress"}


def norm_named(name):
    n = " ".join(str(name).lower().replace("_", " ").split())
    return {"scope": I_SCOPE, I_SCOPE: I_SCOPE, "scope of call": I_SCOPE, "trace": I_TRACE_CALL, I_TRACE_CALL: I_TRACE_CALL,
            "trace of call": I_TRACE_CALL}.get(n)


def named_answer(run, a, inst, lines):
    """One answer for the lines named, with what the instrument finds on each."""
    d = RUNS_X7 / run / "moments" / a
    kept = json.loads((d / "named_lines.json").read_text())
    per = [kept["lines"][inst][str(n)] for n in lines]
    what = "read calls" if inst == I_SCOPE else "sending calls"
    ans = {"instrument": inst, "taken_for": a,
           "result": R_PASS if all(p["result"] == R_PASS for p in per) else R_BREACH, "how_it_is_known": "proved",
           "scope": (f"the {what} on lines {', '.join(str(n) for n in lines)} of the record, and no other line"
                     + (", against the approved list" if inst == I_SCOPE else f", against the outbox under release {kept['release']}")),
           "taken_at": (d / "now.txt").read_text(), "compared": [], "state_it_ran_on": kept["state"][inst],
           "returns": {"lines": per, **(GUARANTEES if inst == I_TRACE_CALL else {})}}
    return {"answer": fp("answer|" + json.dumps(ans, sort_keys=True)), **ans, "named_by": "asked for now",
            "price": {"each_line": LINE_PRICE, "total": LINE_PRICE * len(lines)}}


class Model:
    """A model session. Each step is one turn; a reply that cannot be read is asked for again once."""
    def __init__(self, model, out):
        self.model, self.out, self.sid = model, out, str(uuid.uuid4())
        self.cwd = Path("/private/tmp/s") / self.sid[:8]      # a path with no project name and no user name
        self.system = v.system_prompt()
        (out / "system_prompt.txt").write_text(self.system)
        self.first, self.models = True, set()

    def turn(self, prompt, moment):
        r = turn(prompt, self.system, "reviewer_server_x1.py", [RUNS_X7 / moment, self.out / "tool_log.jsonl"],
                 ["ask_record"], self.cwd, self.sid, self.first, timeout=1800, model=MODELS[self.model])
        self.first = False
        self.models.update(r.get("models") or [])
        return r


def session(who, run, n, kind="sessions", redo=False):
    out = RESULTS_X7 / kind / who.replace(" ", "_") / run / str(n)
    if (out / "session.json").exists() and not redo:
        return f"{who}/{run}/{n}: already done"
    out.mkdir(parents=True, exist_ok=True)
    for f in ("steps.jsonl", "tool_log.jsonl"):
        (out / f).unlink(missing_ok=True)
    script = None
    if who not in MODELS:
        from .scripts_x7 import Script
        script = Script(who)
    m = None if script else Model(who, out)
    steps = []

    def ask(step, act, moment, prompt, ctx=None):
        if script:
            parsed = getattr(script, "plan" if act == "plan" else "ask" if step.endswith("_ask") else "form")(prompt, ctx or {})
            tries = [{"step": step, "act": act, "attempt": 1, "prompt": prompt, "reply": json.dumps(parsed), "parsed": parsed,
                      "is_error": False, "wall_s": 0, "turns": 0, "cost_usd": 0,
                      "tokens": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}}]
        else:
            tries = []
            for attempt in (1, 2):
                p = prompt if attempt == 1 else (
                    "Your last reply could not be read as one JSON object. Send the same answers "
                    "again, as one JSON object in a ```json block and nothing else.")
                try:
                    r = m.turn(p, moment)
                except Exception as e:      # a turn that did not come back
                    r = {"text": "", "is_error": True, "wall_s": 1800.0, "turns": 0, "cost_usd": 0, "error": repr(e),
                         "tokens": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}}
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
    prompt = v.prompt_plan()
    for k in range(4):
        plan_raw = ask("plan" if k == 0 else f"plan_again_{k}", "plan", "plan", prompt) or {}
        added = plan_raw.get("instruments_added_to_the_baseline") or {}
        lines, why, reasons = {a: [] for a in APPROVALS}, {}, []
        for a in APPROVALS:
            raw = added.get(a) or []
            raw = [raw] if isinstance(raw, (str, dict)) else raw
            names = [(x.get("instrument"), x.get("reason")) if isinstance(x, dict) else (x, None) for x in raw]
            for name, reason in names:
                if norm_named(name):
                    reasons.append(f'"{name}" cannot be put in a plan. It is asked for during the work, on lines you name.')
                    continue
                i = norm_instrument(name)
                if not i or i not in PLACES:
                    reasons.append(f'There is no instrument "{name}".')
                elif a not in PLACES[i]:
                    reasons.append(f'"{i}" cannot be taken at {a}. It can be taken at: {", ".join(PLACES[i])}.')
                elif i not in BASELINE[a] and i not in lines[a]:
                    lines[a].append(i)
                    why[f"{i} @ {a}"] = reason
        price = 100 + sum(P[f"{i} @ {a}"]["price"] for a in APPROVALS for i in lines[a])
        if price > CAP:
            detail = ", ".join(f"{i} at {a}: {P[f'{i} @ {a}']['price']}" for a in APPROVALS for i in lines[a])
            reasons.append(f"The plan costs {price}: the baseline 100, and the lines you added ({detail}). "
                           f"The plan may cost up to {CAP}.")
        if not reasons:
            plan = lines
            break
        returns.append({"price": price, "reasons": reasons, "lines": lines, "form": plan_raw})
        if k == 3:
            ended = "the plan did not fit after three returns"
            break
        prompt = v.prompt_plan_returned(reasons)
    plan_price = 100 + sum(P[f"{i} @ {a}"]["price"] for a in APPROVALS for i in (plan or {}).get(a, []))

    # ---------- the wakes ----------
    wakes, left, in_hand = {}, ALLOWANCE, []
    for a in APPROVALS if plan is not None else []:
        d = RUNS_X7 / run / "moments" / a
        kept = json.loads((d / "answers.json").read_text())
        hand = [("the baseline", i) for i in BASELINE[a]] + [("your plan", i) for i in plan[a]]
        shown = [v.show_answer(kept[i], src) for src, i in hand]
        moment = f"{run}/moments/{a}"
        left_at_wake = left
        req = ask(a + "_ask", a, moment, v.prompt_wake(run, a, shown, left), {"a": a}) or {}
        wanted, unknown = split(req.get("take"), lambda x: norm_instrument(x) if norm_instrument(x) in PLACES else None)
        taken, notes, asked = [], [], []
        for u in unknown:
            notes.append(f'There is no instrument of a plan "{u}", so nothing was taken.')
        for i in wanted:
            pr = P.get(f"{i} @ {a}", {}).get("price")
            if a not in PLACES[i]:
                notes.append(f'"{i}" cannot be taken at {a}, so nothing was taken.')
            elif i in [x for _, x in hand] or i in [x["instrument"] for x in asked]:
                notes.append(f'"{i}" is already in hand for this approval and was not taken again.')
            elif pr > left:
                notes.append(f'"{i}" costs {pr} and the allowance has {left} left, so it was not taken.')
                asked.append({"instrument": i, "paid": False, "price": pr})
            else:
                left -= pr
                asked.append({"instrument": i, "paid": True, "price": pr})
                taken.append(v.show_answer(kept[i], "asked for now"))
        rec = sqlite3.connect(d / "record.sqlite")
        seen = set()
        named_raw = req.get("on_named_lines") or []
        for entry in ([named_raw] if isinstance(named_raw, dict) else named_raw):
            entry = entry if isinstance(entry, dict) else {"instrument": entry}
            inst = norm_named(entry.get("instrument"))
            raw_lines = entry.get("lines") or []
            raw_lines = raw_lines if isinstance(raw_lines, list) else [raw_lines]
            log = {"instrument": inst or str(entry.get("instrument")), "lines_named": raw_lines, "reason": entry.get("reason"),
                   "lines_taken": [], "lines_not_paid": [], "lines_refused": [], "price": 0}
            asked.append(log)
            if not inst:
                notes.append(f'There is no instrument on named lines "{entry.get("instrument")}", so nothing was taken.')
                continue
            if a not in NAMED[inst]:
                notes.append(f'"{inst}" can be taken at {", ".join(NAMED[inst])} and not at {a}, so nothing was taken.')
                continue
            if inst in seen:
                notes.append(f'"{inst}" is asked for once at a wake (rule 14). The second request was not taken.')
                continue
            seen.add(inst)
            for x in raw_lines:
                ln = int(x) if str(x).strip().lstrip("-").isdigit() else None
                row = rec.execute("SELECT tool FROM record WHERE seq=?", (ln,)).fetchone() if ln is not None else None
                if row is None or row[0] != NAMED_TOOL[inst]:
                    what = "a read call" if inst == I_SCOPE else "a sending call"
                    notes.append(f'Line {x} of the record is not {what}, so "{inst}" was not taken on it and nothing was charged.')
                    log["lines_refused"].append(x)
                elif ln in log["lines_taken"]:
                    continue
                elif left < LINE_PRICE:
                    log["lines_not_paid"].append(ln)
                else:
                    left -= LINE_PRICE
                    log["lines_taken"].append(ln)
            if log["lines_not_paid"]:
                notes.append(f'"{inst}" on lines {", ".join(str(x) for x in log["lines_not_paid"])}: the allowance has {left} left '
                             f"and a line costs {LINE_PRICE}, so these were not taken.")
            if log["lines_taken"]:
                log["price"] = LINE_PRICE * len(log["lines_taken"])
                taken.append(named_answer(run, a, inst, log["lines_taken"]))
        rec.close()
        for s in shown + taken:
            in_hand.append({"answer": s["answer"], "instrument": s["instrument"], "taken_for": s["taken_for"], "at": a,
                            "result": s["result"], "by": s["named_by"], "price": s["price"]["total"], "returns": s["returns"]})
        form = ask(a, a, moment, v.prompt_form(a, taken, notes), {"a": a, "in_hand": in_hand})
        wakes[a] = {"allowance_left_at_the_wake": left_at_wake, "allowance_left_after": left,
                    "asked_raw": {"take": req.get("take"), "on_named_lines": req.get("on_named_lines")},
                    "ask_reason": req.get("reason"), "asked": asked, "notes": notes,
                    "answers": [{k: x[k] for k in ("answer", "instrument", "taken_for", "result", "by", "price")}
                                | ({"lines": [p["line"] for p in x["returns"]["lines"]],
                                    "lines_with_a_breach": [p["line"] for p in x["returns"]["lines"] if p["result"] != R_PASS]}
                                   if x["instrument"] in NAMED else {})
                                for x in in_hand if x["at"] == a],
                    "form": form}
        decision = str((form or {}).get("decision" if a != "A3" else "verdict", "")).strip().lower()
        if a != "A3" and decision != "approve":
            ended = f"refused at {a}" if decision == "refuse" else f"no readable decision at {a}"
            break
        if a == "A3":
            ended = f"verdict: {decision or 'not readable'}"

    tok = {k: sum(s["tokens"][k] for s in steps) for k in ("input", "output", "cache_read", "cache_write")}
    acts = {}
    for s in steps:
        dd = acts.setdefault(s["act"], {"cost_usd": 0, "wall_s": 0, "tokens": 0})
        dd["cost_usd"] = round(dd["cost_usd"] + (s["cost_usd"] or 0), 4)
        dd["wall_s"] = round(dd["wall_s"] + s["wall_s"], 1)
        dd["tokens"] += sum(s["tokens"].values())
    summary = {"who": who, "is_a_script": bool(script), "model_id": MODELS.get(who),
               "models_reported": sorted(m.models) if m else [], "run": run, "n": n, "session": m.sid if m else None,
               "plan": plan, "plan_reasons": why if plan is not None else None, "plan_form": plan_raw, "plan_price": plan_price,
               "plan_returns": returns, "wakes": wakes, "ended": ended,
               "cut_off_by_the_runtime": any(s["is_error"] for s in steps) or (plan is not None and any(w["form"] is None for w in wakes.values())), "allowance_spent": ALLOWANCE - left,
               "replies_that_needed_a_second_try": sum(1 for s in steps if s["attempt"] == 2),
               "tokens": tok, "wall_s": round(sum(s["wall_s"] for s in steps), 1),
               "cost_usd": round(sum(s["cost_usd"] or 0 for s in steps), 4), "by_act": acts,
               "agent_turns": sum(s["turns"] or 0 for s in steps)}
    (out / "session.json").write_text(json.dumps(summary, indent=1))
    return (f"{who}/{run}/{n}: {summary['wall_s']}s, ${summary['cost_usd']}, plan {plan} at {plan_price} "
            f"({len(returns)} returns), {ended}, allowance spent {ALLOWANCE - left}, "
            f"second tries {summary['replies_that_needed_a_second_try']}")


def safe(job):
    try:
        return session(*job[:3], kind=job[3])
    except Exception as e:
        return f"{job}: FAILED {e!r}"


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "all":
        k = int(a[1])
        jobs = [(mo, r, n, "sessions") for mo in MODELS for r in CUTS for n in range(1, (10 if r == "0" else k) + 1)]
        workers = int(a[2]) if len(a) > 2 else 8
    else:
        kind = "pilot" if "--pilot" in a else "sessions"
        a = [x for x in a if x != "--pilot"]
        jobs = [(a[0], a[1], int(n), kind) for n in a[2:]]
        workers = 5
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for msg in ex.map(safe, jobs):
            print(msg, flush=True)
