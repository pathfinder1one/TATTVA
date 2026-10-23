/**
 * TATTVA Backend API Service
 * Connects to the FastAPI backend as defined in FRONTEND_INTEGRATION_GUIDE.md
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8002';
const API_V1 = `${API_BASE}/api/v1`;

// --- Auth Headers (local dev mode) ---
function getAuthHeaders() {
  return {
    'X-User-Id': 'local-investigator',
    'X-Tenant-Id': 'local-tenant',
  };
}

function jsonHeaders() {
  return {
    ...getAuthHeaders(),
    'Content-Type': 'application/json',
  };
}

async function handleResponse(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body.detail || `HTTP ${res.status}`);
    err.status = res.status;
    err.detail = body.detail;
    err.requestId = res.headers.get('X-Request-Id');
    throw err;
  }
  return res.json();
}

// ============================================================
// Health
// ============================================================
export async function checkHealth() {
  const res = await fetch(`${API_BASE}/healthz`, { headers: getAuthHeaders() });
  return handleResponse(res);
}

export async function checkReady() {
  const res = await fetch(`${API_BASE}/readyz`, { headers: getAuthHeaders() });
  return handleResponse(res);
}

// ============================================================
// Cases
// ============================================================
export async function listCases() {
  const res = await fetch(`${API_V1}/cases`, { headers: getAuthHeaders() });
  return handleResponse(res);
}

export async function createCase({ case_number, title, description }) {
  const res = await fetch(`${API_V1}/cases`, {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify({ case_number, title, description }),
  });
  return handleResponse(res);
}

export async function getCase(caseId) {
  const res = await fetch(`${API_V1}/cases/${caseId}`, { headers: getAuthHeaders() });
  return handleResponse(res);
}

// ============================================================
// Documents
// ============================================================
export async function listDocuments(caseId) {
  const res = await fetch(`${API_V1}/cases/${caseId}/documents`, { headers: getAuthHeaders() });
  return handleResponse(res);
}

export async function uploadDocument(caseId, file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_V1}/cases/${caseId}/documents`, {
    method: 'POST',
    headers: getAuthHeaders(), // No Content-Type; browser adds multipart boundary
    body: form,
  });
  return handleResponse(res);
}

export async function indexDocument(caseId, documentId) {
  const res = await fetch(`${API_V1}/cases/${caseId}/documents/${documentId}/index`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function getChunk(caseId, documentId, chunkId) {
  const res = await fetch(
    `${API_V1}/cases/${caseId}/documents/${documentId}/chunks/${chunkId}`,
    { headers: getAuthHeaders() }
  );
  return handleResponse(res);
}

export async function getDocumentCertificate(caseId, documentId) {
  const res = await fetch(`${API_V1}/cases/${caseId}/documents/${documentId}/certificate`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

// ============================================================
// Evidence
// ============================================================
export async function listEvidence(caseId) {
  const res = await fetch(`${API_V1}/cases/${caseId}/evidence`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function getEvidence(caseId, evidenceId) {
  const res = await fetch(`${API_V1}/cases/${caseId}/evidence/${evidenceId}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function getEvidenceCertificate(caseId, evidenceId) {
  const res = await fetch(`${API_V1}/cases/${caseId}/evidence/${evidenceId}/certificate`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

// ============================================================
// Search
// ============================================================
export async function searchCase(caseId, query, top_k = 5) {
  const res = await fetch(`${API_V1}/cases/${caseId}/search`, {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify({ query, top_k }),
  });
  return handleResponse(res);
}

// ============================================================
// Answers (Grounded Q&A)
// ============================================================
export async function askCase(caseId, query, top_k = 5) {
  const res = await fetch(`${API_V1}/cases/${caseId}/answers`, {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify({ query, top_k }),
  });
  return handleResponse(res);
}

// ============================================================
// Entities
// ============================================================
export async function listEntities(caseId) {
  const res = await fetch(`${API_V1}/cases/${caseId}/entities`, { headers: getAuthHeaders() });
  return handleResponse(res);
}

export async function createEntity(caseId, entity) {
  const res = await fetch(`${API_V1}/cases/${caseId}/entities`, {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify(entity),
  });
  return handleResponse(res);
}

// ============================================================
// Relationships
// ============================================================
export async function listRelationships(caseId) {
  const res = await fetch(`${API_V1}/cases/${caseId}/relationships`, { headers: getAuthHeaders() });
  return handleResponse(res);
}

export async function createRelationship(caseId, rel) {
  const res = await fetch(`${API_V1}/cases/${caseId}/relationships`, {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify(rel),
  });
  return handleResponse(res);
}

export async function verifyRelationship(caseId, relationshipId, { decision, rationale }) {
  const res = await fetch(
    `${API_V1}/cases/${caseId}/relationships/${relationshipId}/verify`,
    {
      method: 'POST',
      headers: jsonHeaders(),
      body: JSON.stringify({ decision, rationale }),
    }
  );
  return handleResponse(res);
}

export async function reviewRelationship(caseId, relationshipId, { decision, rationale }) {
  const res = await fetch(
    `${API_V1}/cases/${caseId}/relationships/${relationshipId}/review`,
    {
      method: 'POST',
      headers: jsonHeaders(),
      body: JSON.stringify({ decision, rationale }),
    }
  );
  return handleResponse(res);
}

// ============================================================
// Graph
// ============================================================
export async function getCaseGraph(caseId) {
  const res = await fetch(`${API_V1}/cases/${caseId}/graph`, { headers: getAuthHeaders() });
  return handleResponse(res);
}

// ============================================================
// Findings
// ============================================================
export async function listFindings(caseId) {
  const res = await fetch(`${API_V1}/cases/${caseId}/findings`, { headers: getAuthHeaders() });
  return handleResponse(res);
}

export async function createFinding(caseId, finding) {
  const res = await fetch(`${API_V1}/cases/${caseId}/findings`, {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify(finding),
  });
  return handleResponse(res);
}

export async function reviewFinding(caseId, findingId, { decision, rationale }) {
  const res = await fetch(
    `${API_V1}/cases/${caseId}/findings/${findingId}/review`,
    {
      method: 'POST',
      headers: jsonHeaders(),
      body: JSON.stringify({ decision, rationale }),
    }
  );
  return handleResponse(res);
}

// ============================================================
// Analysis Runs
// ============================================================
export async function listAnalysisRuns(caseId) {
  const res = await fetch(`${API_V1}/cases/${caseId}/analysis-runs`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function createAnalysisRun(caseId, { query, top_k = 5, idempotencyKey }) {
  const res = await fetch(`${API_V1}/cases/${caseId}/analysis-runs`, {
    method: 'POST',
    headers: {
      ...jsonHeaders(),
      'Idempotency-Key': idempotencyKey,
    },
    body: JSON.stringify({ query, top_k }),
  });
  return handleResponse(res);
}

export async function getAnalysisRun(caseId, runId) {
  const res = await fetch(`${API_V1}/cases/${caseId}/analysis-runs/${runId}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function cancelAnalysisRun(caseId, runId) {
  const res = await fetch(`${API_V1}/cases/${caseId}/analysis-runs/${runId}/cancel`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function getRunEvents(caseId, runId, afterSeq = 0, limit = 100) {
  const res = await fetch(
    `${API_V1}/cases/${caseId}/analysis-runs/${runId}/events?after_seq=${afterSeq}&limit=${limit}`,
    { headers: getAuthHeaders() }
  );
  return handleResponse(res);
}

/**
 * Subscribe to Server-Sent Events for a run.
 * Returns an EventSource instance. Caller manages lifecycle.
 */
export function subscribeRunEvents(caseId, runId, afterSeq = 0) {
  const url = `${API_V1}/cases/${caseId}/analysis-runs/${runId}/events/stream?after_seq=${afterSeq}`;
  return new EventSource(url);
}

// ============================================================
// Report Drafts
// ============================================================
export async function createReportDraft(caseId, runId) {
  const res = await fetch(
    `${API_V1}/cases/${caseId}/analysis-runs/${runId}/report-draft`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
    }
  );
  return handleResponse(res);
}

export async function listReportDrafts(caseId, runId) {
  const res = await fetch(
    `${API_V1}/cases/${caseId}/analysis-runs/${runId}/reports`,
    { headers: getAuthHeaders() }
  );
  return handleResponse(res);
}

export async function getReportDraft(caseId, runId, reportId) {
  const res = await fetch(
    `${API_V1}/cases/${caseId}/analysis-runs/${runId}/reports/${reportId}`,
    { headers: getAuthHeaders() }
  );
  return handleResponse(res);
}
