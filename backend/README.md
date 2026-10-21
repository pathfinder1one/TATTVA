# TATTVA backend

This is the backend foundation for the TATTVA evidence-first case analysis workspace. It uses FastAPI, MongoDB and local opaque-key file storage. MVP data must be synthetic. Development identity headers work only when `APP_ENV=development`; other environments require a verified OIDC bearer token and case membership.

## Run the complete local stack

From this directory in PowerShell:

```powershell
Copy-Item .env.example .env
# Set APP_SECRET_KEY to a long random development value in .env.
docker compose up --build -d
docker compose ps
```

The Compose stack runs MongoDB, Qdrant, the FastAPI server and a separate Mongo-backed analysis worker. TATTVA publishes the API at `http://localhost:8002/docs` and readiness at `http://localhost:8002/readyz`, leaving port 8000 available for the existing MuktiVersAIO project. Stop this stack with `docker compose down` (volumes are retained). Do not use `--remove-orphans`; other projects may have containers with similar Compose labels.

## Run locally without Docker

1. Create and activate a Python virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. For unit tests, also install `pip install -r requirements-dev.txt` and run `pytest app/tests/unit -q`.
4. Copy `.env.example` to `.env` and set a development secret.
5. Start MongoDB and Qdrant at the configured URIs.
6. From this directory, run `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`.

`GET /healthz` reports process liveness. `GET /readyz` checks MongoDB indexes and Qdrant readiness. Interactive API documentation is available at `/docs` in local development.

## Foundation API

For frontend connection details, workflows, request examples, statuses and current integration limits, see [the frontend integration guide](docs/FRONTEND_INTEGRATION_GUIDE.md).

- `POST /api/v1/cases` creates a case and owner membership.
- `GET /api/v1/cases` lists cases available to the current development identity.
- `GET /api/v1/cases/{case_id}` returns an authorized case.
- `POST /api/v1/cases/{case_id}/documents` streams and stores an allowlisted source file, recording SHA-256 and processing status.
- `GET /api/v1/cases/{case_id}/documents` lists authorized document metadata.
- `POST /api/v1/cases/{case_id}/documents/{document_id}/index` extracts text, stores an immutable parser/source version and chunks, embeds them, and indexes their IDs in Qdrant.
- `POST /api/v1/cases/{case_id}/search` returns authorized semantic retrieval matches with exact stored text and offsets. It does not synthesize an answer or assert that a relationship is supported.
- `POST /api/v1/cases/{case_id}/answers` synthesizes a concise answer from authorized retrieved passages when the core model is configured. Returned citation IDs are restricted to the retrieved passages; unsupported questions are marked as insufficient evidence.
- `GET /api/v1/cases/{case_id}/documents/{document_id}/chunks/{chunk_id}` resolves a chunk to its current authorized source span.
- `POST /api/v1/cases/{case_id}/entities` creates a distinct entity and source-linked mentions; similarly named entities are never merged automatically.
- `POST /api/v1/cases/{case_id}/relationships` creates a candidate relationship with validated source spans. It remains a candidate until a case owner or reviewer verifies it.
- `POST /api/v1/cases/{case_id}/relationships/{relationship_id}/verify` records a human verification decision and rationale after revalidating its immutable evidence spans.
- `POST /api/v1/cases/{case_id}/relationships/{relationship_id}/review` records the separate report-review state. `accepted_for_report` requires `verification_status=supported`.
- `GET /api/v1/cases/{case_id}/evidence/{evidence_id}` returns the exact authorized quote and offsets for an evidence record.
- `GET /api/v1/cases/{case_id}/graph` returns recorded entities, candidate/verified links, and transparent structural counts.
- `POST /api/v1/cases/{case_id}/analysis-runs` queues source retrieval and, when the hosted core model is configured, source-grounded candidate extraction.
- `GET /api/v1/cases/{case_id}/analysis-runs` lists authorized runs; `GET .../{run_id}` returns task state and retrieved citations.
- `POST /api/v1/cases/{case_id}/analysis-runs/{run_id}/cancel` cancels a queued run or requests cancellation of an active run.
- `GET /api/v1/cases/{case_id}/analysis-runs/{run_id}/events?after_seq=0` reads ordered persisted progress events.
- `GET /api/v1/cases/{case_id}/analysis-runs/{run_id}/events/stream` streams ordered progress using Server-Sent Events.
- `POST /api/v1/cases/{case_id}/analysis-runs/{run_id}/report-draft` creates an audited, persisted report draft version.
- `GET /api/v1/cases/{case_id}/analysis-runs/{run_id}/reports` lists saved draft versions; `GET .../reports/{report_id}` retrieves one.
- `GET` and `POST /api/v1/cases/{case_id}/findings` list and create source-linked findings; `POST .../{finding_id}/review` records owner/reviewer decisions.
- `WS /api/v1/cases/{case_id}/voice` opens a case-authorized Gemini Live voice session when configured. Its allowlisted tools start analysis, read status, request cancellation, and create a source-checked report draft for review.

After upload, explicitly index the document. The first call can take longer while FastEmbed downloads its configured model into `data/embedding_cache`.

Create an analysis run with the same case-scoped identity headers. Mongo-backed workers record ordered progress events; task output includes source citations and, when configured, exact-quote-validated entity and relationship candidates.

Candidate extraction is enabled only when `CORE_LLM_BASE_URL`, `CORE_LLM_API_KEY`, and `CORE_LLM_MODEL` are set for an OpenAI-compatible chat-completions endpoint. Without all three, the planner queues retrieval only. Provider credentials stay in the backend environment; provider output is schema-validated and must resolve to exact retrieved quotes before it appears in run output.

```http
POST /api/v1/cases/{case_id}/analysis-runs
Content-Type: application/json
Idempotency-Key: analysis-20261021-demo01
X-User-Id: local-investigator
X-Tenant-Id: local-tenant

{"query": "Who was reported using the vehicle?", "top_k": 5}
```

```http
POST /api/v1/cases/{case_id}/documents/{document_id}/index
X-User-Id: local-investigator
X-Tenant-Id: local-tenant
```

Search only returns source matches. Its `retrieval_score` is a vector similarity value and must not be interpreted as evidence strength or a relationship confidence.

```http
POST /api/v1/cases/{case_id}/search
Content-Type: application/json
X-User-Id: local-investigator
X-Tenant-Id: local-tenant

{"query": "Who was reported using the vehicle?", "top_k": 5}
```

For local calls, set `X-User-Id` and `X-Tenant-Id`. In non-development environments configure `AUTH_JWKS_URL`, `AUTH_ISSUER`, and `AUTH_AUDIENCE`; identity and tenant claim names default to `sub` and `tenant_id` and can be changed with `AUTH_USER_ID_CLAIM` and `AUTH_TENANT_ID_CLAIM`. Production JWKS and issuer URLs must use HTTPS, and tokens are verified with RS256. WebSocket clients pass the bearer token in the upgrade request's `Authorization` header. Every case operation also checks case membership and tenant ownership.

## Structure

The application is organized according to the proposed engineering specification. API routes delegate to services, repositories own MongoDB operations, and domain types remain independent of provider code. The generic OIDC verifier is implemented; the deployment must still provide the identity issuer, JWKS URL, audience and claim mappings.

```text
backend/
  app/
    api/v1/          case, document, evidence, analysis, report, finding and voice routes
    core/            configuration-independent app concerns
    domain/          records, IDs and status vocabulary
    schemas/         request, response and event contracts
    repositories/    MongoDB access and index bootstrap
    services/        case, document, evidence, analysis and report business logic
    llm/             provider interface and output validation boundary
    orchestrator/    bounded task planning and execution boundary
    agents/          typed specialist handlers
    workers/         background queue entry points
    voice/           separate Gemini Live integration boundary
    tests/           unit, integration, security and evaluation suites
  migrations_or_indexes/
  sample_data/
  docker-compose.yml
```

The analysis worker runs retrieval and can run model-assisted candidate extraction when the OpenAI-compatible core provider is configured. Extracted candidates remain in the run output and are not written to the evidence graph. The case graph exposes structural metrics and data-integrity flags; these do not indicate evidence strength. Report drafts are versioned in MongoDB and include only revalidated citations and findings explicitly accepted by an authorized reviewer.

For future orchestration, retrieval, voice and observability work, see [the Riva-AGI reference map](docs/RIVA_AGI_REUSE_MAP.md). The orchestration, RAG, and voice implementations have separate [orchestration review](docs/ORCHESTRATION_REVIEW.md), [RAG review](docs/RAG_KNOWLEDGE_REVIEW.md), and [voice review](docs/VOICE_SPEECH_REVIEW.md) documents.

## Current boundary

The orchestration backend persists a bounded task DAG in MongoDB, runs it with worker leases, scoped retrieval, recorded-graph structural summary, optional model-assisted extraction, deterministic candidate-value discrepancy grouping, balanced hypothesis suggestions, retries, cancellation, ordered run events and SSE delivery. Extraction outputs are validated against strict schemas and must cite exact quotes from retrieved source passages. Hypotheses require exact source spans on both the supporting and opposing sides. All generated claims remain unverified run output and are not written to the evidence graph. Discrepancy groups cite retrieval passages and are review leads, not confirmed contradictions. Findings have a separate owner/reviewer decision workflow; accepted findings are revalidated before inclusion in a persisted draft report version. Report citations are revalidated against the currently indexed source before persistence. Run status is `completed_with_warnings` to mark the human-review boundary. Retrieval uses a multilingual local embedding model and Qdrant. Extracted text versions are immutable files under the configured source storage root; MongoDB stores version metadata and chunks. Do not upload real investigation records until a deployment identity provider, retention rules, provider data handling and operating controls are approved.

### Voice gateway

Set `GEMINI_API_KEY` and `GEMINI_LIVE_MODEL` to enable the optional voice WebSocket. The API key stays on the server. The local gateway requires the configured allowed `Origin`, `X-User-Id`, `X-Tenant-Id`, and existing case membership. Production use is disabled until a deployment authentication provider replaces local header identity. The client sends JSON text messages (`{"type":"text","text":"..."}`), or 16 kHz mono signed 16-bit little-endian PCM as base64 (`{"type":"audio","data":"...","mime_type":"audio/pcm;rate=16000"}`). The gateway returns JSON audio chunks, transcriptions and status messages. Its tools are limited to starting analysis, reading run status, requesting cancellation, and creating a report draft for the current case. Audio and transcripts are not persisted; operational tool calls are audited.
