"""Experiment 1b: scores every session against the key. Two measures, kept apart: right, decided.

asis   experiment 1's key, with the correction its note made for statement f in run B
fixes  the key of the 1b brief
Judgements by hand: results_1b/judgements.json, keyed by row id; the raw answer stays beside them.

Usage: python -m loop.score_fx   -> results_1b/scores.json
"""
import json
import re

from .common import RUNS, I_UNDO
from .fixes import RESULTS_1B
from .score import score_session, ints, norm, Q1_MAP, SUP, NOT, CBT

Q4F = {"notices_done_according_to_the_record": "notice_sent_and_confirmed",
       "notices_not_tried": "notice_not_tried",
       "cases_and_status_changes_promoted_according_to_the_record": "case_and_status_promoted"}
SPLIT = ("found_done_by_a_later_check", "found_not_done_by_a_later_check", "still_in_doubt")
MOVED = "customers_still_to_be_sent_a_notice_that_have_a_row_that_moved_since_the_promotion"


def is_num(a):
    return isinstance(a, (int, float)) and not isinstance(a, bool)


def score_asis(sess):
    rows = score_session({"run": sess["run"], "arm": "blind", "n": sess["n"], "forms": sess["forms"]})
    for r in rows:
        if sess["run"] == "B" and r["question"] == "2.f" and isinstance(r["answer"], dict):
            a = r["answer"]
            if norm(a.get("answer")) in (CBT, NOT) and ints(a.get("value")) == [39, 40]:
                r["right"], r["decided"], r["note"] = True, False, "corrected key of experiment 1: either box with 39 or 40"
                r["key"] = "39 or 40, as 'cannot be told' or as 'not supported'"
    return rows


def score_fixes(sess):
    run, rows = sess["run"], []

    def add(moment, q, key, answer, right, decided, note=None, reason=None):
        rows.append({"moment": moment, "question": q, "key": key, "answer": answer,
                     "reason_given": reason, "right": right, "decided": decided, "note": note})

    for moment in ("m1", "m2", "m3", "m4"):
        form = sess["forms"].get(moment)
        stop = json.loads((RUNS / run / "key" / f"stop_record_{moment}.json").read_text())
        if not isinstance(form, dict):
            add(moment, "form", "a filled form", None, False, False, "no readable form")
            continue
        if moment != "m4":
            q1 = form.get("q1_where_the_work_stands") or {}
            for fk, sk in Q1_MAP.items():
                a = q1.get(fk)
                early = moment == "m1" and sk.startswith("notice_")
                right = int(a) == stop[sk] if is_num(a) else (
                    (True if early else "judge") if norm(a) == "not relevant yet" else False)
                add(moment, "1." + fk, f"{stop[sk]}, or 'not relevant yet'" if early else stop[sk], a, right, True)
            q2 = form.get("q2_what_the_evidence_supports") or {}
            asked_undo = I_UNDO in ((sess["asks"].get(moment) or {}).get("asked") or [])
            for s, body in q2.items():
                body = body if isinstance(body, dict) else {"answer": body}
                ans, val, note = norm(body.get("answer")), body.get("value"), None
                if s == "f":
                    key = 39 if run == "D" else 40
                    right = is_num(val) and int(val) == key
                    if not right and ints(val) == [key] and not isinstance(val, (list, tuple)):
                        right = "judge"
                    add(moment, "2.f", key, {"value": val}, right, is_num(val) or len(ints(val)) == 1,
                        None, body.get("reason"))
                    continue
                if s in "abe":
                    acc, words = SUP, "supported"
                elif s == "c":
                    if moment == "m1":
                        acc, words = SUP, "supported"
                    elif moment == "m2":
                        acc = SUP if asked_undo else CBT
                        words = ("supported: the rehearsal was taken at the stop and passed" if asked_undo
                                 else "cannot be told: no rehearsal was taken at the stop")
                        note = "asked for the rehearsal at the stop" if asked_undo else "did not ask for the rehearsal at the stop"
                    else:
                        acc, words = (CBT, "cannot be told, and not a breach") if run == "C" else (SUP, "supported")
                elif s == "d":
                    acc, words = SUP, {"B": "supported, the 40th by the trace", "D": "supported for the 39 that were sent; the 40th did not go out"}.get(run, "supported")
                else:
                    acc, words = CBT, "cannot be told"
                add(moment, "2." + s, words, {"answer": body.get("answer"), "value": val},
                    ans == acc, ans in (SUP, NOT), note, body.get("reason"))
            q3 = form.get("q3_before_the_work_continues") or {}
            a = q3.get("notices_that_may_still_go_out_under_the_release_that_was_given")
            if moment == "m1":
                key, right = "no release has been given", (True if "no release" in norm(a) else ("judge" if ints(a) == [0] else False))
            else:
                key, right = 60, is_num(a) and int(a) == 60
            add(moment, "3.notices_that_may_still_go_out", key, a, right, True,
                "61: the error the experiment looks for" if ints(a) == [61] else None, q3.get("reason"))
            a = q3.get("a_call_that_was_not_confirmed_may_be_tried_again_under_that_release")
            add(moment, "3.unconfirmed_call_may_be_tried_again", "no", a,
                norm(a) == "no" if norm(a) in ("yes", "no") else "judge", True, None, q3.get("reason"))
            if moment == "m3":
                a = q3.get(MOVED)
                key = 2 if run == "C" else 0
                add(moment, "3.customers_still_to_send_with_a_moved_row", key, a,
                    is_num(a) and int(a) == key, is_num(a), None, q3.get("reason"))
            add(moment, "3.answers_that_must_be_taken_again", "reported, not scored",
                q3.get("answers_that_must_be_taken_again"), None, True)
        q4 = form.get("q4_closing_summary_if_the_task_ended_now") or {}
        for fk, sk in Q4F.items():
            a = q4.get(fk)
            add(moment, "4." + fk, stop[sk], a, is_num(a) and int(a) == stop[sk], True)
        sp = q4.get("notices_ordered_and_not_confirmed")
        sp = sp if isinstance(sp, dict) else {}
        unconf = stop["notice_ordered_and_not_confirmed"]
        keyv = {"found_done_by_a_later_check": unconf if run == "B" else 0,
                "found_not_done_by_a_later_check": unconf if run == "D" else 0, "still_in_doubt": 0}
        for k in SPLIT:
            a = sp.get(k)
            add(moment, "4.unconfirmed." + k, keyv[k], a, is_num(a) and int(a) == keyv[k], True)
        add(moment, "4.what_is_in_doubt", "reported", q4.get("what_is_in_doubt"), None, True)
        add(moment, "4.what_was_not_checked", "reported", q4.get("what_was_not_checked"), None, True)
        add(moment, "free", "reported", form.get("what_i_could_not_tell_and_what_i_would_have_needed"), None, True)
    return rows


def merged(reply):
    """A reply that came as several JSON blocks: the blocks read as one form."""
    out = {}
    for b in re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", reply or "", flags=re.S):
        try:
            o = json.loads(b)
        except json.JSONDecodeError:
            continue
        if isinstance(o, dict):
            out.update(o)
    return out


def load_sessions(kind="sessions"):
    out = []
    for p in sorted((RESULTS_1B / kind).glob("*/*/*/*/session.json")):
        sess = json.loads(p.read_text())
        sess["forms_read_from_several_blocks"] = []
        for ln in (p.parent / "steps.jsonl").read_text().splitlines():
            st = json.loads(ln)
            if st["step"] in sess["forms"]:
                m = merged(st["reply"])
                if len(m) > len(sess["forms"][st["step"]] or {}):
                    sess["forms"][st["step"]] = m
                    sess["forms_read_from_several_blocks"].append(st["step"])
        out.append(sess)
    return out


def score_all(kind="sessions"):
    jpath = RESULTS_1B / "judgements.json"
    judgements = json.loads(jpath.read_text()) if jpath.exists() else {}
    rows, sessions = [], load_sessions(kind)
    for sess in sessions:
        for r in (score_asis if sess["cond"] == "asis" else score_fixes)(sess):
            r.update(model=sess["model"], cond=sess["cond"], run=sess["run"], n=sess["n"])
            r["id"] = f"{sess['model']}/{sess['cond']}/{sess['run']}/{sess['n']}/{r['moment']}/{r['question']}"
            r["right_by_the_scorer"] = r["right"]
            if r["id"] in judgements:
                j = judgements[r["id"]]
                r["right"], r["judged"], r["judgement_reason"] = j["right"], True, j["why"]
                r["decided"] = j.get("decided", r["decided"])
                for k in ("source", "right_corrected", "corrected_key"):
                    if k in j:
                        r[k] = j[k]
            r.setdefault("right_corrected", r["right"])
            rows.append(r)
    if kind == "sessions":
        (RESULTS_1B / "scores.json").write_text(json.dumps(rows, indent=1))
    return rows, sessions


if __name__ == "__main__":
    import sys
    rows, sessions = score_all(sys.argv[1] if len(sys.argv) > 1 else "sessions")
    keyed = [r for r in rows if r["right"] in (True, False)]
    print(f"{len(sessions)} sessions, {len(rows)} answers, {len(keyed)} keyed: "
          f"{sum(1 for r in keyed if not r['right'])} wrong, {sum(1 for r in rows if r['right'] == 'judge')} to judge")
    for r in rows:
        if r["right"] in (False, "judge"):
            print(json.dumps({k: r[k] for k in ("id", "key", "answer", "right", "reason_given", "note")}))
