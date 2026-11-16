"""The reviewer's tool server for experiment X8: the record tool, with ELEF's log of what it returned.
Usage: reviewer_server_x8.py <run_dir> <moment> <log_file> <took: 0|1> <log tool: 0|1>"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from loop import log_x8 as lg  # noqa: E402
from loop.mcp_stdio import serve  # noqa: E402

run_dir, moment, log_file = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
took, log_tool = sys.argv[4] == "1", sys.argv[5] == "1"
mdir = run_dir / "moments" / moment if moment != "plan" else run_dir.parent / "plan"
db = mdir / ("record_took.sqlite" if took else "record.sqlite")


def write(tool, args, text, err):
    with open(log_file, "a") as f:
        f.write(json.dumps({"moment": moment, "tool": tool, "args": args, "error": err, "reply": text}) + "\n")


def ask(args):
    text, err = lg.ask_record(db, took, args)
    write("ask_record", args, text, err)
    return text, err


def stage():
    import sqlite3
    order = ["A1", "A2", "A3"]
    if moment not in order:
        return None
    last = lambda m: sqlite3.connect(run_dir / "moments" / m / "record.sqlite").execute("SELECT MAX(seq) FROM record").fetchone()[0]  # noqa: E731
    k = order.index(moment)
    return ((last(order[k - 1]) + 1) if k else 1, last(moment))


def ask_log(args):
    text = lg.holds_text(lg.holds(lg.entries(log_file), run_dir, took, stage()))
    write("ask_log", args, text, False)
    return text, False


if __name__ == "__main__":
    tools = {"ask_record": (lg.describe(took), lg.rt.RECORD_SCHEMA, ask)}
    if log_tool:
        tools["ask_log"] = (lg.LOG_DESC, lg.LOG_SCHEMA, ask_log)
    serve("review", tools)
