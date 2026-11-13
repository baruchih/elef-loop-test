"""The reviewer's tool server. Usage: reviewer_server.py <moment_dir> <blind|sighted> <log_file> <salt_file>"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from loop import reviewer_tools as rt  # noqa: E402
from loop.mcp_stdio import serve  # noqa: E402

moment_dir, arm, log_file, salt_file = sys.argv[1:5]


def logged(name, fn):
    def wrapped(args):
        text, err = fn(args)
        with open(log_file, "a") as f:
            f.write(json.dumps({"moment": Path(moment_dir).name, "tool": name, "args": args,
                                "error": err, "reply": text}) + "\n")
        return text, err
    return wrapped


tools = {"ask_record": (rt.RECORD_DESC, rt.RECORD_SCHEMA,
                        logged("ask_record", lambda a: rt.ask_record(moment_dir, a)))}
if arm == "sighted":
    salt = Path(salt_file).read_text().strip()
    tools["read_database"] = (rt.DB_DESC, rt.DB_SCHEMA,
                              logged("read_database", lambda a: rt.read_database(moment_dir, salt, a)))
serve("review", tools)
