# Review of Riva-AGI `rag_knowledge`

Reviewed on 2026-10-21 from `C:\Users\chira\Downloads\Riva-AGI---Copy-main.zip`. The archive was read without extracting or executing it. This is a source review, not a runtime, privacy, or retrieval-quality test.

## Assessment

Riva's RAG subsystem is a useful single-organization knowledge assistant, especially as a reference for separating ingestion readers, privacy checks, retrieval, vector storage, and answer synthesis. It is not a safe drop-in for TATTVA case evidence. It has no tenant/case boundary, does not retain exact source spans for citations, and stores full document content in Qdrant payloads. Keep TATTVA's current source-version and case-scoped retrieval design.

## What looks useful

- The package separates `ingestion/`, `retrieval/`, `storage/`, and `clients/`, which is easy to navigate and replace by layer.
- The Qdrant wrapper centralizes collection setup, payload indexes, embedding, and upserts. Its batch retry and timeout handling are useful operational ideas, subject to bounded retry and async-worker design.
- Ingestion supports text, PDF, DOCX, images/OCR, JSON, and tabular data. It includes an opt-in cloud OCR path and a dry-run mode.
- The privacy gate scans text destined for embedding and can fail closed or opt into redaction. The prompt says to treat retrieved context and user text as untrusted instructions and sets context/query size limits.
- The Gemini client has a timeout, bounded output tokens, and model fallback configuration. These are useful service controls when adapted to TATTVA's provider boundary.

## Findings to address before adaptation

### High: retrieval is global and has no tenant or case filters

`rag_knowledge/storage/qdrant_storage.py` filters only on `is_active`. `search_text` and `list_documents` do not accept an authorization scope. This fits a single shared knowledge base, but would expose cross-case records if reused for investigations. TATTVA must keep tenant and case filters mandatory on every Qdrant query and write, and independently verify returned IDs against authorized Mongo records.

### High: direct identifier fallback bypasses the active-record filter

In `search_text`, the semantic search applies `is_active=True`, but the fallback for an identifier token uses Qdrant `retrieve(ids=...)` directly without that filter. A matching inactive point may therefore be returned by the fallback. TATTVA should avoid direct vector-store record retrieval for identifiers; route ID lookups through an authorized repository query and validate active source version.

### High: it has no exact source citation contract

Riva's ingestion converts files into knowledge documents and Qdrant payloads containing title, summary, content, aliases, keywords, and metadata. Results return a synthesized string or a whole document's content without source offsets, page/row locators, immutable parser version, or hash-checked text span. Its PDF loader also replaces non-ASCII characters with `-`, which loses original-language text and source fidelity. TATTVA must preserve the original source, store immutable extracted text versions, keep stable offsets and units, and return exact validated spans with citations.

### High: complete extracted content is stored in Qdrant payloads

`upsert_documents` writes full document content and metadata as point payloads. The privacy gate is useful defense in depth, but regex and known-value scans are not a comprehensive legal-evidence data policy. TATTVA should keep source text in its controlled source store and vector payloads limited to opaque IDs plus tenant/case/version metadata. Access to source text should go through case authorization and integrity checks.

### Medium: privacy handling is specific to student datasets

The `StudentEntityJoiner`, safe identifier rules, column heuristics, and PII checks are tailored to student records. This is not a general privilege, retention, or sensitive-evidence policy. The privacy gate's failure message includes detected private values, which can leak those values if exception details reach logs or CLI output. Adapt the fail-closed concept, but use TATTVA-specific policy and sanitized diagnostics. Preserve evidence used for citations; do not silently redact source records.

### Medium: RAG prompt instructions do not provide evidence verification

`rag_knowledge/prompts.py` includes useful anti-injection wording, delimiter sanitation, and context/query limits. These are model instructions, not an authorization boundary or proof that context is safe. `RAGService` sends retrieved content to Gemini and returns plain generated text without citation IDs or exact source spans. TATTVA should treat retrieved text as untrusted data, keep outputs advisory, validate structured claims, and attach exact source evidence before presenting findings.

### Medium: query/content logging and fallback behavior need tighter privacy controls

The retriever and service log user queries, and retrieval errors include the query and exception details. The synthesis client logs upstream HTTP response text, although truncated. These can carry names or other sensitive case data. TATTVA should log correlation IDs, operation names, counts, and sanitized failure classes rather than source text, user queries, prompt content, or raw provider responses.

## Comparison with current TATTVA backend

TATTVA already uses a stronger evidence-oriented design in `app/services/ingestion_service.py`, `retrieval_service.py`, `qdrant_store.py`, and `text_store.py`:

- Qdrant queries require tenant and case filters; returned payloads are checked again against those values.
- Qdrant points contain opaque document/chunk/source-version IDs and unit metadata, not extracted document text.
- Mongo chunk metadata and immutable extracted text versions are checked against the active document version and source hash before a citation is returned.
- The search endpoint returns exact text and offsets from the stored source version; it does not synthesize a model answer.
- The parser normalizes line endings while preserving Unicode text, rather than rewriting non-ASCII characters.

Current format coverage is narrower than Riva's: TATTVA supports PDF, TXT, DOCX, JSON, and CSV, but has no image OCR, XLSX/TSV, or format-specific page/table extraction for all supported types yet. Add those only with exact source locators, parser versioning, immutable text, and the same case-scoped authorization checks.

## Recommended reuse decisions

| Riva source | TATTVA destination | Decision |
| --- | --- | --- |
| `ingestion/readers/word.py`, `ingestion/readers/ocr.py` | `app/services/document_parser.py` or focused reader modules | Use as parser design references for heading/table units and OCR confidence metadata. Preserve Unicode and exact page/table/row provenance; do not reuse reconstructed content as a citation without source locators. |
| `ingestion/privacy.py` | Future TATTVA ingestion policy service | Reuse the pre-indexing gate concept. Replace student-specific rules, avoid sensitive values in errors, and make retention/redaction decisions explicit. |
| `storage/qdrant_storage.py` | `app/services/qdrant_store.py`, `embedding_service.py` | Reuse the adapter boundary, health handling, and bounded retry ideas. Keep mandatory tenant/case filters and metadata-only vector payloads. |
| `retrieval/retriever.py`, `service.py` | `app/services/retrieval_service.py` | Use only for separation of retrieval from synthesis. TATTVA search must retain exact span citations; synthesis remains a later, separate feature. |
| `clients/gemini_client.py`, `prompts.py` | `app/llm/` and future report/answer services | Reuse timeout, output-budget, and prompt-version ideas. Route through TATTVA's provider abstraction and evidence validation; do not treat prompt text as a security control. |
| `ingestion/ingest.py` student joiner and tabular schema | None directly | This is domain-specific student data handling. Rebuild only if TATTVA gets a matching, approved source-data requirement. |

## Recommendation

Keep TATTVA's current retrieval and citation architecture. Borrow the modular reader/adapter layout, OCR confidence metadata, dry-run ingestion workflow, and bounded provider-call patterns. Do not import Riva's global collection behavior, full-content vector payloads, student-specific identity joiner, or uncited answer synthesis into case evidence workflows.

The ZIP contains RAG tests, but they were not executed for this review. No runtime or retrieval-quality guarantee is claimed.
