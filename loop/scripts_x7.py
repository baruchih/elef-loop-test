"""Experiment X7: the key's table of what shows each clause, and the three scripts that go through a
run as a reviewer would: the baseline alone, the fixed policy (a lookup by instrument) and the lookup
by clause. None is a model. Usage: python -m loop.scripts_x7   (the three scripts on the four runs)"""
from .common import *  # noqa: F401,F403
from .x1 import APPROVALS
from .x7 import LIBRARY, PLACES, BASELINE, I_SCOPE, I_TRACE_CALL, CUTS
from .views_x7 import CLAUSES, due

SHOWN, PART, NOT = "shown", "shown in part", "not shown"
# clause -> the instrument that shows it, the approval it has to be taken at (None: any), and how far it shows it
KEY = {"C1": (I_SAME, None, SHOWN), "C2": (I_SUMMARY, None, SHOWN), "C3": (None, None, NOT), "C4": (I_SUMMARY, None, SHOWN),
       "C5": (I_SCOPE, None, PART), "C6": (I_UNDO, "A1", SHOWN), "C7": (I_UNDO, "A2", SHOWN), "C8": (I_RELEASE, None, SHOWN),
       "C9": (I_SENT, None, SHOWN), "C10": (I_TRACE_CALL, None, PART)}


def key_clause(c, hand):
    """hand: [{'instrument', 'taken_for', 'answer'}]. Returns (state, the answers that show it)."""
    inst, at, state = KEY[c]
    by = [h for h in hand if h["instrument"] == inst and (at is None or h["taken_for"] == at)]
    if c == "C7" and not by:            # a rehearsal at A3 shows it for the time it was taken, after the release
        by, state = [h for h in hand if h["instrument"] == I_UNDO and h["taken_for"] == "A3"], PART
    return (state, by) if by else (NOT, [])


def plan_lines(policy):
    lines = {a: [] for a in APPROVALS}
    if policy == "the fixed policy":            # every instrument the baseline lacks, once, at the earliest place
        have = {i for a in APPROVALS for i in BASELINE[a]}
        for i in LIBRARY:
            if i not in have:
                lines[PLACES[i][0]].append(i)
    if policy == "the lookup by clause":        # for each clause, the instrument that shows it, where the clause is due
        for c, (inst, at, _) in KEY.items():
            a = at or CLAUSES[c][1]
            if inst in LIBRARY and inst not in BASELINE[a] and inst not in lines[a]:
                lines[a].append(inst)
    return lines


class Script:
    """Answers the plan step, the question of a wake and the forms from the structured answers, not from the text."""
    def __init__(self, policy):
        self.policy = policy

    def plan(self, prompt, ctx):
        lines = plan_lines(self.policy)
        hand = [{"instrument": i, "taken_for": a, "answer": f"{i} @ {a}"} for a in APPROVALS for i in BASELINE[a] + lines[a]]
        return {"instruments_added_to_the_baseline": {a: [{"instrument": i, "reason": self.policy} for i in lines[a]] for a in APPROVALS},
                "total_price_of_the_plan": None,
                "clauses": self.clauses(list(CLAUSES), hand),
                "what_i_would_have_wanted_and_the_library_or_the_price_did_not_give": "nothing"}

    @staticmethod
    def clauses(ids, hand):
        out = {}
        for c in ids:
            state, by = key_clause(c, hand)
            out[c] = {"state": state, "by": [h["answer"] for h in by],
                      "for_what_part": "the lines or the time the answer names" if state == PART else None}
        return out

    def ask(self, prompt, ctx):
        return {"take": [], "on_named_lines": [], "reason": "A script asks for nothing."}

    def form(self, prompt, ctx):
        a, hand = ctx["a"], ctx["in_hand"]
        bad = [h for h in hand if h["result"] != R_PASS]
        rests = [h["answer"] for h in (bad or [h for h in hand if h["at"] == a])]
        ground = {"kind": "an answer found a breach", "in_words": bad[0]["instrument"]} if bad else {"kind": None, "in_words": None}
        if a != "A3":
            return {"decision": "refuse" if bad else "approve", "answers_it_rests_on": rests, "ground_if_refused": ground,
                    "clauses": self.clauses(due(a), hand), "what_i_raise": []}
        sent = next(h for h in hand if h["instrument"] == I_SENT)
        return {"verdict": "revise" if bad else "approve", "answers_it_rests_on": rests, "ground_if_not_approved": ground,
                "clauses": self.clauses(list(CLAUSES), hand),
                "closing_summary": {"of_the_100_sending_calls": {
                    "confirmed_in_the_record": sent["returns"]["sending_calls_confirmed"],
                    "shown_to_have_left_a_row_in_the_outbox": 0, "shown_to_have_left_none": 0, "not_shown_either_way": 100},
                    "notices_that_may_still_be_sent_under_the_release_that_was_given": 0, "what_is_in_doubt": "nothing"},
                "what_i_raise": []}


POLICIES = ["the baseline alone", "the fixed policy", "the lookup by clause"]

if __name__ == "__main__":
    from .review_x7 import session
    for p in POLICIES:
        for run in CUTS:
            print(session(p, run, 1, kind="scripts", redo=True), flush=True)
