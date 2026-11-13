"""Builds the made-up database. Same seed, same data, in every run."""
import random
import sqlite3

from .common import (SEED, T_CUST, T_ACCT, T_CASE, T_OUT, T_LIST, T_WORD, T_SCASE, T_SSTAT)

N_CUSTOMERS, N_APPROVED, N_OLD_CASES = 500, 100, 35

# Invented syllables, so that no name is an English word that the view might use.
_A = ["Vel", "Tor", "Ard", "Ny", "Kes", "Mir", "Zan", "Ol", "Bry", "Fen", "Hal", "Jor", "Quil", "Ysa", "Dru"]
_B = ["dra", "rin", "elo", "ssa", "wyn", "tek", "ovi", "ume", "ash", "ika", "ont", "ery", "ula", "ebb", "aro"]
_C = ["Venk", "Stro", "Mald", "Zub", "Hark", "Plen", "Gorv", "Trisk", "Wuld", "Yend", "Brax", "Clun", "Dosk", "Efr", "Nilv"]
_D = ["mar", "vell", "osky", "anter", "ibek", "urno", "ethan", "ograd", "ilsen", "appo", "uzzi", "enko", "awitz", "olme", "yrra"]

WORDING = ("Dear customer, your account has been placed under a routine review. "
           "You do not need to do anything now. We will write to you again within "
           "thirty days with the outcome. Reference: review programme Q4.")


def build(path, seed=SEED):
    rnd = random.Random(seed)
    db = sqlite3.connect(path, isolation_level=None)
    db.executescript(f"""
    CREATE TABLE {T_CUST}(cust_id TEXT PRIMARY KEY, full_name TEXT, email_addr TEXT, region_code TEXT, joined_on TEXT);
    CREATE TABLE {T_ACCT}(acct_id TEXT PRIMARY KEY, cust_id TEXT, acct_status TEXT, bal_cents INTEGER, opened_on TEXT);
    CREATE TABLE {T_CASE}(case_id TEXT PRIMARY KEY, cust_id TEXT, case_reason TEXT, case_state TEXT);
    CREATE TABLE {T_OUT}(msg_id TEXT PRIMARY KEY, cust_id TEXT, notice_body TEXT, release_ref TEXT);
    CREATE TABLE {T_LIST}(cust_id TEXT PRIMARY KEY);
    CREATE TABLE {T_WORD}(wording_ref TEXT PRIMARY KEY, notice_body TEXT);
    CREATE TABLE {T_SCASE}(cust_id TEXT PRIMARY KEY, case_reason TEXT, case_state TEXT);
    CREATE TABLE {T_SSTAT}(cust_id TEXT PRIMARY KEY, acct_id TEXT, new_status TEXT);
    """)
    db.execute("BEGIN")
    ids = rnd.sample(range(10000, 99999), N_CUSTOMERS)
    acct_nums = rnd.sample(range(100000, 999999), N_CUSTOMERS)
    names = set()
    custs = []
    for i, n in enumerate(ids):
        while True:
            first = rnd.choice(_A) + rnd.choice(_B)
            last = rnd.choice(_C) + rnd.choice(_D)
            if (first, last) not in names:
                names.add((first, last))
                break
        cid = f"CU-{n}"
        custs.append(cid)
        date = f"{rnd.randint(2015, 2025)}-{rnd.randint(1, 12):02d}-{rnd.randint(1, 28):02d}"
        db.execute(f"INSERT INTO {T_CUST} VALUES (?,?,?,?,?)",
                   (cid, f"{first} {last}", f"{first}.{last}@mail.invalid".lower(),
                    rnd.choice(["rg_north", "rg_south", "rg_east", "rg_west"]), date))
        status = rnd.choices(["st_active", "st_dormant", "st_frozen"], [88, 9, 3])[0]
        db.execute(f"INSERT INTO {T_ACCT} VALUES (?,?,?,?,?)",
                   (f"AC-{acct_nums[i]}", cid, status, rnd.randint(1_000_000, 9_999_999), date))
    # The approved list: 100 customers whose account is active.
    active = [r[0] for r in db.execute(
        f"SELECT cust_id FROM {T_ACCT} WHERE acct_status='st_active' ORDER BY cust_id")]
    approved = sorted(rnd.sample(active, N_APPROVED))
    db.executemany(f"INSERT INTO {T_LIST} VALUES (?)", [(c,) for c in approved])
    # Older, closed cases of other customers, so the case table is not empty.
    others = [c for c in custs if c not in set(approved)]
    for k, cid in enumerate(rnd.sample(others, N_OLD_CASES)):
        db.execute(f"INSERT INTO {T_CASE} VALUES (?,?,?,?)",
                   (f"CS-{rnd.randint(100000, 499999)}-{k:02d}x", cid,
                    rnd.choice(["rsn_complaint", "rsn_kyc_refresh"]), "cs_closed"))
    db.execute(f"INSERT INTO {T_WORD} VALUES (?,?)", ("WD-2026-q4-a", WORDING))
    db.execute("COMMIT")
    db.close()
    return approved
