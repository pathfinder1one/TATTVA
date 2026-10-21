# Backend folder audit

Audited on 2026-10-21 after the backend implementation pass and local runtime checks.

## Inventory and checks

- 350 files under `backend/` at the time of this audit, excluding `.venv` and generated `__pycache__` files. This includes local runtime data and the synthetic smoke fixture.
- 0 zero-byte files.
- 106 Python source files; all passed `compileall`.
- 4 Python test files; `pytest app/tests/unit -q` passed 27 tests.
- Docker Compose runs under the isolated `tattva` project name and started the API, MongoDB, Qdrant and dedicated analysis worker. `/healthz` and `/readyz` both passed.
- Authenticated API smoke checks passed case creation, analysis run creation and same-key idempotent replay.
- A fabricated text upload, indexing and citation-returning search were checked as an end-to-end retrieval smoke flow.
- Python modules without executable statements are package `__init__.py` markers, not missing route, service, repository, provider, agent or worker implementations.

## Implemented backend behavior

- FastAPI application, liveness/readiness routes, request ID middleware, and request ID logging context.
- Case, membership, document, evidence, entity, relationship, search, graph, finding, run, event, voice, answer and report API boundaries.
- MongoDB repositories and indexes, durable run/task records, worker leases, cancellation, retries, audit events, and ordered run progress.
- Authenticated case-scoped polling and Server-Sent Events delivery for run progress.
- Case-scoped ingestion, immutable extracted-text/source versions, chunking, embeddings, Qdrant retrieval, and exact source-span validation.
- A case-authorized RAG answer endpoint that sends only validated retrieved passages to the configured core model and rejects citations outside that retrieved set.
- Deterministic bounded orchestration with source retrieval, graph-pattern summary, optional source-grounded extraction, citation-checked value discrepancy grouping, and balanced hypothesis suggestions. Hosted model tasks run only when the OpenAI-compatible URL, key, and model are configured.
- Strict candidate output schemas and exact-quote/source validation. Model candidates do not write or approve graph claims.
- Hypotheses require exact source spans on both supporting and opposing sides and remain unverified suggestions.
- Persisted source-linked finding candidates, owner/reviewer decisions, audit records, and evidence revalidation before report inclusion.
- Versioned report drafts stored in MongoDB, with authorized list/read routes and source evidence revalidation.
- Gemini Live WebSocket bridge with server-held key, bounded PCM input and session time, allowed-origin and case checks, typed message contracts, and four allowlisted case-scoped tools. Audio/transcripts are not persisted.
- A dedicated Mongo-backed analysis worker entry point; Docker Compose runs API and worker as separate services while local development can keep workers in the API process.
- Deterministic helpers for exact-name duplicate suggestions, explicit-value conflict grouping, structural graph metrics, integrity flags, and report assembly.
- Unit coverage for authentication validation, security helpers, planning and idempotent request semantics.

## Intentional empty-code files

Package `__init__.py` files contain only package documentation. They are normal markers, not missing modules. The unused Celery placeholder was removed because the implemented queue is MongoDB-backed and Celery is not a runtime dependency.

## Remaining deployment work

1. Expand automated integration, security and provider contract tests beyond the current unit suite and local manual smoke flows.
2. Select and configure the deployment identity provider, issuer, JWKS URL, audience and tenant claims. The current header identity deliberately fails closed outside development.
3. Supply valid provider credentials and chosen models, then run authenticated end-to-end core LLM and Gemini Live sessions. The exposed Gemini key from the chat must be revoked and replaced; it was not written to project files.
4. Define retention, consent, provider data handling, quotas, monitoring and deployment operations before any real investigation data is processed.

The Riva archive remains reference material. Its broad orchestration and voice tools were not copied; TATTVA keeps source-grounded outputs, case access checks and human review boundaries.
