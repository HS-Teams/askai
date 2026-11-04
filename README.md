<img src="https://iili.io/J8wvc1n.png" width="64" height="64" align="right" />

# AskAI
>
> Unleash the Power of AI in Your Terminal

[![Terminal](https://badgen.net/badge/icon/terminal?icon=terminal&label)](https://github.com/yorevs/homesetup)
[![License](https://badgen.net/badge/license/MIT/gray)](LICENSE.md)
[![Release](https://badgen.net/badge/release/v2.0.1/gray)](docs/CHANGELOG.md#unreleased)
[![Donate](https://badgen.net/badge/paypal/donate/yellow)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=J5CDEFLF6M3H4)
[![build-and-test](https://github.com/yorevs/askai/actions/workflows/build-and-test.yml/badge.svg)](https://github.com/yorevs/askai/actions/workflows/build-and-test.yml)

<img src="https://iili.io/J8vkAYX.png" width="100%" height="100%" />

---

<img src="https://iili.io/J8wrBSe.png" width="360" height="360" align="right" />

Born from the idea of empowering individuals with disabilities to navigate the digital world effortlessly, AskAI stands as a beacon of accessibility in the realm of computing. It emerges as a revolutionary solution, harnessing the prowess of AI to bridge the gap between users and the terminal interface. With its intuitive design, AskAI welcomes users of all abilities, eliminating the need for extensive familiarity with shells like bash or zsh. Now, individuals with disabilities can effortlessly command their machines, whether it involves listing files and folders, summarizing documents, accessing real-time data, or delving into a myriad of other functions.

At the heart of AskAI lies its innovative integration of Speech-to-Text and Text-to-Speech technologies, offering a seamless experience for both visually and hearing impaired users. Through these cutting-edge features, individuals can interact with their computers using their natural voice, transcending the barriers imposed by traditional input methods. Moreover, AskAI introduces a unique push-to-talk input mechanism, enabling users to issue commands effortlessly, enhancing the fluidity and ease of interaction.

<img src="https://iili.io/J8wiCqQ.png" style="padding-right: 10px" width="270" height="154" align="left" />

Furthermore, AskAI embraces diversity by breaking language barriers, ensuring that no matter the tongue spoken, users can communicate effectively with their systems. Its adaptive language capabilities ensure that commands are understood and executed accurately, regardless of linguistic nuances. By championing inclusivity on all fronts, AskAI redefines the landscape of computing accessibility, empowering individuals with disabilities to navigate the digital realm with confidence and autonomy.


> The world speaks many languages. AskAI understands them all.

🔥 Checkout the [YouTube](https://www.youtube.com/watch?v=ZlVOisiUEvs) video with our Demo!

🔥 Checkout the new AskAI Teaser on [LinkedIn](https://www.linkedin.com/posts/yorevs_the-world-is-changing-paradigms-are-being-activity-7282570183578181632-Hjke?utm_source=share&utm_medium=member_desktop)

[![YouTube Video](https://img.youtube.com/vi/ZlVOisiUEvs/0.jpg)](https://www.youtube.com/watch?v=ZlVOisiUEvs)


## Key Features

- Integrate OpenAI models and local Llama models through Ollama.
- Activate Speech-to-Text Inputs via Push-to-Talk Keybinding.
- Control Text-to-Speech Outputs with Adjustable Speed.
- Enable Assistive Technology for Visually Impaired Terminal Usage.
- Enjoy a Natural Typewriter Effect Synced with Speaking Text.
- Automate Offline Language Translations for Enhanced Accessibility.
- Interactive and Non-Interactive modes.
- Image captions are used to provide textual descriptions of visual content.
- Enhanced accuracy in responses is achieved through the implementation of a Retrieval-Augmented Generation (RAG) system.

## Installation

### Requirements

#### Python

- Python 3.10 and higher

#### Operating Systems

- Darwin
  - High Sierra and higher
- Linux
  - Ubuntu 16 and higher
  - CentOS 7 and higher
  - Fedora 31 and higher

You may want to install HsPyLib on another OS's and it will probably work, but there are no guarantees that it
**WILL ACTUALLY WORK**.

#### Applications / Libraries

The following software is required:

- FFMPEG (This allows you to play audio and video files from your terminal).
- PORTAUDIO (To allow microphone recordings).

##### macOS installation

Use Homebrew to install the prerequisite portaudio:

```bash
$ brew install portaudio ffmpeg libmagic
```

##### GNU/Linux installation

Debian-based systems:

```bash
$ sudo apt install python3-pyaudio ffmpeg libmagic-dev
```

RedHat-based systems:

```bash
$ sudo dnf install portaudio-devel redhat-rpm-config ffmpeg libmagic-dev
```

#### AskAI installation

AskAI is available at [PyPi](https://pypi.org/project/hspylib-askai/)

```bash
$ python3 -m pip install hspylib-askai
```

#### ApiKeys

In order to use AskAI you need to have the following Api Keys:

- DEEPL_API_KEY (for translations).
- GOOGLE_API_KEY (for internet browsing).
- OPENAI_API_KEY (to use ChatGPT api).

##### Google Search API Integration

To enable the Custom Search API:

1. Navigate to the APIs & Services→Dashboard panel in Cloud Console.
2. Click Enable APIs and Services.
3. Search for Custom Search API and click on it.
4. Click Enable.

> URL for it: https://console.cloud.google.com/apis/library/customsearch.googleapis.com

To create an API key:

1. Navigate to the APIs & Services → Credentials panel in the Cloud Console.
2. Select Create credentials, then select the API key from the drop-down menu.
3. The API key-created dialog box displays your newly created key.
4. You now have a GOOGLE_API_KEY.

> Alternatively, you can just generate an API key here: https://developers.google.com/custom-search/docs/paid_element#api_key

##### DeepL API

To enable the DeepL online translation:

1. Navigate to your account settings.
2. Select the API Keys tab.
3. Click on Create key +.
4. You now have a DEEPL_API_KEY.

##### OpenAI API

To enable your OpenAI LLM:

1. Access the OpenAI [API Section](https://platform.openai.com/settings/profile?tab=api-keys):
2. Navigate to the API section of the OpenAI dashboard.
3. Create a New API Key by clicking on “Create API Key” or a similar button.
4. Name Your API Key:
5. You now have an OPENAI_API_KEY.


## Support

> Your support and contributions are greatly appreciated in helping us improve and enhance HomeSetup. Together, we can
make it even better!

You can support HomeSetup by [donating](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=J5CDEFLF6M3H4)
or contributing code. Feel free to contact me for further details. When making code contributions, please make sure to
review our [guidelines](docs/CONTRIBUTING.md) and adhere to our [code of conduct](docs/CODE_OF_CONDUCT.md).

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/yorevs)

You can also sponsor it by using our [GitHub Sponsors](https://github.com/sponsors/yorevs) page.

This project is already supported by:

<a href="https://www.jetbrains.com/community/opensource/?utm_campaign=opensource&utm_content=approved&utm_medium=email&utm_source=newsletter&utm_term=jblogo#support">
  <img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png" width="120" height="120">
</a>

Thank you <3 !!

## Contacts

- License: [MIT](LICENSE.md)
- Maintainer: [REDDIT](https://www.reddit.com/user/yorevs)
- Mailto: [HomeSetup](mailto:homesetup@gmail.com)

Enjoy!

## Local Llama with Ollama

Install the Python dependencies through the project build. AskAI communicates with
Ollama through its native HTTP endpoints. Start Ollama and install the models you intend to use:

```bash
ollama serve
# In another terminal:
ollama pull llama3.1
ollama pull phonon
# Required for RAG and validator retrieval:
ollama pull nomic-embed-text

PYTHONPATH=src/main python3 -m askai -e llama -m llama3.1 -r chat -i -s
```

The Llama engine uses the local service without an OpenAI API key. It supports
chat, task splitting, embeddings and image captions when the selected model
supports vision. Phonon supplies speech output; microphone transcription retains
AskAI's existing recorder/transcriber (Google recognition by default).

Speech is exposed through `AIEngine.speech() -> AISpeech`. Every provider implements
`model_name`, `voice`, `voices()`, `select_voice()` and `synthesize()`. The voice
commands depend only on this contract. A synthesis voice override previews a
voice without changing the saved selection:

```text
/voices list
/voices set "Grub the Ogre"
/voices play "Grub the Ogre"
/voices play 0
```

Indices are zero-based. Voice selection is saved per provider. OpenAI and Ollama
both generate previews using their speech provider; there is no provider-specific
sample-file lookup in the commands. Quoted and unquoted multiword voice names are
accepted. Standalone usage is also supported:

```bash
PYTHONPATH=src/main python3 -m askai -e llama '/voices list'
```

| Environment variable | Default |
| --- | --- |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` |
| `ASKAI_LLAMA_MODEL` | `llama3.1` |
| `ASKAI_LLAMA_EMBEDDING_MODEL` | `nomic-embed-text` |
| `ASKAI_LLAMA_CONTEXT_LENGTH` | `4096` |
| `ASKAI_LLAMA_TIMEOUT` | `120` seconds |
| `ASKAI_LLAMA_TTS_MODEL` | `phonon` |

Chat model selection uses `-m`, then `askai.<engine>.default.model`, then the
engine's built-in default (`gpt-4o-mini` for OpenAI, `llama3.1` for Ollama;
`ASKAI_LLAMA_MODEL` can override the latter). Starting a session saves the selected
model for that engine. Switching engines preserves each engine's selection.
The old global `askai.default.engine.model` setting is no longer read. The default speech voice is
`Grub the Ogre`; `/voices list` queries the installed speech model's catalogue.
Phonon runs through the Ollama CLI with redirected WAV output, then uses AskAI's
existing audio player and playback speed. The CLI handles long input, and failed
synthesis is not cached. Ollama speech requires a compatible Ollama/Phonon runtime;
see the [Ollama speech guide](https://docs.ollama.com/capabilities/speech).

Persisted RAG indexes now include the embedding provider/model identity. Existing
indexes are retained, and a new index is built on first use. Chat and speech have
no automatic fallback to another provider. Restart AskAI after installing the new
Python dependency or changing environment configuration.


### Taius orchestration and Codex

The interactive `taius` routing mode replaces the task splitter. AskAI retains its
STM, document RAG, validator and refiner. Every question in this mode goes to
Codex, including conversation. There is no local-model routing decision or function-call
splitter. The flow is text (or STT) -> Codex -> validation -> refiner -> text,
with TTS only when `/speak` is on. Configured RAG supplies context when indexed
documents exist. Validation failure never automatically replays an executed task.

```bash
codex login
ollama pull llama3.1
ollama pull nomic-embed-text
askai -e llama -r taius
```

Use `askai --help` for invocation options; `/mode taius` selects orchestration in
an existing session. The inference engine and specialized agent are separate:
`-e llama` handles validation, refinement and local capabilities; Codex processes every question using its existing
ChatGPT account via `codex app-server`, without an OpenAI API key. The existing
OpenAI engine remains available during migration and still requires its own key.

The new agent and orchestration core has no CLI/TUI imports. CLI and Textual
adapters handle requests for per-action approval or user answers. Codex runs in
the launch working directory with `workspace-write` sandboxing and `on-request`
approvals; actions within that sandbox may run without a further prompt. Additional
permission-profile grants are currently denied explicitly. Unknown interaction
methods fail explicitly. Ctrl+C (CLI) or Stop (TUI) requests cancellation; completed
side effects are not rolled back. No task is retried or switched to another agent
silently.

The adapter was exercised against Codex CLI 0.162.1. It uses structured final-answer
items, not keyword filtering. Specialist sessions are reused within the running
AskAI process. With conversation history enabled, daily session references are
persisted by agent and working directory and can resume after an application
restart; see [Persistent memory](docs/PERSISTENT_MEMORY.md).
The old function-call executor and framework dependencies
have been removed. Existing document indexes are left intact; native retrieval
uses a separate index namespace and rebuilds from source documents on first use.
Audio caching and voice selection remain unchanged.

### Clarification without restarting the task

When an ambiguity or missing preference affects the result, Codex can call
`askai_clarify` with one to three questions and optional choices. The CLI accepts
a numbered choice or a written answer; the TUI provides selectable options and a
free-text field. Users can cancel the question without supplying an answer.

Execution pauses while the user answers, then continues in the same agent turn
and session. Completed actions are not replayed, and the waiting period does not
consume the host's turn timeout. Clarification answers do not grant permissions;
action approvals retain their own checks. Restart AskAI to load this feature;
existing Codex sessions need `/session reset` once to register the new tool.

### Agent readiness between questions

Session continuity and connection readiness are separate. Taius retains the agent
session, but the current connection manager closes the app-server process when
switching between execution and read-only review scopes. With persistent history,
the next question therefore requires connection preparation and session resume.
Each request also goes through validation and refinement. Document retrieval runs
when RAG is enabled and documents are available; web searches are agent tool
decisions, not a mandatory step for every question.

Keeping the connection and loaded session ready between messages is a proposed
optimization, not an implemented standby mode. It would reduce repeated local
setup while preserving permission boundaries. Consulting sources only when
needed is another possible improvement; it is not the current RAG policy.
Each new answer still requires remote model processing, so readiness does not
guarantee an immediate response or eliminate necessary searches. Latency gains
have not been measured. See [Performance](docs/PERFORMANCE.md) for the current
execution stages and timing logs, and the [Codex App Server documentation](https://learn.chatgpt.com/docs/app-server)
for session and turn lifecycle.

### AskAI commands through conversation

In Taius mode, spoken or typed requests such as "slash help", "barra help" or
"ative o ditado" can invoke the current app's commands. Codex has a compact
`askai_command` tool and requests the command catalogue or individual help only
when needed; the full help is not included in the initial context.

The tool returns live app state, zero-based voice catalogues and structured command
results with status, data and console output. Voice queries and selection run in
the current turn, so Codex can resolve "voice 12" without asking for its name.
Commands involving another inference or session/router changes (camera, dictation,
summarization, session, mode and usage) run after the agent turn ends. Their results
are available through `action=state` on the next turn. Direct slash commands use
the same result store. The app still displays command output and errors.
Codex consults current state first. After failures it uses `action=diagnostics`
for bounded, current-process command failure logs; logs never establish current
state or voice indices. Returned console output is limited to 16,000 characters
with an explicit truncation flag.
No second AskAI instance is launched. Cancellation prevents queued commands from
running. Commands retain their existing interaction and permission checks;
permission changes and factory settings reset must be performed directly by the
user with slash commands. Restart AskAI and use `/session reset` for an existing
Codex session to receive the new tool and orientation.

### Communication bus

User input, assistant replies, initial agent commentary and command results share
one communication bus. Each message carries an ID, UTC timestamp, application
session ID, kind and structured payload. CLI/TUI delivery uses the existing views;
command output remains visible live. Output chunks go only to the screen, while
the completed result is recorded once with its captured output.

The bus keeps the latest 100 messages in the running session. Codex can inspect
recent messages with `askai_command` using `action=state`. Command result queries
return at most ten results; diagnostics include destination delivery failures.
When conversation history is enabled, messages are also appended to
`${ASKAI_DIR}/sessions/communication/<session>-<run-id>.jsonl` and the normal
application log. With history disabled, payloads stay in memory and on screen;
the bus writes neither journal entries nor message payloads to the log. Failed
destinations are reported independently and do not stop the remaining deliveries.
Restart AskAI after updating to initialize the bus for the application session.

### Switch engine and model without restarting

```text
/engine list
/engine set codex
/model list
/model set <model-id-from-the-list>
```

`/engine list` shows the implemented engines (Codex and OpenAI). `/model list`
queries Codex's model catalogue, or lists the OpenAI models supported by AskAI.
Switches run between turns and keep the existing conversation context, STM,
speech providers and routing mode. Codex model changes also preserve its native
session and connection. Engine instances are retained during the running app,
so switching back to Codex reuses its connection and sessions. Each engine keeps
its saved model. Failed construction or invalid selection keeps the active engine.

OpenAI currently supports Chat/RAG; enter `/mode chat` or `/mode rag` before
`/engine set openai`. Taius orchestration requires Codex. Requests made through
`askai_command` queue engine/model commands until the agent turn finishes.
The communication bus carries the structured selection result and console output.
Response-cache identities include engine, model and mode; indexes are reopened
for the selected embedding space when needed. Context is retained without
truncation, so the selected model's context-window limits still apply.
