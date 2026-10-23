#!/usr/bin/env python3
"""Add a brief Codex PostToolUse reminder at most once per interval."""

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time


MESSAGE = (
    "Is everything we're doing necessary? Briefly reassess the next action "
    "against the user's current task and accepted completion conditions, "
    "using the context already available. Drop redundant checks and optional "
    "verification tooling; continue useful work without asking for renewed "
    "permission. Keep required checks and known material defects in scope. "
    "Do not create a report, checklist, audit, or subagent for this reminder. "
    "This is an automated reminder, not a new user reply or approval."
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval-seconds", type=float, default=1800)
    parser.add_argument("--state-file", type=Path)
    parser.add_argument("--message-file", type=Path)
    args = parser.parse_args()
    if not 0 < args.interval_seconds < float("inf"):
        parser.error("--interval-seconds must be a finite positive number")

    event = json.load(sys.stdin)
    if not isinstance(event, dict) or event.get("hook_event_name") != "PostToolUse":
        return
    if not event.get("session_id"):
        return

    # Use transcript_path only as an opaque identifier; never read the transcript.
    identity = json.dumps([event["session_id"], event.get("transcript_path")])
    session_key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    user_key = hashlib.sha256(str(Path.home()).encode("utf-8")).hexdigest()[:16]
    state_file = args.state_file or (
        Path(tempfile.gettempdir()) / ("codex-necessity-" + user_key) / "timer.sqlite3"
    )
    state_file.parent.mkdir(parents=True, exist_ok=True)
    message = args.message_file.read_text(encoding="utf-8") if args.message_file else MESSAGE
    now = time.time()

    # A short transaction prevents simultaneous tool returns from sending duplicates.
    with sqlite3.connect(str(state_file), timeout=1) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS timer (session TEXT PRIMARY KEY, last REAL)")
        row = db.execute("SELECT last FROM timer WHERE session = ?", (session_key,)).fetchone()
        if row and 0 <= now - row[0] < args.interval_seconds:
            return
        db.execute("INSERT OR REPLACE INTO timer VALUES (?, ?)", (session_key, now))

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse", "additionalContext": message
    }}))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, sqlite3.Error) as exc:
        # This optional reminder must never block project work or trigger a repair loop.
        print("Necessity reminder skipped: " + str(exc), file=sys.stderr)
        sys.exit(0)
