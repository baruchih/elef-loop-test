"""Experiment X8: one reviewer session in one condition. The plan, then up to three wakes; a refusal ends it.
As X7's session, with the log, the audit's check of the statement at every sending of a form, and in D
and DF the return of an approval: twice at most, with the request for named lines reopened after the first.

Usage: python -m loop.review_x8 <model> <condition> <run> <n> [<n> ...] [--pilot]
"""
import json
import sqlite3
import sys
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from . import views_x8 as v
from . import log_x8 as lg
from .agent import turn
from .common import R_PASS
from .fixes import MODELS
from .review import parse_json, norm_instrument
from .review_fx import split
from .review_x7 import norm_named, named_answer
from .x1 import APPROVALS
from .x7 import PLACES, BASELINE, NAMED, NAMED_TOOL, CAP, ALLOWANCE, LINE_PRICE
from .x8 import RUNS_X8, RESULTS_X8, CONDITIONS, stage

ZERO = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}


class Model:
    """A model session. Each step is one turn; a reply that cannot be read is asked for again once."""
    def __init__(self, model, cond, run, out):
        self.model, self.cond, self.run, self.out, self.sid = model, cond, run, out, str(uuid.uuid4())
        self.cwd = Path("/private/tmp/s") / self.sid[:8]      # a path with no project name and no user name
        self.system = v.system_prompt(cond)
        (out / "system_prompt.txt").write_text(self.system)
        self.first, self.models, self.cum = True, set(), 0.0

    def turn(self, prompt, moment):
        c = CONDITIONS[self.cond]
        r = turn(prompt, self.system, "reviewer_server_x8.py",
                 [RUNS_X8 / self.run, moment, self.out / "tool_log.jsonl", int(c["took"]), int(c["statement"])],
                 ["ask_record"] + (["ask_log"] if c["statement"] else []), self.cwd, self.sid, self.first,
                 timeout=1800, model=MODELS[self.model])
        self.first = False
        self.models.update(r.get("models") or [])
        # The runtime's cost figure runs on over the turns of a resumed session: a turn's own cost is the difference.
        r["cost_as_reported"] = r["cost_usd"]
        if r["cost_usd"] is not None:
            r["cost_usd"], self.cum = round(max(0.0, r["cost_usd"] - self.cum), 6), max(self.cum, r["cost_usd"])
        return r


def session(who, cond, run, n, kind="sessions", redo=False):
    c = CONDITIONS[cond]
    out = RESULTS_X8 / kind / who.replace(" ", "_") / cond / run / str(n)
    if (out / "session.json").exists() and not redo:
        return f"{who}/{cond}/{run}/{n}: already done"
    out.mkdir(parents=True, exist_ok=True)
    for f in ("steps.jsonl", "tool_log.jsonl"):
        (out / f).unlink(missing_ok=True)
    log_file = out / "tool_log.jsonl"
    script = None
    if who not in MODELS:
        from .scripts_x8 import Script8
        script = Script8(who, cond, run, log_file)
    m = None if script else Model(who, cond, run, out)
    steps = []

    def ask(step, act, moment, prompt, ctx=None):
        if script:
            parsed = getattr(script, "plan" if act == "plan" else "ask" if "_ask" in step else "form")(prompt, ctx or {})
            tries = [{"step": step, "act": act, "attempt": 1, "prompt": prompt, "reply": json.dumps(parsed), "parsed": parsed,
                      "is_error": False, "wall_s": 0, "turns": 0, "cost_usd": 0, "tokens": dict(ZERO)}]
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
                         "tokens": dict(ZERO)}
                parsed = parse_json(r["text"])
                tries.append({"step": step, "act": act, "attempt": attempt, "prompt": p, "reply": r["text"],
                              "parsed": parsed, "is_error": r["is_error"], "wall_s": r["wall_s"], "turns": r["turns"],
                              "cost_usd": r["cost_usd"], "cost_as_reported": r.get("cost_as_reported"), "tokens": r["tokens"],
                              "questions_in_the_log_after": len(lg.entries(log_file))})
                if parsed is not None:
                    break
        with open(out / "steps.jsonl", "a") as f:
            for t in tries:
                f.write(json.dumps(t) + "\n")
        steps.extend(tries)
        return parsed

    # ---------- the plan: as in X7 ----------
    P = v.v7.prices()
    plan, returns, plan_raw, ended, why = None, [], None, None, {}
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
        d = RUNS_X8 / run / "moments" / a
        st = stage(run, a)
        kept = json.loads((d / "answers.json").read_text())
        hand = [("the baseline", i) for i in BASELINE[a]] + [("your plan", i) for i in plan[a]]
        shown = [v.show_answer(kept[i], src) for src, i in hand]
        left_at_wake = left
        rec = sqlite3.connect(d / "record.sqlite")
        asked_all = []

        def take_named(named_raw, taken, notes, asked):
            """One request for answers on named lines: one entry for an instrument at most."""
            nonlocal left
            seen = set()
            for entry in ([named_raw] if isinstance(named_raw, dict) else named_raw or []):
                entry = entry if isinstance(entry, dict) else {"instrument": entry}
                inst = norm_named(entry.get("instrument"))
                raw_lines = entry.get("lines") or []
                raw_lines = raw_lines if isinstance(raw_lines, list) else [raw_lines]
                log = {"instrument": inst or str(entry.get("instrument")), "lines_named": raw_lines, "reason": entry.get("reason"),
                       "lines_taken": [], "lines_not_paid": [], "lines_refused": [], "price": 0,
                       "allowance_left_before": left, "questions_in_the_log_before": len(lg.entries(log_file))}
                asked.append(log)
                if not inst:
                    notes.append(f'There is no instrument on named lines "{entry.get("instrument")}", so nothing was taken.')
                    continue
                if a not in NAMED[inst]:
                    notes.append(f'"{inst}" can be taken at {", ".join(NAMED[inst])} and not at {a}, so nothing was taken.')
                    continue
                if inst in seen:
                    notes.append(f'"{inst}" is asked for once in a request (rule 14). The second entry was not taken.')
                    continue
                seen.add(inst)
                for x in raw_lines:
                    ln = int(x) if str(x).strip().lstrip("-").isdigit() else None
                    row = rec.execute("SELECT tool FROM record WHERE seq=?", (ln,)).fetchone() if ln is not None else None
                    if row is None or row[0] != NAMED_TOOL[inst]:
                        what = "a read call" if inst == "scope of a call" else "a sending call"
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

        def to_hand(answers):
            for s in answers:
                in_hand.append({"answer": s["answer"], "instrument": s["instrument"], "taken_for": s["taken_for"], "at": a,
                                "result": s["result"], "by": s["named_by"], "price": s["price"]["total"], "returns": s["returns"]})

        # the wake's one request, as in X7
        req = ask(a + "_ask", a, a, v.prompt_wake(cond, run, a, shown, left), {"a": a, "stage": st}) or {}
        wanted, unknown = split(req.get("take"), lambda x: norm_instrument(x) if norm_instrument(x) in PLACES else None)
        taken, notes = [], []
        for u in unknown:
            notes.append(f'There is no instrument of a plan "{u}", so nothing was taken.')
        for i in wanted:
            pr = P.get(f"{i} @ {a}", {}).get("price")
            if a not in PLACES[i]:
                notes.append(f'"{i}" cannot be taken at {a}, so nothing was taken.')
            elif i in [x for _, x in hand] or i in [x["instrument"] for x in asked_all]:
                notes.append(f'"{i}" is already in hand for this approval and was not taken again.')
            elif pr > left:
                notes.append(f'"{i}" costs {pr} and the allowance has {left} left, so it was not taken.')
                asked_all.append({"instrument": i, "paid": False, "price": pr})
            else:
                left -= pr
                asked_all.append({"instrument": i, "paid": True, "price": pr})
                taken.append(v.show_answer(kept[i], "asked for now"))
        take_named(req.get("on_named_lines"), taken, notes, asked_all)
        to_hand(shown + taken)
        form = ask(a, a, a, v.prompt_form(cond, a, taken, notes), {"a": a, "in_hand": in_hand, "stage": st})

        # every sending of the form, the audit's check of each, and in D and DF the return
        sendings, n_returns, asks_after, not_accepted = [], 0, [], False
        while True:
            log = lg.entries(log_file)
            decision = str((form or {}).get("decision" if a != "A3" else "verdict", "")).strip().lower()
            chk = (lg.audit((form or {}).get("the_record_of_this_stage"), log, RUNS_X8 / run, c["took"], st)
                   if c["statement"] else None)
            sendings.append({"form": form, "decision": decision, "questions_in_the_log": len(log),
                             "the_log_holds": {k: x for k, x in lg.holds(log, RUNS_X8 / run, c["took"], st).items() if k != "not_read"},
                             "check_of_the_statement": chk})
            lacking = c["duty"] and decision == "approve" and not (chk["says_in_full"] and chk["read_in_full_by_the_log"])
            if form is None or not lacking:
                break
            if n_returns == 2:
                not_accepted = True
                break
            n_returns += 1
            sendings[-1]["returned"] = n_returns
            h = lg.holds(log, RUNS_X8 / run, c["took"], st)
            if n_returns == 1:
                req2 = ask(a + "_ask_after_return", a, a, v.prompt_returned_1(a, h), {"a": a, "stage": st, "returned": 1}) or {}
                taken2, notes2, asked2 = [], [], []
                take_named(req2.get("on_named_lines"), taken2, notes2, asked2)
                for x in asked2:
                    x["after_a_return"] = True
                asked_all += asked2
                asks_after.append({"asked_raw": req2.get("on_named_lines"), "reason": req2.get("reason"), "notes": notes2})
                to_hand(taken2)
                form = ask(a + "_again_1", a, a, v.prompt_form(cond, a, taken2, notes2, again=True),
                           {"a": a, "in_hand": in_hand, "stage": st, "returned": 1})
            else:
                form = ask(a + "_again_2", a, a, v.prompt_returned_2(cond, a, h), {"a": a, "in_hand": in_hand, "stage": st, "returned": 2})
        rec.close()
        wakes[a] = {"stage": list(st), "allowance_left_at_the_wake": left_at_wake, "allowance_left_after": left,
                    "asked_raw": {"take": req.get("take"), "on_named_lines": req.get("on_named_lines")},
                    "ask_reason": req.get("reason"), "asked": asked_all, "notes": notes,
                    "answers": [{k: x[k] for k in ("answer", "instrument", "taken_for", "result", "by", "price")}
                                | ({"lines": [p["line"] for p in x["returns"]["lines"]],
                                    "lines_with_a_breach": [p["line"] for p in x["returns"]["lines"] if p["result"] != R_PASS]}
                                   if x["instrument"] in NAMED else {})
                                for x in in_hand if x["at"] == a],
                    "sendings": sendings, "returns": n_returns, "asked_after_a_return": asks_after,
                    "approval_not_accepted": not_accepted, "form": form}
        if not_accepted:
            ended = f"approval not accepted at {a}"
            break
        if a != "A3" and decision != "approve":
            ended = f"refused at {a}" if decision == "refuse" else f"no readable decision at {a}"
            break
        if a == "A3":
            ended = f"verdict: {decision or 'not readable'}"

    tok = {k: sum(s["tokens"][k] for s in steps) for k in ZERO}
    acts = {}
    for s in steps:
        dd = acts.setdefault(s["act"], {"cost_usd": 0, "wall_s": 0, "tokens": 0})
        dd["cost_usd"] = round(dd["cost_usd"] + (s["cost_usd"] or 0), 4)
        dd["wall_s"] = round(dd["wall_s"] + s["wall_s"], 1)
        dd["tokens"] += sum(s["tokens"].values())
    summary = {"who": who, "is_a_script": bool(script), "model_id": MODELS.get(who), "condition": cond,
               "models_reported": sorted(m.models) if m else [], "run": run, "n": n, "session": m.sid if m else None,
               "plan": plan, "plan_reasons": why if plan is not None else None, "plan_form": plan_raw, "plan_price": plan_price,
               "plan_returns": returns, "wakes": wakes, "ended": ended,
               "cut_off_by_the_runtime": any(s["is_error"] for s in steps) or (plan is not None and any(w["form"] is None for w in wakes.values())),
               "allowance_spent": ALLOWANCE - left,
               "replies_that_needed_a_second_try": sum(1 for s in steps if s["attempt"] == 2),
               "tokens": tok, "wall_s": round(sum(s["wall_s"] for s in steps), 1),
               "cost_usd": round(sum(s["cost_usd"] or 0 for s in steps), 4), "by_act": acts,
               "agent_turns": sum(s["turns"] or 0 for s in steps)}
    (out / "session.json").write_text(json.dumps(summary, indent=1))
    rets = sum(w["returns"] for w in wakes.values())
    return (f"{who}/{cond}/{run}/{n}: {summary['wall_s']}s, ${summary['cost_usd']}, plan at {plan_price}, {ended}, "
            f"returns {rets}, allowance spent {ALLOWANCE - left}, questions {len(lg.entries(log_file))}, "
            f"second tries {summary['replies_that_needed_a_second_try']}")


def safe(job):
    try:
        return session(*job[:4], kind=job[4])
    except Exception as e:
        import traceback
        return f"{job}: FAILED {e!r}\n{traceback.format_exc()}"


if __name__ == "__main__":
    a = sys.argv[1:]
    kind = "pilot" if "--pilot" in a else "sessions"
    a = [x for x in a if x != "--pilot"]
    jobs = [(a[0], a[1], a[2], int(n), kind) for n in a[3:]]
    with ThreadPoolExecutor(max_workers=5) as ex:
        for msg in ex.map(safe, jobs):
            print(msg, flush=True)
