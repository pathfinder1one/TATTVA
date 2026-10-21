# TATTVA Backend: Frontend Integration Guide

This guide maps the implemented backend to frontend screens and workflows. The live OpenAPI schema is the contract source of truth; use `/docs` or `/openapi.json` when a field detail is not listed here.

## 1. Connect to the API

| Setup | API base URL | API documentation |
|---|---|---|
| Docker Compose in this backend folder | `http://localhost:8002` | `http://localhost:8002/docs` |
| Local Uvicorn (README command) | `http://localhost:8000` | `http://localhost:8000/docs` |

REST routes use `/api/v1`. Health routes are at the root: `GET /healthz` and `GET /readyz`. Docker maps host port `8002` to container port `8000`, keeping the existing project on port 8000 separate.

For local browser development, the default allowed frontend origin is `http://localhost:3000`. If your frontend runs on a different origin, add it to backend `ALLOWED_ORIGINS` and restart the API. Send JSON requests with `Content-Type: application/json`; uploads use `multipart/form-data`.

### Authentication

In local development, send these headers on every REST call:

```http
X-User-Id: local-investigator
X-Tenant-Id: local-tenant
```

Use a stable user and tenant ID while developing so case ownership remains consistent. This identity mode is enabled only when the backend is in development and local auth is enabled.

In a deployed environment, use `Authorization: Bearer <OIDC access token>`. The backend verifies RS256 tokens against its configured JWKS URL, issuer, and audience. By default, the user ID comes from the `sub` claim and the tenant ID from `tenant_id`. Every case-specific request also checks that the authenticated user belongs to that case. Do not put Gemini or other model-provider keys in frontend code.

## 2. Recommended frontend workflow

1. **Case dashboard:** call `GET /api/v1/cases`; create a case with `POST /api/v1/cases`; open details with `GET /api/v1/cases/{case_id}`.
2. **Evidence library:** upload each file to `POST /api/v1/cases/{case_id}/documents` as multipart field `file`. Refresh with `GET .../documents`. After upload, explicitly call `POST .../documents/{document_id}/index`; show returned status and chunk count. Indexing may take longer on first use while the embedding model downloads.
3. **Search and source viewer:** send a query to `POST .../search`. Render citations with filename, exact passage, and source offsets. For a current authorized source span, call `GET .../documents/{document_id}/chunks/{chunk_id}`. `retrieval_score` is cosine similarity for ranking; it is not evidence confidence.
4. **Analysis workspace:** create a run with `POST .../analysis-runs`, then show status/tasks from the response or poll `GET .../analysis-runs/{run_id}`. Prefer the event stream for progress; the ordered event list is also available. Offer cancel while active.
5. **Evidence graph:** load `GET .../graph` for graph nodes, links, structural metrics, and integrity flags. Use entities and relationships routes to add or inspect records. A new relationship starts as a candidate. Verification and report review are separate user actions.
6. **Findings and report review:** list/create findings, collect an explicit reviewer decision, and create a report draft from a run. Label generated material as a draft and show its limitations and review requirement.
7. **Question answering:** optionally call `POST .../answers` when the backend model provider is configured. If it returns `503`, explain that answer synthesis is unavailable; use `/search` to show passages without inventing an answer.

## 3. API endpoint map

All routes below are under `/api/v1` unless marked as health. Path parameters in braces are IDs returned by the backend.

| Frontend feature | Method and path | Request / result |
|---|---|---|
| Liveness | `GET /healthz` | `{"status":"ok"}` when process responds. |
| Dependency readiness | `GET /readyz` | MongoDB/index/Qdrant readiness; `503` means not ready. |
| Cases | `GET /cases`, `POST /cases` | Lists caller's cases; create body: `case_number`, `title`, optional `description`. |
| Case details | `GET /cases/{case_id}` | One case, subject to membership. |
| Documents | `GET /cases/{case_id}/documents`, `POST /cases/{case_id}/documents` | Upload one multipart `file`; PDF, TXT, DOCX, JSON, CSV; default max 25 MB. |
| Index document | `POST /cases/{case_id}/documents/{document_id}/index` | No body; returns status, version IDs, chunk count, character count. |
| Read source chunk | `GET /cases/{case_id}/documents/{document_id}/chunks/{chunk_id}` | Exact source text and offsets for current index version. |
| Read evidence quote | `GET /cases/{case_id}/evidence/{evidence_id}` | Exact authorized quote and source metadata. |
| Semantic search | `POST /cases/{case_id}/search` | Body `{"query":"...","top_k":5}`; top_k 1–20, default 5; retrieval citations only. |
| Grounded answer | `POST /cases/{case_id}/answers` | Same body as search; requires configured core LLM provider. |
| Entities | `GET`, `POST /cases/{case_id}/entities` | Entity create body shown below; similarly named entities are not auto-merged. |
| Relationships | `GET`, `POST /cases/{case_id}/relationships` | New relationship is a candidate. |
| Verify relationship | `POST /cases/{case_id}/relationships/{relationship_id}/verify` | `{"decision":"supported|disputed|insufficient_evidence","rationale":"..."}`. |
| Review relationship | `POST /cases/{case_id}/relationships/{relationship_id}/review` | `{"decision":"accepted_for_report|rejected|needs_more_evidence|not_reviewed","rationale":"..."}`; acceptance requires supported verification. |
| Case graph | `GET /cases/{case_id}/graph` | Entities, relationships, structural metrics, integrity flags. Metrics do not measure evidence strength. |
| Findings | `GET`, `POST /cases/{case_id}/findings` | Create body shown below; findings need review. |
| Review finding | `POST /cases/{case_id}/findings/{finding_id}/review` | Same decision/rationale shape as relationship review. |
| Analysis runs | `GET`, `POST /cases/{case_id}/analysis-runs` | Creation requires `Idempotency-Key`; body `{"query":"...","top_k":5}`; returns `202`. |
| Read/cancel run | `GET /cases/{case_id}/analysis-runs/{run_id}`, `POST .../{run_id}/cancel` | Run includes status, tasks, result_summary. Cancel may return `409` if terminal. |
| Run event list | `GET /cases/{case_id}/analysis-runs/{run_id}/events?after_seq=0&limit=100` | Ordered event page; `limit` 1–500. |
| Run event stream | `GET /cases/{case_id}/analysis-runs/{run_id}/events/stream?after_seq=0` | Server-Sent Events; reconnect from last received sequence. |
| Create report draft | `POST /cases/{case_id}/analysis-runs/{run_id}/report-draft` | No body; persists a versioned report draft. |
| List/read report drafts | `GET .../{run_id}/reports`, `GET .../{run_id}/reports/{report_id}` | Saved draft versions. |
| Voice session | `WS /cases/{case_id}/voice` | Optional Gemini Live WebSocket; see limitation below. |

List endpoints currently return complete arrays; pagination is not implemented. Treat IDs as opaque strings. Use `/openapi.json` for complete schemas.

## 4. Request examples

### Create a case

```http
POST /api/v1/cases
Content-Type: application/json
X-User-Id: local-investigator
X-Tenant-Id: local-tenant
```

```json
{"case_number":"CASE-001","title":"Sample investigation","description":"Synthetic development case"}
```

### Upload, then index

```javascript
const form = new FormData();
form.append("file", file);

const uploaded = await fetch(`${API_BASE}/api/v1/cases/${caseId}/documents`, {
  method: "POST",
  headers: authHeaders, // Do not set Content-Type; browser adds the multipart boundary.
  body: form,
});
const document = await uploaded.json();

const indexed = await fetch(
  `${API_BASE}/api/v1/cases/${caseId}/documents/${document.document_id}/index`,
  { method: "POST", headers: authHeaders },
);
```

Document statuses: `uploaded`, `indexing`, `indexed`, `indexing_failed`, `quarantined`. Upload alone does not make a document searchable.

### Search

```http
POST /api/v1/cases/{case_id}/search
Content-Type: application/json
X-User-Id: local-investigator
X-Tenant-Id: local-tenant
```

```json
{"query":"Who was reported using the vehicle?","top_k":5}
```

Each citation has `citation_id`, `document_id`, `filename`, `chunk_id`, `text`, `start_offset`, `end_offset`, `retrieval_score`, and `score_type`. Preserve citation IDs when showing answer citations. Search responds with `result_type: "retrieval_only"` and limitations.

### Start an analysis run

```http
POST /api/v1/cases/{case_id}/analysis-runs
Content-Type: application/json
Idempotency-Key: analysis-CASE001-unique-001
X-User-Id: local-investigator
X-Tenant-Id: local-tenant
```

```json
{"query":"Identify people linked to the vehicle","top_k":5}
```

Use a fresh 8–128 character idempotency key per new logical run; reuse it only to retry the same request. Reusing the key with a different payload can return `409 Conflict`.

### Create evidence-linked entities and relationships

Entity:

```json
{"entity_type":"person","display_name":"Example Person","source_spans":[{"chunk_id":"<chunk_id>","start_offset":0,"end_offset":24}]}
```

Relationship:

```json
{"subject_entity_id":"<entity_id>","predicate":"associated_with","object_entity_id":"<entity_id>","source_spans":[{"chunk_id":"<chunk_id>","start_offset":0,"end_offset":24}]}
```

Offsets are character positions into the exact indexed source chunk. Fetch the chunk text and let a user select the span; do not guess offsets. Entity types: `person`, `organization`, `phone`, `email`, `address`, `vehicle`, `account`, `event`, `location`, `device`, `other`.

### Create a finding

```json
{"finding_type":"pattern","statement":"A concise, evidence-linked statement","evidence_ids":["<evidence_id>"]}
```

Finding types: `relationship`, `contradiction`, `pattern`, `hypothesis`. Evidence IDs must be unique; at least one is required.

## 5. Statuses and review states

Analysis run statuses: `queued`, `running`, `awaiting_review`, `completed`, `completed_with_warnings`, `failed`, `cancel_requested`, `cancelled`. A run with warnings may still contain useful retrieval output. Show `result_summary` warnings and task errors; `completed_with_warnings` is neither a clean success nor a failed run.

Relationship verification states: `candidate`, `supported`, `disputed`, `insufficient_evidence`, `verification_failed`. Review states for relationships and findings: `not_reviewed`, `accepted_for_report`, `rejected`, `needs_more_evidence`. Keep verification distinct from review: evidence support and approval for report inclusion are different decisions.

Report drafts identify themselves with `report_type: "machine_generated_draft"` and `review_required: true`. They can include source citations, candidate mentions/relationships, potential value discrepancies, hypotheses, graph pattern summary, reviewed findings, and limitations. Candidate sections are unverified suggestions. A draft is not an approved or exported report.

## 6. Errors to handle

| HTTP status | Typical meaning | Suggested UI behavior |
|---|---|---|
| `401` | Missing/invalid identity or expired token | Prompt sign-in or refresh session. |
| `403` / `404` | Case access denied or record unavailable | Show access/not-found state without exposing other case data. |
| `409` | Idempotency conflict or action invalid in current state | Explain conflict and refresh state before retry. |
| `413` | File exceeds configured size limit | Ask for a smaller file. |
| `415` | Unsupported extension, missing media type, or extension/type mismatch | Show allowed formats and check browser file metadata. |
| `422` | Validation error or empty upload | Show field validation where possible. |
| `502` | Answer provider returned invalid/unmatched citations | Show answer-generation error; search may still work. |
| `503` | Dependency, identity provider, answer provider, or voice provider unavailable/unconfigured | Show unavailable state and allow retry. |

FastAPI validation responses contain `detail`; HTTP errors generally provide a human-readable `detail` string. Responses also include `X-Request-Id`; include this ID in bug reports.

## 7. Current integration limits

- **Answer synthesis:** needs backend `CORE_LLM_BASE_URL`, `CORE_LLM_API_KEY`, and `CORE_LLM_MODEL`. When unset, `/answers` responds `503`; `/search` remains usable.
- **Analysis enrichment:** without the core LLM provider, runs can retrieve evidence and produce deterministic summaries, but model-assisted candidate extraction is unavailable. Inspect `result_summary` and task output before deciding what to show.
- **Browser voice:** the WebSocket supports local development identity headers or a bearer token in the upgrade request. Native browser `WebSocket` cannot set arbitrary `Authorization` or `X-User-Id`/`X-Tenant-Id` headers. Browser voice needs a browser-compatible auth handoff (such as a short-lived WebSocket ticket or secure cookie) before production use. It also needs backend Gemini Live settings and an allowed `Origin`. Never expose the Gemini key in the frontend.
- **Pagination and editing:** list endpoints return full arrays. The API offers create/review operations for graph records, but no general update/delete endpoints for cases, documents, entities, or findings.
- **Data:** the backend README says MVP data must be synthetic. Keep development uploads synthetic.

## 8. Suggested screens

| Screen | Backend connections | Main UI states |
|---|---|---|
| Case dashboard/detail | cases | loading, empty, create form, case list, access error |
| Documents/evidence | documents, indexing, evidence/chunks | upload progress, uploaded, indexing, indexed, failure, source viewer |
| Search | search, chunks/evidence | query, ranked passages, no matches, retrieval limitations |
| Analysis | runs, events/SSE, cancel | queued, running, warnings, completed, failed, cancelled |
| Graph | graph, entities, relationships | candidate edges, verification result, review decision, integrity flags |
| Findings/reports | findings, report drafts | unreviewed finding, decision/rationale, draft limitations, version history |
| Ask case | answers | provider unavailable, answer, citations, insufficient evidence |
| Voice (later) | WebSocket | unavailable until browser auth handoff and provider setup are complete |

## 9. Contract discovery and startup

- Open `http://localhost:8002/docs` to try requests and inspect schemas when using Docker Compose.
- Fetch `http://localhost:8002/openapi.json` to generate frontend types or an API client. Prefer this live schema over treating examples here as exhaustive schemas.
- Check `GET /readyz` before starting a workflow. `/healthz` indicates process liveness; `/readyz` checks backend dependencies.
- The backend README explains startup. Use this backend folder's Compose project so TATTVA remains isolated from the older MuktiVersAIO stack.
