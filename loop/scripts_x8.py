"""Experiment X8: the two scripts that go through a run as a reviewer would, under S and under D.
- The fixed policy, as X7 ran it: a Summary of the change at A1, no question to the record, rulings by the answers.
  It states that none of the lines were read and that the record shows nothing.
- The fetching policy: the fixed policy, and before each approval one question that shows every line of the
  stage with all its fields. It does nothing with what comes back, and states "in full" and "nothing".
Neither is a model. Usage: python -m loop.scripts_x8   (twelve passes, under results_x8/scripts/)"""
import json

from . import log_x8 as lg
from .scripts_x7 import Script
from .x8 import RUNS_X8, CONDITIONS, CUTS

POLICIES = ["the fixed policy", "the fetching policy"]


class Script8(Script):
    def __init__(self, policy, cond, run, log_file):
        super().__init__("the fixed policy")            # the plan and the rulings are the fixed policy's
        self.name, self.cond, self.run, self.log_file = policy, cond, run, log_file

    def ask(self, prompt, ctx):
        if self.name == "the fetching policy" and not ctx.get("returned"):
            a, (first, last) = ctx["a"], ctx["stage"]
            took = CONDITIONS[self.cond]["took"]
            args = {"seq_from": first, "seq_to": last, "show_lines": True, "limit": 200}
            db = RUNS_X8 / self.run / "moments" / a / ("record_took.sqlite" if took else "record.sqlite")
            text, err = lg.ask_record(db, took, args)           # the same question a session's tool would put, and the same log
            with open(self.log_file, "a") as f:
                f.write(json.dumps({"moment": a, "tool": "ask_record", "args": args, "error": err, "reply": text}) + "\n")
        return {"take": [], "on_named_lines": [], "reason": "A script asks for no answer."}

    def form(self, prompt, ctx):
        f = super().form(prompt, ctx)
        if CONDITIONS[self.cond]["statement"]:
            f["the_record_of_this_stage"] = {"read": "in full" if self.name == "the fetching policy" else 0,
                                            "shows_that_does_not_fit_the_agreement": "nothing"}
        return f


if __name__ == "__main__":
    from .review_x8 import session
    for p in POLICIES:
        for cond in ("S", "D"):
            for run in CUTS:
                print(session(p, cond, run, 1, kind="scripts", redo=True), flush=True)
