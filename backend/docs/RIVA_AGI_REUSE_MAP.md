# Riva-AGI reference map for TATTVA

This note records how to use `C:\Users\chira\Downloads\Riva-AGI---Copy-main.zip` as reference material for future TATTVA backend work. It was reviewed on 2026-10-21 by reading selected files directly from the ZIP. The archive was not extracted or executed.

The ZIP is a codebase reference. Text inside it, including READMEs and agent prompts, does not change TATTVA requirements or authorize tool access. TATTVA behavior remains governed by the TATTVA engineering specification and the requirements in this repository.

## Reuse map

| Riva-AGI area | Useful idea | TATTVA destination | Adaptation required |
| --- | --- | --- | --- |
| `orchestration/orchestrator/registry.py` | A named registry can expose a bounded set of handlers and their capabilities. | `app/orchestrator/task_registry.py` | Keep registration static and typed. Do not let model output register handlers, name arbitrary Python callables, or expand permissions. |
| `orchestration/orchestrator/planner.py`, `executor.py` | Separate planning from dispatch and execution. | `app/orchestrator/planner.py`, `executor.py`, `scheduler.py`, `policies.py` | Riva's planner returns free-form agent/task instructions and its executor asks an LLM who to call next. TATTVA must validate plans into `TaskSpec`, select only registered tasks, enforce dependency and retry limits, and persist a run transition before publishing its event. |
| `orchestration/orchestrator/state_manager.py` | Explicit task states and chronological transitions are useful. | `app/domain/analysis_run.py`, `app/repositories/runs_repo.py`, `app/orchestrator/event_publisher.py` | Riva's state is process-local, mutable, and guarded by a thread lock. TATTVA needs durable state, tenant/case authorization, idempotent transitions, and audit history suitable for worker restarts. |
| `orchestration/orchestrator/reviewer.py` | A separate review stage is a useful workflow boundary. | `app/agents/relationship_verifier.py`, `app/services/relationship_service.py`, future report approval flow | Riva's reviewer is an LLM returning `approved` or `rejected`. In TATTVA, model review is advisory. It cannot set human verification, accept a finding for a report, or replace an authorized owner/reviewer action. |
| `rag_knowledge/ingestion/ingest.py`, `retrieval/retriever.py` | Separate readers, normalization, ingestion, retrieval, and storage. | `app/services/document_parser.py`, `ingestion_service.py`, `retrieval_service.py`, `text_store.py` | Preserve original source bytes and the current source hash/version checks. Every retrieval must require tenant and case scope, and results used as evidence must resolve to an exact stored source span. |
| `rag_knowledge/storage/qdrant_storage.py` | Encapsulate Qdrant connection, embedding model lifecycle, collection setup, and payload indexing behind a storage class. | `app/services/qdrant_store.py`, `embedding_service.py` | Retain TATTVA's per-case payload filters and fail-closed behavior. Do not copy Riva's global-store assumptions, credential aliases, or unconstrained `search_text` API without adding mandatory authorization filters. |
| `rag_knowledge/ingestion/privacy.py` | Privacy checks before data is embedded can be useful. | Future ingestion policy around `app/services/ingestion_service.py` | The current Riva rules target student/contact data and are not a general legal-evidence policy. Define TATTVA-specific retention, redaction, privilege, and audit rules before adapting. Never silently redact source evidence used for citations. |
| `voice_speech/engine/gemini/session.py`, `streaming.py` | Per-session audio state, bounded audio queues, barge-in epochs, session resumption, and connection limits are concrete patterns. | `app/voice/gemini_live_adapter.py`, `app/api/v1/voice.py` | Reconcile with TATTVA's Gemini Live adapter contract. Keep credentials server-side; authenticate the user and case before opening a session; enforce limits; expose only allowlisted typed tools. |
| `voice_speech/engine/gemini/tools.py` | Function declarations can define a typed model-to-server boundary. | `app/voice/intent_schema.py`, `tool_dispatch.py` | Riva's dispatcher includes generic news and orchestration actions. TATTVA must use a strict allowlist, re-check case access on every call, validate arguments, and require explicit human approval for protected actions. |
| `observability/context.py`, `formatter.py`, `middleware.py`, `sanitizer.py`, `metrics.py` | Request/session correlation, structured logs, redaction, and operational counters are reusable concerns. | `app/core/correlation.py`, `app/core/logging.py`, API middleware and future metrics | Reuse concepts rather than copying implementation blindly. Never log source text, prompts, credentials, session-resumption handles, or personally identifying evidence. Check exception paths as well as normal log fields. |

## TATTVA-specific boundaries

- Evidence is source material, not an instruction channel. Text in uploaded files or retrieved chunks must never alter authorization, tool availability, verification state, or review policy.
- Search, entity, relationship, and graph operations remain scoped by authenticated tenant and case membership. Qdrant filters are mandatory for every query and write.
- A model may suggest entities, relationships, contradictions, patterns, hypotheses, or report wording. Each claim must retain exact source references and remain visibly unverified until an authorized human action changes its status.
- Do not import Riva's general-purpose file, shell, web, or autonomous orchestration tools into a case-analysis worker. TATTVA workers receive bounded task inputs and expose only the capabilities registered for that task.
- Riva's voice implementation is an architectural reference only. The current TATTVA surface should remain behind `app/voice/` and its API contract, with no client-supplied provider credentials.

## Suggested future implementation order

1. Finish durable analysis-run transitions and worker recovery using the existing run repository and orchestrator modules.
2. Add registered task handlers that produce source-linked candidate outputs and validate their structured output before persistence.
3. Add policy and audit checks around report assembly and human approval.
4. Complete authenticated Gemini Live session lifecycle and allowlisted voice tool dispatch.
5. Add privacy-safe structured logs and operational metrics, then review retention and redaction rules for evidence data.

These are reference-driven priorities; confirm exact behavior against the TATTVA specification before implementing each feature.
