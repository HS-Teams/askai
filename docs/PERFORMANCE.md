# Response latency and concurrency

Startup uses at most three workers for independent NLTK preparation, history
loading (CLI), silent speech availability probing and RAG index preparation.
Microphone setup, scheduler setup and player calibration remain coordinated by
the application. Progress callbacks run on the caller thread. Errors propagate;
startup does not silently disable failed services.

Before execution, document retrieval overlaps with Codex connection preparation.
Execution, validation and refinement remain sequential on the same session.
Persistent journal writes remain ordered and synchronous.

The Codex app-server connection is reused across consecutive turns with the same
permission scope. The runtime permits only one active writer per session, so the
process is closed when switching between execution and read-only review. Both
validation and refinement use the same review process; a normal complete request
therefore starts two processes instead of three. Failed transports are discarded
without replaying the action. Shutdown closes the retained connection.

A live four-turn text-only check on 2026-10-31 preserved the test token across
execution, two review turns, and execution again, using three processes. The
observed turn durations were 3.48, 5.00, 1.71 and 4.46 seconds. This is a functional
check, not a controlled before/after latency benchmark.

Debug logs include `AskAI timing` entries for startup tasks, retrieval/connection,
execution, validation, refinement, total orchestration, memory snapshots, speech
synthesis and playback. These timing messages contain stage names and elapsed
seconds, not question or answer text.

Voice output uses an ordered worker and synchronized text presentation; see
[SPEECH_ENGINES.md](SPEECH_ENGINES.md). No speculative answer or speech is shown
before validation and refinement complete. The core exposes callbacks and has no
dependency on CLI or Textual presentation code.
