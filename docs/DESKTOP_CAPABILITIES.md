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
| `capture_camera` (host tool) | Confirm, count down, save a photo and release the device | Saved path |

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

Commands are argument arrays, not shell strings. Opening apps uses bounded subprocesses. ffplay runs independently for the duration of the media. Camera
capture uses the original AskAI Camera in the host and releases its device on completion/failure. Playback continues across agent turns. Its PID and process creation time are stored
in the capability directory; controls verify ownership and do not signal reused PIDs.
Use `control_music` to pause, resume or stop; starting a new file stops the previous
AskAI player. Playback does not use the macOS Music app or AppleScript.

The host `capture_camera` tool uses AskAI's original camera and saves photos under
`ASKAI_DIR/cache/pictures/photos` (normally `~/.config/hhs/askai/cache/pictures/photos`).
The user confirms access before the visible 3–2–1 countdown, click sounds and shutter.
Codex opens the saved photo for analysis. Desktop playback state defaults to
`ASKAI_DIR/cache/capabilities`; an explicit `ASKAI_CAPABILITY_DIR` overrides that
state directory. Generated artifacts stay under `ASKAI_DIR` unless the user requests
another destination. macOS may also request camera permission.
A dispatched open request does not prove that a window appeared or audio played.

## Other agents

The same server can be registered in another MCP-capable client using the AskAI
virtualenv Python executable with arguments `-m askai.mcp_server`. This does not
implement the Claude/Cursor conversation adapters themselves.

The implementation uses the [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
and [Codex MCP process configuration](https://learn.chatgpt.com/docs/extend/mcp).

Restart Taius after upgrading. Dependencies include `mcp==1.30.0`, `psutil==7.2.2` and FFmpeg/ffplay.

## Screenshots

The host `capture_screenshot` tool reuses AskAI's PyAutoGUI capture and JPEG output.
It asks for confirmation, displays 3–2–1 with click sounds, captures the screen and
plays the shutter. Files use `ASKAI_DIR/cache/screenshots`. Capture has no vision
provider dependency: Codex opens the returned path with `view_image` for analysis.
The final answer retains the former screenshot presentation (visible applications,
documents, web pages and the answer), omitting empty or unreadable information.
Cancellation before capture does not access the screen. Read-only review turns
cannot invoke the capture tool. Restart AskAI and use `/session reset` once to
register newly introduced host tools; existing history is preserved.

### Local identification and named enrollment

AskAI runs YuNet detection, landmark alignment and SFace embeddings locally through
OpenCV. Models load once per process from `ASKAI_DIR/cache/models/faces`; downloads
use the official OpenCV Zoo files with SHA-256 verification. No face images or
vectors are sent to Codex by identification/enrollment tools: it only summarizes
returned labels, statuses and cosine similarity. Unknown faces remain unknown.

- `/camera register`: confirm camera access, capture with 3..2..1 sounds, open a
  numbered preview and ask the human to name each detected face.
- `/camera register "/absolute/photo.jpg" "/absolute/another.jpg"`: the same local
  enrollment flow for existing photos, leaving originals unchanged.
- `/camera review`: open a contact sheet of existing samples and manage their identities.
- `/camera identify`: confirm capture and recognize each detected face locally.
- `/camera identify 0.5`: use a stricter cosine threshold for this request.
- `/camera --help`: help and examples; register is included in input completion.

For each numbered face, choose:
- **New identity**: create a name (several selected samples can share it).
- **Merge**: assign the sample to an existing identity, retaining its other samples.
- **Replace**: replace all samples of the target identity with the selected ones.
- **Skip** (blank action): do not select this sample.

The same choices work on new photos and existing samples in `/camera review`.
Existing names and sample counts are shown; capitalization/extra spaces do not
create separate identities. A final confirmation lists the changes. Replace affects
all old samples of its target, including unselected ones, but never deletes photos.
Merge moves the selected sample, not every sample bearing its former name; select
all samples of the duplicate identity to consolidate the whole group.
Cancellation discards the entire batch. Choices and names come from human input.
Captured photos remain in their normal directory. Temporary previews and unselected
crops are removed. Names come only from the human input component. Selected aligned
crops are stored as PNGs in `cache/pictures/faces`; names, captions and normalized
128-dimensional SFace vectors are stored in `identities/sface.sqlite3`.
The core has no dependency on CLI/TUI presentation. Reviews cannot invoke tools.

BLIP captions are disabled by default and are not required for recognition.
Enable them with `/settings set askai.camera.identity.caption.enabled true`.
The cosine threshold uses the independent setting
`askai.camera.identity.sface.cosine.threshold` (default 0.363, from OpenCV's LFW
example). The previous OpenCLIP distance setting does not apply. Similarity is
not a probability or a calibrated identity confidence.

### Existing photos and vector migration

The first use migrates the active legacy Chroma image_store's face metadata,
reading its SQLite database in read-only mode. It recalculates vectors from
original files, keeping names, captions and paths. Original photos and Chroma data
are never rewritten or deleted. OpenCLIP vectors are never reused as SFace vectors.
Records lacking names remain unlabelled; captions are not treated as names.

Faces that cannot be read or yield zero/multiple detections retain their metadata
in the new `pending_faces` table, with the reason. No face alignment is guessed.
The migration is transactional and recorded in `migrations`, so normal startup
does not recompute it. To retry pending original records explicitly:

```sh
python -m askai.core.component.faces.migration --rebuild
```

Rebuild replaces only untouched migrated records and preserves new enrollments and human Merge/Replace changes. Use
`/camera register` with a clearer photo to create a usable named sample.

Removed the old Haar resource, OpenCLIP image-store implementation/dependency,
legacy webcam wrappers, old import path and their obsolete demos/tests.
The preserved original database exists only as migration input.
BLIP/Transformers, Chroma for RAG and other still-used image features remain.

Restart AskAI and run `/session reset` once so Codex receives the updated tool
schemas and instructions. No cache clearing or destructive database reset is needed.

Model references: [OpenCV detection and recognition](https://docs.opencv.org/4.x/d0/dd4/tutorial_dnn_face.html),
[YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet),
[SFace](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface).

## Persistent grants

The core permission policy reads `askai.grants.<capability>.<action>.<scope>` from
AskAI's existing SetMan settings table. There is no separate permissions database.
All grants default to `ask`; upgrades add missing keys without changing existing
choices. Values are:

- `ask`: ask for this action only; an accepted answer does not persist permission.
- `allow`: execute the covered operation without a permission dialog.
- `deny`: block before execution, without asking the agent or user to override it.

Only registered exact keys are accepted; wildcards and invalid values cannot
permit actions. A combined operation checks every required grant first, rejects
if any is denied, and consolidates outstanding `ask` permissions into one dialog.
The core reads the settings afresh for each action, including in the MCP process.
Both `/settings set` and `/grants set` validate grant names and values.

```text
/grants
/grants list camera
/grants get camera.capture.local
/grants set media.play.local allow
/grants set vision.share.agent deny
/grants reset media.play.local
/grants reset
/settings set askai.grants.camera.capture.local ask
```

`/grants reset` restores only grants to `ask`; it does not reset other settings.
`/grants --help` and `/help grants` use the existing colored help, and operations
are included in input completion. Full `askai.grants.*` keys or short names work.

| Grant suffix | Covered action |
| --- | --- |
| `camera.capture.local` | Local camera photo |
| `camera.preview.local` | Photo Booth preview |
| `screen.capture.local` | Screenshot |
| `vision.share.agent` | Share captured image with the agent |
| `images.read.local` | Read photos and open enrollment previews |
| `identities.read.local` | Read identity samples for review or recognition |
| `identities.create.local` | Save new named samples |
| `identities.merge.local` | Merge/reassign selected samples |
| `identities.replace.local` | Replace the target identity's samples |
| `media.play.local` | Play/resume media, including media opened via open_path |
| `media.pause.local` | Pause playback |
| `media.stop.local` | Stop playback |
| `paths.open.local` | Open files/folders |
| `applications.open.local` | Launch applications |

Camera/screenshot analysis requires both local capture and image-sharing grants.
Local face recognition requires camera capture plus identity read, but not image
sharing. Enrollment first checks source access/identity read, then checks the
actual create/merge/replace choices before committing. Its generated preview is
part of the authorized enrollment operation, not another generic file-open action.
Forms collecting names and choices use the host's typed input channel and no
longer ask permission merely to display a form. Data entry remains mandatory even
when all related grants are `allow`; cancellation never commits pending choices.

Desktop MCP handlers enforce the same policy themselves, even with another MCP
client. Only these five protected tools use Codex's per-tool `approval_mode`
`approve` to avoid duplicate native prompts; shell/file approvals and other servers
are unchanged. A per-connection execution-scope guard independently blocks desktop
actions during validation/refinement, including private sessions sharing a process,
and between turns. Missing scope state fails closed.

Grant settings are user-managed commands and are not exposed as agent tools.
The agent is instructed not to modify them or bypass denial with terminal commands.
These application grants do not replace Codex's sandbox or operating-system access
controls. Restart AskAI once to load the new handlers/MCP configuration; subsequent
grant edits take effect immediately without restarting or resetting the session.

Codex configuration reference:
[Per-tool MCP approval mode](https://learn.chatgpt.com/docs/config-file/config-reference).
