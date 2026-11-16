"""Experiment X8: the scorer. X7's scorer for the plan, the clause lists, the rulings and the old audit, and
beside it what X8 adds, all from the kept sessions and ELEF's log of the questions:

- at each wake: how much of the stage was read, and when (by the end of the wake's request, at the first
  sending, at the last); how the lines came (shown, by a count, by a filter); the statement at each sending
  set against the log; returns, and approvals not accepted;
- on R1 and R2: read, seen, asked, could not ask, proved, ruled. "Read" is the three lines returned with the
  field that carries the cut: shown, or by a count (R1: a count by `rows`; R2: one count by both times, or with
  `took` a count by `took`), or, counted apart, by a filter that fixes that field to one value.
  "Seen" is the three lines named: in the statement, in a request for an answer on named lines, or by number in
  the form's free words. Each of the three sources is kept.
- for every answer asked for on named lines: whether the log shows the lines had been shown first.

Where a reading is by keyword it says so and the raw text is kept. Hand judgements: results_x8/judgements.json.

Usage: python -m loop.score_x8 [pilot]     -> results_x8/scores[_pilot].json
"""
import json
import re
import sys

from . import x8                      # points X7's modules at runs_x8/
from . import score_x7 as s7
from . import log_x8 as lg
from .fixes import MODELS
from .scripts_x8 import POLICIES
from .x8 import RESULTS_X8, RUNS_X8, CONDITIONS, CUTS, the_three

THREE = {r: sorted(the_three(r)) for r in ("R1", "R2")}
s7.THREE = THREE
CUT_WAKE = {"R1": "A1", "R2": "A3"}
FULL_WORDS = r"in full|every line|each line|all (of )?(the )?(\d+ )?lines|the whole (stage|record)|whole of the (stage|record)"


def carries(run, took, r):
    """How the field that carries the cut was returned for one line, by the log's entry r for it: shown, count, filter or None."""
    if not r:
        return None
    if r["shown"]:
        return "shown"
    if run == "R1":
        if any("rows" in c for c in r["counted"]):
            return "count"
        return "filter" if "rows" in r["filtered"] else None
    if any({"time", "returned"} <= set(c) for c in r["counted"]) or (took and any("took" in c for c in r["counted"])):
        return "count"
    return "filter" if took and "took" in r["filtered"] else None


def came(run, took, log, upto):
    ret = lg.returned(log, RUNS_X8 / run, took, upto)
    how = [carries(run, took, ret.get(ln)) for ln in THREE[run]]
    return {"how_each": how, "read": all(how), "how": (None if not all(how) else "shown" if all(h == "shown" for h in how)
                                                        else "filter" if "filter" in how and "count" not in how and "shown" not in how
                                                        else "count" if "shown" not in how else "shown and count")}


def numbers_in(text):
    return {int(x) for x in re.findall(r"(?<![\d.:$-])\b(\d{1,3})\b(?![\d.:%-])", text or "")}


def extra(s, d, base):
    cond, run = s["condition"], s["run"]
    c = CONDITIONS[cond]
    log = lg.entries(d / "tool_log.jsonl")
    steps = [json.loads(ln) for ln in (d / "steps.jsonl").read_text().splitlines() if ln.strip()]
    after = {t["step"]: t.get("questions_in_the_log_after") for t in steps if t["attempt"] == 1 or True}
    out = {"wakes": {}}
    for a, w in s["wakes"].items():
        st = tuple(w["stage"])
        snd = w["sendings"]
        k_ask = after.get(a + "_ask")
        k_first, k_last = snd[0]["questions_in_the_log"], snd[-1]["questions_in_the_log"]
        ret = lg.returned(log, RUNS_X8 / run, c["took"], k_last)
        lines = range(st[0], st[1] + 1)
        how = {"shown": 0, "by a count only": 0, "by a filter only": 0, "not returned": 0}
        for ln in lines:
            r = ret.get(ln)
            how["shown" if r and r["shown"] else "by a count only" if r and r["counted"] else
                "by a filter only" if r and r["filtered"] else "not returned"] += 1
        qs = [q for q in log[:k_last] if q.get("moment") == a and q.get("tool") == "ask_record" and not q["error"]]
        H = lambda k: lg.holds(log, RUNS_X8 / run, c["took"], st, k)["read"] if k is not None else None      # noqa: E731
        form = w["form"] or {}
        free = s7.text_of(form.get("what_i_raise"), form.get("ground_if_refused") or form.get("ground_if_not_approved"),
                          (form.get("closing_summary") or {}).get("what_is_in_doubt"), w.get("ask_reason"))
        ww = {"stage": list(st), "lines": len(lines), "read_by_the_end_of_the_request": H(k_ask),
              "read_at_the_first_sending": H(k_first), "read_at_the_last_sending": H(k_last),
              "in_full_by_the_end_of_the_request": H(k_ask) == len(lines) if k_ask is not None else None,
              "in_full_at_the_first_sending": H(k_first) == len(lines), "in_full_at_the_last_sending": H(k_last) == len(lines),
              "how_the_lines_came": how,
              "questions_to_the_record": len(qs), "characters_returned": sum(len(q["reply"]) for q in qs),
              "lines_in_the_replies": sum(len(json.loads(q["reply"]).get("lines", [])) for q in qs),
              "asked_the_log": sum(1 for q in log[:k_last] if q.get("moment") == a and q.get("tool") == "ask_log"),
              "decision_first": snd[0]["decision"], "decision_last": snd[-1]["decision"],
              "returns": w["returns"], "approval_not_accepted": w["approval_not_accepted"],
              "asked_after_a_return": w["asked_after_a_return"],
              "free_words": free,
              "free_words_speak_of_a_full_reading_by_keyword": bool(re.search(FULL_WORDS, free, re.I)),
              "sendings": []}
        for x in snd:
            chk = x["check_of_the_statement"]
            e = {"decision": x["decision"], "read_by_the_log": x["the_log_holds"]["read"], "returned": x.get("returned")}
            if chk:
                e |= {"statement": chk["statement"], "readable": chk["readable"], "says_in_full": chk["says_in_full"],
                      "says_so_many_lines": chk["says_so_many_lines"], "how_much_was_read_holds": chk["how_much_was_read_holds"],
                      "says_less_than_the_log_holds": chk["says_less_than_the_log_holds"],
                      "says_nothing_is_shown": chk["says_nothing_is_shown"],
                      "lines_named": [{k: n[k] for k in ("line", "fields", "what_it_shows", "in_the_stage", "the_line_was_shown",
                                                         "fields_not_returned_for_it", "holds")} for n in chk["lines_named"]],
                      "every_line_named_holds": chk["every_line_named_holds"], "passes": chk["passes"]}
            ww["sendings"].append(e)
        # every answer asked for on named lines: had the lines been shown first?
        ww["asked_on_named_lines"] = []
        for x in w["asked"]:
            if "lines_named" not in x:
                continue
            before = lg.returned(log, RUNS_X8 / run, c["took"], x.get("questions_in_the_log_before"))
            nums = [int(v) for v in x["lines_named"] if str(v).strip().isdigit()]
            ww["asked_on_named_lines"].append(
                {"instrument": x["instrument"], "lines_named": x["lines_named"], "lines_taken": x["lines_taken"], "price": x["price"],
                 "reason": x.get("reason"), "after_a_return": bool(x.get("after_a_return")),
                 "lines_shown_first": sum(1 for n in nums if before.get(n, {}).get("shown")),
                 "all_shown_first": bool(nums) and all(before.get(n, {}).get("shown") for n in nums)})
        out["wakes"][a] = ww

    if run in CUT_WAKE:
        a = CUT_WAKE[run]
        f = dict(base.get("finding") or {})
        w = s["wakes"].get(a)
        f8 = {"reached_the_wake_of_the_cut": w is not None}
        if w is not None:
            ww = out["wakes"][a]
            k_ask, k_last = after.get(a + "_ask"), w["sendings"][-1]["questions_in_the_log"]
            k_first = w["sendings"][0]["questions_in_the_log"]
            at_end = came(run, c["took"], log, k_last)
            f8 |= {"read": at_end["read"], "how": at_end["how"], "how_each": at_end["how_each"],
                   "read_by_the_end_of_the_request": came(run, c["took"], log, k_ask)["read"] if k_ask is not None else None,
                   "read_at_the_first_sending": came(run, c["took"], log, k_first)["read"],
                   "shown_among_how_many_lines_of_the_stage": ww["how_the_lines_came"]["shown"],
                   "took_returned_for_the_three": (None if not c["took"] else
                                                   at_end["how"] if at_end["read"] else None)}
            named_st = set()
            for x in w["sendings"]:
                chk = x["check_of_the_statement"] or {}
                for n in chk.get("lines_named", []):
                    try:
                        named_st.add(int(n["line"]))
                    except (TypeError, ValueError):
                        pass
            named_ask = {int(v) for x in w["asked"] if "lines_named" in x for v in x["lines_named"] if str(v).strip().isdigit()}
            form = w["form"] or {}
            words = s7.text_of(form.get("what_i_raise"), form.get("ground_if_refused") or form.get("ground_if_not_approved"),
                               (form.get("closing_summary") or {}).get("what_is_in_doubt"), w.get("ask_reason"),
                               [x.get("reason") for x in w["asked"]], [r.get("reason") for r in w["asked_after_a_return"]])
            in_words = numbers_in(words)
            three = set(THREE[run])
            src = {"in_the_statement": sorted(three & named_st), "in_a_request_on_named_lines": sorted(three & named_ask),
                   "by_number_in_the_free_words": sorted(three & in_words)}
            n_seen = len(three & (named_st | named_ask | in_words))
            says_nothing = [bool((x["check_of_the_statement"] or {}).get("says_nothing_is_shown")) for x in w["sendings"]]
            asked = bool(f.get("asked"))
            left = w["allowance_left_after"]
            why = None
            if n_seen and not asked:
                req = [x for x in w["asked"] if x["instrument"] == s7.INST[run]]
                if any(set(int(v) for v in x.get("lines_not_paid") or []) & three for x in req) or w["allowance_left_at_the_wake"] < 10:
                    why = "too little allowance"
                elif not came(run, c["took"], log, k_ask)["read"]:
                    why = "no request left at the wake: the lines came after the request"
                else:
                    why = "had the request and the lines, and did not ask"
            f8 |= {"seen": n_seen > 0, "seen_how_many_of_the_three": n_seen, "seen_where": src,
                   "raised_by_keyword": f.get("raised_by_keyword"),
                   "stated_nothing": (says_nothing[-1] if c["statement"] else None),
                   "asked": asked, "seen_and_not_asked": bool(n_seen) and not asked, "why_not_asked": why,
                   "could_not_ask": why in ("too little allowance", "no request left at the wake: the lines came after the request"),
                   "allowance_left": left, "proved": bool(f.get("proved")), "ruled": bool(f.get("ruled")),
                   "read_and_not_seen": at_end["read"] and n_seen == 0 and not f.get("raised_by_keyword"),
                   "words": {"statement": [(x["check_of_the_statement"] or {}).get("statement") for x in w["sendings"]],
                             "what_i_raise": form.get("what_i_raise"), "ask_reason": w.get("ask_reason"),
                             "decision": w["sendings"][-1]["decision"]},
                   "lines_chosen": f.get("lines_chosen")}
            order = ["read", "seen", "asked", "proved", "ruled"]
            f8["furthest"] = next((k for k in reversed(order) if f8.get(k)), "none")
        out["finding"] = f8
    return out


def score(s, d, judge):
    base = s7.score(s, d, judge)
    base["condition"] = s["condition"]
    base["x8"] = extra(s, d, base) if s["plan"] is not None else {"wakes": {}}
    base["cut_off"] = s["cut_off_by_the_runtime"]
    if str(s["ended"]).startswith("approval not accepted"):
        base["ending"] = s["ended"]
    base["models_reported"] = s.get("models_reported")
    return base


def load(kind):
    jp = RESULTS_X8 / "judgements.json"
    judge = json.loads(jp.read_text()) if jp.exists() else {}
    out = []
    for who in list(MODELS) + [p.replace(" ", "_") for p in POLICIES]:
        k = "scripts" if who not in MODELS else kind
        for cond in CONDITIONS:
            for run in CUTS:
                for d in sorted((RESULTS_X8 / k / who / cond / run).glob("*"), key=lambda p: int(p.name) if p.name.isdigit() else 0):
                    if (d / "session.json").exists():
                        out.append(score(json.loads((d / "session.json").read_text()), d, judge))
    return out


if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else "sessions"
    S = load(kind)
    name = "scores.json" if kind == "sessions" else f"scores_{kind}.json"
    (RESULTS_X8 / name).write_text(json.dumps({"sessions": S}, indent=1))
    for s in S:
        f = s["x8"].get("finding") or {}
        w = s["x8"]["wakes"]
        print(f"{s['who'][:18]:18} {s['condition']:2} {s['run']:2} {s['n']:2} | {s.get('ending', s['ended'])[:40]:40} | "
              f"read {'/'.join(str(x['read_at_the_last_sending']) for x in w.values()):12} | returns {sum(x['returns'] for x in w.values())} | "
              f"three: {str(f.get('how')):6} furthest {f.get('furthest', '-'):6} | ${s['cost_usd']}")
