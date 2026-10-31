# Persistent memory

Taius keeps its bounded STM and also writes a durable SQLite journal to
`ASKAI_DIR/memory/history.sqlite3`. This is outside the response/audio cache.
Existing plain-text conversation history remains unchanged; this journal starts
recording when the updated application runs.

The journal records requests, agent session/turn identifiers, completed tool
activity, explicit user interaction decisions, agent results, final answers and
failures. Daily session pointers are scoped by agent, resolved working directory and local
calendar date (`YYYY-MM-DD`). Codex threads receive that date as their name.
Records are committed during execution, so a later validation failure does not
remove evidence of earlier actions. Secret answers marked by the agent are
redacted from interaction records.

When `askai.context.keep.conversation` (History) is enabled, the first request
after restart resumes the stored session for the current day. With History off,
that request starts a new session; subsequent requests in the running app still
reuse it. Changing the setting never discards the active session or the journal.
The first request on a new day creates a new session. A request that crosses
midnight stays assigned to the date on which it began; rotation occurs on the next
request. Older dated sessions and all activity remain in SQLite. Existing undated
session pointers are retained, but are not reused as a new daily session.

At creation only, the agent receives `taius-session-start.txt`, describing the
AskAI MCP capabilities, their arguments and boundaries. No tool is called merely
because a session started. The initial prompt is not replayed on resume. Execution,
validation and refinement use that same session; previous answers, tool output
and journal entries are not copied back into each turn. The current request and
its retrieved sources are sent as new input. STM remains bounded as before.
The SQLite journal remains a durable audit record, not an automatically injected
prompt. There is no inferred decision extraction or full-archive search yet.
Oversized new input is rejected locally with an actionable error; it is not
silently truncated or moved into temporary context files.

History is past evidence, not current filesystem state or authorization. The
agent is instructed to verify mutable facts, not reuse approvals and not replay
incomplete requests. Missing final answers indicate an incomplete workflow, not
proof that no action happened. If the agent cannot resume its stored session,
the error is surfaced; no replacement session or repeated action is silently
created. Database failures also surface instead of silently disabling memory.

The journal is local and contains conversation and tool output. Records are available through `/history`; they are not reinjected into agent turns. Restart Taius to load
the implementation. No cache clearing or existing database reset is required.

## Reset the current session

Run `/session reset` inside Taius. The next request creates a new Codex session,
named for the current date, and sends the initial AskAI capabilities prompt again.
The command retires only today's pointer for the active agent and directory; the
old session ID is recorded in the journal. Prior activity, older daily sessions,
STM and saved preferences remain intact. A reset is rejected while a task runs.

## History commands

- `/history` or `/history list`: list recorded conversations grouped by date and
  session for the selected agent and working directory.
- `/history list YYYY-MM-DD`: show one local session date.
- `/history enable 1`: record conversations and resume saved sessions (default ON).
- `/history enable 0`: stop journal, keyboard history and memory snapshot recording
  and do not restore saved conversations. Codex uses an ephemeral session, retained
  in memory only while AskAI runs. STM stays available. The UI uses a temporary
  transcript that is removed on exit. Switching the flag separates native sessions;
  private STM entries are excluded from subsequent snapshots.
- `/history forget`: clear keyboard input history only. It does not erase the
  durable journal or reset the agent; use `/session reset` for a new session.

The listing distinguishes final answers, failed requests and unfinished requests.
New records retain their actual session ID even after a reset on the same date.
Older records lacking session/date metadata are shown as not recorded in the
unfiltered listing; their association is not guessed. Disabling History preserves
previously saved data. Automatic exit compaction is skipped while History is OFF.

## Compact the native session

`/session compact` asks Codex to compact the active session's model context. It
retains the session ID and leaves the AskAI SQLite journal and STM unchanged.
The runtime owns the summary and persistence; AskAI does not rewrite its session
files or substitute a new thread.

`askai.session.compact.on.exit` defaults to `true`, including existing installs
where this setting was absent. Change it with:

```text
/settings set askai.session.compact.on.exit false
```

On normal exit, AskAI waits up to 30 seconds for its current task to release the
session before attempting compaction. It waits for a completed `contextCompaction`
item and a successful terminal turn notification; the immediate `{}` response to
`thread/compact/start` is not success. Event completion has a 60-second deadline,
in addition to the existing bounded transport request waits.

Only sessions with observed agent activity newer than their last confirmed
compaction are compacted. The revision marker survives restarts. A reset does not
compact or revive the retired session. Exiting without using a session does not
start a new agent session just to compact it. Normal shutdown runs this hook once
across CLI/TUI cleanup paths.

Interrupted tasks and forced exits skip automatic compaction. A failure or timeout
is reported, leaves the revision eligible for a later attempt, and does not prevent
cleanup or erase history. No compaction runs from a process-exit signal handler.

A live native-compaction check on 2026-10-31 confirmed completion, resumed the
same session ID, and recovered the exact test token after compaction.
