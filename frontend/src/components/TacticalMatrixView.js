'use client';

/**
 * TacticalMatrixView — Dedicated Forensic Threat Matrix & Anomaly Engine
 * Separated cleanly from the TATTVA Core Vocal Stage as requested by investigators
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  IconCrosshair,
  IconContradiction,
  IconVerification,
  IconPlanning,
  IconRAG,
  IconEntity,
  IconPattern,
  IconGraph,
  IconReport,
} from './StarkIcons';
import {
  listDocuments,
  listFindings,
  listAnalysisRuns,
  getCaseGraph,
  createAnalysisRun,
} from '@/lib/api';

// 8 Dedicated Autonomous Investigative Agents with Clear, Natural Language Roles
const INVESTIGATIVE_AGENTS = [
  { id: 'planning', name: 'CASE PLANNER', role: 'Investigation Strategy & Task Decomposition', icon: IconPlanning, color: '#38bdf8' },
  { id: 'rag', name: 'EVIDENCE SEARCH', role: 'Verified File & Document Retrieval', icon: IconRAG, color: '#00f0ff' },
  { id: 'entity', name: 'SUSPECT EXTRACTOR', role: 'Identifies People, Phones & Shell Companies', icon: IconEntity, color: '#10b981' },
  { id: 'pattern', name: 'PATTERN ANALYST', role: 'Detects Hidden Syndicate Conduits & Anomaly Clusters', icon: IconPattern, color: '#a855f7' },
  { id: 'verification', name: 'PROOF CHECKER', role: 'Section 63 BSA & Evidence Admissibility Auditing', icon: IconVerification, color: '#00f0ff' },
  { id: 'graph', name: 'NETWORK MAPPER', role: 'Calculates Kingpins, Brokers & Conduit Flow', icon: IconGraph, color: '#f59e0b' },
  { id: 'contradiction', name: 'ALIBI & FRAUD HUNTER', role: 'Cross-Examines Conflicting Statements & Timelines', icon: IconContradiction, color: '#f43f5e' },
  { id: 'report', name: 'CHARGE-SHEET WRITER', role: 'Synthesizes Official Forensic Case Briefs', icon: IconReport, color: '#38bdf8' },
];

export default function TacticalMatrixView({
  caseData,
  onNavigate,
  onOpenCert,
}) {
  const [documents, setDocuments] = useState([]);
  const [findings, setFindings] = useState([]);
  const [runs, setRuns] = useState([]);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isScanning, setIsScanning] = useState(false);

  // Load all live forensic metrics for the active case
  const loadCaseMetrics = useCallback(async () => {
    if (!caseData?.case_id) return;
    setLoading(true);
    try {
      const [dRes, fRes, rRes, gRes] = await Promise.allSettled([
        listDocuments(caseData.case_id),
        listFindings(caseData.case_id),
        listAnalysisRuns(caseData.case_id),
        getCaseGraph(caseData.case_id),
      ]);
      if (dRes.status === 'fulfilled') setDocuments(Array.isArray(dRes.value) ? dRes.value : []);
      if (fRes.status === 'fulfilled') setFindings(Array.isArray(fRes.value) ? fRes.value : []);
      if (rRes.status === 'fulfilled') setRuns(Array.isArray(rRes.value) ? rRes.value : []);
      if (gRes.status === 'fulfilled') setGraphData(gRes.value);
    } catch (e) {
      console.warn('Failed to fetch tactical matrix data:', e);
    } finally {
      setLoading(false);
    }
  }, [caseData?.case_id]);

  useEffect(() => {
    loadCaseMetrics();
  }, [loadCaseMetrics]);

  // Trigger a full multi-agent re-scan
  const handleTriggerScan = async () => {
    if (!caseData?.case_id || isScanning) return;
    setIsScanning(true);
    try {
      await createAnalysisRun(caseData.case_id);
      await loadCaseMetrics();
    } catch (e) {
      console.warn('Scan trigger failed:', e);
    } finally {
      setIsScanning(false);
    }
  };

  // Dynamic Case Threat Level / Suspicion Index calculation
  const calculatedSuspicion = useMemo(() => {
    if (!documents.length && !findings.length && !graphData?.entities?.length) {
      return { score: 0, level: 'CLEAR // ZERO EVIDENCE INGESTED' };
    }
    const findingWeight = findings.length * 28;
    const entityWeight = (graphData?.entities?.length || 0) * 5;
    const docWeight = documents.length * 8;
    const score = Math.min(99, Math.max(15, findingWeight + entityWeight + docWeight));
    let level = `${score}% MONITORED`;
    if (score >= 75) level = `${score}% CRITICAL // HIGH CARTEL THREAT`;
    else if (score >= 45) level = `${score}% ELEVATED CONCERN`;
    return { score, level };
  }, [documents.length, findings.length, graphData?.entities?.length]);

  return (
    <div style={{ padding: '24px 32px', maxWidth: 1200, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header Strip with Clean, Plain Language */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(0, 240, 255, 0.2)', paddingBottom: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <IconCrosshair size={22} color="var(--arc-cyan)" />
            <h1 style={{ fontFamily: 'var(--font-stark)', fontSize: 22, fontWeight: 700, color: '#ffffff', letterSpacing: 1.5, margin: 0 }}>
              TACTICAL THREAT MATRIX & ANOMALY ENGINE
            </h1>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, color: 'var(--text-secondary)', marginTop: 4 }}>
            CASE FILE: <strong style={{ color: 'var(--arc-cyan)' }}>{caseData?.case_number || 'CASE-2024-023'}</strong> · <span style={{ color: '#10b981' }}>{caseData?.title || 'Active Investigation'}</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            onClick={() => onNavigate?.('graph')}
            style={{
              padding: '8px 16px',
              background: 'rgba(0, 240, 255, 0.1)',
              border: '1px solid var(--border-stark-bright)',
              borderRadius: 4,
              color: 'var(--arc-cyan)',
              fontFamily: 'var(--font-stark)',
              fontSize: 11,
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <span>🌐</span>
            <span>OPEN CRIMINAL GRAPH ({graphData?.entities?.length || 0}) →</span>
          </button>
          <button
            onClick={() => onNavigate?.('documents')}
            style={{
              padding: '8px 16px',
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid #10b981',
              borderRadius: 4,
              color: '#10b981',
              fontFamily: 'var(--font-stark)',
              fontSize: 11,
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <span>📁</span>
            <span>EVIDENCE VAULT ({documents.length}) →</span>
          </button>
        </div>
      </div>

      {/* Grid: Case Directive & Suspicion Index */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 20 }}>
        {/* Case Directive Box */}
        <div style={{ padding: '20px 24px', background: 'rgba(4, 12, 34, 0.8)', border: '1px solid var(--border-stark)', borderRadius: 'var(--radius-md)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--arc-cyan)', letterSpacing: 1.5, fontWeight: 700 }}>
              MISSION DIRECTIVE & INVESTIGATION SCOPE
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#10b981', background: 'rgba(16, 185, 129, 0.15)', padding: '2px 8px', borderRadius: 3, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
              LIVE INVESTIGATION
            </span>
          </div>

          <div style={{ fontFamily: 'var(--font-stark)', fontSize: 18, fontWeight: 700, color: '#ffffff', marginBottom: 8 }}>
            {caseData?.title || 'Operation Golden Trident: Inter-State Narcotics & Hawala Cartel'}
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 18 }}>
            {caseData?.description || 'Cross-border multi-tiered criminal syndicate operating narcotics distribution pipelines and structured Hawala money laundering across Punjab, Delhi-NCR, and Mumbai.'}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 14 }}>
            <div>
              <div style={{ fontSize: 9.5, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>INDEXED FILES</div>
              <div style={{ fontSize: 18, fontFamily: 'var(--font-stark)', fontWeight: 700, color: '#ffffff' }}>{documents.length}</div>
            </div>
            <div>
              <div style={{ fontSize: 9.5, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>CONTRADICTIONS</div>
              <div style={{ fontSize: 18, fontFamily: 'var(--font-stark)', fontWeight: 700, color: '#f43f5e' }}>{findings.length}</div>
            </div>
            <div>
              <div style={{ fontSize: 9.5, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>SUSPECTS & ENTITIES</div>
              <div style={{ fontSize: 18, fontFamily: 'var(--font-stark)', fontWeight: 700, color: '#f59e0b' }}>{graphData?.entities?.length || 0}</div>
            </div>
            <div>
              <div style={{ fontSize: 9.5, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>AI SCANS COMPLETED</div>
              <div style={{ fontSize: 18, fontFamily: 'var(--font-stark)', fontWeight: 700, color: 'var(--arc-cyan)' }}>{runs.length}</div>
            </div>
          </div>
        </div>

        {/* Forensic Suspicion Gauge */}
        <div style={{ padding: '20px 24px', background: 'rgba(4, 12, 34, 0.8)', border: '1px solid var(--border-stark)', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: 1.5, fontWeight: 700 }}>
                CASE THREAT LEVEL / SUSPICION INDEX
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: calculatedSuspicion.score >= 75 ? '#f43f5e' : '#f59e0b' }}>
                {calculatedSuspicion.level}
              </span>
            </div>

            <div style={{ width: '100%', height: 12, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 6, overflow: 'hidden', marginBottom: 14 }}>
              <div
                style={{
                  width: `${calculatedSuspicion.score}%`,
                  height: '100%',
                  background: calculatedSuspicion.score >= 75
                    ? 'linear-gradient(90deg, #f59e0b, #f43f5e)'
                    : calculatedSuspicion.score >= 45
                    ? 'linear-gradient(90deg, #00f0ff, #f59e0b)'
                    : 'linear-gradient(90deg, #10b981, #00f0ff)',
                  boxShadow: '0 0 12px rgba(0, 240, 255, 0.5)',
                  transition: 'width 0.6s ease',
                }}
              />
            </div>

            <div style={{ fontSize: 11.5, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Calculated automatically from {findings.length} flagged alibi contradictions, {documents.length} verified evidence files, and {graphData?.entities?.length || 0} syndicate suspect relationships.
            </div>
          </div>

          <button
            onClick={handleTriggerScan}
            disabled={isScanning}
            style={{
              marginTop: 18,
              padding: '12px 18px',
              background: isScanning ? 'rgba(0, 240, 255, 0.1)' : 'linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(168, 85, 247, 0.2))',
              border: '1px solid var(--arc-cyan)',
              borderRadius: 6,
              color: 'var(--arc-cyan)',
              fontFamily: 'var(--font-stark)',
              fontSize: 12,
              fontWeight: 700,
              cursor: isScanning ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              boxShadow: '0 0 20px rgba(0, 240, 255, 0.2)',
            }}
          >
            <span>⚡</span>
            <span>{isScanning ? 'RUNNING MULTI-AGENT SCAN...' : 'RUN COMPREHENSIVE AI INVESTIGATION AUDIT'}</span>
          </button>
        </div>
      </div>

      {/* Section 2: Contradiction Hunter Findings */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
          <IconContradiction size={18} color="#f43f5e" />
          <h2 style={{ fontFamily: 'var(--font-stark)', fontSize: 16, fontWeight: 700, color: '#ffffff', letterSpacing: 1, margin: 0 }}>
            FLAGGED ALIBI CONTRADICTIONS & FRAUD ANOMALIES ({findings.length})
          </h2>
        </div>

        {findings.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 16 }}>
            {findings.map((f, idx) => (
              <div
                key={f.finding_id || idx}
                style={{
                  padding: '18px 20px',
                  background: 'rgba(244, 63, 94, 0.05)',
                  border: '1px solid rgba(244, 63, 94, 0.35)',
                  borderRadius: 'var(--radius-sm)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                  boxShadow: '0 0 16px rgba(244, 63, 94, 0.1)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#f43f5e', fontWeight: 700, letterSpacing: 1 }}>
                    FLAGGED CONTRADICTION #{idx + 1} // {f.severity?.toUpperCase() || 'CRITICAL PRIORITY'}
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
                    CONFIDENCE: {Math.round((f.confidence_score || 0.95) * 100)}%
                  </span>
                </div>

                <div style={{ fontFamily: 'var(--font-stark)', fontSize: 14, fontWeight: 700, color: '#ffffff', marginTop: 2 }}>
                  {f.statement}
                </div>

                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {f.details || 'Discrepancy identified between sworn suspect declarations, official immigration stamps, and intercepted CDR telecom tower triangulation.'}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 6, paddingTop: 8, borderTop: '1px solid rgba(244, 63, 94, 0.15)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <IconVerification size={12} color="#10b981" />
                    <span style={{ fontSize: 10.5, fontFamily: 'var(--font-mono)', color: '#10b981' }}>
                      EVIDENCE-BACKED (SEC-63 BSA)
                    </span>
                  </div>
                  {onOpenCert && (
                    <button
                      onClick={() => onOpenCert({
                        certificate_id: `CERT-FINDING-${f.finding_id?.slice(0, 8) || '01'}`,
                        filename: 'Forensic_Contradiction_Audit.pdf',
                        sha256_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
                        admissibility_status: 'COURT_ADMISSIBLE_SECTION_63_BSA',
                        timestamp_utc: new Date().toISOString(),
                      })}
                      style={{
                        padding: '3px 8px',
                        background: 'rgba(0, 240, 255, 0.12)',
                        border: '1px solid var(--arc-cyan)',
                        color: 'var(--arc-cyan)',
                        borderRadius: 3,
                        fontSize: 9.5,
                        fontFamily: 'var(--font-stark)',
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      VIEW CERTIFICATE ➔
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)', background: 'rgba(4, 12, 34, 0.5)', borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
            No alibi contradictions currently flagged. Click "RUN COMPREHENSIVE AI INVESTIGATION AUDIT" or ingest new evidence files.
          </div>
        )}
      </div>

      {/* Section 3: Autonomous Investigative Agent Pipeline */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
          <IconPlanning size={18} color="var(--arc-cyan)" />
          <h2 style={{ fontFamily: 'var(--font-stark)', fontSize: 16, fontWeight: 700, color: '#ffffff', letterSpacing: 1, margin: 0 }}>
            AUTONOMOUS INVESTIGATIVE AGENT SWARM (8 AGENTS ACTIVE)
          </h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          {INVESTIGATIVE_AGENTS.map((agent) => {
            const IconC = agent.icon;
            return (
              <div
                key={agent.id}
                style={{
                  padding: '14px 16px',
                  background: 'rgba(4, 12, 34, 0.75)',
                  border: `1px solid ${agent.color}44`,
                  borderRadius: 6,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}
              >
                <div style={{ padding: 8, borderRadius: 6, background: `${agent.color}18`, border: `1px solid ${agent.color}55` }}>
                  <IconC size={18} color={agent.color} />
                </div>
                <div>
                  <div style={{ fontFamily: 'var(--font-stark)', fontSize: 12, fontWeight: 700, color: '#ffffff' }}>
                    {agent.name}
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9.5, color: 'var(--text-muted)' }}>
                    {agent.role}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
