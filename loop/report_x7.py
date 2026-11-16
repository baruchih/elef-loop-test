"""Experiment X7: the tables, from results_x7/scores.json. Usage: python -m loop.report_x7"""
import json
from collections import Counter

from .fixes import MODELS
from . import reading_x7
from .report_x1 import table, cnt
from .views_x7 import CLAUSES
from .x1 import APPROVALS
from .x7 import RESULTS_X7, CUTS

WATCH = ["C3", "C5", "C7", "C10"]


def main():
    S = json.loads((RESULTS_X7 / "scores.json").read_text())["sessions"]
    M = [s for s in S if not s["script"]]
    SC = [s for s in S if s["script"]]
    whos = list(MODELS)

    def sel(who, run=None, pool=M):
        return [s for s in pool if s["who"] == who and (run is None or s["run"] == run)]

    out = ["# Loop experiment X7: tables", "",
           f"{len(M)} sessions, and {len(SC)} passes of the three scripts. Made by `python -m loop.report_x7` from `results_x7/scores.json`.", ""]

    # ---------- 1. finding ----------
    out += ["## 1. Finding, on the runs with a cut", "",
            "Sessions that passed each step. For run U there is no step of looking or raising.", ""]
    rows = []
    for run in ("U", "R1", "R2"):
        for w in whos + sorted({s["who"] for s in SC}):
            ss = sel(w, run, M if w in whos else SC)
            f = [s["finding"] for s in ss]
            n = len(ss)
            g = lambda k: sum(1 for x in f if x.get(k))      # noqa: E731
            rows.append([run, w, n, "—" if run == "U" else g("looked"), "—" if run == "U" else g("raised"), g("asked"),
                         "—" if run == "U" else g("could_not_ask"), g("proved"), g("ruled"),
                         cnt(Counter(x["where"] for x in f if x["where"])), cnt(Counter(x["furthest"] for x in f))])
    out += [table(["run", "reviewer", "sessions", "looked", "raised", "asked", "could not ask", "proved", "ruled",
                   "where the catch came", "furthest step reached"], rows), ""]
    out += ["How the three lines were chosen, for each find on R1 and R2; and for run U, how the rehearsal came:", ""]
    rows = []
    for run in ("U", "R1", "R2"):
        for w in whos:
            f = [s["finding"] for s in sel(w, run)]
            if run == "U":
                rows.append([run, w, cnt(Counter(x["how"] for x in f)), cnt(Counter(str(x["clause_entered_as"]) for x in f if x["proved"]))])
            else:
                rows.append([run, w, cnt(Counter(x["lines_chosen"]["by"] for x in f if x["lines_chosen"])) + "; asked on other lines only: "
                             + str(sum(1 for x in f if x["asked_on_other_lines_only"])),
                             cnt(Counter(str(x["clause_entered_as"]) for x in f if x["proved"]))])
    out += [table(["run", "model", "how", "its clause entered as, where proved"], rows), ""]

    # ---------- 2. the plans ----------
    out += ["## 2. The plans", ""]
    rows = []
    for w in whos + sorted({s["who"] for s in SC}):
        ss = [s for s in sel(w, None, M if w in whos else SC) if s["plan"] is not None]
        n = len(ss)
        lines, pr = [s["lines_added"] for s in ss], [s["plan_price"] for s in ss]
        rows.append([w, n, f"{sum(lines) / n:.1f} ({min(lines)}–{max(lines)})", f"{sum(pr) / n:.0f} ({min(pr)}–{max(pr)})",
                     cnt(Counter(s["undo_in_plan"] for s in ss)), sum(1 for s in ss if s["is_the_plan_of_the_lookup_by_clause"]),
                     cnt(Counter(s["plan_clauses"]["C7"]["state"] for s in ss)),
                     sum(1 for s in ss if s["plan_reached_the_cap"]), sum(s["plan_returns"] for s in sel(w, None, M if w in whos else SC)),
                     f"{sum(pr) / n - 114:.0f}"])
    out += [table(["reviewer", "plans", "lines added: mean (range)", "price: mean (range)", "undo rehearsal after the promotion",
                   "the lookup's plan exactly", "C7 in the plan's clause list", "at the cap", "returned for price",
                   "price above the fixed policy's plan (114)"], rows), ""]
    rows = []
    for w in whos:
        k = Counter(f"{i} @ {a}" for s in sel(w) if s["plan"] for a in APPROVALS for i in s["plan"][a])
        rows.append([w, cnt(k)])
    out += ["Lines added, by place:", "", table(["model", "lines"], rows), ""]

    # ---------- 3. clean work ----------
    out += ["## 3. Clean work (run 0)", ""]
    rows = []
    for w in whos:
        ss = sel(w, "0")
        asked = [x for s in ss for x in s.get("asked_during_the_work", []) if x["paid"]]
        rows.append([w, len(ss), cnt(Counter(s["ending"] for s in ss)),
                     sum(1 for s in ss if s.get("refused_or_withheld_with_no_answer_behind_it")),
                     sum(1 for s in ss if any(x["paid"] for x in s.get("asked_during_the_work", []))),
                     len(asked), sum(x["price"] for x in asked), sum(1 for x in asked if x["found_a_breach"]),
                     f"{sum(len(w_['raise_raw']) for s in ss for w_ in s.get('wakes', {}).values()) / max(1, len(ss)):.1f}"])
    out += [table(["model", "sessions", "ending", "refusals or withheld verdicts", "sessions that asked for an answer",
                   "answers asked for", "their price, in all", "of them found a breach", "things raised, mean for a session"], rows), ""]
    out += ["The answers asked for on clean work, by the kind of reason: count, and price in units.", ""]
    rows = []
    kinds = ["the record showed something on those lines", "a sample taken to show a clause in part", "none given", "not sorted"]
    for w in whos:
        asked = [x for s in sel(w, "0") for x in s.get("asked_during_the_work", []) if x["paid"]]
        rows.append([w] + [f"{sum(1 for x in asked if x['kind_of_reason'] == k)} answers, {sum(x['price'] for x in asked if x['kind_of_reason'] == k)} units"
                           for k in kinds] + [cnt(Counter(x["instrument"] + " @ " + x["at"] for x in asked))])
    out += [table(["model"] + kinds + ["which"], rows), ""]

    out += ["What was raised on clean work, by kind (a keyword reading): items in all.", ""]
    allk = sorted({k for s in M for k in s.get("raised_by_kind", {})})
    out += [table(["model"] + allk, [[w] + [sum(s.get("raised_by_kind", {}).get(k, 0) for s in sel(w, "0")) for k in allk] for w in whos]), ""]

    # ---------- 4. the clause lists ----------
    out += ["## 4. The clause lists", "", "Entries by score, at the plan and at each approval, all runs together.", ""]
    rows = []
    for w in whos:
        for where in ["plan"] + APPROVALS:
            for c in CLAUSES:
                es = [(s["plan_clauses"] if where == "plan" else s.get("wakes", {}).get(where, {}).get("clauses", {})).get(c)
                      for s in sel(w) if s["plan"] is not None]
                es = [e for e in es if e]
                if not es:
                    continue
                k = Counter(e["score"] for e in es)
                two = Counter(e["state"] for e in es if e["score"] == "right" and len(e["key"]) > 1)
                kc = Counter(e["score_on_the_corrected_key"] for e in es)
                rows.append([w, where, c, len(es), f'{k["right"]} ({kc["right"]})', k["over-claimed"], k["under-claimed"],
                             k["a breach in hand, and not entered as broken"], k["broken, with no answer in hand that found a breach"],
                             k["not readable"], cnt(two) if two else "",
                             sum(1 for e in es if e.get("names_an_answer_that_shows_it") is False and e["score"] == "right")])
    out += [table(["model", "where", "clause", "entries", "right (on the corrected key)", "over-claimed", "under-claimed", "a breach in hand, not entered as broken",
                   "broken with no such answer", "not readable", "where two entries are right: which", "right state, names another answer"],
                  [r for r in rows if r[2] in WATCH or r[5] or r[6] or r[7] or r[8] or r[9] or r[10]]), "",
            "Rows are left out where every entry is right and the key takes one entry only, except for C3, C5, C7 and C10.", ""]

    # ---------- 5. rulings ----------
    out += ["## 5. Rulings and the audit", ""]
    rows = []
    for w in whos + sorted({s["who"] for s in SC}):
        for run in CUTS:
            ss = sel(w, run, M if w in whos else SC)
            rows.append([w, run, len(ss), cnt(Counter(s.get("ending", s["ended"]) for s in ss))])
    out += [table(["reviewer", "run", "sessions", "ending"], rows), ""]
    rows = []
    for w in whos:
        ss = sel(w)
        au = [x["audit"] for s in ss for x in s.get("wakes", {}).values() if x.get("audit")]
        cl = [s["wakes"]["A3"]["closing"] for s in ss if "A3" in s.get("wakes", {})]
        rows.append([w, len(au), sum(1 for s in ss for _ in s.get("approvals_given_while_a_breach_stood", [])),
                     sum(1 for a in au if a["passes"]), sum(1 for a in au if a["an_answer_left_out"]),
                     sum(1 for a in au if a["names_something_not_in_hand"]),
                     sum(1 for s in ss if s.get("refused_or_withheld_with_no_answer_behind_it")),
                     sum(1 for s in ss if s.get("finding", {}).get("proved") and not s["finding"]["ruled"]),
                     f"{sum(1 for c in cl if c['four_numbers_right'])}/{len(cl)}", f"{sum(1 for c in cl if c['may_right'])}/{len(cl)}"])
    out += [table(["model", "approvals given", "given while a breach stood", "pass the audit", "an answer left out",
                   "name something not in hand", "refusals or withheld verdicts with no answer behind them",
                   "proved and not ruled on", "closing summary: four numbers right", "may still be sent = 0"], rows), ""]

    # ---------- 6. cost ----------
    out += ["## 6. Cost", "", "Cost is the figure the runtime reports for a session.", ""]
    rows = []
    for w in whos:
        for run in list(CUTS) + [None]:
            ss = sel(w, run)
            n = len(ss)
            acts = [(f"${sum(s['by_act'].get(a, {}).get('cost_usd', 0) for s in ss) / sum(1 for s in ss if a in s['by_act']):.3f}"
                     if any(a in s["by_act"] for s in ss) else "—") for a in ["plan"] + APPROVALS]
            rows.append([w, run or "all", n, f"${sum(s['cost_usd'] for s in ss):.2f}", f"${sum(s['cost_usd'] for s in ss) / n:.3f}",
                         f"{sum(s['wall_s'] for s in ss) / n:.0f} s"] + acts +
                        [f"{sum(s['allowance_spent'] for s in ss) / n:.1f}", f"{sum(s['record_questions'] for s in ss) / n:.1f}",
                         sum(s["tokens"]["output"] for s in ss), sum(s["tokens"]["cache_read"] for s in ss),
                         sum(s["tokens"]["cache_write"] for s in ss), sum(s["second_tries"] for s in ss)])
    rows.append(["all", "all", len(M), f"${sum(s['cost_usd'] for s in M):.2f}"] + [""] * 12 + [sum(s["second_tries"] for s in M)])
    out += [table(["model", "run", "sessions", "cost", "a session", "wall, mean", "the plan", "wake A1", "wake A2", "the verdict",
                   "allowance spent, mean", "questions to the record, mean", "output tokens", "cache read", "cache write",
                   "replies asked for again"], rows), ""]
    # ---------- 7. how much of the record was read ----------
    R = reading_x7.main()
    out += ["## 7. How much of the record a session read", "",
            "From the logs of the questions to the record, by `python -m loop.reading_x7`; no new session. "
            "A question covers all the account reads if it is a count grouped by `rows` over lines that take in all hundred of them, "
            "or if the hundred lines themselves were shown, over one question or several. "
            "A sending line counts when both its times were returned to the session. The sending lines are in the record only at A3, "
            "so that column is over the sessions that reached A3.", ""]
    rows = []
    for run in CUTS:
        for w in whos:
            rs = [r for r in R if r["who"] == w and r["run"] == run]
            a3 = [r["sending_lines_with_their_times_returned"] for r in rs if r["reached_A3"]]
            rows.append([w, run, len(rs), f"{sum(r['questions'] for r in rs) / len(rs):.1f}",
                         sum(1 for r in rs if r["all_the_account_reads_covered"]),
                         sum(1 for r in rs if r["a_count_by_rows_over_all_the_account_reads"]),
                         sum(1 for r in rs if r["account_read_lines_shown"] == 100),
                         len(a3), f"{sum(a3) / len(a3):.1f} ({min(a3)}–{max(a3)})" if a3 else "—",
                         sum(1 for x in a3 if x == 100) if a3 else "—", sum(1 for x in a3 if x == 0) if a3 else "—"])
    out += [table(["model", "run", "sessions", "questions to the record, mean", "covered all the account reads",
                   "by a count by rows", "by all hundred lines shown", "reached A3",
                   "sending lines with their times returned, of 100: mean (range)", "sessions with all 100", "sessions with none"], rows), ""]
    (RESULTS_X7 / "tables.md").write_text("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
