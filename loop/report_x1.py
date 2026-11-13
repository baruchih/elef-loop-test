"""Experiment X1: the tables, from results_x1/scores.json. Usage: python -m loop.report_x1"""
import json
from collections import Counter, defaultdict

from .common import I_SUMMARY
from .fixes import I_TRACE, MODELS
from .x1 import RESULTS_X1, APPROVALS, CUTS

CONDS = ["priced", "free"]
REF = {"A1": [I_SUMMARY], "A2": [], "A3": [I_TRACE]}


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def cnt(c):
    return "; ".join(f"{k}: {v}" for k, v in sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0])))) or "—"


def main():
    d = json.loads((RESULTS_X1 / "scores.json").read_text())
    S = d["sessions"]
    cells = [(m, c) for m in MODELS for c in CONDS]

    def sel(m, c, run=None):
        return [s for s in S if s["model"] == m and s["cond"] == c and (run is None or s["run"] == run)]

    out = ["# Loop experiment X1: tables", "",
           f"{len(S)} sessions. Made by `python -m loop.report_x1` from `results_x1/scores.json`.", ""]

    # ---------- the baseline alone ----------
    out += ["## The baseline alone and the reference plan, on the five runs", ""]
    rows = [[name, v["price"]] + [v["runs"][r] for r in CUTS] for name, v in d["baseline"].items()]
    out += [table(["", "price"] + [f"run {r}" for r in CUTS], rows), ""]

    # ---------- the plans ----------
    out += ["## The plans", ""]
    rows = []
    for m, c in cells:
        ss = [s for s in sel(m, c) if s["plan"] is not None]
        n = len(ss)
        lines = [s["plan_lines"] for s in ss]
        pr = [s["plan_price"] for s in ss]
        first2 = Counter(s["covers_run_2_first_at"] or "not covered" for s in ss)
        rows.append([m, c, n, f"{sum(lines) / n:.1f} ({min(lines)}–{max(lines)})",
                     f"{sum(pr) / n:.0f} ({min(pr)}–{max(pr)})",
                     sum(1 for s in ss if s["plan"] == REF), sum(s["plan_returns"] for s in sel(m, c)),
                     sum(1 for s in ss if s["covers_run_2"]), cnt(first2),
                     sum(1 for s in ss if s["covers_run_3"]),
                     f"{sum(len(s['repeats']) for s in ss)} lines, {sum(x['price'] for s in ss for x in s['repeats'])} units"])
    out += [table(["model", "condition", "plans", "lines added: mean (range)", "price: mean (range)",
                   "the reference plan exactly", "returned for price", "cover run 2", "run 2 first shown at",
                   "cover run 3", "lines that repeat an answer"], rows), ""]
    out += ["Lines added, by place:", ""]
    rows = []
    for m, c in cells:
        k = Counter(f"{i} @ {a}" for s in sel(m, c) if s["plan"] for a in APPROVALS for i in s["plan"][a])
        rows.append([m, c, cnt(k)])
    out += [table(["model", "condition", "lines"], rows), ""]

    out += ["Plan coverage on the five runs: plans with a line that finds a breach, and where it is first found.", ""]
    rows = []
    for m, c in cells:
        ss = [s for s in sel(m, c) if s["plan"] is not None]
        rows.append([m, c, len(ss)] + [cnt(Counter(s["coverage"][r]["first_at"] or "none" for s in ss)) for r in CUTS])
    out += [table(["model", "condition", "plans"] + [f"run {r}" for r in CUTS], rows), ""]

    # ---------- endings ----------
    out += ["## How the sessions ended, by run", ""]
    rows = []
    for m, c in cells:
        for r in ("0123" if c == "priced" else "03"):
            ss = sel(m, c, r)
            rows.append([m, c, r, len(ss), cnt(Counter(s["ending"] for s in ss)),
                         cnt(Counter(f"{s['catch']['instrument']} taken at {s['catch']['taken_at']}, from {s['catch']['from']}"
                                     for s in ss if s.get("catch")))])
    out += [table(["model", "condition", "run", "sessions", "ending", "the answer the catch rests on"], rows), ""]

    # ---------- rulings ----------
    out += ["## The rulings on the way", ""]
    rows = []
    for m, c in cells:
        ss = sel(m, c)
        given = [(s, a, w) for s in ss for a, w in s.get("wakes", {}).items() if w["decision"] == "approve"]
        bad = Counter(a for s in ss for a in s.get("approvals_given_while_a_breach_stood", []))
        rows.append([m, c, len(given), cnt(bad),
                     sum(1 for s in ss if str(s["ending"]).startswith("refused with no answer")),
                     sum(1 for s in ss if str(s["ending"]).startswith("verdict withheld")),
                     sum(1 for s in ss if s["ending"] == "insufficient evidence with a breach in hand"),
                     sum(1 for s in ss if s.get("catch") and not s["catch"]["breach_answer_named"])])
    out += [table(["model", "condition", "approvals given", "given while a breach stood, by approval",
                   "refusals with no answer behind them", "verdicts withheld with none",
                   "insufficient evidence with a breach in hand", "catches that did not name the breach answer"], rows), ""]

    out += ["## The audit of every approval given", ""]
    rows = []
    for m, c in cells:
        au = [w["audit"] for s in sel(m, c) for w in s.get("wakes", {}).values() if w.get("audit")]
        al = [(w["allowance_answers_named"], w["allowance_answers"]) for s in sel(m, c) for w in s.get("wakes", {}).values()
              if w.get("audit")]
        rows.append([m, c, len(au), sum(1 for a in au if a["passes"]), sum(1 for a in au if a["an_answer_left_out"]),
                     sum(1 for a in au if a["a_breach_found_at_this_wake"]),
                     sum(1 for a in au if a["a_breach_that_stood_from_earlier"]),
                     f"{sum(x for x, _ in al)} of {sum(y for _, y in al)}",
                     sum(1 for s in sel(m, c) for w in s.get("wakes", {}).values() if w["names_not_in_hand"])])
    out += [table(["model", "condition", "approvals given", "pass", "an answer left out", "a breach found at that wake",
                   "a breach that stood from earlier", "allowance answers named", "forms naming something not in hand"], rows), ""]

    # ---------- during the work ----------
    out += ["## Asked for during the work", ""]
    rows = []
    for m, c in cells:
        ss = sel(m, c)
        asked = [x for s in ss for x in s.get("asked_during_the_work", [])]
        rows.append([m, c, len(asked), cnt(Counter(f"{x['instrument']} @ {x['at']}" for x in asked)),
                     sum(1 for x in asked if x["found_a_breach"]), sum(s["allowance_spent"] for s in ss),
                     sum(1 for s in ss for w in s.get("wakes", {}).values() for n in w["notes"] if "allowance has" in n),
                     f"{sum(s['record_questions'] or 0 for s in ss) / max(1, len(ss)):.1f}"])
    out += [table(["model", "condition", "answers asked for", "which", "of them found a breach", "allowance spent, in all",
                   "answers the allowance could not pay", "questions to the record, mean"], rows), ""]

    # ---------- closing summary ----------
    out += ["## The closing summary, in sessions that reached A3", ""]
    rows = []
    for m, c in cells:
        cl = [(s, s["wakes"]["A3"]["closing"]) for s in sel(m, c) if "A3" in s.get("wakes", {}) and "closing" in s["wakes"]["A3"]]
        tr = [x for _, x in cl if x["trace_in_hand"]]
        no = [x for _, x in cl if not x["trace_in_hand"]]
        r3 = [x for s, x in cl if s["run"] == "3" and x["trace_in_hand"]]
        rows.append([m, c, len(cl), f"{sum(1 for _, x in cl if x['confirmed_right'])}/{len(cl)}",
                     f"{sum(1 for x in tr if x['rows_right'])}/{len(tr)}",
                     f"{sum(1 for x in no if x['rows_right'])}/{len(no)}",
                     f"{sum(1 for _, x in cl if x['may_right'])}/{len(cl)}",
                     f"{sum(1 for x in r3 if x['confirmed_right'] and x['rows_right'] and x['may_right'])}/{len(r3)}"])
    out += [table(["model", "condition", "reached A3", "confirmed = 100", "rows right, with a trace",
                   "'cannot be told', without a trace", "may still be sent = 0", "run 3 with a trace: 100 / 90 / 0"], rows), ""]

    # ---------- not checked ----------
    out += ["## What was given as not checked", "",
            "Each cell: named / due. A clause is due where no answer in hand (or no line of the plan) shows it. "
            "The last column of each pair counts where the clause was named though an answer showed it.", ""]
    rows = []
    for m, c in cells:
        for where in ["plan"] + APPROVALS:
            row = [m, c, where]
            for clause in ("K3 the category", "K2/K4 what was changed", "K8 whether a call sent"):
                xs = []
                for s in sel(m, c):
                    src = s.get("plan_not_shown") if where == "plan" else s.get("wakes", {}).get(where, {}).get("not_checked")
                    if src and clause in src:
                        xs.append(src[clause])
                due = [x for x in xs if x["due"]]
                nd = [x for x in xs if not x["due"]]
                row += [f"{sum(1 for x in due if x['named'])}/{len(due)}" if due else "—",
                        f"{sum(1 for x in nd if x['named'])}/{len(nd)}" if nd else "—"]
            rows.append(row)
    out += [table(["model", "condition", "where", "K3 named / due", "K3 not due", "K2/K4 named / due", "K2/K4 named, not due",
                   "K8 named / due", "K8 named, not due"], rows), ""]

    # ---------- raised ----------
    out += ["## What was raised", "", "Sessions that raised it at one approval or more. A keyword reading, checked by hand where the note says so.", ""]
    keys = list(next(w["raised"] for s in S for w in s.get("wakes", {}).values()))
    rows = []
    for m, c in cells:
        for r in ("0123" if c == "priced" else "03"):
            ss = sel(m, c, r)
            rows.append([m, c, r, len(ss)] + [sum(1 for s in ss if any(w["raised"][k] for w in s.get("wakes", {}).values())) for k in keys]
                        + [sum(1 for s in ss if any(w["says_notices_arrived"] for w in s.get("wakes", {}).values()))])
    out += [table(["model", "condition", "run", "sessions"] + keys + ["says that notices arrived"], rows), ""]

    # ---------- cost ----------
    out += ["## Tokens, wall time and cost", ""]
    rows = []
    for m, c in cells:
        ss = sel(m, c)
        t = defaultdict(int)
        for s in ss:
            for k, v in s["tokens"].items():
                t[k] += v
        rows.append([m, c, len(ss), f"${sum(s['cost_usd'] for s in ss):.2f}", f"${sum(s['cost_usd'] for s in ss) / len(ss):.3f}",
                     f"{sum(s['wall_s'] for s in ss) / len(ss):.0f} s", t["input"], t["output"], t["cache_read"], t["cache_write"],
                     sum(s["second_tries"] for s in ss)])
    rows.append(["all", "", len(S), f"${sum(s['cost_usd'] for s in S):.2f}", "", "", "", "", "", "", sum(s["second_tries"] for s in S)])
    out += [table(["model", "condition", "sessions", "cost", "per session", "wall, mean", "input", "output", "cache read",
                   "cache write", "replies asked for again"], rows), ""]
    out += ["Cost by act, mean per session that reached the act:", ""]
    rows = []
    for m, c in cells:
        row = [m, c]
        for act in ["plan"] + APPROVALS:
            xs = [s["by_act"][act]["cost_usd"] for s in sel(m, c) if act in s["by_act"]]
            row.append(f"${sum(xs) / len(xs):.3f} (n={len(xs)})" if xs else "—")
        rows.append(row)
    out += [table(["model", "condition", "the plan", "wake A1", "wake A2", "the verdict, A3"], rows), ""]

    (RESULTS_X1 / "tables.md").write_text("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
