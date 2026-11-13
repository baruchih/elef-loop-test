"""Runs one turn of a headless agent session (claude -p) with one MCP server and no built-in tools."""
import json
import subprocess
import sys
import time
from pathlib import Path

from .common import MODEL, ROOT


def turn(prompt, system, server_script, server_args, allowed, cwd, session_id, first,
         timeout=3600, log=None, model=MODEL):
    cwd = Path(cwd)
    cwd.mkdir(parents=True, exist_ok=True)
    cfg = {"mcpServers": {"t": {"command": sys.executable,
                                "args": [str(ROOT / "loop" / server_script)] + [str(a) for a in server_args]}}}
    cmd = ["claude", "-p", "--model", model, "--output-format", "json",
           "--system-prompt", system,
           "--tools", "", "--strict-mcp-config", "--mcp-config", json.dumps(cfg),
           "--allowedTools", ",".join(f"mcp__t__{a}" for a in allowed),
           "--setting-sources", "", "--disable-slash-commands", "--permission-prompts", "none"]
    cmd += ["--session-id", session_id] if first else ["--resume", session_id]
    t0 = time.time()
    p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    wall = time.time() - t0
    try:
        out = json.loads(p.stdout)
    except json.JSONDecodeError:
        out = {"is_error": True, "result": "", "raw_stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:]}
    if isinstance(out, list):                         # some versions print the event list
        out = next((e for e in reversed(out) if e.get("type") == "result"), {"is_error": True, "result": ""})
    u = out.get("usage") or {}
    res = {"text": out.get("result", ""), "is_error": out.get("is_error", False), "wall_s": round(wall, 1),
           "turns": out.get("num_turns"), "cost_usd": out.get("total_cost_usd"),
           "tokens": {"input": u.get("input_tokens", 0), "output": u.get("output_tokens", 0),
                      "cache_read": u.get("cache_read_input_tokens", 0),
                      "cache_write": u.get("cache_creation_input_tokens", 0)},
           "models": sorted((out.get("modelUsage") or {}).keys()),
           "raw": out}
    if log:
        with open(log, "a") as f:
            f.write(json.dumps({"prompt": prompt, **res}) + "\n")
    return res
