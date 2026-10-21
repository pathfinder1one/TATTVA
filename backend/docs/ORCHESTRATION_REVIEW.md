# Review of Riva-AGI orchestration

Reviewed on 2026-10-21 from `C:\Users\chira\Downloads\Riva-AGI---Copy-main.zip`. The archive was read without extracting or executing it. This is a source review, not a runtime or security test.

## Assessment

Riva provides a useful prototype for splitting an agent system into a classifier, planner, executor, specialist registry, reviewer, and tool registry. Its control flow is not reliable enough to use as TATTVA's execution design without substantial changes. In particular, planned work is not actually dispatched as written, review can fail open, state is only in memory, and general-purpose system tools are unsafe for case analysis.

At the time of this review, TATTVA's orchestration, task, and worker files were scaffolds. The current implementation adds a Mongo-persisted queue, worker leases, a static task registry, retrieval, graph summaries, citation-validated extraction, value discrepancy grouping, and balanced source-grounded hypothesis suggestions. Riva's unrestricted model-based planning remains out of scope.

## Current implementation status (2026-10-21)

The API now also supports case-scoped SSE delivery for persisted run events, persisted findings with human owner/reviewer decisions, persisted versioned report drafts, and voice tools that reuse the same analysis-run service as HTTP. The DAG includes structural graph summaries, citation-checked candidate value discrepancy grouping, and balanced hypothesis suggestions with exact source spans for and against. Hypotheses and discrepancy groups are unverified review leads; no model output changes human review status. The unit suite and a local API retrieval smoke flow pass. Hosted model and live voice provider behavior still require deployment credentials and contract tests.

## What looks useful

- `orchestration/orchestrator/main.py` makes the high-level graph visible: classify, plan, execute, review, and finish.
- `orchestration/orchestrator/registry.py` and `orchestration/tools/registry.py` separate agent/tool registration from orchestration flow. A static, typed allowlist is a useful foundation.
- `orchestration/orchestrator/schemas/` separates input, response, and tool-call contracts. Pydantic contracts can help once extra fields, size limits, and task-specific constraints are enforced.
- The code separates specialists and centralizes model invocation in `orchestrator/llm.py`. Per-task specialist handlers and a provider adapter are useful TATTVA boundaries.
- `TaskStateManager` illustrates explicit status transitions and history as concepts, though its implementation is too ephemeral for production use.

## Findings to address before adaptation

### High: execution does not follow the plan

`planner_node` parses the planner response as an unvalidated JSON value. The executor then receives a serialized plan and asks another LLM which registered agent to run. `create_agent_node` passes the original `task_payload` to every worker; it does not pass the current plan step's `task` field. `current_step` is initialized but not advanced. As a result, the system can repeat the full user request instead of assigning bounded work, and the plan is not an execution contract.

TATTVA should parse a planner proposal into a strict `TaskSpec` with a fixed task type, validated inputs, dependencies, evidence scope, and resource limits. The scheduler should choose only dependency-ready registered task types and pass each handler only its assigned inputs.

### High: review fails open on malformed model output

`reviewer_node` defaults to `approved` if the reviewer output cannot be parsed and routes to completion for any status other than the exact string `rejected`. The reviewer is also just another model call. This is unsafe even for general task review and cannot represent TATTVA human verification or report approval.

TATTVA must reject invalid or missing review output and leave the run pending/error for recovery. Model review can offer advisory feedback, but only an authorized human can verify evidence or approve report inclusion.

### High: built-in tools allow arbitrary host access

`orchestration/tools/builtin/system_tools.py` runs model-supplied commands with `subprocess.run(..., shell=True)`. Its denylist does not provide a command sandbox. `file_tools.py` reads, writes, edits, and lists arbitrary paths; writes can overwrite by default and create parent directories. `web_tools.py` fetches model-supplied URLs without a visible SSRF/private-network guard and reads the full response before truncating it. Specialist agents receive these tools directly through the LLM SDK.

Do not bring these tools into TATTVA workers. Analysis tasks should receive bounded data through repositories/services and have no shell, arbitrary filesystem, browser, or general URL-fetching capabilities.

### High: there are no application-level execution budgets

The graph has no explicit limit for plan length, model/tool calls, retries, review cycles, elapsed time, or cost. A rejected review routes back to the executor, so the loop can continue until a framework-level guard or external failure stops it. Tool wrappers and LLM calls have no consistent cancellation or total-run deadline.

TATTVA should enforce explicit limits per run and task, include bounded retry/backoff, support cancellation, and persist the reason when a limit stops execution.

### Medium: task state is process-local and not case-scoped

`main.py` owns one global `TaskStateManager`; `state_manager.py` keeps state in a Python dictionary protected by a thread lock. It is lost on restart, does not coordinate across workers, and has no tenant/case ownership. `get_task_status` returns the stored mutable object. This is insufficient for background execution, worker recovery, or an auditable case record.

Persist runs and transitions in TATTVA's repositories with tenant/case scope, actor/run correlation, idempotency, and append-only audit events. Publish progress only after persistence succeeds.

### Medium: structured contracts are permissive and status handling is weak

`InputData.metadata`, `AgentResponse.metadata`, and tool parameters accept arbitrary dictionaries. Planner and executor responses are parsed manually rather than validated against strict response models. Worker functions generally return `ResponseStatus.SUCCESS` even when the shared LLM helper returns an error string. Tool and model errors may be exposed in content.

TATTVA should use strict input/output schemas per task, validate status and provenance before persistence, bound payload sizes, and map provider/tool failures to stable internal error classes without returning secrets or raw exception details.

### Medium: diagnostics can record user data and secrets

`orchestrator/llm.py` logs tool arguments and output-derived details; the tool registry also logs arguments. Inputs may contain sensitive user or case content. `KeyManager` can fall back from a role-specific key to the global key or any available Gemini key, so the documented role separation is not guaranteed by the implementation.

TATTVA should log task/run IDs, operation names, timings, and outcome classes. Keep evidence, prompts, tokens, credentials, and raw tool arguments out of normal logs. Use explicit provider credentials and policy per provider integration rather than silently rotating across all configured keys.

## TATTVA mapping and recommendation

| Riva source | TATTVA destination | Decision |
| --- | --- | --- |
| `orchestrator/main.py` graph and routing | `app/orchestrator/planner.py`, `scheduler.py`, `executor.py` | Reuse the visible stage separation. Replace LLM-controlled step selection with deterministic scheduling over validated task specs. |
| `orchestrator/registry.py` | `app/orchestrator/task_registry.py` | Reuse the static registry idea. Enforce typed input/output contracts, declared permissions, and timeouts at registration and dispatch. |
| `orchestrator/state_manager.py` | `app/domain/analysis_run.py`, `app/repositories/runs_repo.py`, `app/orchestrator/event_publisher.py` | Reuse status/history vocabulary only. Persist authorized transitions and audit data; do not keep the system of record in a process dictionary. |
| `orchestrator/planner.py`, `executor.py`, `reviewer.py` | `app/orchestrator/` and review services | Use as workflow examples only. Validate planner output, execute exact assigned work, fail closed, and keep human review separate from model feedback. |
| `orchestrator/schemas/` | `app/domain/task_spec.py`, `app/schemas/` | Reuse schema separation. Make contracts strict and TATTVA-specific, with source IDs, scope, bounded sizes, and explicit uncertainty/provenance. |
| `orchestration/tools/builtin/` | None | Do not reuse shell, arbitrary file, browser, or unbounded URL tools in case analysis. |
| `orchestrator/llm.py`, `orchestrator/config.py` | `app/llm/` | Reuse provider encapsulation and timing concepts. Add deadlines, cancellation, explicit retry/cost policy, strict result validation, and secret-safe diagnostics. |

The current TATTVA files `app/orchestrator/{planner,executor,scheduler,policies,task_registry,event_publisher}.py`, `app/domain/{task_spec,analysis_run}.py`, and `app/workers/run_analysis.py` implement the bounded retrieval, graph summary, optional source-grounded extraction, discrepancy and hypothesis tasks. Extraction uses a provider-neutral interface with an OpenAI-compatible adapter and strict output/provenance checks. Candidates are returned in run output only; they do not modify evidence records or review state. Run creation inserts task records before the run becomes visible to workers, then activates it after the initial event and audit record persist. A stale unactivated run can be recovered after a short grace period if the API process stops mid-enqueue. New specialist behavior should receive its own bounded contract and human-review boundary before registration.

The Riva ZIP was not run. Local checks cover unit behavior and basic API, storage, indexing and retrieval paths; they do not establish hosted provider compatibility, deployment security, or production reliability.
