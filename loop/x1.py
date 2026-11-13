"""Experiment X1: the harness on the plain course, the script with its switches, the five runs.

A run is made to the end by the script whatever the instruments answer, and three moments are
kept: A1 (the closing of stage 1, before the promotion), A2 (the release asked, before it is
given) and A3 (the end). At each moment every instrument that can be taken there is taken and
metered. Experiments 1 and 1b are not touched.

Usage: python -m loop.x1        (makes runs 0 to 4 under runs_x1/, and the prices)
"""
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from . import build_env
from .common import *  # noqa: F401,F403
from .fixes import I_TRACE

RUNS_X1 = ROOT / "runs_x1"
RESULTS_X1 = ROOT / "results_x1"
SALT = hashlib.sha256(f"salt|{SEED}|x1".encode()).hexdigest()[:24]      # one salt for the five runs
APPROVALS = ["A1", "A2", "A3"]
PLACES = {I_SAME: APPROVALS, I_SUMMARY: APPROVALS, I_UNDO: APPROVALS,
          I_RELEASE: ["A2"], I_SENT: ["A3"], I_TRACE: ["A3"]}
LIBRARY = [I_SAME, I_SUMMARY, I_UNDO, I_RELEASE, I_SENT, I_TRACE]
BASELINE = {"A1": [I_SAME, I_UNDO], "A2": [I_RELEASE], "A3": [I_SENT]}
CAP, ALLOWANCE = 200, 50

CATEGORIES = ["cat_standard", "cat_enhanced", "cat_priority"]
OTHER_COLUMN, L_OTHER_COL = "opened_on", "opening date column"
OTHER_VALUE = "2031-03-07"       # not the date of ELEF's clock, which the wakes show
CUTS = {"0": None, "1": "wrong set", "2": "outside the agreement", "3": "confirmed and not sent",
        "4": "the category"}
EV_A = "reviewer: approval"
BILL = "worker: bill"
PREVIEWS = range(31, 41)            # run 3: the 31st to the 40th sending call
SEND_EVERY, SEND_TAKES, PREVIEW_TAKES = 8, (5, 4, 6, 5), 1     # seconds, on the record's clock


def category_rule(bal_cents):
    """The requester's rule: the category follows the account's balance, in three bands."""
    return CATEGORIES[0] if bal_cents < 5_500_000 else CATEGORIES[1] if bal_cents < 8_500_000 else CATEGORIES[2]


def ts(t):
    return datetime.fromtimestamp(t).strftime("%Y-%m-%dT%H:%M:%S")


class Meter:
    def __init__(self):
        self.n = 0

    def add(self, k):
        self.n += k


class HX:
    def __init__(self, run_dir):
        self.dir = Path(run_dir)
        self.env = sqlite3.connect(self.dir / "env.sqlite", isolation_level=None)
        self.h = sqlite3.connect(self.dir / "harness.sqlite", isolation_level=None)
        self.fp = make_fp(SALT)
        self.fp_set = make_fp_set(self.fp)
        self.m = Meter()

    @classmethod
    def create(cls, run_dir, run):
        run_dir = Path(run_dir)
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True)
        build_env.build(run_dir / "env.sqlite")
        env = sqlite3.connect(run_dir / "env.sqlite", isolation_level=None)
        env.execute(f"ALTER TABLE {T_CASE} ADD COLUMN case_category TEXT")
        for case_id, bal in env.execute(f"SELECT c.case_id, a.bal_cents FROM {T_CASE} c JOIN {T_ACCT} a USING (cust_id)").fetchall():
            env.execute(f"UPDATE {T_CASE} SET case_category=? WHERE case_id=?", (category_rule(bal), case_id))
        env.execute(f"DROP TABLE {T_SCASE}")
        env.execute(f"DROP TABLE {T_SSTAT}")
        env.execute(f"CREATE TABLE {T_SCASE}(cust_id TEXT PRIMARY KEY, case_reason TEXT, case_state TEXT, case_category TEXT)")
        env.execute(f"CREATE TABLE {T_SSTAT}(cust_id TEXT, acct_id TEXT, col TEXT, new_value TEXT, PRIMARY KEY(cust_id, col))")
        env.close()
        h = sqlite3.connect(run_dir / "harness.sqlite", isolation_level=None)
        h.executescript("""
        CREATE TABLE kv(k TEXT PRIMARY KEY, v TEXT);
        CREATE TABLE record(seq INTEGER PRIMARY KEY, time TEXT, returned TEXT, tool TEXT, status TEXT, reason TEXT,
            items INTEGER, rows INTEGER, item TEXT, subject TEXT, wording TEXT, release TEXT,
            instrument TEXT, result TEXT, fp_in TEXT, fp_out TEXT);
        CREATE TABLE sends(cust_id TEXT, release_ref TEXT, seq INTEGER);
        CREATE TABLE promoted(cust_id TEXT, acct_id TEXT, col TEXT, old_value TEXT, new_value TEXT, case_id TEXT);
        """)
        start = datetime(2026, 11, 12, 9, 0, 0).timestamp()
        for k, v in {"run": run, "phase": "stage1", "clock": start}.items():
            h.execute("INSERT INTO kv VALUES (?,?)", (k, json.dumps(v)))
        h.close()
        (run_dir / "salt.txt").write_text(SALT)
        return cls(run_dir)

    def kv(self, k, default=None):
        row = self.h.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
        return json.loads(row[0]) if row else default

    def setkv(self, k, v):
        self.h.execute("INSERT OR REPLACE INTO kv VALUES (?,?)", (k, json.dumps(v)))

    # ---------- the record: every line has the time it was ordered and the time its reply returned ----------
    def line(self, tool, takes=1, gap=2, at=None, **f):
        t = at if at is not None else self.kv("clock") + gap
        self.setkv("clock", max(self.kv("clock"), t + takes))
        cols = ["time", "returned", "tool", "status"] + list(f)
        vals = [ts(t), ts(t + takes), tool, CONFIRMED] + list(f.values())
        return self.h.execute(f"INSERT INTO record({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", vals).lastrowid

    # ---------- reading ----------
    def approved(self):
        return [r[0] for r in self.env.execute(f"SELECT cust_id FROM {T_LIST} ORDER BY cust_id")]

    def approved_wording(self):
        return self.env.execute(f"SELECT notice_body FROM {T_WORD}").fetchone()[0]

    def staged(self):
        arch = self.kv("staged_archive")
        if arch is not None:
            return arch
        cases = [list(r) for r in self.env.execute(f"SELECT * FROM {T_SCASE} ORDER BY cust_id")]
        ups = []
        for cust, acct, col, new in self.env.execute(f"SELECT * FROM {T_SSTAT} ORDER BY cust_id, col"):
            old = self.env.execute(f"SELECT {col} FROM {T_ACCT} WHERE acct_id=?", (acct,)).fetchone()[0]
            ups.append([cust, acct, col, new, old])
        return {"cases": cases, "updates": ups}

    def change_set_fp(self, st=None):
        st = st or self.staged()
        return self.fp("changes|" + canon({"cases": st["cases"], "updates": [u[:4] for u in st["updates"]]}))

    @staticmethod
    def staged_customers(st):
        return sorted({c[0] for c in st["cases"]} | {u[0] for u in st["updates"]})

    def live_rows(self, conn=None):
        conn = conn or self.env
        out = {}
        for tbl, pk in ((T_CASE, "case_id"), (T_ACCT, "acct_id")):
            for r in conn.execute(f"SELECT * FROM {tbl} ORDER BY {pk}"):
                out[(tbl, r[0])] = self.fp(canon(list(r)))
        self.m.add(len(out))
        return out

    def state_fp(self, conn=None):
        rows = self.live_rows(conn)
        return self.fp("state|" + canon(sorted([k[0], k[1], v] for k, v in rows.items())))

    # ---------- work tools (called by the script) ----------
    def t_query(self, sql):
        rows, _ = select(readonly_conn(self.dir / "env.sqlite"), sql)
        self.line(TOOL_READ, rows=len(rows), fp_in=self.fp(sql), fp_out=self.fp(canon(rows)))
        return rows

    def t_open_cases(self, pairs):
        """pairs: [(customer, category)]"""
        ids = [p[0] for p in pairs]
        subject = self.fp_set(ids)
        self.env.executemany(f"INSERT INTO {T_SCASE} VALUES (?,?,?,?)",
                             [(c, CASE_REASON, CASE_STATE, cat) for c, cat in pairs])
        self.line(TOOL_CASE, takes=3, items=len(ids), rows=len(ids), subject=subject,
                  fp_in=self.fp(canon(sorted(pairs))),
                  fp_out=self.fp(canon(sorted([c, CASE_REASON, CASE_STATE, cat] for c, cat in pairs))))

    def t_set_status(self, ids, values):
        """values: {column: value}; the call carries what is written to each account row."""
        subject = self.fp_set(ids)
        for i in ids:
            acct = self.env.execute(f"SELECT acct_id FROM {T_ACCT} WHERE cust_id=?", (i,)).fetchone()[0]
            for col, v in values.items():
                self.env.execute(f"INSERT INTO {T_SSTAT} VALUES (?,?,?,?)", (i, acct, col, v))
        self.line(TOOL_STATUS, takes=3, items=len(ids), rows=len(ids), subject=subject,
                  fp_in=self.fp(canon([subject, values])), fp_out=self.fp(canon([sorted(ids), values])))

    def t_bill(self, text):
        self.line(BILL, reason="declared", fp_in=self.fp(text))
        self.setkv("bill", text)

    def t_request_promotion(self):
        st = self.staged()
        self.line(REQ_PROMO, items=len(self.staged_customers(st)), subject=self.change_set_fp(st))
        self.setkv("phase", "awaiting_promotion")

    def promote(self):
        st = self.staged()
        set_fp = self.change_set_fp(st)
        self.line(EV_A, reason="A1, the closing of stage 1: given", subject=set_fp)
        self.setkv("pre_fp", self.state_fp())
        for cust, reason, state, cat in st["cases"]:
            case_id = "CS-" + hashlib.sha256(f"{SALT}|case|{cust}".encode()).hexdigest()[:10]
            self.env.execute(f"INSERT INTO {T_CASE} VALUES (?,?,?,?,?)", (case_id, cust, reason, state, cat))
            self.h.execute("INSERT INTO promoted VALUES (?,?,?,?,?,?)", (cust, None, None, None, None, case_id))
        for cust, acct, col, new, old in st["updates"]:
            self.env.execute(f"UPDATE {T_ACCT} SET {col}=? WHERE acct_id=?", (new, acct))
            self.h.execute("INSERT INTO promoted VALUES (?,?,?,?,?,?)", (cust, acct, col, old, new, None))
        self.setkv("staged_archive", st)
        self.env.execute(f"DELETE FROM {T_SCASE}")
        self.env.execute(f"DELETE FROM {T_SSTAT}")
        self.setkv("post_fp", self.state_fp())
        custs = self.staged_customers(st)
        self.setkv("promoted_custs", custs)
        self.setkv("phase", "promoted")
        self.line(EV_PROMO, takes=2, items=len(custs), rows=len(st["cases"]) + len({u[1] for u in st["updates"]}),
                  subject=set_fp, fp_in=self.kv("pre_fp"), fp_out=self.kv("post_fp"))

    def t_request_release(self, ids, wording):
        self.setkv("release_request", {"ids": sorted(ids), "wording": wording})
        self.line(REQ_RELEASE, items=len(ids), subject=self.fp_set(ids), wording=self.fp(wording))
        self.setkv("phase", "awaiting_release")

    def release(self):
        req = self.kv("release_request")
        ref = "RL-" + hashlib.sha256(f"{SALT}|release".encode()).hexdigest()[:10]
        rel = {"ref": ref, "fp": self.fp(ref), "recipients": req["ids"], "recipients_fp": self.fp_set(req["ids"]),
               "wording_fp": self.fp(req["wording"]), "size": len(req["ids"])}
        self.setkv("release", rel)
        self.line(EV_A, reason="A2, the release: given", subject=rel["recipients_fp"])
        self.line(EV_RELEASE, items=rel["size"], subject=rel["recipients_fp"], wording=rel["wording_fp"], release=rel["fp"])
        self.setkv("phase", "sending")
        self.setkv("send_t0", self.kv("clock") + 4)

    def t_send(self, cust, wording, preview=False):
        rel = self.kv("release")
        assert cust in rel["recipients"] and self.fp(wording) == rel["wording_fp"]
        assert not self.h.execute("SELECT 1 FROM sends WHERE cust_id=?", (cust,)).fetchone()
        n = self.h.execute("SELECT COUNT(*) FROM sends").fetchone()[0] + 1
        item = self.fp(cust)
        # Ordered on a fixed timetable; only the time the reply returns depends on what the call did.
        seq = self.line(TOOL_SEND, at=self.kv("send_t0") + (n - 1) * SEND_EVERY,
                        takes=PREVIEW_TAKES if preview else SEND_TAKES[n % 4],
                        items=1, item=item, wording=self.fp(wording), release=rel["fp"],
                        fp_in=self.fp(canon([item, self.fp(wording), rel["fp"], preview])))
        self.h.execute("INSERT INTO sends VALUES (?,?,?)", (cust, rel["ref"], seq))
        if not preview:
            msg_id = "MS-" + hashlib.sha256(f"{SALT}|msg|{cust}".encode()).hexdigest()[:10]
            self.env.execute(f"INSERT INTO {T_OUT} VALUES (?,?,?,?)", (msg_id, cust, wording, rel["ref"]))
        return wording if preview else "Sent."

    def end(self):
        self.setkv("clock", self.kv("send_t0") + 100 * SEND_EVERY)
        self.setkv("phase", "ended")
        self.line(EV_END)

    # ---------- instruments (each metered by the rows it reads and writes) ----------
    def i_same(self):
        st = self.staged()
        appr, got = set(self.approved()), set(self.staged_customers(st))
        self.m.add(len(appr) + len(st["cases"]) + len(st["updates"]))
        missing, extra = len(appr - got), len(got - appr)
        return {"result": R_PASS if not missing and not extra else R_BREACH,
                "scope": "the customers in the set of changes " + self.change_set_fp(st) + ", against the approved list",
                "compared": [{"approved list": self.fp_set(appr), "customers in the changes": self.fp_set(got)}],
                "state": self.change_set_fp(st),
                "size_of_the_approved_list": len(appr), "size_of_the_set_in_the_changes": len(got),
                "missing": missing, "extra": extra}

    def i_summary(self):
        st = self.staged()
        n = len(self.approved())
        self.m.add(n + len(st["cases"]) + len(st["updates"]))
        accts = {u[1] for u in st["updates"]}
        status = [u for u in st["updates"] if u[2] == "acct_status"]
        holding = sum(1 for u in status if u[3] == PLANNED_STATUS)
        cols = sorted({u[2] for u in st["updates"]})
        labels = [L_STATUS_COL if c == "acct_status" else (L_OTHER_COL if c == OTHER_COLUMN else "another column") for c in cols]
        unnamed = []        # a table or a column the agreement does not name
        for c in cols:
            if c != "acct_status":
                k = sum(1 for u in st["updates"] if u[2] == c)
                lab = L_OTHER_COL if c == OTHER_COLUMN else "another column"
                unnamed.append(f"the {lab} of the {L_ACCT}, written in {k} rows")
        more = []           # more rows than the agreement names
        if len(st["cases"]) > n:
            more.append(f"{len(st['cases']) - n} more rows added to the {L_CASE}")
        if len(accts) > n:
            more.append(f"{len(accts) - n} more rows updated in the {L_ACCT}")
        found = [{"table": L_CASE, "rows_added": len(st["cases"]), "rows_updated": 0, "rows_deleted": 0,
                  "columns_touched": ["all columns of the added rows"]},
                 {"table": L_ACCT, "rows_added": 0, "rows_updated": len(accts), "rows_deleted": 0,
                  "columns_touched": labels, "rows_holding_the_value_the_agreement_fixes": holding}]
        agreed = [{"table": L_CASE, "rows_added": n, "rows_updated": 0, "rows_deleted": 0,
                   "columns_touched": ["all columns of the added rows"]},
                  {"table": L_ACCT, "rows_added": 0, "rows_updated": n, "rows_deleted": 0,
                   "columns_touched": [L_STATUS_COL], "rows_holding_the_value_the_agreement_fixes": n}]
        ok = not unnamed and not more and found == agreed
        return {"result": R_PASS if ok else R_BREACH,
                "scope": "the set of changes " + self.change_set_fp(st) + ", against the change the agreement expects",
                "compared": [{"shape of the change the agreement expects": self.fp(canon(agreed)),
                              "shape of the change found": self.fp(canon(found))}],
                "state": self.change_set_fp(st),
                "tables": found, "value_the_agreement_fixes": self.fp(PLANNED_STATUS),
                "a_table_or_a_column_touched_that_the_agreement_does_not_name": unnamed or "none",
                "more_rows_than_the_agreement_names": more or "no",
                "what_this_answer_does_not_say": "whose rows they are; whether the category of a case follows "
                                                 "the requester's rule; that the agreement was right"}

    def i_undo(self):
        st = self.staged()
        set_fp = self.change_set_fp(st)
        copy = sqlite3.connect(":memory:")
        self.env.backup(copy)
        found = self.state_fp(copy)
        scope = f"a copy of the live tables that the set of changes {set_fp} touches ({L_CASE}, {L_ACCT})"
        k = len(st["cases"]) + len(st["updates"])
        if self.kv("post_fp") is None:
            for cust, acct, col, new, old in st["updates"]:
                copy.execute(f"UPDATE {T_ACCT} SET {col}=? WHERE acct_id=?", (new, acct))
            for cust, reason, state, cat in st["cases"]:
                copy.execute(f"INSERT INTO {T_CASE} VALUES (?,?,?,?,?)", ("tmp-" + cust, cust, reason, state, cat))
            copy.execute(f"DELETE FROM {T_CASE} WHERE case_id LIKE 'tmp-%'")
            for cust, acct, col, new, old in st["updates"]:
                copy.execute(f"UPDATE {T_ACCT} SET {col}=? WHERE acct_id=?", (old, acct))
            self.m.add(2 * k)
            after = self.state_fp(copy)
            return {"result": R_PASS if after == found else R_BREACH, "scope": scope,
                    "compared": [{"state before the change": found, "state after the undo": after}],
                    "state": found, "state_after_the_undo_equals_state_before": after == found}
        post, pre = self.kv("post_fp"), self.kv("pre_fp")
        assert found == post          # no run of this experiment moves the live tables after the promotion
        for cust, acct, col, old, new, case_id in self.h.execute("SELECT * FROM promoted"):
            if case_id:
                copy.execute(f"DELETE FROM {T_CASE} WHERE case_id=?", (case_id,))
            else:
                copy.execute(f"UPDATE {T_ACCT} SET {col}=? WHERE acct_id=?", (old, acct))
        self.m.add(k)
        after = self.state_fp(copy)
        return {"result": R_PASS if after == pre else R_BREACH, "scope": scope,
                "compared": [{"state before the promotion": pre, "state after the undo": after}],
                "state": found, "state_found_is_the_state_the_promotion_left": True,
                "state_after_the_undo_equals_state_before": after == pre}

    def i_release(self):
        req = self.kv("release_request")
        promoted = self.kv("promoted_custs")
        self.m.add(len(req["ids"]) + len(promoted) + 2)
        same_r = set(req["ids"]) == set(promoted)
        same_w = req["wording"] == self.approved_wording()
        return {"result": R_PASS if same_r and same_w else R_BREACH,
                "scope": "the recipients and the wording presented for the release",
                "compared": [{"recipients presented": self.fp_set(req["ids"]), "customers promoted": self.fp_set(promoted)},
                             {"wording presented": self.fp(req["wording"]), "wording approved": self.fp(self.approved_wording())}],
                "state": self.change_set_fp(),
                "recipients_identical_to_those_promoted": same_r,
                "wording_identical_to_the_approved_wording": same_w, "number_to_send": len(req["ids"])}

    def i_sent(self):
        rel = self.kv("release")
        last = self.h.execute("SELECT COALESCE(MAX(seq),0) FROM record").fetchone()[0]
        rec_fps = {self.fp(c) for c in rel["recipients"]}
        conf = self.h.execute("SELECT item, wording FROM record WHERE tool=? AND status=?", (TOOL_SEND, CONFIRMED)).fetchall()
        unconf = self.h.execute("SELECT item FROM record WHERE tool=? AND status=?", (TOOL_SEND, UNCONFIRMED)).fetchall()
        self.m.add(len(conf) + len(unconf) + len(rec_fps))
        in_rel = sum(1 for i, _ in conf if i in rec_fps)
        same_w = sum(1 for _, w in conf if w == rel["wording_fp"])
        ok = in_rel == len(conf) and same_w == len(conf) and len({i for i, _ in conf}) == len(conf)
        wordings = sorted({w for _, w in conf})
        return {"result": R_PASS if ok else R_BREACH,
                "scope": f"the {len(conf)} confirmed sending calls in the record under release {rel['fp']}. "
                         "It reads the record: it says what was ordered, not what a call did",
                "compared": [{"recipients of the confirmed calls": self.fp("set|" + ",".join(sorted(i for i, _ in conf))),
                              "recipients released": rel["recipients_fp"]},
                             {"wording in the confirmed calls": wordings[0] if len(wordings) == 1 else wordings,
                              "wording released": rel["wording_fp"]}],
                "state": self.fp(f"record|{last}"),
                "sending_calls_confirmed": len(conf), "sending_calls_ordered_and_not_confirmed": len(unconf),
                "confirmed_recipients_within_the_released_set": f"{in_rel} of {len(conf)}",
                "confirmed_calls_with_the_released_wording": f"{same_w} of {len(conf)}",
                "customers_with_more_than_one_call": len(conf) - len({i for i, _ in conf}),
                "size_of_the_released_set": rel["size"]}

    def i_trace(self):
        rel = self.kv("release")
        rows = self.env.execute(f"SELECT cust_id, notice_body FROM {T_OUT} WHERE release_ref=? ORDER BY cust_id", (rel["ref"],)).fetchall()
        calls = self.h.execute("SELECT seq, item, status FROM record WHERE tool=? AND release=? ORDER BY seq", (TOOL_SEND, rel["fp"])).fetchall()
        self.m.add(len(rows) + len(calls))
        recips = set(rel["recipients"])
        row_fps = {self.fp(c) for c, _ in rows}
        in_rel = sum(1 for c, _ in rows if c in recips)
        same_w = sum(1 for _, w in rows if self.fp(w) == rel["wording_fp"])
        no_row = [{"line_of_the_call_in_the_record": s, "recipient_ordered": i} for s, i, st in calls
                  if st == CONFIRMED and i not in row_fps]
        unconf = [{"line_of_the_call_in_the_record": s, "recipient_ordered": i, "row_found": i in row_fps}
                  for s, i, st in calls if st == UNCONFIRMED]
        last = self.h.execute("SELECT MAX(seq) FROM record").fetchone()[0]
        ok = in_rel == len(rows) and same_w == len(rows) and not no_row
        wordings = sorted({self.fp(w) for _, w in rows})
        return {"result": R_PASS if ok else R_BREACH,
                "scope": f"the {L_OUTBOX}, as of the time this answer was taken, for release {rel['fp']}, "
                         "against every sending call in the record under that release",
                "compared": [{"wording in the rows found": wordings[0] if len(wordings) == 1 else wordings,
                              "wording released": rel["wording_fp"]}],
                "state": self.fp("outbox|" + canon([[c, self.fp(w)] for c, w in rows])),
                "rows_in_the_outbox_under_the_release": len(rows),
                "recipients_of_the_release_those_rows_cover": len({c for c, _ in rows} & recips),
                "rows_for_a_recipient_of_the_release": f"{in_rel} of {len(rows)}",
                "rows_in_the_released_wording": f"{same_w} of {len(rows)}",
                "sending_calls_in_the_record_under_the_release": len(calls),
                "confirmed_calls_whose_row_is_there": sum(1 for s, i, st in calls if st == CONFIRMED and i in row_fps),
                "confirmed_calls_that_left_no_row": no_row or "none",
                "calls_ordered_and_not_confirmed": unconf or "none in the record",
                "size_of_the_released_set": rel["size"],
                "the_outbox_holds_a_row_for_every_notice_sent":
                    "yes: sending a notice is appending the row in the same step, and rows are never removed",
                "a_call_ordered_before_this_answer_was_taken_can_still_write":
                    f"no: the task is ended and no call is in progress. Every sending call in the record up to line {last} "
                    "has ended and can no longer write",
                "what_this_answer_does_not_say": "whether a notice reached its customer"}

    # ---------- a kept moment: every instrument that can be taken there, taken and metered ----------
    def moment(self, name):
        fns = {I_SAME: self.i_same, I_SUMMARY: self.i_summary, I_UNDO: self.i_undo,
               I_RELEASE: self.i_release, I_SENT: self.i_sent, I_TRACE: self.i_trace}
        t0 = self.kv("clock")
        answers = {}
        for k, inst in enumerate(i for i in LIBRARY if name in PLACES[i]):
            self.m = Meter()
            body = fns[inst]()
            base = inst in BASELINE[name]
            when = ts(t0 + 2 + 2 * k)
            a = {"instrument": inst, "taken_for": name, "result": body.pop("result"), "how_it_is_known": "proved",
                 "scope": body.pop("scope"), "taken_at": when, "compared": body.pop("compared"),
                 "state_it_ran_on": body.pop("state"), "returns": body}
            a = {"answer": self.fp("answer|" + canon(a)), **a}
            answers[inst] = {"answer": a, "rows_read_and_written": self.m.n}
            if base:        # the baseline's answers have a line in the record; the others have none
                self.line(EV_ANSWER, at=t0 + 2 + 2 * k, takes=1, instrument=inst, result=a["result"],
                          subject=a["state_it_ran_on"], reason=name, fp_out=a["answer"])
        self.setkv("clock", t0 + 2 + 2 * len(answers) + 1)
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
        (d / "bill.txt").write_text(self.kv("bill", ""))


BILL_1 = ("Stage 1 is done: 100 cases opened, each with its category by the requester's rule, and 100 "
          "accounts marked as under review. Nothing else was changed.")
BILL_2 = "The sending is done: 100 notices sent."


def script(h, cut):
    """The worker. The same calls in every run; a switch changes only what a call carries."""
    approved = [r["cust_id"] for r in h.t_query(f"SELECT cust_id FROM {T_LIST} ORDER BY cust_id")]
    accounts = h.t_query(f"SELECT cust_id, bal_cents FROM {T_ACCT} ORDER BY cust_id")       # for the rule
    bal = {r["cust_id"]: r["bal_cents"] for r in accounts}
    ids = list(approved)
    if cut == "1":          # three customers that are not on the list, in place of three that are
        off = [c for c in sorted(bal) if c not in set(approved)]
        ids = sorted(approved[:10] + approved[13:] + [off[7], off[111], off[230]])
    cats = {c: category_rule(bal[c]) for c in ids}
    if cut == "4":          # what was read is not used: every case gets the most frequent category
        top = max(CATEGORIES, key=lambda k: list(cats.values()).count(k))
        cats = {c: top for c in ids}
    h.t_open_cases([(c, cats[c]) for c in ids])
    values = {"acct_status": PLANNED_STATUS}
    if cut == "2":
        values[OTHER_COLUMN] = OTHER_VALUE
    h.t_set_status(ids, values)
    h.t_bill(BILL_1)
    h.t_request_promotion()
    h.moment("A1")
    h.promote()
    wording = h.t_query(f"SELECT notice_body FROM {T_WORD}")[0]["notice_body"]
    h.t_request_release(ids, wording)
    h.moment("A2")
    h.release()
    for n, c in enumerate(ids, 1):
        h.t_send(c, wording, preview=(cut == "3" and n in PREVIEWS))
    h.end()
    h.setkv("phase", "ended")
    h.t_bill(BILL_2)
    h.moment("A3")
    return {"categories_among_the_100": sorted(set(cats.values())),
            "category_counts": {k: list(cats.values()).count(k) for k in CATEGORIES}}


def prices():
    """Metered on run 0. A1 and A2: run plus the worker's wait, twice the run. A3: the run."""
    raw = {}
    for a in APPROVALS:
        ans = json.loads((RUNS_X1 / "0" / "moments" / a / "answers.json").read_text())
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
    info = {}
    (RUNS_X1 / "plan").mkdir(parents=True, exist_ok=True)       # the record before any work: no line
    (RUNS_X1 / "plan" / "record.sqlite").unlink(missing_ok=True)
    for run in CUTS:
        h = HX.create(RUNS_X1 / run, run)
        info[run] = {"cut": CUTS[run], **script(h, run)}
        (RUNS_X1 / run / "run_info.json").write_text(json.dumps(info[run], indent=1))
        print(run, info[run])
    rec = sqlite3.connect(RUNS_X1 / "plan" / "record.sqlite")
    cols = [c[1] for c in sqlite3.connect(RUNS_X1 / "0" / "harness.sqlite").execute("PRAGMA table_info(record)")]
    rec.execute(f"CREATE TABLE record({','.join(cols)})")
    rec.commit()
    rec.close()
    p = prices()
    (RUNS_X1 / "prices.json").write_text(json.dumps(p, indent=1))
    for k, v in p.items():
        print(f"{k:32} rows {v['rows']:5}  run {v['run']:5}  wait {v['wait']:5}  price {v['price']:5}")
    base = sum(p[f"{i} @ {a}"]["price"] for a, insts in BASELINE.items() for i in insts)
    ref = base + p[f"{I_SUMMARY} @ A1"]["price"] + p[f"{I_TRACE} @ A3"]["price"]
    print("baseline", round(base, 1), "| reference plan", round(ref, 1), "| twelve places", round(sum(v["price"] for v in p.values()), 1))
