"""Interactive stdio MCP client: records real requests and server responses.

Start with the app's Python and --mcp-cli pointing to @playwright/mcp/cli.js.
Each stdin line: {"tool": "browser_navigate", "arguments": {...}, "record": "..."}.
Special tools: initialize, tools/list, restart_app, quit.
All browser interaction remains in the real Playwright MCP server.
"""

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcp-cli", required=True)
    parser.add_argument("--node", default="node")
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    server_log = (evidence / "server.stderr.txt").open("a")
    app_log = (evidence / "app.stdout-stderr.txt").open("a")
    app = None

    def start_app(path):
        nonlocal app
        if app:
            app.terminate()
            app.wait(timeout=10)
        app = subprocess.Popen([sys.executable, "-m", "uvicorn", "bublik.main:create_app",
                                "--factory", "--host", "127.0.0.1", "--port", "8003"],
                               cwd=path, env={**os.environ, "PYTHONPATH": str(path / "src")},
                               stdout=app_log, stderr=app_log)
        for _ in range(50):
            try:
                with urllib.request.urlopen("http://127.0.0.1:8003/health", timeout=1) as r:
                    if r.status == 200:
                        return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("App health did not become ready")

    start_app(args.app.resolve())
    command = [args.node, str(Path(args.mcp_cli).resolve()), "--headless", "--isolated",
               "--browser", "firefox", "--output-dir", str(evidence),
               "--allowed-origins", "http://127.0.0.1:8003"]
    server = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=server_log, text=True, bufsize=1, cwd=evidence.parent.parent)
    print("READY: app health 200; real Playwright MCP stdio started", flush=True)
    try:
        for line in sys.stdin:
            try:
                item = json.loads(line)
                name = item["tool"]
                if name == "quit":
                    break
                if name == "restart_app":
                    start_app(Path(item["app"]).resolve())
                    print("APP_RESTARTED: health 200", flush=True)
                    continue
                destination = evidence.parent.parent / item["record"]
                if destination.exists():
                    raise FileExistsError("Refusing to overwrite evidence")
                if name == "initialize":
                    method = name
                    params = {"protocolVersion": "2025-03-26", "capabilities": {},
                              "clientInfo": {"name": "BublikTestingAgent", "version": "1.0.0"}}
                elif name == "tools/list":
                    method, params = name, {}
                else:
                    method = "tools/call"
                    params = {"name": name, "arguments": item.get("arguments", {})}
                request = {"jsonrpc": "2.0", "id": time.time_ns() // 1_000_000, "method": method, "params": params}
                started = datetime.now(timezone.utc).isoformat()
                server.stdin.write(json.dumps(request) + "\n")
                server.stdin.flush()
                while True:
                    raw = server.stdout.readline()
                    if not raw:
                        raise RuntimeError("MCP server closed stdout")
                    response = json.loads(raw)
                    if response.get("id") == request["id"]:
                        break
                if name == "initialize":
                    server.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
                    server.stdin.flush()
                for block in response.get("result", {}).get("content", []):
                    if block.get("type") == "image" and "data" in block:
                        png = base64.b64decode(block.pop("data"))
                        block["png_sha256"] = hashlib.sha256(png).hexdigest()
                        block["data_omitted"] = "Screenshot file saved by real MCP tool"
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(json.dumps({"started_utc": started,
                    "finished_utc": datetime.now(timezone.utc).isoformat(),
                    "request": request, "response": response}, ensure_ascii=False, indent=2) + "\n")
                print(json.dumps(response, ensure_ascii=False, indent=2), flush=True)
            except Exception as error:
                print(f"CLIENT_ERROR: {type(error).__name__}: {error}", flush=True)
    finally:
        server.terminate()
        server.wait(timeout=10)
        if app:
            app.terminate()
            app.wait(timeout=10)


if __name__ == "__main__":
    main()
