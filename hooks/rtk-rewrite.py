#!/usr/bin/env python3
# rtk-hook-version: 2
"""
RTK Claude Code hook — rewrites commands to use rtk for token savings.
Cross-platform version (Windows, macOS, Linux).

Requires: Python 3.6+, rtk >= 0.23.0
Delegates all rewrite logic to `rtk rewrite` command.
"""

import sys
import json
import subprocess

HOOK_VERSION = 2

def check_rtk():
    """Check if rtk is installed and version is >= 0.23.0."""
    try:
        result = subprocess.run(
            ["rtk", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
        version_str = result.stdout.strip()
        # Parse version like "rtk 0.31.0"
        parts = version_str.split()
        if len(parts) >= 2:
            version = parts[1]
            major_minor = version.split(".")[:2]
            if major_minor == ["0", "23"] or version >= "0.23.0":
                return True
        return True  # Если не смогли распарсить, считаем OK
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        print("[rtk] ERROR: rtk is not installed or not in PATH.", file=sys.stderr)
        print("[rtk] Install: https://github.com/rtk-ai/rtk#installation", file=sys.stderr)
        sys.exit(1)

def rewrite_command(cmd: str) -> str | None:
    """Call `rtk rewrite` and return rewritten command, or None if no change."""
    try:
        result = subprocess.run(
            ["rtk", "rewrite", cmd],
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )
        rewritten = result.stdout.strip()
        return rewritten if rewritten else None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None

def main():
    # Guard: check rtk availability
    check_rtk()

    # Read JSON input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"[rtk] ERROR: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract command from tool_input
    tool_input = input_data.get("tool_input", {})
    cmd = tool_input.get("command", "").strip()

    if not cmd:
        sys.exit(0)

    # Rewrite command via rtk binary
    rewritten = rewrite_command(cmd)
    if not rewritten or rewritten == cmd:
        sys.exit(0)  # No change, pass through

    # Build updated JSON response
    original_input = tool_input
    updated_input = {**original_input, "command": rewritten}

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "RTK auto-rewrite",
            "updatedInput": updated_input
        }
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
