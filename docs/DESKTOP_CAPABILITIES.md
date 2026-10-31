# Desktop capabilities

AskAI exposes local actions through an MCP stdio server, started automatically by
its Codex adapter. This initial implementation supports macOS. The service uses
an independent core with typed action results, with no CLI/TUI or model imports.
It recovers the desktop operations formerly buried in terminal/webcam tools
without restoring the splitter or a generic shell executor.

## Available actions

| Tool | Purpose | Result |
| --- | --- | --- |
| `open_path` | Open an absolute path; audio/video uses ffplay, other files use their default app | OS dispatch confirmation |
| `open_application` | Launch a named app | OS dispatch confirmation |
| `play_music` | Play a local audio/video file with ffplay | Process started or early failure |
| `control_music` | Resume, pause or stop AskAI playback | Owned process control result |
| `open_camera` | Launch Photo Booth preview | Dispatch; no photo taken by AskAI |
| `capture_camera` | Save a single camera frame and release the device | Saved path and byte count |

Example requests: "Abra a pasta Downloads", "Abra a Calculadora", "Toque o
arquivo ~/Music/song.mp3", "Pause a musica", "Abra a camera", "Tire uma foto".
The agent resolves ambiguous names or paths before invoking an action. Audio plays
without a window; videos open in ffplay's window. Supported extensions include
mp3, m4a, aac, wav, aiff, flac, ogg, opus, wma, mp4, mov, mkv, avi and webm.
Streaming services and playlists (including next/previous track) are not integrated.
Camera capture does not perform image
analysis, identity recognition or continuous monitoring.

## Runtime behavior

The Codex subprocess receives the MCP definition through process-local `-c`
overrides. Validation/refinement launches disable this MCP server. No global
Codex configuration is edited. MCP tool results enter the existing agent events,
execution evidence and persistent activity journal.

Commands are argument arrays, not shell strings. Opening apps and camera capture
use bounded subprocesses. ffplay runs independently for the duration of the media. Camera
capture runs in a subprocess, releases its device on completion/failure and
removes partial files on failure. Playback continues across agent turns. Its PID and process creation time are stored
in the capability directory; controls verify ownership and do not signal reused PIDs.
Use `control_music` to pause, resume or stop; starting a new file stops the previous
AskAI player. Playback does not use the macOS Music app or AppleScript.

Photo output goes to `~/.local/share/askai/capabilities/photos`, or the directory
specified by `ASKAI_CAPABILITY_DIR`. macOS may request camera permission. Errors are returned as MCP tool errors, not successful actions.
A dispatched open request does not prove that a window appeared or audio played.

## Other agents

The same server can be registered in another MCP-capable client using the AskAI
virtualenv Python executable with arguments `-m askai.mcp_server`. This does not
implement the Claude/Cursor conversation adapters themselves.

The implementation uses the [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
and [Codex MCP process configuration](https://learn.chatgpt.com/docs/extend/mcp).

Restart Taius after upgrading. Dependencies include `mcp==1.30.0`, `psutil==7.2.2` and FFmpeg/ffplay.
