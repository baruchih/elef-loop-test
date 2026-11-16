"""Experiment X8: the tables, from results_x8/scores.json, with X7's cells beside them.
Every cost is the corrected figure (a turn costs the difference of the runtime's running total).
Usage: python -m loop.report_x8"""
import json
from collections import Counter

from . import x8                      # noqa: F401
from . import cost
from .fixes import MODELS
from .report_x1 import table, cnt
from .score_x8 import THREE, CUT_WAKE
from .views_x7 import CLAUSES
from .x1 import APPROVALS
from .x8 import RESULTS_X8, CONDITIONS, ROOT

CONDS = list(CONDITIONS)
CELLS = [("0", "S"), ("0", "D"), ("0", "F"), ("0", "DF"), ("R1", "S"), ("R1", "D"),
         ("R2", "X"), ("R2", "S"), ("R2", "D"), ("R2", "F"), ("R2", "DF")]
WHOS = ["sonnet", "haiku", "opus"]


def pct(a, b):
    return f"{a}/{b}" if b else "—"


def mean(xs, f="{:.1f}"):
    xs = [x for x in xs if x is not None]
    return f.format(sum(xs) / len(xs)) if xs else "—"


def usd(xs, n=3):
    return mean(xs, "${:." + str(n) + "f}")


def main():
    S = json.loads((RESULTS_X8 / "scores.json").read_text())["sessions"]
    M = [s for s in S if not s["script"]]
    SC = [s for s in S if s["script"]]
    X7 = [s for s in json.loads((ROOT / "results_x7/scores.json").read_text())["sessions"] if not s["script"]]
    for s in X7:
        s["cost"], _, s["acts"] = cost.of_session(ROOT / "results_x7/sessions" / s["who"] / s["run"] / str(s["n"]))
    R7 = {(r["who"], r["run"], r["n"]): r for r in json.loads((ROOT / "results_x7/reading_of_the_record.json").read_text())}

    def sel(who=None, cond=None, run=None, pool=M):
        return [s for s in pool if (who is None or s["who"] == who) and (cond is None or s["condition"] == cond
                                                                          or (isinstance(cond, (list, tuple)) and s["condition"] in cond))
                and (run is None or s["run"] == run)]

    def x7(who, run):
        return [s for s in X7 if s["who"] == who and s["run"] == run]

    def cells(runs=None, conds=None, whos=WHOS):
        for run, cond in CELLS:
            if (runs and run not in runs) or (conds and cond not in conds):
                continue
            for w in whos:
                ss = sel(w, cond, run)
                if ss:
                    yield run, cond, w, ss

    W = lambda s, a: s["x8"]["wakes"].get(a)      # noqa: E731
    F = lambda s: s["x8"].get("finding") or {}      # noqa: E731

    out = ["# Loop experiment X8: tables", "",
           f"{len(M)} sessions, and {len(SC)} passes of the two scripts. Made by `python -m loop.report_x8` from `results_x8/scores.json`. "
           "Conditions: X, X7's rules and record; S, the statement; D, the statement and the duty; F, the field `took`; DF, both. "
           "Every cost is the corrected figure. X7's cells are from `results_x7/`, which ran before, on other lines.", ""]
    out += [table(["run", "condition"] + WHOS, [[run, cond] + [len(sel(w, cond, run)) for w in WHOS] for run, cond in CELLS]), ""]

    # ---------- 1. execution ----------
    out += ["## 1. Execution", "",
            "At A1 (107 lines) and at A3 (105 lines): sessions that had every line of the stage shown to them, by the end of the wake's request "
            "(while an answer on named lines could still be asked for), at the first sending of the form, and at the last; the mean share of the "
            "stage's lines shown at the last sending; and the lines that came only by a count or only by a filter, as a mean for a session.", ""]
    for a in ("A1", "A3"):
        rows = []
        for run, cond, w, ss in cells():
            ws = [W(s, a) for s in ss if W(s, a)]
            if not ws:
                continue
            n = len(ws)
            rows.append([run, cond, w, n, sum(1 for x in ws if x["in_full_by_the_end_of_the_request"]),
                         sum(1 for x in ws if x["in_full_at_the_first_sending"]), sum(1 for x in ws if x["in_full_at_the_last_sending"]),
                         sum(1 for x in ws if x["read_at_the_last_sending"] == 0),
                         mean([100 * x["read_at_the_last_sending"] / x["lines"] for x in ws], "{:.0f}%"),
                         mean([x["how_the_lines_came"]["by a count only"] for x in ws]),
                         mean([x["how_the_lines_came"]["by a filter only"] for x in ws]),
                         mean([x["questions_to_the_record"] for x in ws]), sum(x["asked_the_log"] for x in ws)])
        out += [f"**At {a}:**", "",
                table(["run", "condition", "model", "sessions at the wake", "in full by the end of the request", "in full at the first sending",
                       "in full at the last sending", "no line shown", "share of the lines shown, mean", "lines by a count only, mean",
                       "lines by a filter only, mean", "questions to the record, mean", "times the log was asked"], rows), ""]
    # the same, by condition and model over the runs
    rows = []
    for cond in CONDS:
        for w in WHOS:
            for a in APPROVALS:
                ws = [W(s, a) for s in sel(w, cond) if W(s, a)]
                if ws:
                    rows.append([cond, w, a, len(ws), sum(1 for x in ws if x["in_full_at_the_first_sending"]),
                                 sum(1 for x in ws if x["in_full_at_the_last_sending"]),
                                 mean([100 * x["read_at_the_last_sending"] / x["lines"] for x in ws], "{:.0f}%")])
    out += ["By condition and model, all runs together, at each approval:", "",
            table(["condition", "model", "approval", "sessions at the wake", "in full at the first sending", "in full at the last sending",
                   "share of the lines shown, mean"], rows), ""]
    # returns
    rows, detail = [], []
    for cond in ("D", "DF"):
        for w in WHOS:
            ss = sel(w, cond)
            if not ss:
                continue
            ws = [(s, a, x) for s in ss for a, x in s["x8"]["wakes"].items()]
            appr = [(s, a, x) for s, a, x in ws if x["decision_first"] == "approve"]
            ret = [(s, a, x) for s, a, x in ws if x["returns"]]
            rows.append([cond, w, len(ss), len(appr), len(ret), sum(1 for _, _, x in ret if x["returns"] == 2),
                         sum(1 for _, _, x in ret if x["in_full_at_the_last_sending"] and x["decision_last"] == "approve" and not x["approval_not_accepted"]),
                         sum(1 for _, _, x in ret if x["decision_last"] != "approve"),
                         sum(1 for _, _, x in ws if x["approval_not_accepted"]),
                         sum(1 for _, _, x in ret if any(r.get("asked_raw") for r in x["asked_after_a_return"]))])
            for s, a, x in ret:
                detail.append([cond, w, s["run"], s["n"], a, x["returns"],
                               "; ".join(f"said {json.dumps((e.get('statement') or {}).get('read'))}, the log held {e['read_by_the_log']} of {x['lines']}"
                                         for e in x["sendings"]),
                               x["decision_last"] + (", not accepted" if x["approval_not_accepted"] else ""),
                               json.dumps([r.get("asked_raw") for r in x["asked_after_a_return"]])])
    out += ["Approvals returned, in D and DF (a wake is an approval asked for):", "",
            table(["condition", "model", "sessions", "wakes where the first sending approved", "wakes with a return", "returned twice",
                   "then read in full and approved", "then did not approve", "approvals not accepted", "asked on named lines after a return"], rows), ""]
    if detail:
        out += ["Every wake with a return:", "",
                table(["condition", "model", "run", "n", "approval", "returns", "each sending", "the last sending", "asked after the return"], detail), ""]
    rows = []
    for w in WHOS:
        for s in sel(w, "S"):
            for a, x in s["x8"]["wakes"].items():
                e = x["sendings"][-1]
                if e["decision"] == "approve" and not x["in_full_at_the_last_sending"]:
                    rows.append([w, s["run"], s["n"], a, f"{x['read_at_the_last_sending']} of {x['lines']}",
                                 json.dumps((e.get("statement") or {}).get("read")), "yes" if e.get("passes") else "no",
                                 "nothing" if e.get("says_nothing_is_shown") else json.dumps([n["line"] for n in e.get("lines_named", [])])])
    out += ["In S: approvals given on a part of the record, with what the statement said:", "",
            table(["model", "run", "n", "approval", "shown by the log", "the statement: read", "passes the audit's check", "the statement: shows"], rows)
            if rows else "None: every approval in S was given with the stage shown in full.", ""]

    # ---------- 2. the statement against the log ----------
    out += ["## 2. The statement against the log", "",
            "Every sending of a form in S, D and DF, whatever it decided. A statement passes the audit's check when it says no more than the log "
            "holds: on how much was read, and for every line it names, on the fields it names for the line. A line can be shown only with all its "
            "fields, so a statement cannot be over by a field of a line that was shown; it can be over only by speaking for a line that was not returned.", ""]
    rows, over = [], []
    for cond in ("S", "D", "DF"):
        for w in WHOS:
            ss = sel(w, cond)
            es = [(s, a, x, e) for s in ss for a, x in s["x8"]["wakes"].items() for e in x["sendings"] if "passes" in e]
            if not es:
                continue
            named = [n for _, _, _, e in es for n in e["lines_named"]]
            rows.append([cond, w, len(es), sum(1 for *_, e in es if e["readable"]), sum(1 for *_, e in es if e["passes"]),
                         sum(1 for *_, e in es if e["says_in_full"]),
                         sum(1 for _, _, x, e in es if e["says_in_full"] and e["read_by_the_log"] < x["lines"]),
                         sum(1 for *_, e in es if e["says_so_many_lines"] is not None),
                         sum(1 for *_, e in es if e["says_so_many_lines"] is not None and e["says_so_many_lines"] > e["read_by_the_log"]),
                         sum(1 for *_, e in es if e["says_less_than_the_log_holds"]),
                         len(named), sum(1 for n in named if n["holds"]),
                         sum(1 for n in named if not n["holds"] and n["the_line_was_shown"]),
                         sum(1 for n in named if not n["holds"] and not n["the_line_was_shown"]),
                         sum(1 for _, _, x, e in es if e is x["sendings"][-1] and x["free_words_speak_of_a_full_reading_by_keyword"]
                             and not x["in_full_at_the_last_sending"])])
            for s, a, x, e in es:
                if not e["passes"]:
                    over.append([cond, w, s["run"], s["n"], a, e["decision"], json.dumps(e["statement"])[:600],
                                 f"{e['read_by_the_log']} of {x['lines']}",
                                 "; ".join(f"line {n['line']}: {'shown, fields not named' if n['the_line_was_shown'] else 'not returned'}"
                                           + (f" ({', '.join(n['fields_not_returned_for_it'])})" if n["fields_not_returned_for_it"] else "")
                                           for n in e["lines_named"] if not n["holds"])])
    out += [table(["condition", "model", "sendings", "statement readable", "pass the check", "say \"in full\"", "\"in full\" against the log",
                   "say so many lines", "a number above the log", "a number below the log (no error)", "lines named", "hold",
                   "named with no field, the line shown", "named, the line not returned",
                   "free words speak of a full reading, the log not full (keyword)"], rows), ""]
    out += ["Every statement that did not pass the check:", "",
            table(["condition", "model", "run", "n", "approval", "decision", "the statement", "shown by the log", "what does not hold"], over)
            if over else "None.", ""]
    rows = []
    for cond in ("D", "DF"):
        for w in WHOS:
            first = [(x, x["sendings"][0]) for s in sel(w, cond) for x in s["x8"]["wakes"].values() if x["decision_first"] == "approve"]
            if first:
                rows.append([cond, w, len(first), sum(1 for x, e in first if e["says_in_full"] and x["in_full_at_the_first_sending"]),
                             sum(1 for x, e in first if e["says_in_full"] and not x["in_full_at_the_first_sending"]),
                             sum(1 for x, e in first if not e["says_in_full"])])
    out += ["In D and DF, the first sending of an approval:", "",
            table(["condition", "model", "first sendings that approve", "\"in full\", and the log agrees", "\"in full\" against the log, returned",
                   "so many lines, returned"], rows), ""]

    # ---------- 3. correctness, given execution ----------
    out += ["## 3. Correctness, given execution", "",
            "On R1 and R2, sessions that passed each step. Read: the three lines returned with the field that carries the cut, by the last sending "
            "at the wake of the cut (A1 on R1, A3 on R2), and how: the lines shown, a count, or a filter on one value. Seen: at least one of the "
            "three named, in the statement, in a request on named lines or by number in the form's free words. Asked: an answer on named lines "
            "that takes in one of the three. In S the reading is chosen; in D and DF it is forced. X7's cell of the same model and run is beside, "
            "with its own steps (looked, raised).", ""]
    rows = []
    for run in ("R1", "R2"):
        for w in WHOS:
            c7 = [s["finding"] for s in x7(w, run)]
            if c7 and sel(w, None, run):
                rows.append([run, "X7", w, len(c7), "", sum(1 for f in c7 if f["looked"]), "", "", sum(1 for f in c7 if f["raised"]), "",
                             sum(1 for f in c7 if f["asked"]), sum(1 for f in c7 if f["could_not_ask"]), "",
                             sum(1 for f in c7 if f["proved"]), sum(1 for f in c7 if f["ruled"])])
        for r2, cond, w, ss in cells([run]):
            fs = [F(s) for s in ss]
            at = [f for f in fs if f.get("reached_the_wake_of_the_cut")]
            g = lambda k: sum(1 for f in at if f.get(k))      # noqa: E731
            cna = [f for f in at if f.get("could_not_ask")]
            rows.append([run, cond, w, len(ss), len(at), g("read"), cnt(Counter(f["how"] for f in at if f.get("read"))),
                         g("read_by_the_end_of_the_request"), g("seen"),
                         cnt(Counter(f"{f['seen_how_many_of_the_three']} of 3" for f in at if f.get("seen"))),
                         g("asked"), len(cna),
                         cnt(Counter(f"{f['why_not_asked']} (allowance left {f['allowance_left']})" for f in at if f.get("seen_and_not_asked"))),
                         g("proved"), g("ruled")])
    out += [table(["run", "condition", "model", "sessions", "at the wake of the cut", "read", "how it came", "read by the end of the request",
                   "seen", "how many of the three", "asked", "could not ask", "seen and not asked: why", "proved", "ruled"], rows), ""]
    rows = []
    for run in ("R1", "R2"):
        for w in ("sonnet", "haiku"):
            for name, conds in [("S (chosen)", ["S"]), ("D", ["D"]), ("S and D together", ["S", "D"])] + \
                               ([("DF", ["DF"]), ("D and DF together (forced)", ["D", "DF"])] if run == "R2" else []):
                fs = [F(s) for s in sel(w, conds, run)]
                if fs:
                    g = lambda k: sum(1 for f in fs if f.get(k))      # noqa: E731
                    rows.append([run, w, name, len(fs), g("read"), g("seen"), g("asked"), g("could_not_ask"), g("proved"), g("ruled")])
    out += ["S and D apart and together:", "",
            table(["run", "model", "conditions", "sessions", "read", "seen", "asked", "could not ask", "proved", "ruled"], rows), ""]

    # ---------- 4. read and not seen ----------
    out += ["## 4. The rate of read and not seen", "",
            "Of the sessions that had the three lines returned with the field that carries the cut, how many named none of them "
            "(not in the statement, not in a request, not by number in the free words, and no keyword of the cut in what they raised).", ""]
    rows, each = [], []
    for run in ("R1", "R2"):
        for w in WHOS:
            for name, conds in [("chosen: S", ["S"]), ("forced: D and DF", ["D", "DF"]), ("no statement: X and F", ["X", "F"])]:
                ss = [s for s in sel(w, conds, run) if F(s).get("read")]
                if not sel(w, conds, run):
                    continue
                ns = [s for s in ss if F(s).get("read_and_not_seen")]
                rows.append([run, w, name, len(sel(w, conds, run)), len(ss), len(ns), f"{len(ns) / len(ss):.2f}" if ss else "—",
                             sum(1 for s in ss if F(s).get("seen") and F(s)["seen_how_many_of_the_three"] < 3)])
                for s in ns:
                    f = F(s)
                    st = f["words"]["statement"][-1] if f["words"]["statement"] else None
                    each.append([run, s["condition"], w, s["n"],
                                 f"{f['how']}" + (f", among {f['shown_among_how_many_lines_of_the_stage']} lines of the stage shown" if "shown" in str(f["how"]) else ""),
                                 json.dumps(st)[:300] if st else "no statement in this condition",
                                 f["words"]["decision"], json.dumps(f["words"]["what_i_raise"])[:700]])
    out += [table(["run", "model", "the reading", "sessions", "read", "read and not seen", "rate", "seen, one or two of the three only"], rows), "",
            "Every session that read and did not see, with its words:", "",
            table(["run", "condition", "model", "n", "how the three lines came", "the statement", "decision", "what it raised"], each) if each else "None.", ""]

    # ---------- 5. the field ----------
    out += ["## 5. The field `took`, on R2", ""]
    rows = []
    for w in WHOS:
        c7 = x7(w, "R2")
        if c7 and sel(w, None, "R2"):
            rows.append(["X7", w, len(c7), "no field", sum(1 for s in c7 if s["finding"]["looked"]), "", sum(1 for s in c7 if s["finding"]["raised"]),
                         sum(1 for s in c7 if s["finding"]["proved"]), sum(1 for s in c7 if s["finding"]["ruled"])])
    for cond in ("X", "F", "S", "D", "DF"):
        for w in WHOS:
            ss = sel(w, cond, "R2")
            if ss:
                fs = [F(s) for s in ss]
                rows.append([cond, w, len(ss), cnt(Counter(str(f.get("took_returned_for_the_three") or "not returned") for f in fs))
                             if CONDITIONS[cond]["took"] else "no field",
                             sum(1 for f in fs if f.get("read")), cnt(Counter(f["how"] for f in fs if f.get("read"))),
                             sum(1 for f in fs if f.get("seen")), sum(1 for f in fs if f.get("proved")), sum(1 for f in fs if f.get("ruled"))])
    out += [table(["condition", "model", "sessions", "`took` returned for the three lines", "read", "how", "seen (X7: raised)", "proved", "ruled"], rows), ""]

    # ---------- 6. clean work ----------
    out += ["## 6. Clean work (run 0)", ""]
    rows, named_rows = [], []
    for w in WHOS:
        c7 = x7(w, "0")
        asked7 = [x for s in c7 for x in s.get("asked_during_the_work", []) if x["paid"] and x.get("lines")]
        rows.append(["X7", w, len(c7), cnt(Counter(s["ending"] for s in c7)), 0, "", len(asked7), sum(x["price"] for x in asked7),
                     sum(1 for x in asked7 if x["found_a_breach"]), "", ""])
    for run, cond, w, ss in cells(["0"]):
        asked = [x for s in ss for x in s.get("asked_during_the_work", []) if x["paid"] and x.get("lines")]
        nm = [(s, a, n) for s in ss for a, x in s["x8"]["wakes"].items() for n in (x["sendings"][-1].get("lines_named") or [])]
        an = [x for s in ss for wk in s["x8"]["wakes"].values() for x in wk["asked_on_named_lines"] if x["lines_taken"]]
        rows.append([cond, w, len(ss), cnt(Counter(s["ending"] for s in ss)),
                     sum(1 for s in ss if str(s["ended"]).startswith("approval not accepted")), len(nm),
                     len(asked), sum(x["price"] for x in asked), sum(1 for x in asked if x["found_a_breach"]),
                     cnt(Counter(x["kind_of_reason"] for x in asked)), pct(sum(1 for x in an if x["all_shown_first"]), len(an))])
        for s, a, n in nm:
            asks = [x for x in s["x8"]["wakes"][a]["asked_on_named_lines"] if str(n["line"]) in [str(v) for v in x["lines_named"]]]
            named_rows.append([cond, w, s["n"], a, n["line"], ", ".join(n["fields"]), str(n["what_it_shows"])[:300],
                               "; ".join(f"{x['instrument']} ({x['price']} units)" for x in asks) or "nothing asked",
                               "no breach" if asks else ""])
    out += [table(["condition", "model", "sessions", "ending", "approvals not accepted", "lines named as not fitting",
                   "answers on named lines", "their price, units", "found a breach", "by the kind of reason (keyword)",
                   "the lines had been shown first"], rows), "",
            "Lines named as not fitting on clean work:", "",
            table(["condition", "model", "n", "approval", "line", "fields", "what it shows, in the session's words", "asked for on it", "it found"], named_rows)
            if named_rows else "None.", ""]
    rows = []
    for run, cond, w, ss in cells():
        an = [x for s in ss for wk in s["x8"]["wakes"].values() for x in wk["asked_on_named_lines"] if x["lines_named"]]
        if an:
            nl = sum(len(x["lines_named"]) for x in an)
            rows.append([run, cond, w, len(an), nl, sum(x["lines_shown_first"] for x in an), sum(1 for x in an if x["all_shown_first"]),
                         sum(1 for x in an if x["lines_shown_first"] == 0), sum(1 for x in an if x["after_a_return"])])
    out += ["Every answer asked for on named lines, in every run: had the log shown those lines to the session first?", "",
            table(["run", "condition", "model", "requests", "lines named", "of them shown first", "requests with every line shown first",
                   "requests with no line shown first", "asked after a return"], rows), ""]

    # ---------- 7. rulings and the audit ----------
    out += ["## 7. Rulings and the audit", ""]
    rows = []
    for run, cond, w, ss in cells():
        rows.append([run, cond, w, len(ss), cnt(Counter(s.get("ending", s["ended"]) for s in ss))])
    out += [table(["run", "condition", "model", "sessions", "ending"], rows), ""]
    rows = []
    for cond in CONDS:
        for w in WHOS:
            ss = sel(w, cond)
            if not ss:
                continue
            au = [(x["audit"], s["x8"]["wakes"][a]["sendings"][-1]) for s in ss for a, x in s.get("wakes", {}).items() if x.get("audit")]
            cl = [s["wakes"]["A3"]["closing"] for s in ss if "A3" in s.get("wakes", {}) and "closing" in s["wakes"]["A3"]]
            new = [e for _, e in au if "passes" in e]
            rows.append([cond, w, len(au), sum(1 for s in ss for _ in s.get("approvals_given_while_a_breach_stood", [])),
                         sum(1 for a, _ in au if a["passes"]), sum(1 for a, _ in au if a["an_answer_left_out"]),
                         sum(1 for a, _ in au if a["names_something_not_in_hand"]),
                         pct(sum(1 for e in new if e["passes"]), len(new)) if CONDITIONS[cond]["statement"] else "no statement",
                         pct(sum(1 for a, e in au if a["passes"] and e.get("passes")), len(new)) if CONDITIONS[cond]["statement"] else "",
                         sum(1 for s in ss if s.get("refused_or_withheld_with_no_answer_behind_it") and not str(s["ended"]).startswith("approval not accepted")),
                         sum(1 for s in ss if (s.get("finding") or {}).get("proved") and not s["finding"]["ruled"]),
                         f"{sum(1 for c in cl if c['four_numbers_right'])}/{len(cl)}"])
    out += [table(["condition", "model", "approvals given", "given while a breach stood", "pass the old audit", "an answer left out",
                   "name something not in hand", "pass the new check of the statement", "pass both",
                   "refusals or withheld verdicts with no answer behind them", "proved and not ruled on", "closing summary: four numbers right"], rows), ""]

    # ---------- 8. cost ----------
    out += ["## 8. Cost", "",
            "The runtime's figure at list prices, corrected: a turn costs the difference of the running total. The acts are means over the sessions "
            "that reached the act. X7's cells are on the corrected figure too.", ""]
    rows = []
    for run in ("0", "R1", "R2"):
        for w in WHOS:
            c7 = x7(w, run)
            if c7 and sel(w, None, run):
                rows.append([run, "X7", w, len(c7), usd([s["cost"] for s in c7]), f"${sum(s['cost'] for s in c7):.2f}"] +
                            [usd([s["acts"][a] for s in c7 if a in s["acts"]]) for a in ["plan"] + APPROVALS] +
                            [mean([s["wall_s"] for s in c7], "{:.0f} s"), mean([s["tokens"]["output"] for s in c7], "{:.0f}"),
                             mean([s["tokens"]["cache_read"] for s in c7], "{:.0f}"), mean([s["tokens"]["cache_write"] for s in c7], "{:.0f}"),
                             mean([s["record_questions"] for s in c7]), mean([s["allowance_spent"] for s in c7]), ""])
        for r2, cond, w, ss in cells([run]):
            rows.append([run, cond, w, len(ss), usd([s["cost_usd"] for s in ss]), f"${sum(s['cost_usd'] for s in ss):.2f}"] +
                        [usd([s["by_act"][a]["cost_usd"] for s in ss if a in s["by_act"]]) for a in ["plan"] + APPROVALS] +
                        [mean([s["wall_s"] for s in ss], "{:.0f} s"), mean([s["tokens"]["output"] for s in ss], "{:.0f}"),
                         mean([s["tokens"]["cache_read"] for s in ss], "{:.0f}"), mean([s["tokens"]["cache_write"] for s in ss], "{:.0f}"),
                         mean([s["record_questions"] for s in ss]), mean([s["allowance_spent"] for s in ss]), sum(s["second_tries"] for s in ss)])
    out += [table(["run", "condition", "model", "sessions", "a session", "all", "the plan", "wake A1", "wake A2", "the verdict", "wall, mean",
                   "output tokens, mean", "cache read, mean", "cache write, mean", "questions to the record, mean", "allowance spent, mean",
                   "replies asked for again"], rows), "",
            f"All {len(M)} sessions: ${sum(s['cost_usd'] for s in M):.2f}. By model: " +
            "; ".join(f"{w} ${sum(s['cost_usd'] for s in sel(w)):.2f} ({len(sel(w))} sessions)" for w in WHOS) + ".", ""]
    # what the reading adds
    rows = []
    for w in ("sonnet", "haiku"):
        for run, base_name, base in [("R2", "X", [s["cost_usd"] for s in sel(w, "X", "R2")]),
                                     ("0", "X7", [s["cost"] for s in x7(w, "0")]), ("R1", "X7", [s["cost"] for s in x7(w, "R1")])]:
            for cond in ("S", "D", "DF"):
                ss = sel(w, cond, run)
                if not ss or not base:
                    continue
                full = [s for s in ss if all(x["in_full_at_the_last_sending"] for x in s["x8"]["wakes"].values())]
                b = sum(base) / len(base)
                m = sum(s["cost_usd"] for s in ss) / len(ss)
                lines = sum(x["read_at_the_last_sending"] for s in ss for x in s["x8"]["wakes"].values()) / len(ss)
                rows.append([run, w, cond, len(ss), f"${m:.3f}", f"{base_name} ${b:.3f}", f"${m - b:+.3f}", f"{m / b:.1f}x" if b else "—",
                             f"{lines:.0f}", f"${100 * (m - b) / lines:.3f}" if lines else "—",
                             len(full), usd([s["cost_usd"] for s in full])])
    out += ["What the reading adds: the condition against the cell without the rules (X on the previews; X7's cell on clean work and on the wide reads). "
            "A session on R1 that finds the cut ends at A1, so on R1 the difference is not the price of the reading alone.", "",
            table(["run", "model", "condition", "sessions", "a session", "the cell without the rules", "difference", "ratio",
                   "lines of the record shown, mean for a session", "difference for a hundred lines shown",
                   "sessions that read every stage in full", "a session of those"], rows), ""]
    # the reading, by stage: lines, characters, tokens
    turns = {w: [] for w in WHOS}
    for s in M:
        d = RESULTS_X8 / "sessions" / s["who"] / s["condition"] / s["run"] / str(s["n"])
        log = [json.loads(ln) for ln in (d / "tool_log.jsonl").read_text().splitlines()] if (d / "tool_log.jsonl").exists() else []
        prev = 0
        for ln in (d / "steps.jsonl").read_text().splitlines():
            t = json.loads(ln)
            k = t.get("questions_in_the_log_after")
            if k is None:
                continue
            chars = sum(len(q["reply"]) for q in log[prev:k])
            turns[s["who"]].append((chars, t["tokens"]["input"] + t["tokens"]["cache_write"], t["cost_usd"] or 0))
            prev = k
    slope = {}
    for w, ts in turns.items():
        if len(ts) > 5:
            n = len(ts)
            mx, my = sum(x for x, _, _ in ts) / n, sum(y for _, y, _ in ts) / n
            den = sum((x - mx) ** 2 for x, _, _ in ts)
            slope[w] = sum((x - mx) * (y - my) for x, y, _ in ts) / den if den else None
    rows = []
    for w in WHOS:
        for a in APPROVALS:
            ws = [W(s, a) for s in sel(w, ["S", "D", "DF"]) if W(s, a) and W(s, a)["in_full_at_the_last_sending"]]
            if ws and slope.get(w):
                ch = sum(x["characters_returned"] for x in ws) / len(ws)
                li = sum(x["lines_in_the_replies"] for x in ws) / len(ws)
                rows.append([w, a, len(ws), ws[0]["lines"], f"{li:.0f}", f"{ch:.0f}", f"{slope[w]:.3f}", f"{ch * slope[w]:.0f}",
                             f"{100 * ch * slope[w] / li:.0f}" if li else "—"])
    out += ["The reading, by stage, over the wakes of S, D and DF where the stage was shown in full. The runtime does not meter a question's reply, "
            "so the tokens are an estimate: the characters the record's questions returned, times the tokens for a character, which is the slope of a "
            "turn's new tokens (input and cache write) on the characters returned in that turn, over every turn of the model's sessions.", "",
            table(["model", "stage of", "wakes", "lines of the stage", "lines in the replies, mean", "characters returned, mean",
                   "tokens for a character (fitted)", "tokens returned, estimate", "tokens for a hundred lines returned"], rows), ""]

    # ---------- 9. the scripts ----------
    out += ["## 9. The two scripts", ""]
    rows = []
    for s in SC:
        f = F(s)
        ws = s["x8"]["wakes"]
        rows.append([s["who"].replace("_", " "), s["condition"], s["run"], s.get("ending", s["ended"]),
                     "/".join(f"{x['read_at_the_last_sending']} of {x['lines']}" for x in ws.values()),
                     sum(x["returns"] for x in ws.values()),
                     pct(sum(1 for x in ws.values() for e in x["sendings"] if e.get("passes")), sum(1 for x in ws.values() for e in x["sendings"] if "passes" in e)),
                     "—" if s["run"] == "0" else ("read" if f.get("read") else "not read") + (", seen" if f.get("seen") else ", not seen")
                     + (", proved" if f.get("proved") else ", not proved")])
    out += [table(["script", "condition", "run", "ending", "lines shown, at A1/A2/A3", "returns", "statements that pass the check", "the cut"], rows), ""]

    # ---------- 10. the three lines ----------
    out += ["## 10. The three lines", "",
            f"The draws put the wide reads on lines {', '.join(map(str, THREE['R1']))} of the record and the previews on lines "
            f"{', '.join(map(str, THREE['R2']))}. X7's were 32, 63, 94 and 146, 177, 208.", "",
            "For every find, how the lines were chosen (the reason of the request cites what the record shows, by keyword, and the log shows the "
            "session had the lines first):", ""]
    rows = []
    for run, cond, w, ss in cells(["R1", "R2"]):
        fs = [F(s) for s in ss if F(s).get("proved")]
        if fs:
            other = sum(1 for s in ss if (s.get("finding") or {}).get("asked_on_other_lines_only"))
            rows.append([run, cond, w, len(fs), cnt(Counter((f["lines_chosen"] or {}).get("by", "not determined") for f in fs)),
                         cnt(Counter(f"{f['seen_how_many_of_the_three']} of 3 named" for f in fs)), other])
    out += [table(["run", "condition", "model", "finds", "how the lines were chosen", "how many of the three", "sessions that asked on other lines only"], rows), ""]
    rows = []
    for run in ("R1", "R2"):
        a = CUT_WAKE[run]
        for cond in ("X", "F"):
            for w in WHOS:
                ss = sel(w, cond, run)
                if ss:
                    d0 = RESULTS_X8 / "sessions"
                    shown = Counter()
                    for s in ss:
                        from . import log_x8 as lg
                        ret = lg.returned(lg.entries(d0 / w / cond / run / str(s["n"]) / "tool_log.jsonl"), x8.RUNS_X8 / run,
                                          CONDITIONS[cond]["took"])
                        st = s["x8"]["wakes"].get(a, {}).get("stage")
                        if st:
                            shown.update(k for k, r in ret.items() if r["shown"] and st[0] <= k <= st[1])
                    top = ", ".join(f"{k} ({v})" for k, v in sorted(shown.items(), key=lambda kv: (-kv[1], kv[0]))[:12])
                    rows.append([run, cond, w, len(ss), top or "none", ", ".join(f"{t}: {shown.get(t, 0)}" for t in THREE[run])])
    out += ["Where no rule asks for a reading (X and F): the lines of the cut's stage that the sessions were shown most often (line, sessions), "
            "and how many sessions were shown each of the three:", "",
            table(["run", "condition", "model", "sessions", "the lines shown most often", "the three"], rows), ""]

    # ---------- 11. the clause lists ----------
    out += ["## 11. The clause lists, on the corrected key", "", "Entries at the plan and at every approval, all runs together.", ""]
    rows = []
    for cond in CONDS:
        for w in WHOS:
            ss = [s for s in sel(w, cond) if s["plan"] is not None]
            if not ss:
                continue
            es = [e for s in ss for e in s["plan_clauses"].values()] + [e for s in ss for x in s.get("wakes", {}).values() for e in x["clauses"].values()]
            k, k0 = Counter(e["score_on_the_corrected_key"] for e in es), Counter(e["score"] for e in es)
            oc = Counter(c for s in ss for where, cl in [("plan", s["plan_clauses"])] + [(a, x["clauses"]) for a, x in s.get("wakes", {}).items()]
                         for c, e in cl.items() if e["score_on_the_corrected_key"] == "over-claimed")
            rows.append([cond, w, len(es), k["right"], k0["right"], k["over-claimed"], k["under-claimed"],
                         k["a breach in hand, and not entered as broken"], k["broken, with no answer in hand that found a breach"],
                         k["not readable"], cnt(oc)])
    for w in WHOS:
        ss = [s for s in X7 if s["who"] == w and s["plan"] is not None]
        es = [e for s in ss for e in s["plan_clauses"].values()] + [e for s in ss for x in s.get("wakes", {}).values() for e in x["clauses"].values()]
        k, k0 = Counter(e["score_on_the_corrected_key"] for e in es), Counter(e["score"] for e in es)
        rows.append(["X7", w, len(es), k["right"], k0["right"], k["over-claimed"], k["under-claimed"],
                     k["a breach in hand, and not entered as broken"], k["broken, with no answer in hand that found a breach"], k["not readable"], ""])
    out += [table(["condition", "model", "entries", "right", "right on the original key", "over-claimed", "under-claimed",
                   "a breach in hand, not entered as broken", "broken with no such answer", "not readable", "over-claims, by clause"], rows), ""]
    (RESULTS_X8 / "tables.md").write_text("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
