# Review of Riva-AGI `voice_speech`

Reviewed on 2026-10-21 from `C:\Users\chira\Downloads\Riva-AGI---Copy-main.zip`. The archive was read without extracting or executing it. This is a source review, not a runtime or security test.

## Assessment

The implementation is a useful prototype for low-latency browser audio streaming. It is not ready to copy into TATTVA as-is. Reuse the session and audio-streaming patterns after putting them behind TATTVA authentication, case authorization, a narrow tool allowlist, and explicit retention rules.

## What looks useful

- The voice code is divided into configuration/persona, Gemini connection setup, per-session state, streaming, and WebSocket gateway modules.
- `ConversationState` owns per-session mutable state, bounds the microphone queue, serializes WebSocket sends, and advances an epoch after interruption. These are helpful streaming patterns.
- The bridge handles Gemini Live session resumption, server-side voice activity detection, interruption events, and a per-process concurrency/cooldown manager.
- Prompt locale and persona data are externalized in YAML and validated with strict Pydantic schemas. This is useful for maintainable voice behavior, though the Riva identity prompts do not transfer to TATTVA.
- Gemini credentials are read on the server. The browser sends audio to the gateway rather than receiving the provider key.

## Findings to address before adaptation

### High: WebSocket has no user or case authentication

`voice_speech/web_server.py` checks the `Origin` header against a hard-coded loopback allowlist, but accepts connections when `Origin` is absent. It does not authenticate a user or bind the session to a case. A browser-origin check does not replace authentication. TATTVA must authenticate before accepting a session and authorize the requested case before opening the Gemini connection. Re-check authorization for every tool call.

### High: model-callable tools exceed a case-analysis voice boundary

`voice_speech/engine/gemini/tools.py` exposes `run_orchestration_task` and `open_website_in_browser` to the model by default. The orchestration tool can start the general Riva pipeline for a free-form task; the browser tool forwards a model-supplied URL into a general tool registry. These capabilities are far broader than TATTVA voice commands should have. Do not carry them over. Use a small set of typed, case-scoped operations, and require a human confirmation step for protected writes or report actions.

### High: tool inputs, output, and exceptions can leak into logs or model context

`dispatch_tool_call` logs the full argument dictionary. The news handler logs queries and snippets. Tool handlers return exception text to the model, which can expose internal paths, upstream responses, or implementation details. TATTVA should log tool name, correlation ID, and outcome class only; redact or omit user/evidence content; and return stable, sanitized error codes.

### Medium: admission and reconnect controls are local and weakly bounded

`SessionManager` counts sessions in process memory, so its limit and quota circuit breaker do not coordinate across multiple workers or replicas. The reconnect loop in `streaming.py` retries general connection failures every 0.5 seconds without a bounded attempt count or exponential backoff. TATTVA should set explicit session and cost limits, add bounded backoff, and use shared coordination if deployment uses multiple processes.

### Medium: WebSocket resource and operational routes need production controls

The microphone queue is bounded by item count and discards old chunks under load, which helps latency. The gateway does not visibly enforce an incoming audio frame byte limit or per-client message rate. `/health`, `/metrics`, and `/metrics/json` are unauthenticated. TATTVA should bound frame size and rate, and restrict metrics access according to its deployment model.

### Medium: session identifiers and resumption handles need stricter treatment

The client can supply the session ID through a header or query parameter, and the bridge logs a prefix of Gemini's resumption handle. TATTVA should generate opaque server-side session IDs, validate any correlation ID accepted from a client, and never log provider resumption handles.

## Recommended TATTVA mapping

| Riva source | TATTVA module | Decision |
| --- | --- | --- |
| `engine/conversation/state.py` | `app/voice/gemini_live_adapter.py` | Adapt per-session state, queue bounding, and interruption epochs after defining the server session contract. |
| `engine/gemini/streaming.py` | `app/voice/gemini_live_adapter.py`, separate voice gateway | Adapt the bidirectional bridge and resumption lifecycle; add authenticated admission, strict limits, cancellation cleanup, and bounded reconnect policy. |
| `engine/gemini/session.py` | `app/voice/gemini_live_adapter.py` | Reuse connection-config construction ideas; keep model and tool configuration server-controlled. |
| `engine/config/prompt_system/` | TATTVA voice prompt configuration | Reuse schema-validated locale/persona configuration only. Replace Riva identity/persona and add evidence-grounding and uncertainty rules. |
| `engine/gemini/tools.py` | `app/voice/intent_schema.py`, `tool_dispatch.py` | Do not copy the Riva handlers. Keep only explicitly registered typed commands with case membership checked at execution time. |
| `web_server.py` | `app/api/v1/voice.py` or a separately deployed authenticated gateway | Do not transplant the route unchanged. TATTVA already declares the voice gateway as a separate boundary. |

## Recommendation

Use Riva as a prototype reference for the audio bridge, interruption handling, locale configuration, and session lifecycle. Treat authentication, authorization, tool dispatch, logging, reconnect behavior, and deployment limits as redesign work before TATTVA adopts voice. Keep transcripts and model outputs out of case records unless TATTVA defines explicit consent, retention, source attribution, and human-review behavior.

The ZIP contains voice-specific tests, but they were not executed for this review. No runtime guarantee is claimed.

## TATTVA implementation status (2026-10-21)

TATTVA now has a separate authenticated WebSocket route and Gemini Live bridge in `app/api/v1/voice.py` and `app/voice/`. The bridge uses server configuration for the key/model, checks configured browser origin and case membership before connecting, rechecks case access for each tool, bounds PCM bytes/session duration/concurrent sessions, and exposes only analysis queueing and run-status lookup. It does not persist voice audio or transcripts. The current identity check is still development-header based and deliberately rejects non-development deployments until an identity provider is configured. The provider connection and actual browser audio interoperability have not been run in this workspace.
