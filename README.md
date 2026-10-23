# Codex necessity reminder

A small, optional PostToolUse hook for local Codex sessions, including sessions
using AI-DLC. It adds a brief reminder to the model's context. It does not call
another model, inspect the repository, run tests, or launch a background service.

## What it does

- Sends a reminder on the first matching tool result, so you can check delivery.
- Sends another on the first tool result at least 1800 seconds after the last one.
- Produces no stdout between reminders. Simultaneous tool results share one timer.
- Keeps one timestamp per session/transcript pair in the operating system's temp
  directory. It does not read or store conversation text.
- Does not restart idle sessions. It does not interrupt a running shell command
  or a model response that has not yet returned to a tool boundary.
- Adds context to the thread that runs the hook. It does not forward a parent
  reminder to other agents. Threads with distinct session IDs or transcript
  paths have separate timers; threads sharing both share a timer.

This is an elapsed-time reminder, not a hard limit on the agent. Delivery does
not prove that the model changed course. Required tests and accepted project
requirements remain in force.

## Install alongside AI-DLC

1. Check `codex --version` and the existing project hook setup. This package uses
   the current documented Codex PostToolUse JSON contract. It needs Python 3
   with its standard-library sqlite3 module. No pip packages are required.
2. Copy `necessity_check.py` to `<project>/.codex/hooks/necessity_check.py`.
3. In `hooks.fragment.json`, replace the script path and Python command for the
   machine actually running Codex. Linux/WSL usually use `python3`; Windows may
   use `py -3` or the full path to `python.exe`. `commandWindows` overrides
   `command` on Windows. Use absolute paths; the session may change directories.
4. APPEND the fragment's one PostToolUse matcher group to the existing
   `<project>/.codex/hooks.json` under `hooks.PostToolUse`. If that array is absent,
   add it. Preserve all AI-DLC hooks and other settings. Do not replace the
   existing file with this fragment. If the project uses inline TOML hooks,
   use that same representation instead of adding a second hook source.
5. Open `/hooks` in local Codex and review/trust the added hook. Codex requires
   this review before an untrusted hook can run. Keep the existing project trust
   and permission controls in place.
6. In one live session, ask for a harmless tool call and check that the reminder
   arrives. If the client has not reloaded the hook, restart/resume that session.
   The second immediate tool call should not produce another reminder.

For a Windows session, a valid commandWindows example is:

    py -3 "C:\Projects\Blueprint\.codex\hooks\necessity_check.py"

For a session running on your Debian VM, use the VM's path and Python command,
even if you control it from a Windows workstation.

Local command hooks do not apply to cloud-orchestrated Work sessions. Check the
installed client's supported hook surface instead of assuming this local hook
can attach to an arbitrary hosted conversation.

## Adjust the interval or message

The default interval is 1800 seconds. Append `--interval-seconds 1800` to the
configured command if you want the value explicit. For one brief delivery
check, you can temporarily use a shorter interval, then restore 1800.

To use your exact question or other wording, create a UTF-8 text file containing
the desired reminder and add `--message-file "/absolute/path/message.txt"` to
the command. Otherwise, the script uses its short built-in message, which asks
the agent to drop redundant work without starting a new audit.

Keep the reminder brief. It should not ask the agent to produce evidence that
the reminder itself worked, build a tracking system, or seek approval for each
normal action. It is automated context, not a human response to an approval gate.

## Disable

Disable this hook in `/hooks`, or remove only its matcher group from the project
configuration. Keep the AI-DLC registrations. The script and its temporary
timestamp file can then be removed if desired.

## Verification and limits

The supplied hook was checked locally with synthetic Codex event payloads for
initial delivery, suppression before the interval, delivery after the interval,
independent sessions, and simultaneous tool returns. No model/API call was
needed. It has not been installed or observed in your Codex environment.

A PostToolUse hook sends at the next tool result after the interval. If you need
an actual user-message injection while a turn is active, Codex App Server has
`turn/steer`; a client connected to the server that owns the live thread must
send it. Starting a separate `codex exec resume` process is not a way to steer
the existing live turn.

## Sources

Checked October 22, 2026:

- Codex hook events, JSON output, registration, and trust:
  https://learn.chatgpt.com/docs/hooks
- Codex configuration and local/cloud hook scope:
  https://learn.chatgpt.com/docs/config-file/config-reference
- AI-DLC Codex setup:
  https://github.com/awslabs/aidlc-workflows/blob/main/docs/guide/harnesses/codex-cli.md
- AI-DLC PostToolUse context forwarding:
  https://github.com/awslabs/aidlc-workflows/blob/main/docs/reference/06-hooks-and-tools.md
- Active-turn input:
  https://learn.chatgpt.com/docs/app-server

These links describe current upstream behavior. They do not establish which
versions or hook settings your existing project uses.
