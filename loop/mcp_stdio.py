"""A minimal MCP server over stdio (newline-delimited JSON-RPC). Tools only."""
import json
import sys


def serve(name, tools):
    """tools: {tool_name: (description, input_schema, fn(args) -> (text, is_error))}"""
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        msg = json.loads(raw)
        mid, method = msg.get("id"), msg.get("method")
        if mid is None:
            continue                                  # a notification
        if method == "initialize":
            result = {"protocolVersion": msg["params"].get("protocolVersion", "2024-11-05"),
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": name, "version": "1"}}
        elif method == "tools/list":
            result = {"tools": [{"name": n, "description": d, "inputSchema": s}
                                for n, (d, s, _) in tools.items()]}
        elif method == "tools/call":
            p = msg["params"]
            try:
                text, err = tools[p["name"]][2](p.get("arguments") or {})
            except Exception as e:                    # never let the server die on a call
                text, err = f"Tool error: {type(e).__name__}: {e}", True
            result = {"content": [{"type": "text", "text": text}], "isError": bool(err)}
        elif method == "ping":
            result = {}
        else:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid,
                                         "error": {"code": -32601, "message": "unknown method"}}) + "\n")
            sys.stdout.flush()
            continue
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "result": result}) + "\n")
        sys.stdout.flush()
