"""Builds the result tables from the scores. Usage: python -m loop.report  -> results/tables.md"""
import json
from collections import Counter, defaultdict

from .common import RESULTS
from .score import score_all

MOMENT_NAME = {"m1": "before promotion", "m2": "stop", "m3": "resume", "m4": "end"}
SHORT = {"supported": "sup", "not supported": "not", "cannot be told": "cbt"}


def cell(rs):
    """Five sessions' answers to one question -> 'right/5 · decided/5', or the spread if there is no key."""
    if not rs:
        return "–"
    n = len(rs)
    if all(r["right"] is None for r in rs):
        c = Counter(SHORT.get(str((r["answer"] or {}).get("answer")).lower(), "?")
                    if isinstance(r["answer"], dict) else "…" for r in rs)
        return "no key: " + ", ".join(f"{k} {v}" for k, v in c.most_common())
    right = sum(1 for r in rs if r["right"] is True)
    judge = sum(1 for r in rs if r["right"] == "judge")
    dec = sum(1 for r in rs if r["decided"])
    s = f"{right}/{n} right"
    if judge:
        s += f" ({judge} unjudged)"
    corr = sum(1 for r in rs if r.get("right_corrected") is True)
    if corr != right:
        s += f" ({corr}/{n} on the corrected key)"
    return s + f" · {dec}/{n} decided"


def reading(b, s):
    def state(rs):
        if any(r["right"] == "judge" for r in rs):
            return "unjudged"
        if all(r["right"] is True for r in rs):
            return "right, decided" if all(r["decided"] for r in rs) else (
                "right, in doubt" if not any(r["decided"] for r in rs) else "right, mixed")
        if not any(r["right"] is True for r in rs):
            return "wrong"
        return "mixed"
    return state(b), state(s)


def build():
    rows, sessions = score_all()
    by = defaultdict(list)
    for r in rows:
        by[(r["run"], r["moment"], r["question"], r["arm"])].append(r)
    questions = []
    for r in rows:
        if r["question"] not in questions:
            questions.append(r["question"])
    scored_q = [q for q in questions if not q.startswith("free") and "what_" not in q
                and "taken_again" not in q and q != "form"]
    out = ["# Result tables\n",
           f"{len(sessions)} sessions. In every cell: how many of the five sessions gave a right "
           "inference, and how many settled the question. The two are separate measures.\n"]

    for run in "ABC":
        out.append(f"\n## Run {run}: the two measures by question, moment and arm\n")
        head = "| Question |" + "".join(f" {MOMENT_NAME[m]}: blind | {MOMENT_NAME[m]}: sighted |"
                                       for m in MOMENT_NAME)
        out += [head, "|---|" + "---|" * 8]
        for q in scored_q:
            line = f"| {q} |"
            for m in MOMENT_NAME:
                for arm in ("blind", "sighted"):
                    line += f" {cell(by.get((run, m, q, arm), []))} |"
            out.append(line)

    out.append("\n## The two arms side by side\n")
    groups = defaultdict(list)
    for run in "ABC":
        for m in MOMENT_NAME:
            for q in scored_q:
                b, s = by.get((run, m, q, "blind"), []), by.get((run, m, q, "sighted"), [])
                if not b or all(r["right"] is None for r in b):
                    continue
                groups[reading(b, s)].append(f"{run} {MOMENT_NAME[m]} {q}")
    out += ["| Blind arm | Sighted arm | Questions (run, moment, question) | How many |", "|---|---|---|---|"]
    for (b, s), items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        shown = "; ".join(items) if len(items) <= 14 else "; ".join(items[:6]) + f"; … and {len(items) - 6} more"
        out.append(f"| {b} | {s} | {shown} | {len(items)} |")

    out.append("\n## Every answer that was wrong or is not yet judged\n")
    bad = [r for r in rows if r["right"] in (False, "judge")]
    if not bad:
        out.append("None.\n")
    for r in bad:
        out.append(f"- `{r['id']}` — key: {r['key']!r}; answer: {json.dumps(r['answer'])}; "
                   f"right: {r['right']}; reason given: {r.get('reason_given')!r}"
                   + (f"; judged: {r['judgement_reason']}" if r.get("judged") else "")
                   + (f"; corrected key: {r['corrected_key']!r} -> right" if r.get("corrected_key") else ""))

    out.append("\n## Answers judged by hand (raw answer beside the judgement)\n")
    for r in [r for r in rows if r.get("judged")]:
        out.append(f"- `{r['id']}` — judged {'right' if r['right'] else 'wrong'}: {r['judgement_reason']} "
                   f"Raw: {json.dumps(r['answer'])}; reason given: {r.get('reason_given')!r}")

    out.append("\n## What the reviewers asked to be taken again at the resume\n")
    out += ["| Run | Arm | Session | Asked for | Undo rehearsal asked | Shown unasked | Asked for what does not exist |",
            "|---|---|---|---|---|---|---|"]
    for s in sessions:
        t = s["retake"]
        out.append(f"| {s['run']} | {s['arm']} | {s['n']} | {', '.join(t['taken']) or 'none'} | "
                   f"{'yes' if t['asked_for_undo_rehearsal'] else 'no'} | "
                   f"{'yes' if t['undo_rehearsal_shown_unasked'] else 'no'} | "
                   f"{', '.join(t['asked_for_instruments_that_do_not_exist']) or '–'} |")

    out.append("\n## Statement c where the brief gives no key\n")
    for r in rows:
        if r["question"] == "2.c" and r["right"] is None:
            out.append(f"- `{r['id']}`: {r['answer']['answer']} — {r.get('reason_given')}")

    out.append("\n## Tokens and wall time\n")
    out += ["| Run | Arm | Session | Tokens in | Tokens out | Cache read | Cache written | Wall s | Agent turns | Record questions | Database queries | Second tries |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in sessions:
        log = RESULTS / "sessions" / s["run"] / s["arm"] / str(s["n"]) / "tool_log.jsonl"
        calls = [json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []
        t = s["tokens"]
        out.append(f"| {s['run']} | {s['arm']} | {s['n']} | {t['input']} | {t['output']} | {t['cache_read']} | "
                   f"{t['cache_write']} | {s['wall_s']} | {s['agent_turns']} | "
                   f"{sum(1 for c in calls if c['tool'] == 'ask_record')} | "
                   f"{sum(1 for c in calls if c['tool'] == 'read_database')} | {s['replies_that_needed_a_second_try']} |")
    (RESULTS / "tables.md").write_text("\n".join(out) + "\n")
    return rows, sessions


if __name__ == "__main__":
    rows, sessions = build()
    keyed = [r for r in rows if r["right"] in (True, False)]
    print(f"{len(sessions)} sessions; {len(keyed)} keyed answers, {sum(1 for r in keyed if not r['right'])} wrong, "
          f"{sum(1 for r in rows if r['right'] == 'judge')} unjudged")
