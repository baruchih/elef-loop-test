"""Experiment 1b: the result tables. Usage: python -m loop.report_fx -> results_1b/tables.md"""
import json
from collections import Counter, defaultdict

from .common import I_UNDO
from .fixes import RESULTS_1B, I_TRACE, MODELS
from .score_fx import score_all, MOVED

MN = {"m1": "before promotion", "m2": "stop", "m3": "resume", "m4": "end"}
CONDS = ("asis", "fixes")
CN = {"asis": "as it was", "fixes": "with the fixes"}


def val(a):
    if isinstance(a, dict):
        if "answer" in a and a["answer"] is not None:
            v = a.get("value")
            return str(a["answer"]) + (f" ({json.dumps(v)})" if v is not None else "")
        return json.dumps(a.get("value"))
    return json.dumps(a)


def spread(rs):
    c = Counter(val(r["answer"]) for r in rs)
    return "; ".join(f"{k} ×{v}" for k, v in c.most_common())


def build():
    rows, sessions = score_all()
    by = defaultdict(list)
    for r in rows:
        by[(r["model"], r["cond"], r["run"], r["moment"], r["question"])].append(r)
    out = ["# Experiment 1b: result tables\n", f"{len(sessions)} sessions.\n"]

    out.append("## Totals by model and condition\n")
    out += ["| Model | Condition | Sessions | Keyed answers | Right, key as written | Right, corrected key | Judged by hand | Second tries |", "|---|---|---|---|---|---|---|---|"]
    for m in MODELS:
        for c in CONDS:
            rs = [r for r in rows if r["model"] == m and r["cond"] == c and r["right"] in (True, False)]
            ss = [s for s in sessions if s["model"] == m and s["cond"] == c]
            out.append(f"| {m} | {CN[c]} | {len(ss)} | {len(rs)} | {sum(r['right'] for r in rs)} | "
                       f"{sum(1 for r in rs if r['right_corrected'] is True)} | {sum(1 for r in rs if r.get('judged') and r['right'])} | "
                       f"{sum(s['replies_that_needed_a_second_try'] for s in ss)} |")

    out.append("\n## Every question, both conditions side by side (right / decided of five)\n")
    for m in MODELS:
        for run in "ABCD":
            out.append(f"\n### {m}, run {run}\n")
            out += ["| Moment | Question | As it was | With the fixes |", "|---|---|---|---|"]
            qs = []
            for r in rows:
                k = (r["moment"], r["question"])
                if r["model"] == m and r["run"] in (run, "B" if run == "D" else run) and k not in qs and r["right"] is not None:
                    qs.append(k)
            for mo, q in sorted(qs, key=lambda k: k[0]):
                cells = []
                for c in CONDS:
                    rs = by.get((m, c, "B" if (run == "D" and c == "asis") else run, mo, q), [])
                    if not rs:
                        cells.append("–")
                        continue
                    if all(r["right"] is None for r in rs):
                        cells.append("no key — " + spread(rs))
                        continue
                    ri = sum(1 for r in rs if r["right"] is True)
                    co = sum(1 for r in rs if r["right_corrected"] is True)
                    s = f"{ri}/{len(rs)} right" + (f" ({co} corrected key)" if co != ri else "") + f" · {sum(1 for r in rs if r['decided'])}/{len(rs)} decided"
                    if ri < len(rs) or q in ("2.f", "2.c", "2.d") or "moved" in q:
                        s += " — " + spread(rs)
                    cells.append(s)
                out.append(f"| {MN[mo]} | {q} | {cells[0]} | {cells[1]} |")

    out.append("\n## Which answers were asked for, with the fixes\n")
    out += ["| Model | Run | Moment | Asked for the trace | Trace shown unasked | Asked for the undo rehearsal | Rehearsal shown unasked | Other answers asked | Asked for what does not exist |", "|---|---|---|---|---|---|---|---|---|"]
    for m in MODELS:
        for run in "ABCD":
            ss = [s for s in sessions if s["model"] == m and s["cond"] == "fixes" and s["run"] == run]
            for mo in ("m2", "m3", "m4"):
                a = [s["asks"][mo] for s in ss]
                other = Counter(x for t in a for x in t["asked"] if x not in (I_TRACE, I_UNDO))
                out.append(f"| {m} | {run} | {MN[mo]} | {sum(I_TRACE in t['asked'] for t in a)}/5 | {sum(I_TRACE in t['shown_unasked'] for t in a)}/5 | "
                           f"{sum(I_UNDO in t['asked'] for t in a)}/5 | {sum(I_UNDO in t['shown_unasked'] for t in a)}/5 | "
                           f"{', '.join(f'{k} ×{v}' for k, v in other.items()) or '–'} | {sum(len(t['do_not_exist']) for t in a)} |")
    out.append("\n## Which answers were asked for at the resume, as it was\n")
    out += ["| Model | Run | Asked for | Rehearsal shown unasked |", "|---|---|---|---|"]
    for m in MODELS:
        for run in "ABC":
            a = [s["asks"]["m3"] for s in sessions if s["model"] == m and s["cond"] == "asis" and s["run"] == run]
            c = Counter(x for t in a for x in t["asked"])
            out.append(f"| {m} | {run} | {', '.join(f'{k} ×{v}' for k, v in c.items()) or 'none'} | {sum(bool(t['shown_unasked']) for t in a)}/5 |")

    out.append("\n## Statement c at the stop: every answer with its reason\n")
    for r in rows:
        if r["question"] == "2.c" and r["moment"] == "m2":
            out.append(f"- `{r['id']}` ({r.get('note') or 'no rehearsal could be asked for'}): {val(r['answer'])} — {r['reason_given']}")

    out.append("\n## Run C at the resume: the customers still to be sent a notice whose rows moved\n")
    for r in rows:
        if "moved" in r["question"] and r["run"] == "C":
            out.append(f"- `{r['id']}`: {val(r['answer'])} — {r['reason_given']}")

    out.append("\n## Every answer that differs from the key, with its source\n")
    for r in rows:
        if r["right"] is False:
            out.append(f"- `{r['id']}` — key: {r['key']!r}; answer: {json.dumps(r['answer'])}; reason given: {r['reason_given']!r}; "
                       f"source: {r.get('source', 'not determined')}" + (f"; corrected key: {r['corrected_key']!r} -> right" if r.get("corrected_key") else ""))

    out.append("\n## Answers judged by hand (raw answer beside the judgement)\n")
    for r in rows:
        if r.get("judged") and r["right"] is True:
            out.append(f"- `{r['id']}` — judged right: {r['judgement_reason']} Raw: {json.dumps(r['answer'])}; reason given: {r['reason_given']!r}")

    out.append("\n## Tokens, wall time and cost\n")
    out += ["| Model | Identifier | Condition | Sessions | Tokens per session (mean, with cache reads) | Output tokens (mean) | Wall s (mean) | Record questions (mean) | Cost per session (mean) | Cost in all |", "|---|---|---|---|---|---|---|---|---|---|"]
    for m in MODELS:
        for c in CONDS:
            ss = [s for s in sessions if s["model"] == m and s["cond"] == c]
            n = len(ss)
            calls = 0
            for s in ss:
                p = RESULTS_1B / "sessions" / m / c / s["run"] / str(s["n"]) / "tool_log.jsonl"
                calls += len(p.read_text().splitlines()) if p.exists() else 0
            out.append(f"| {m} | {', '.join(sorted({x for s in ss for x in s['models_reported']}))} | {CN[c]} | {n} | {round(sum(sum(s['tokens'].values()) for s in ss) / n):,} | "
                       f"{round(sum(s['tokens']['output'] for s in ss) / n):,} | {sum(s['wall_s'] for s in ss) / n:.0f} | {calls / n:.1f} | "
                       f"${sum(s['cost_usd'] for s in ss) / n:.2f} | ${sum(s['cost_usd'] for s in ss):.2f} |")
    (RESULTS_1B / "tables.md").write_text("\n".join(out) + "\n")
    return rows, sessions


if __name__ == "__main__":
    build()
    print("written")
