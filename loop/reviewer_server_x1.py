"""The reviewer's tool server for experiment X1: the record tool of 1b, with the second time of a line.
Usage: reviewer_server_x1.py <moment_dir> <log_file>"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from loop import reviewer_tools as rt  # noqa: E402
from loop.mcp_stdio import serve  # noqa: E402

rt.FIELDS.insert(2, "returned")
DESC = rt.RECORD_DESC.replace(", ".join(f for f in rt.FIELDS if f != "returned"), ", ".join(rt.FIELDS)) + (
    " `time` is when the call was ordered and `returned` is when its reply returned.")
moment_dir, log_file = sys.argv[1:3]


def ask(args):
    text, err = rt.ask_record(moment_dir, args)
    with open(log_file, "a") as f:
        f.write(json.dumps({"moment": Path(moment_dir).name, "tool": "ask_record", "args": args,
                            "error": err, "reply": text}) + "\n")
    return text, err


if __name__ == "__main__":
    serve("review", {"ask_record": (DESC, rt.RECORD_SCHEMA, ask)})
