"""The worker's work tools, served to an agent session. Usage: worker_server.py <run_dir>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from loop.harness import Harness, Refused  # noqa: E402
from loop.mcp_stdio import serve  # noqa: E402

run_dir = sys.argv[1]


def call(fn):
    def wrapped(args):
        h = Harness(run_dir)
        try:
            return fn(h, args), False
        except Refused as e:
            return str(e), True
    return wrapped


IDS = {"type": "array", "items": {"type": "string"}, "description": "customer ids"}


def obj(props, req):
    return {"type": "object", "properties": props, "required": req}


serve("work", {
    "query": ("[read] Run one SELECT statement on the database.",
              obj({"sql": {"type": "string"}}, ["sql"]),
              call(lambda h, a: h.t_query(a["sql"]))),
    "open_cases": ("[staged write] Open a review case for each of the given customers. "
                   "Writes to the staging area, never to the live tables.",
                   obj({"customer_ids": IDS}, ["customer_ids"]),
                   call(lambda h, a: h.t_open_cases(a["customer_ids"]))),
    "set_account_status": ("[staged write] Set the status of the account of each of the given "
                           "customers. Writes to the staging area, never to the live tables.",
                           obj({"customer_ids": IDS, "status": {"type": "string"}},
                               ["customer_ids", "status"]),
                           call(lambda h, a: h.t_set_status(a["customer_ids"], a["status"]))),
    "discard_staged": ("[staged write] Empty the staging area, to start stage 1 again.",
                       obj({}, []), call(lambda h, a: h.t_discard())),
    "request_promotion": ("Ask the requester to promote the staged set. The harness takes the "
                          "three checks of stage 1 first.",
                          obj({}, []), call(lambda h, a: h.t_request_promotion())),
    "request_release": ("Ask the requester for the release of the sending: present the "
                        "recipients and the wording.",
                        obj({"customer_ids": IDS, "wording": {"type": "string"}},
                            ["customer_ids", "wording"]),
                        call(lambda h, a: h.t_request_release(a["customer_ids"], a["wording"]))),
    "send_notice": ("[cannot be undone] Send the notice to one customer. Appends one row to the outbox.",
                    obj({"customer_id": {"type": "string"}, "wording": {"type": "string"}},
                        ["customer_id", "wording"]),
                    call(lambda h, a: h.t_send(a["customer_id"], a["wording"]))),
})
