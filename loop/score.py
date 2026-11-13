"""Scores the filled forms against the key. Two measures for every answer, kept apart:

  right    is the answer justified by what that reviewer could see at that moment?
           True / False / None (the brief gives no key: reported only) / "judge" (needs a judgement)
  decided  did the answer settle the question (True) or leave it in doubt (False)?

Judgements made by hand live in results/judgements.json, keyed by the row id, with the raw
answer kept beside them in the scores.

Usage: python -m loop.score            (scores every finished session, writes results/scores.json)
"""
import json
import re

from .common import RUNS, RESULTS

Q1_MAP = {"notice_sent_and_confirmed": "notice_sent_and_confirmed",
          "notice_ordered_and_not_confirmed": "notice_ordered_and_not_confirmed",
          "notice_not_tried": "notice_not_tried",
          "case_and_status_promoted": "case_and_status_promoted",
          "case_and_status_still_in_the_staging_area": "case_and_status_still_in_staging",
          "waiting_for_an_approval": "waiting_for_an_approval"}
Q4_MAP = {"notices_done_according_to_the_record": "notice_sent_and_confirmed",
          "notices_in_doubt": "notice_ordered_and_not_confirmed",
          "notices_not_tried": "notice_not_tried",
          "cases_and_status_changes_promoted_according_to_the_record": "case_and_status_promoted"}
SUP, NOT, CBT = "supported", "not supported", "cannot be told"


def ints(v):
    return sorted({int(x) for x in re.findall(r"\d+", str(v))}) if v is not None else []


def norm(v):
    return re.sub(r"\s+", " ", str(v).strip().lower())


def q2_key(run, arm, moment, s):
    """-> (accepted answer or None or 'judge', expected numbers or None, the key in words)"""
    if s in "ab":
        return SUP, None, "supported"
    if s == "c":
        if moment == "m1":
            return SUP, None, "supported"
        if run == "C" and moment == "m3":
            return CBT, None, "cannot be told, and not a breach"
        return None, None, "no key: report the answer and its reason"
    if s == "d":
        if run == "B" and arm == "blind":
            return "judge", None, "supported for the confirmed calls; the unconfirmed call cannot be told"
        if run == "B":
            return SUP, None, "supported for every row in the outbox, the 40th included"
        return SUP, None, "supported"
    if s == "e":
        return SUP, None, "supported"
    if s == "f":
        if run == "B" and arm == "blind":
            return CBT, [39, 40], "cannot be told: 39 or 40"
        return SUP, [40], "supported: 40" + (" (after looking)" if run == "B" else "")
    return CBT, None, "cannot be told"


def score_session(sess):
    run, arm, n = sess["run"], sess["arm"], sess["n"]
    rows = []

    def add(moment, q, key, answer, right, decided, note=None, reason=None):
        rows.append({"id": f"{run}/{arm}/{n}/{moment}/{q}", "run": run, "arm": arm, "n": n,
                     "moment": moment, "question": q, "key": key, "answer": answer,
                     "reason_given": reason, "right": right, "decided": decided, "note": note})

    for moment in ("m1", "m2", "m3", "m4"):
        form = sess["forms"].get(moment)
        stop = json.loads((RUNS / run / "key" / f"stop_record_{moment}.json").read_text())
        if form is None:
            add(moment, "form", "a filled form", None, False, False, "no readable form")
            continue
        if moment != "m4":
            q1 = form.get("q1_where_the_work_stands") or {}
            for fk, sk in Q1_MAP.items():
                a = q1.get(fk)
                if isinstance(a, (int, float)) and not isinstance(a, bool):
                    right = int(a) == stop[sk]
                elif norm(a) == "not relevant yet":
                    right = True if (moment == "m1" and sk.startswith("notice_")) else "judge"
                else:
                    right = False
                key = stop[sk] if not (moment == "m1" and sk.startswith("notice_")) \
                    else f"{stop[sk]}, or 'not relevant yet'"
                add(moment, "1." + fk, key, a, right, True)
            q2 = form.get("q2_what_the_evidence_supports") or {}
            for s, body in q2.items():
                body = body if isinstance(body, dict) else {"answer": body}
                ans, val = norm(body.get("answer")), body.get("value")
                acc, nums, words = q2_key(run, arm, moment, s)
                note = None
                if acc is None:
                    right = None
                elif acc == "judge":
                    right = False if ans == NOT else "judge"
                else:
                    right = ans == acc
                    if right and nums is not None and ints(val) != nums:
                        right, note = "judge", f"the answer fits the key, the value {val!r} does not plainly"
                add(moment, "2." + s, words, {"answer": body.get("answer"), "value": val},
                    right, ans in (SUP, NOT), note, body.get("reason"))
            q3 = form.get("q3_before_the_work_continues") or {}
            a = q3.get("notices_that_may_still_go_out_under_the_release_that_was_given")
            if moment == "m1":
                key = "no release has been given"
                right = True if "no release" in norm(a) else ("judge" if ints(a) == [0] else False)
            else:
                key = 60
                right = isinstance(a, (int, float)) and int(a) == 60
            add(moment, "3.notices_that_may_still_go_out", key, a, right, True,
                "61: the error the experiment looks for" if ints(a) == [61] else None, q3.get("reason"))
            a = q3.get("a_call_that_was_not_confirmed_may_be_tried_again_under_that_release")
            add(moment, "3.unconfirmed_call_may_be_tried_again", "no", a,
                norm(a) == "no" if norm(a) in ("yes", "no") else "judge", True,
                None if run == "B" and moment != "m1" else "keyed by the brief only for run B from the stop on; "
                "scored here by rule 4 of the rules sheet", q3.get("reason"))
            add(moment, "3.answers_that_must_be_taken_again", "reported, not scored",
                q3.get("answers_that_must_be_taken_again"), None, True)
        q4 = form.get("q4_closing_summary_if_the_task_ended_now") or {}
        for fk, sk in Q4_MAP.items():
            a = q4.get(fk)
            right = isinstance(a, (int, float)) and not isinstance(a, bool) and int(a) == stop[sk]
            add(moment, "4." + fk, stop[sk], a, right, True)
        add(moment, "4.what_is_in_doubt", "reported", q4.get("what_is_in_doubt"), None, True)
        add(moment, "4.what_was_not_checked", "reported", q4.get("what_was_not_checked"), None, True)
        add(moment, "free", "reported",
            form.get("what_i_could_not_tell_and_what_i_would_have_needed"), None, True)
    return rows


def score_all():
    jpath = RESULTS / "judgements.json"
    judgements = json.loads(jpath.read_text()) if jpath.exists() else {}
    rows, sessions = [], []
    for p in sorted((RESULTS / "sessions").glob("*/*/*/session.json")):
        sess = json.loads(p.read_text())
        sessions.append(sess)
        for r in score_session(sess):
            r["right_by_the_scorer"] = r["right"]
            if r["id"] in judgements:
                j = judgements[r["id"]]
                r["right"], r["judged"], r["judgement_reason"] = j["right"], True, j["why"]
                r["decided"] = j.get("decided", r["decided"])
                if "right_corrected" in j:
                    r["right_corrected"], r["corrected_key"] = j["right_corrected"], j["corrected_key"]
            r.setdefault("right_corrected", r["right"])
            rows.append(r)
    (RESULTS / "scores.json").write_text(json.dumps(rows, indent=1))
    return rows, sessions


if __name__ == "__main__":
    rows, sessions = score_all()
    keyed = [r for r in rows if r["right"] in (True, False)]
    print(f"{len(sessions)} sessions, {len(rows)} answers, {len(keyed)} with a key: "
          f"{sum(1 for r in keyed if r['right'])} right, {sum(1 for r in keyed if not r['right'])} wrong, "
          f"{sum(1 for r in rows if r['right'] == 'judge')} waiting for a judgement")
    for r in rows:
        if r["right"] in (False, "judge"):
            print(json.dumps({k: r[k] for k in ("id", "key", "answer", "right", "reason_given", "note")}))
