"""The reviewer's tools over a frozen view: questions to the record, and (sighted arm only) the database."""
import json
import sqlite3

from .common import readonly_conn, select

FIELDS = ["seq", "time", "tool", "status", "reason", "items", "rows", "item", "subject",
          "wording", "release", "instrument", "result", "fp_in", "fp_out"]

RECORD_DESC = (
    "Put one question to the record of calls. The record has one line for each call and for each "
    "act of the requester or the harness. Fields of a line: " + ", ".join(FIELDS) + ". "
    "Give `where` to filter (field: value, or field: [values] for any of them, or field: null for "
    "lines where the field is empty), `seq_from` / `seq_to` to bound the line numbers, `count_by` "
    "(a list of fields) for counts by group, `count_distinct` (a field) for the number of different "
    "values, and `show_lines`: true to see the lines themselves (`limit` up to 200, `offset`). "
    "The number of matching lines is always returned.")

RECORD_SCHEMA = {
    "type": "object",
    "properties": {
        "where": {"type": "object", "description": "field -> value, list of values, or null"},
        "seq_from": {"type": "integer"}, "seq_to": {"type": "integer"},
        "count_by": {"type": "array", "items": {"type": "string"}},
        "count_distinct": {"type": "string"},
        "show_lines": {"type": "boolean"},
        "limit": {"type": "integer"}, "offset": {"type": "integer"},
    },
}

DB_DESC = ("Run one SELECT statement on the database (SQLite). The functions fp(value) and "
           "fp_set(column) are available. At most 300 rows come back.")
DB_SCHEMA = {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}


def ask_record(moment_dir, a):
    conn = sqlite3.connect(f"file:{moment_dir}/record.sqlite?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conds, params = [], []
    for f, v in (a.get("where") or {}).items():
        if f not in FIELDS:
            return f"There is no field '{f}'. The fields are: {', '.join(FIELDS)}.", True
        if v is None:
            conds.append(f"{f} IS NULL")
        elif isinstance(v, list):
            if not v:
                return f"The list for '{f}' is empty.", True
            conds.append(f"{f} IN ({','.join('?' * len(v))})")
            params += v
        else:
            conds.append(f"{f} = ?")
            params.append(v)
    if a.get("seq_from") is not None:
        conds.append("seq >= ?")
        params.append(a["seq_from"])
    if a.get("seq_to") is not None:
        conds.append("seq <= ?")
        params.append(a["seq_to"])
    w = (" WHERE " + " AND ".join(conds)) if conds else ""
    out = {"matching_lines": conn.execute(f"SELECT COUNT(*) FROM record{w}", params).fetchone()[0]}
    by = a.get("count_by") or []
    if isinstance(by, str):
        by = [by]
    if by:
        bad = [f for f in by if f not in FIELDS]
        if bad:
            return f"There is no field '{bad[0]}'. The fields are: {', '.join(FIELDS)}.", True
        cols = ",".join(by)
        out["counts"] = [dict(r) for r in conn.execute(
            f"SELECT {cols}, COUNT(*) AS lines FROM record{w} GROUP BY {cols} ORDER BY MIN(seq)", params)]
    d = a.get("count_distinct")
    if d:
        if d not in FIELDS:
            return f"There is no field '{d}'. The fields are: {', '.join(FIELDS)}.", True
        out["different_values_of_" + d] = conn.execute(
            f"SELECT COUNT(DISTINCT {d}) FROM record{w}", params).fetchone()[0]
    if a.get("show_lines"):
        limit = max(1, min(int(a.get("limit") or 50), 200))
        offset = max(0, int(a.get("offset") or 0))
        rows = conn.execute(f"SELECT * FROM record{w} ORDER BY seq LIMIT ? OFFSET ?",
                            params + [limit, offset]).fetchall()
        out["lines"] = [{k: r[k] for k in r.keys() if r[k] is not None} for r in rows]
        if out["matching_lines"] > offset + len(rows):
            out["more_lines_not_shown"] = out["matching_lines"] - offset - len(rows)
    return json.dumps(out, ensure_ascii=False), False


def read_database(moment_dir, salt, a):
    try:
        rows, more = select(readonly_conn(f"{moment_dir}/env.sqlite", salt), a["sql"], cap=300)
    except sqlite3.Error as e:
        return f"The query was not accepted: {e}", True
    return json.dumps({"rows": rows, "more_rows_not_shown": more}, ensure_ascii=False), False
