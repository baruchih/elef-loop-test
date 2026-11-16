"""The corrected cost figures of experiments 1, 1b, X1 and X7.

The runtime's cost figure for a session that is resumed is a running total over its turns. The harness of
these four experiments added it up turn by turn, so every session's cost was counted several times over.
The cost of a turn is the difference from the turn before, and the cost of a session is the last figure.
The tokens were reported for each turn and were right. Nothing in the kept sessions is changed: this reads
steps.jsonl and writes cost_corrected.json and cost_corrected.md at the top of the repo.

Usage: python -m loop.cost
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def turns(steps):
    """The cost of each turn, from the running figure. A turn with no figure (cut off, or made by the harness) costs 0."""
    out, prev = [], 0.0
    for s in steps:
        c = s.get("cost_as_reported", s.get("cost_usd")) or 0
        if not c:
            out.append(0.0)
            continue
        out.append(c - prev if c >= prev else c)
        prev = c
    return out


def of_session(d):
    """(corrected cost, as first summed, {act: corrected cost}) of the session kept in folder d."""
    f = Path(d) / "steps.jsonl"
    if not f.exists():
        return 0.0, 0.0, {}
    steps = [json.loads(ln) for ln in f.read_text().splitlines() if ln.strip()]
    own, acts = turns(steps), {}
    for s, c in zip(steps, own):
        a = s.get("act") or s.get("moment") or s.get("step")
        acts[a] = acts.get(a, 0.0) + c
    return sum(own), sum(s.get("cost_usd") or 0 for s in steps), acts


def sessions(base, names):
    """Every kept session under base, with the parts of its path named by `names`."""
    out = []
    for f in sorted(Path(base).glob("/".join(["*"] * (len(names) + 1)) + "/steps.jsonl")):
        parts = f.parent.relative_to(base).parts
        c, old, acts = of_session(f.parent)
        sj = f.parent / "session.json"
        ended = json.loads(sj.read_text()).get("ended") if sj.exists() else None
        out.append(dict(zip(names, parts)) | {"n": parts[-1], "cost": c, "as_first_summed": old, "by_act": acts, "ended": ended})
    return out


def table(head, rows):
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] +
                     ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def usd(x, n=2):
    return f"${x:.{n}f}"


def mean(xs, n=3):
    xs = list(xs)
    return usd(sum(xs) / len(xs), n) if xs else "—"


MODELS = ["opus", "sonnet", "haiku"]


def main():
    R = ROOT
    e1 = sessions(R / "results/sessions", ["run", "arm"])
    e1p = [of_session(R / "results/pilot/session_A_blind")]
    b1 = sessions(R / "results_1b/sessions", ["model", "condition", "run"])
    b1p = [dict(zip(["model", "condition", "run"], f.parent.relative_to(R / "results_1b/pilot").parts)) |
         {"cost": of_session(f.parent)[0], "as_first_summed": of_session(f.parent)[1]}
         for f in sorted((R / "results_1b/pilot").glob("*/*/*/*/steps.jsonl"))]
    x1 = sessions(R / "results_x1/sessions", ["model", "condition", "run"])
    x1p = {p: [dict(zip(["model", "condition", "run"], f.parent.relative_to(R / "results_x1" / p).parts)) |
               {"cost": of_session(f.parent)[0], "as_first_summed": of_session(f.parent)[1]}
               for f in sorted((R / "results_x1" / p).glob("*/*/*/*/steps.jsonl"))]
           for p in ["pilot", "pilot_draft2", "pilot_draft3", "pilot_draft4_no_time"]}
    x7 = sessions(R / "results_x7/sessions", ["model", "run"])
    x7p = {p: [dict(zip(["model", "run"], f.parent.relative_to(R / "results_x7" / p).parts)) |
               {"cost": of_session(f.parent)[0], "as_first_summed": of_session(f.parent)[1]}
               for f in sorted((R / "results_x7" / p).glob("*/*/*/steps.jsonl"))]
           for p in ["pilot_1_draft2", "pilot"]}
    tot = lambda ss, k="cost": sum(s[k] for s in ss)      # noqa: E731

    out = ["# The cost figures, corrected", "",
           "**16 November 2026.** The runtime's cost figure for a resumed session is a running total over its turns. "
           "The harness of experiments 1, 1b, X1 and X7 added that figure up turn by turn, so a session's cost was counted "
           "several times over. Here a turn costs the difference from the turn before, and a session costs its last figure. "
           "The figure is the runtime's price of the tokens at list prices; on a subscription it is not a sum that was paid. "
           "Tokens, wall time and every other measure were right and are unchanged. Made by `python -m loop.cost` from the kept sessions.", "",
           "## The totals", "",
           table(["experiment", "sessions", "as the notes gave it", "corrected"],
                 [["1", len(e1), usd(tot(e1, "as_first_summed")), usd(tot(e1))],
                  ["1b", len(b1), usd(tot(b1, "as_first_summed")), usd(tot(b1))],
                  ["X1", len(x1), usd(tot(x1, "as_first_summed")), usd(tot(x1))],
                  ["X7", len(x7), usd(tot(x7, "as_first_summed")), usd(tot(x7))]]), ""]

    out += ["## Experiment 1: the cost of a review", "",
            "One model, `claude-fable-5-2`. A review is one session: the four moments of one run.", "",
            table(["arm", "sessions", "as the note gave it, a review", "corrected, a review", "corrected, all"],
                  [[a, len(ss), mean((s["as_first_summed"] for s in ss), 2), mean((s["cost"] for s in ss), 2), usd(tot(ss))]
                   for a in ["blind", "sighted", None] for ss in [[s for s in e1 if a in (None, s["arm"])]]
                   for a in [a or "both"]]), "",
            f"The pilot session: {usd(e1p[0][0])} (as first summed {usd(e1p[0][1])}).", ""]

    out += ["## Experiment 1b: the cost of a review, by model", "",
            table(["model", "condition", "sessions", "as the note gave it, a review", "corrected, a review", "corrected, all"],
                  [[m, c or "both", len(ss), mean((s["as_first_summed"] for s in ss), 2), mean((s["cost"] for s in ss), 3), usd(tot(ss))]
                   for m in MODELS for c in ["asis", "fixes", None]
                   for ss in [[s for s in b1 if s["model"] == m and c in (None, s["condition"])]]] +
                  [["all", "both", len(b1), "", "", usd(tot(b1))]]), "",
            f"The six pilot sessions: {usd(tot(b1p))} (as first summed {usd(tot(b1p, 'as_first_summed'))}).", ""]

    out += ["## X1: the cost of a session, by model and condition", "",
            table(["model", "condition", "sessions", "as the note gave it, a session", "corrected, a session", "corrected, all",
                   "the plan", "wake A1", "wake A2", "the verdict"],
                  [[m, c or "both", len(ss), mean((s["as_first_summed"] for s in ss), 3), mean((s["cost"] for s in ss), 3), usd(tot(ss))] +
                   [mean((s["by_act"][a] for s in ss if a in s["by_act"]), 3) for a in ["plan", "A1", "A2", "A3"]]
                   for m in MODELS for c in ["priced", "free", None]
                   for ss in [[s for s in x1 if s["model"] == m and c in (None, s["condition"])]]] +
                  [["all", "both", len(x1), "", "", usd(tot(x1)), "", "", "", ""]]), "",
            "A session that goes to the end (run 0), corrected: " +
            "; ".join(f"{m} priced {mean((s['cost'] for s in x1 if s['model'] == m and s['run'] == '0' and s['condition'] == 'priced'), 3)}, "
                      f"free {mean((s['cost'] for s in x1 if s['model'] == m and s['run'] == '0' and s['condition'] == 'free'), 3)}"
                      for m in MODELS) + ".", "",
            "The pilots of X1, six sessions each:", "",
            table(["pilot", "sessions", "as first summed", "corrected"] + MODELS,
                  [[p, len(ss), usd(tot(ss, "as_first_summed")), usd(tot(ss))] +
                   [usd(tot([s for s in ss if s["model"] == m])) for m in MODELS] for p, ss in x1p.items()]), ""]

    out += ["## X7: the cost of a session, by model, by run and by act", "",
            "The acts are means over the sessions that reached the act. A session that goes to the end is one that reached the verdict.", "",
            table(["model", "run", "sessions", "as the note gave it, a session", "corrected, a session", "corrected, all",
                   "the plan", "wake A1", "wake A2", "the verdict", "reached the verdict", "a session to the end"],
                  [[m, r or "all", len(ss), mean((s["as_first_summed"] for s in ss), 3), mean((s["cost"] for s in ss), 3), usd(tot(ss))] +
                   [mean((s["by_act"][a] for s in ss if a in s["by_act"]), 3) for a in ["plan", "A1", "A2", "A3"]] +
                   [len(end), mean((s["cost"] for s in end), 3)]
                   for m in MODELS for r in ["0", "U", "R1", "R2", None]
                   for ss in [[s for s in x7 if s["model"] == m and r in (None, s["run"])]]
                   for end in [[s for s in ss if "A3" in s["by_act"]]]] +
                  [["all", "all", len(x7), "", "", usd(tot(x7))] + [""] * 6]), "",
            "The pilots of X7, six sessions each: " +
            "; ".join(f"`{p}` {usd(tot(ss))} (as first summed {usd(tot(ss, 'as_first_summed'))})" for p, ss in x7p.items()) + ".", ""]

    # ---------- X7: cost by reading ----------
    rd = {(r["who"], r["run"], str(r["n"])): r for r in json.loads((R / "results_x7/reading_of_the_record.json").read_text())}
    sc = {(s["who"], s["run"], str(s["n"])): s for s in json.loads((R / "results_x7/scores.json").read_text())["sessions"] if not s["script"]}
    rows = []
    for run, what in [("R1", "all the account reads covered"), ("R2", "all 100 sending lines with their times returned")]:
        for m in MODELS:
            for had in (True, False):
                ss = []
                for s in x7:
                    if s["model"] != m or s["run"] != run:
                        continue
                    r = rd[(m, run, s["n"])]
                    h = r["all_the_account_reads_covered"] if run == "R1" else (r["reached_A3"] and r["sending_lines_with_their_times_returned"] == 100)
                    if h == had:
                        ss.append(s | {"q": r["questions"], "found": bool(sc[(m, run, s["n"])].get("finding", {}).get("proved"))})
                if ss:
                    rows.append([run, m, what if had else "not", len(ss), sum(1 for s in ss if s["found"]),
                                 f"{sum(s['q'] for s in ss) / len(ss):.1f}", mean((s["cost"] for s in ss), 3),
                                 mean((s["as_first_summed"] for s in ss), 3)])
    out += ["## X7: cost by reading", "",
            "The sessions on the two runs whose cut shows only in the record, set apart by whether the session had the lines in front of it "
            "(table 7 of X7), with what a session of each kind cost. A session that proves a cut ends there, so on R1 a find ends at A1 "
            "and costs less than a miss that goes on to the verdict; on R2 the cut is at A3 and both go to the end.", "",
            table(["run", "model", "the reading", "sessions", "found and proved", "questions to the record, mean",
                   "corrected, a session", "as first summed"], rows), ""]
    c0 = {m: [s for s in x7 if s["model"] == m and s["run"] == "0"] for m in MODELS}
    out += ["On clean work (run 0), where every session goes to the end, by how much of the sending lines the session had returned with their times:", "",
            table(["model", "sessions", "sending lines with their times returned, mean of 100", "questions to the record, mean", "corrected, a session"],
                  [[m, len(ss), f"{sum(rd[(m, '0', s['n'])]['sending_lines_with_their_times_returned'] for s in ss) / len(ss):.1f}",
                    f"{sum(rd[(m, '0', s['n'])]['questions'] for s in ss) / len(ss):.1f}", mean((s["cost"] for s in ss), 3)]
                   for m, ss in c0.items()]), ""]
    (R / "cost_corrected.md").write_text("\n".join(out))
    (R / "cost_corrected.json").write_text(json.dumps(
        {"1": e1, "1b": b1, "X1": x1, "X7": x7, "pilots": {"1": [{"cost": e1p[0][0], "as_first_summed": e1p[0][1]}], "1b": b1p, "X1": x1p, "X7": x7p}}, indent=1))
    print("\n".join(out))


if __name__ == "__main__":
    main()
