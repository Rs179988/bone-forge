#!/usr/bin/env python3
"""
Root Launcher Forwarder for CODE-HIGGSFIELD MCP & Studio HTTP Server.
Allows running `python3 mcp-server/mcp_server.py --http --port 8765` directly from the repository root
(`/workspaces/bone-forge` or `/workspace`) as well as from `studios/code-higgsfield`.
"""
import os
import runpy
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
TARGET = ROOT_DIR / "studios" / "code-higgsfield" / "mcp-server" / "mcp_server.py"

if not TARGET.exists():
    sys.stderr.write(f"Error: Could not find target server at {TARGET}\n")
    sys.exit(1)

os.chdir(TARGET.parents[1])
sys.argv[0] = str(TARGET)
runpy.run_path(str(TARGET), run_name="__main__")
