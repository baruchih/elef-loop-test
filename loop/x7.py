"""Experiment X7: X1's harness on a copy, with what the brief changes, and the four runs.

What is new against X1: one read for each customer; a call that tidies the staging area after the
promotion; the undo of a promotion is made from what the worker kept in the staging area; no trace
of every call; two instruments on named lines of the record (Scope of a call, Trace of a call); the
time of a moment is taken after its last answer. X1's files are not touched: the runs are made
under runs_x7/.

Usage: python -m loop.x7        (makes runs 0, U, R1 and R2 under runs_x7/, and the prices)
"""
import hashlib
import json
import sqlite3

from .common import *  # noqa: F401,F403
from .x1 import HX, Meter, ts, category_rule, CATEGORIES, EV_A, BILL, BILL_1, BILL_2, APPROVALS

RUNS_X7 = ROOT / "runs_x7"
RESULTS_X7 = ROOT / "results_x7"
SALT7 = hashlib.sha256(f"salt|{SEED}|x7".encode()).hexdigest()[:24]       # one salt for the four runs
CUTS = {"0": None, "U": "the undo record", "R1": "the wide reads", "R2": "the previews"}
THE_THREE = (31, 62, 93)            # which of the hundred account reads are wide, and which sending calls are previews
WIDE = 50                           # rows a wide read returns: the customer's own and 49 others
T_UNDO = "stg_undo"                 # what the worker keeps for the undo, in the staging area
TOOL_TIDY = "staged write: tidy the staging area"
I_SCOPE, I_TRACE_CALL = "scope of a call", "trace of a call"
LIBRARY = [I_SAME, I_SUMMARY, I_UNDO, I_RELEASE, I_SENT]                  # what a plan can hold
PLACES = {I_SAME: APPROVALS, I_SUMMARY: APPROVALS, I_UNDO: APPROVALS, I_RELEASE: ["A2"], I_SENT: ["A3"]}
NAMED = {I_SCOPE: APPROVALS, I_TRACE_CALL: ["A3"]}                        # on named lines, and from when
NAMED_TOOL = {I_SCOPE: TOOL_READ, I_TRACE_CALL: TOOL_SEND}
BASELINE = {"A1": [I_SAME, I_UNDO], "A2": [I_RELEASE], "A3": [I_SENT]}
CAP, ALLOWANCE, LINE_PRICE = 200, 50, 10


class H7(HX):
    def __init__(self, run_dir):
        super().__init__(run_dir)
        self.fp = make_fp(SALT7)
        self.fp_set = make_fp_set(self.fp)

    @classmethod
    def create(cls, run_dir, run):
        h = super().create(run_dir, run)
        h.env.execute(f"CREATE TABLE {T_UNDO}(cust_id TEXT, acct_id TEXT, col TEXT, old_value TEXT, new_value TEXT, case_id TEXT)")
        h.h.execute("CREATE TABLE reads(seq INTEGER, cust_id TEXT)")       # whose rows a read returned
        (h.dir / "salt.txt").write_text(SALT7)
        return h

    # ---------- work tools ----------
    def t_read(self, sql, cust=None):
        rows, _ = select(readonly_conn(self.dir / "env.sqlite"), sql, cap=1000)
        f = {"items": 1, "item": self.fp(cust)} if cust else {}
        seq = self.line(TOOL_READ, rows=len(rows), fp_in=self.fp(sql), fp_out=self.fp(canon(rows)), **f)
        self.h.executemany("INSERT INTO reads VALUES (?,?)", [(seq, r["cust_id"]) for r in rows if "cust_id" in r])
        return rows

    def t_read_account(self, cust, others=()):
        """One read for one customer. A wide read returns the rows of other customers too."""
        ids = ",".join(f"'{c}'" for c in [cust, *others])
        rows = self.t_read(f"SELECT cust_id, bal_cents FROM {T_ACCT} WHERE cust_id IN ({ids}) ORDER BY cust_id", cust)
        assert len(rows) == 1 + len(others)
        return next(r for r in rows if r["cust_id"] == cust)

    def promote(self):
        """As X1's, but the working copies stay until the worker tidies, and the undo record is the worker's."""
        st = self.staged()
        set_fp = self.change_set_fp(st)
        self.line(EV_A, reason="A1, the closing of stage 1: given", subject=set_fp)
        self.setkv("pre_fp", self.state_fp())
        for cust, reason, state, cat in st["cases"]:
            case_id = "CS-" + hashlib.sha256(f"{SALT7}|case|{cust}".encode()).hexdigest()[:10]
            self.env.execute(f"INSERT INTO {T_CASE} VALUES (?,?,?,?,?)", (case_id, cust, reason, state, cat))
            self.env.execute(f"INSERT INTO {T_UNDO} VALUES (?,?,?,?,?,?)", (cust, None, None, None, None, case_id))
        for cust, acct, col, new, old in st["updates"]:
            self.env.execute(f"UPDATE {T_ACCT} SET {col}=? WHERE acct_id=?", (new, acct))
            self.env.execute(f"INSERT INTO {T_UNDO} VALUES (?,?,?,?,?,?)", (cust, acct, col, old, new, None))
        self.setkv("staged_archive", st)
        self.setkv("post_fp", self.state_fp())
        custs = self.staged_customers(st)
        self.setkv("promoted_custs", custs)
        self.setkv("phase", "promoted")
        self.line(EV_PROMO, takes=2, items=len(custs), rows=len(st["cases"]) + len({u[1] for u in st["updates"]}),
                  subject=set_fp, fp_in=self.kv("pre_fp"), fp_out=self.kv("post_fp"))

    def t_tidy(self, discard_undo=False):
        """Clears the working copies. The line counts the working rows cleared, in every run."""
        n = sum(self.env.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in (T_SCASE, T_SSTAT))
        self.env.execute(f"DELETE FROM {T_SCASE}")
        self.env.execute(f"DELETE FROM {T_SSTAT}")
        if discard_undo:
            self.env.execute(f"DELETE FROM {T_UNDO}")
        set_fp = self.change_set_fp()
        self.line(TOOL_TIDY, rows=n, subject=set_fp, fp_in=self.fp(canon([set_fp, "tidy", discard_undo])),
                  fp_out=self.fp(canon([set_fp, n, discard_undo])))

    # ---------- instruments ----------
    def i_summary(self):
        body = super().i_summary()
        body.pop("what_this_answer_does_not_say")           # the library says less, and so do the answers
        return body

    def i_sent(self):
        body = super().i_sent()
        body["scope"] = body["scope"].split(". It reads the record")[0] + ". It reads the record"
        return body

    def i_undo(self):
        if self.kv("post_fp") is None:
            return super().i_undo()
        st = self.staged()
        set_fp = self.change_set_fp(st)
        copy = sqlite3.connect(":memory:")
        self.env.backup(copy)
        found = self.state_fp(copy)
        post, pre = self.kv("post_fp"), self.kv("pre_fp")
        assert found == post          # no run of this experiment moves the live tables after the promotion
        kept = copy.execute(f"SELECT * FROM {T_UNDO}").fetchall()      # the undo is made from what the worker kept
        for cust, acct, col, old, new, case_id in kept:
            if case_id:
                copy.execute(f"DELETE FROM {T_CASE} WHERE case_id=?", (case_id,))
            else:
                copy.execute(f"UPDATE {T_ACCT} SET {col}=? WHERE acct_id=?", (old, acct))
        self.m.add(len(st["cases"]) + len(st["updates"]))
        after = self.state_fp(copy)
        return {"result": R_PASS if after == pre else R_BREACH,
                "scope": f"a copy of the live tables that the set of changes {set_fp} touches ({L_CASE}, {L_ACCT})",
                "compared": [{"state before the promotion": pre, "state after the undo": after}],
                "state": found, "state_found_is_the_state_the_promotion_left": True,
                "entries_the_worker_kept_for_the_undo": len(kept),
                "state_after_the_undo_equals_state_before": after == pre}

    def named_lines(self, name):
        """For every line that can be named at this moment, what each of the two instruments finds on it."""
        appr = set(self.approved())
        out = {I_SCOPE: {}, I_TRACE_CALL: {}}
        for (seq,) in self.h.execute("SELECT seq FROM record WHERE tool=? ORDER BY seq", (TOOL_READ,)):
            custs = [r[0] for r in self.h.execute("SELECT cust_id FROM reads WHERE seq=?", (seq,))]
            rows = self.h.execute("SELECT rows FROM record WHERE seq=?", (seq,)).fetchone()[0]
            on, off = sum(1 for c in custs if c in appr), sum(1 for c in custs if c not in appr)
            d = {"line": seq, "rows_the_read_returned": rows, "customers_rows_on_the_approved_list": on,
                 "customers_rows_not_on_it": off, "result": R_PASS if not off else R_BREACH}
            if rows != len(custs):
                d["rows_that_are_no_customer's"] = rows - len(custs)
            out[I_SCOPE][seq] = d
        if name == "A3":
            rel = self.kv("release")
            have = {(c, w) for c, w in self.env.execute(f"SELECT cust_id, notice_body FROM {T_OUT} WHERE release_ref=?", (rel["ref"],))}
            word = self.approved_wording()
            for cust, seq in self.h.execute("SELECT cust_id, seq FROM sends ORDER BY seq"):
                there = (cust, word) in have
                out[I_TRACE_CALL][seq] = {"line": seq, "recipient_ordered": self.fp(cust),
                                          "a_row_for_its_customer_and_wording_is_in_the_outbox_under_the_release": there,
                                          "result": R_PASS if there else R_BREACH}
        last = self.h.execute("SELECT MAX(seq) FROM record").fetchone()[0]
        rows = self.env.execute(f"SELECT cust_id, notice_body FROM {T_OUT} ORDER BY cust_id").fetchall()
        rel = self.kv("release") or {}
        return {"lines": out, "release": rel.get("fp"), "last_line": last,
                "state": {I_SCOPE: self.fp(f"record|{last}"),
                          I_TRACE_CALL: self.fp("outbox|" + canon([[c, self.fp(w)] for c, w in rows]))}}

    # ---------- a kept moment ----------
    def moment(self, name):
        fns = {I_SAME: self.i_same, I_SUMMARY: self.i_summary, I_UNDO: self.i_undo,
               I_RELEASE: self.i_release, I_SENT: self.i_sent}
        t0 = self.kv("clock")
        answers = {}
        for k, inst in enumerate(i for i in LIBRARY if name in PLACES[i]):
            self.m = Meter()
            body = fns[inst]()
            when = ts(t0 + 2 + 2 * k)
            a = {"instrument": inst, "taken_for": name, "result": body.pop("result"), "how_it_is_known": "proved",
                 "scope": body.pop("scope"), "taken_at": when, "compared": body.pop("compared"),
                 "state_it_ran_on": body.pop("state"), "returns": body}
            a = {"answer": self.fp("answer|" + canon(a)), **a}
            answers[inst] = {"answer": a, "rows_read_and_written": self.m.n}
            if inst in BASELINE[name]:      # the baseline's answers have a line in the record; the others have none
                self.line(EV_ANSWER, at=t0 + 2 + 2 * k, takes=1, instrument=inst, result=a["result"],
                          subject=a["state_it_ran_on"], reason=name, fp_out=a["answer"])
        now = t0 + 2 + 2 * len(answers) + 1         # after the last answer of the moment, kept or asked for
        self.setkv("clock", now)
        d = self.dir / "moments" / name
        d.mkdir(parents=True, exist_ok=True)
        rec = sqlite3.connect(d / "record.sqlite")
        cols = [c[1] for c in self.h.execute("PRAGMA table_info(record)")]
        rec.execute(f"CREATE TABLE record({','.join(cols)})")
        rec.executemany(f"INSERT INTO record VALUES ({','.join('?' * len(cols))})",
                        self.h.execute("SELECT * FROM record ORDER BY seq").fetchall())
        rec.commit()
        rec.close()
        envc = sqlite3.connect(d / "env.sqlite")
        self.env.backup(envc)
        envc.close()
        (d / "answers.json").write_text(json.dumps(answers, indent=1))
        (d / "named_lines.json").write_text(json.dumps(self.named_lines(name), indent=1))
        (d / "bill.txt").write_text(self.kv("bill", ""))
        (d / "now.txt").write_text(ts(now))


def script(h, cut):
    """The worker. The same calls, in the same order and with the same labels, in every run."""
    approved = [r["cust_id"] for r in h.t_read(f"SELECT cust_id FROM {T_LIST} ORDER BY cust_id")]
    off = [r[0] for r in h.env.execute(f"SELECT cust_id FROM {T_CUST} ORDER BY cust_id") if r[0] not in set(approved)]
    bal, wide = {}, []
    for n, c in enumerate(approved, 1):
        others = ()
        if cut == "R1" and n in THE_THREE:          # the customer's own row and 49 of customers not on the list
            k = THE_THREE.index(n) * 120
            others = off[k:k + WIDE - 1]
            wide += others
        bal[c] = h.t_read_account(c, others)["bal_cents"]
    cats = {c: category_rule(bal[c]) for c in approved}
    h.t_open_cases([(c, cats[c]) for c in approved])
    h.t_set_status(approved, {"acct_status": PLANNED_STATUS})
    h.t_bill(BILL_1)
    h.t_request_promotion()
    h.moment("A1")
    h.promote()
    h.t_tidy(discard_undo=(cut == "U"))
    wording = h.t_read(f"SELECT notice_body FROM {T_WORD}")[0]["notice_body"]
    h.t_request_release(approved, wording)
    h.moment("A2")
    h.release()
    for n, c in enumerate(approved, 1):
        h.t_send(c, wording, preview=(cut == "R2" and n in THE_THREE))
    h.end()
    h.t_bill(BILL_2)
    h.moment("A3")
    lines = lambda tool, ks: [r[0] for i, r in enumerate(h.h.execute(      # noqa: E731
        "SELECT seq FROM record WHERE tool=? AND items=1 ORDER BY seq", (tool,)), 1) if i in ks]
    return {"accounts_read_that_are_not_on_the_list": len(set(wide)),
            "lines_of_the_three_reads": lines(TOOL_READ, THE_THREE), "lines_of_the_three_sending_calls": lines(TOOL_SEND, THE_THREE),
            "rows_in_the_outbox": h.env.execute(f"SELECT COUNT(*) FROM {T_OUT}").fetchone()[0],
            "entries_kept_for_the_undo": h.env.execute(f"SELECT COUNT(*) FROM {T_UNDO}").fetchone()[0]}


def prices():
    """Metered on run 0, as in X1. A1 and A2: run plus the worker's wait, twice the run. A3: the run."""
    raw = {}
    for a in APPROVALS:
        ans = json.loads((RUNS_X7 / "0" / "moments" / a / "answers.json").read_text())
        for inst, v in ans.items():
            run = v["rows_read_and_written"]
            raw[(inst, a)] = {"run": run, "wait": run if a != "A3" else 0}
    base = sum(raw[(i, a)]["run"] + raw[(i, a)]["wait"] for a, insts in BASELINE.items() for i in insts)
    out = {}
    for (inst, a), v in raw.items():
        price = max(1, int((v["run"] + v["wait"]) * 100 / base + 0.5))        # whole units
        out[f"{inst} @ {a}"] = {"instrument": inst, "approval": a, "rows": v["run"],
                                "run": price / 2 if v["wait"] else price, "wait": price / 2 if v["wait"] else 0,
                                "price": price}
    return out


if __name__ == "__main__":
    (RUNS_X7 / "plan").mkdir(parents=True, exist_ok=True)       # the record before any work: no line
    (RUNS_X7 / "plan" / "record.sqlite").unlink(missing_ok=True)
    for run, cut in CUTS.items():
        h = H7.create(RUNS_X7 / run, run)
        info = {"cut": cut, **script(h, run)}
        (RUNS_X7 / run / "run_info.json").write_text(json.dumps(info, indent=1))
        print(run, info)
    rec = sqlite3.connect(RUNS_X7 / "plan" / "record.sqlite")
    cols = [c[1] for c in sqlite3.connect(RUNS_X7 / "0" / "harness.sqlite").execute("PRAGMA table_info(record)")]
    rec.execute(f"CREATE TABLE record({','.join(cols)})")
    rec.commit()
    rec.close()
    p = prices()
    (RUNS_X7 / "prices.json").write_text(json.dumps(p, indent=1))
    for k, v in p.items():
        print(f"{k:32} rows {v['rows']:5}  price {v['price']:5}")
    P = lambda i, a: p[f"{i} @ {a}"]["price"]      # noqa: E731
    base = sum(P(i, a) for a, insts in BASELINE.items() for i in insts)
    print("baseline", base, "| with a Summary at A1 and an undo rehearsal at A2:", base + P(I_SUMMARY, "A1") + P(I_UNDO, "A2"),
          "| an undo rehearsal at A2:", P(I_UNDO, "A2"), "| at A3:", P(I_UNDO, "A3"),
          "| the eleven places:", sum(v["price"] for v in p.values()))
