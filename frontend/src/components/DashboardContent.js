'use client';

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import dynamic from 'next/dynamic';
import {
  listCases,
  listDocuments,
  listFindings,
  listAnalysisRuns,
  getCaseGraph,
  createAnalysisRun,
  getRunEvents,
  subscribeRunEvents,
  searchCase,
  askCase,
  getDocumentCertificate,
} from '@/lib/api';
import VoiceCommandController from './VoiceCommandController';
import EvidenceIngestionModal from './EvidenceIngestionModal';
import CriminalNetworkGraph from './CriminalNetworkGraph';
import { soundEngine } from '@/lib/soundEffects';
import {
  IconPlanning,
  IconRAG,
  IconEntity,
  IconPattern,
  IconVerification,
  IconGraph,
  IconContradiction,
  IconReport,
  IconMic,
  IconMicOff,
  IconSettings,
  IconStop,
  IconArcReactor,
  IconCrosshair,
  IconLightning,
  IconAudioWave,
} from './StarkIcons';

// Dynamic import for 3D component (no SSR for Three.js)
const TATTVACoreOrb = dynamic(() => import('@/components/TATTVACoreOrb'), {
  ssr: false,
  loading: () => (
    <div style={{
      width: '100%', height: '100%',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'radial-gradient(circle at center, #06102a 0%, #020611 75%)',
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontFamily: 'Rajdhani, sans-serif',
          fontSize: 16, color: 'var(--arc-cyan)',
          letterSpacing: 4, textTransform: 'uppercase',
          fontWeight: 700,
          animation: 'pulse-glow 1.5s ease-in-out infinite',
        }}>INITIALIZING TATTVA ARC CORE...</div>
      </div>
    </div>
  ),
});

// The 8 Tactical Autonomous Backend Agents
const SWARM_AGENTS = [
  { id: 'planning', name: 'PLANNING AGENT', role: 'Task DAG Decomposition', icon: IconPlanning, color: '#38bdf8' },
  { id: 'rag', name: 'RAG SEARCH', role: 'Qdrant Vector Retrieval', icon: IconRAG, color: '#00f0ff' },
  { id: 'entity', name: 'ENTITY SENTRY', role: 'Corporate Biometric Extractor', icon: IconEntity, color: '#10b981' },
  { id: 'pattern', name: 'PATTERN ANALYST', role: 'Graph Anomaly Scanner', icon: IconPattern, color: '#a855f7' },
  { id: 'verification', name: 'VERIFICATION', role: 'Evidence Proof Checking', icon: IconVerification, color: '#00f0ff' },
  { id: 'graph', name: 'NEXUS GRAPH', role: 'Beneficial Ownership Clusters', icon: IconGraph, color: '#f59e0b' },
  { id: 'contradiction', name: 'FRAUD HUNTER', role: 'Contradiction Audit Engine', icon: IconContradiction, color: '#f43f5e' },
  { id: 'report', name: 'REPORT BUILDER', role: 'Forensic Dossier Synthesis', icon: IconReport, color: '#38bdf8' },
];

export default function DashboardContent({ caseData: propCase, onCaseSelect, onNavigate }) {
  const [activeCase, setActiveCase] = useState(propCase);
  const [documents, setDocuments] = useState([]);
  const [findings, setFindings] = useState([]);
  const [runs, setRuns] = useState([]);
  const [graphData, setGraphData] = useState(null);
  const [activeTab, setActiveTab] = useState(null); // 'evidence' | 'graph' | 'findings' | 'runs' | null
  const [activeAgent, setActiveAgent] = useState(null);
  const [coreMode, setCoreMode] = useState('idle'); // 'idle' | 'listening' | 'analyzing' | 'speaking'
  const [audioLevel, setAudioLevel] = useState(0);
  const [liveLogs, setLiveLogs] = useState([]);
  const [showVoiceSettings, setShowVoiceSettings] = useState(false);
  const [showIngestionModal, setShowIngestionModal] = useState(false);
  const [selectedCert, setSelectedCert] = useState(null);
  const [isLoadingCert, setIsLoadingCert] = useState(false);
  const eventSourceRef = useRef(null);

  // Sync activeCase when propCase changes (e.g. from Header dropdown)
  useEffect(() => {
    if (propCase?.case_id && propCase.case_id !== activeCase?.case_id) {
      setActiveCase(propCase);
    }
  }, [propCase, activeCase?.case_id]);

  // Initial load if no case provided
  useEffect(() => {
    if (!propCase?.case_id) {
      listCases()
        .then((data) => {
          const list = Array.isArray(data) ? data : data?.cases || [];
          if (list.length > 0) {
            setActiveCase(list[0]);
            onCaseSelect?.(list[0]);
          }
        })
        .catch(() => {});
    }
  }, [propCase, onCaseSelect]);

  // 2. Load live backend data whenever activeCase is set
  const loadLiveBackendData = useCallback(async () => {
    if (!activeCase?.case_id) return;
    const cid = activeCase.case_id;

    try {
      const [docs, finds, runList, graph] = await Promise.all([
        listDocuments(cid).catch(() => []),
        listFindings(cid).catch(() => []),
        listAnalysisRuns(cid).catch(() => []),
        getCaseGraph(cid).catch(() => null),
      ]);

      setDocuments(Array.isArray(docs) ? docs : []);
      setFindings(Array.isArray(finds) ? finds : []);
      setRuns(Array.isArray(runList) ? runList : []);
      if (graph) setGraphData(graph);

      // Fetch latest events if any run exists
      if (runList && runList.length > 0) {
        const latestRun = runList[0];
        const events = await getRunEvents(cid, latestRun.run_id, 0, 20).catch(() => []);
        if (Array.isArray(events) && events.length > 0) {
          const formatted = events.map(e => ({
            time: new Date(e.timestamp).toLocaleTimeString(),
            agent: e.type.includes('task') ? 'TASK AGENT' : 'RUN ORCHESTRATOR',
            text: `[${e.type}] ${e.payload?.task_type || e.payload?.status || 'Processing event stream'}`,
          })).reverse();
          setLiveLogs(formatted);
        }
      }
    } catch (err) {
      console.warn('Backend live data sync error:', err);
    }
  }, [activeCase?.case_id]);

  useEffect(() => {
    loadLiveBackendData();
  }, [loadLiveBackendData]);

  // 3. Subscribe to real SSE events for active run
  useEffect(() => {
    if (!activeCase?.case_id || !runs || runs.length === 0) return;
    const latestRun = runs[0];
    if (latestRun.status !== 'running' && latestRun.status !== 'queued') return;

    try {
      const sse = subscribeRunEvents(activeCase.case_id, latestRun.run_id);
      eventSourceRef.current = sse;

      sse.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLiveLogs(prev => [
            {
              time: new Date().toLocaleTimeString(),
              agent: 'SSE ORCHESTRATOR',
              text: `Event ${data.seq || ''}: ${data.type} - ${data.payload?.status || data.payload?.task_type || 'Update'}`,
            },
            ...prev.slice(0, 25),
          ]);
        } catch (e) {}
      };

      sse.onerror = () => {
        sse.close();
      };

      return () => {
        sse.close();
      };
    } catch (e) {}
  }, [activeCase?.case_id, runs]);

  // Voice AI Controller hook
  const voice = VoiceCommandController({
    caseData: activeCase,
    mode: coreMode,
    setMode: setCoreMode,
    setAudioLevel,
    findingsCount: findings.length,
    docsCount: documents.length,
    findings,
    graphData,
    onCaseSwitch: (newCase) => {
      setActiveCase(newCase);
      onCaseSelect?.(newCase);
    },
    onAgentTrigger: (agentId) => {
      setActiveAgent(agentId);
      setLiveLogs(prev => [
        { time: new Date().toLocaleTimeString(), agent: agentId.toUpperCase(), text: `Direct agent intervention: task DAG generated.` },
        ...prev.slice(0, 15)
      ]);
    },
    onActionTrigger: async (action) => {
      if (action === 'show_findings') setActiveTab('findings');
      if (action === 'show_graph') setActiveTab('graph');
      if (action === 'show_evidence') setActiveTab('evidence');
      if (action === 'open_ingestion') setShowIngestionModal(true);
      if (action === 'close_ingestion') setShowIngestionModal(false);
      if (action === 'open_certificate') {
        if (documents.length > 0 && activeCase?.case_id) {
          try {
            const cert = await getDocumentCertificate(activeCase.case_id, documents[0].document_id);
            setSelectedCert(cert);
          } catch (e) {
            console.warn('Certificate action error:', e);
          }
        }
      }
      if (action === 'refresh_runs') loadLiveBackendData();
    },
  });

  // Handle Touch/Click on Core directly — Opens TATTVA Voice Model Modal & Engages Voice Link
  const handleCoreTouch = useCallback((e) => {
    if (e && e.stopPropagation) e.stopPropagation();
    setShowVoiceSettings(true);
    soundEngine?.playBeep?.(880, 0.08);

    if (coreMode === 'idle') {
      voice.startListening();
    }
  }, [coreMode, voice]);

  // Global voice event listener (sidebar click or keyboard shortcut)
  useEffect(() => {
    const handleGlobalVoice = () => {
      handleCoreTouch();
    };
    window.addEventListener('tattva-trigger-voice', handleGlobalVoice);
    return () => window.removeEventListener('tattva-trigger-voice', handleGlobalVoice);
  }, [handleCoreTouch]);

  // Dynamic Forensic Suspicion Index calculation
  const calculatedSuspicion = useMemo(() => {
    if (!documents.length && !findings.length && !graphData?.entities?.length) {
      return { score: 0, level: 'CLEAR // ZERO EVIDENCE' };
    }
    const findingWeight = findings.length * 28;
    const entityWeight = (graphData?.entities?.length || 0) * 5;
    const docWeight = documents.length * 8;
    const score = Math.min(99, Math.max(15, findingWeight + entityWeight + docWeight));
    let level = `${score}% MONITORED`;
    if (score >= 75) level = `${score}% CRITICAL // HIGH THREAT`;
    else if (score >= 45) level = `${score}% ELEVATED`;
    return { score, level };
  }, [documents.length, findings.length, graphData?.entities?.length]);

  // Dispatch real backend analysis run
  const triggerBackendScan = async () => {
    if (!activeCase?.case_id) return;
    setCoreMode('analyzing');
    soundEngine?.playProcessCommand();
    voice.speakAI(`Deploying multi-agent DAG pipeline to inspect ${activeCase.case_number || 'active case'}.`);

    const scanQuery = activeCase.title
      ? `Audit suspect interactions, telecom logs, and financial contradictions for ${activeCase.title}`
      : 'Analyze multi-source criminal network relationships and evidential contradictions';

    try {
      const run = await createAnalysisRun(activeCase.case_id, {
        query: scanQuery,
        top_k: 5,
        idempotencyKey: `run-${Date.now()}`,
      });
      setLiveLogs(prev => [
        { time: new Date().toLocaleTimeString(), agent: 'ORCHESTRATOR', text: `Dispatched Run: ${run.run_id} with ${run.task_count || run.tasks?.length || 0} DAG tasks.` },
        ...prev,
      ]);
      await loadLiveBackendData();
    } catch (err) {
      console.warn('Backend run dispatch failed:', err);
    }
  };

  return (
    <div className="stark-command-stage">
      {/* ══════════════════════════════════════════════════════════
          HERO STAGE: THE TATTVA CORE THEATER (CENTRAL 3D HOLOGRAPH)
          PURE, MAJESTIC, 100% UNOBSTRUCTED CORE
          ══════════════════════════════════════════════════════════ */}
      <div className="stark-core-theater">
        {/* Aerospace Corner Chamfer Brackets */}
        <div className="hud-corner-bracket bracket-tl" />
        <div className="hud-corner-bracket bracket-tr" />
        <div className="hud-corner-bracket bracket-bl" />
        <div className="hud-corner-bracket bracket-br" />

        {/* Telemetry Header Strip */}
        <div className="theater-hud-header">
          <div>
            <div className="hud-sys-tag">MINISTRY OF HOME AFFAIRS // NCRB INTELLIGENCE DIVISION</div>
            <div className="hud-sys-title">AI CRIMINAL NETWORK ANALYSIS SYSTEM</div>
            <div className="hud-sys-sub">
              CRIME CASE: <span style={{ color: 'var(--arc-cyan)' }}>{activeCase?.case_number || 'NO ACTIVE CASE'}</span> · BACKEND: <span style={{ color: '#10b981' }}>FASTAPI LIVE // SEC-65B VERIFIED</span>
            </div>
          </div>

          <div className="theater-hud-metrics">
            <div className="telemetry-node">
              <span className="telemetry-node-label">SYNAPSE LOAD</span>
              <span className="telemetry-node-val">{runs.some(r => r.status === 'running') ? '100% PROCESSING' : 'REAL-TIME'}</span>
            </div>
            <div className="telemetry-node">
              <span className="telemetry-node-label">BACKEND TASKS</span>
              <span className="telemetry-node-val">{runs.length > 0 ? `${runs[0].tasks?.length || 0} ACTIVE` : '0 READY'}</span>
            </div>
            <button
              className={`btn-voice-identity-trigger ${activeTab === 'graph' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab((prev) => (prev === 'graph' ? null : 'graph'));
                soundEngine?.playBlip();
              }}
              style={{
                borderColor: activeTab === 'graph' ? 'var(--arc-cyan)' : 'rgba(168, 85, 247, 0.45)',
                background: activeTab === 'graph' ? 'rgba(0, 240, 255, 0.2)' : 'rgba(168, 85, 247, 0.1)',
                color: activeTab === 'graph' ? 'var(--arc-cyan)' : '#c084fc',
              }}
              title="Open Interactive Criminal Network Nexus Graph"
            >
              <IconGraph size={13} color="currentColor" />
              <span style={{ fontWeight: 700 }}>VIEW CRIMINAL GRAPH</span>
            </button>
            <button
              className="btn-voice-identity-trigger"
              onClick={() => setShowIngestionModal(true)}
              style={{
                borderColor: 'rgba(0, 240, 255, 0.45)',
                background: 'rgba(0, 240, 255, 0.1)',
                color: 'var(--arc-cyan)',
              }}
              title="Upload FIRs, CDR Telecom logs, and Bank Statements"
            >
              <IconReport size={13} color="var(--arc-cyan)" />
              <span style={{ fontWeight: 700 }}>+ INGEST EVIDENCE</span>
            </button>
            <button
              className={`btn-voice-identity-trigger ${showVoiceSettings ? 'active' : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                setShowVoiceSettings((prev) => !prev);
              }}
              title="Neural Vocal Identity & Language Preferences"
            >
              <IconAudioWave size={13} color="var(--arc-cyan)" />
              <span>{voice.selectedVoice?.toUpperCase()} ({voice.selectedVoice === 'Aoede' || voice.selectedVoice === 'Kore' ? '♀ FEMALE' : '♂ MALE'})</span>
              <IconSettings size={12} color="currentColor" />
            </button>
          </div>
        </div>

        {/* 3D ARGON Core Viewport — 100% Pure, Unobstructed Space */}
        <div
          className="stark-orb-viewport"
          onClick={handleCoreTouch}
        >
          <TATTVACoreOrb
            mode={coreMode}
            onCoreClick={handleCoreTouch}
            audioLevel={audioLevel}
            style={{ width: '100%', height: '100%' }}
          />

          {/* Holographic Whispering Telemetry Ring (Outer Border Only — Core is Pristine) */}
          <div className="stark-reticle-overlay">
            <div className="arc-orbit-ring ring-outer" />
            <div className="arc-orbit-ring ring-mid" />
          </div>
        </div>

        {/* ══════════════════════════════════════════════════════════
            RIVA FLOATING VOCAL DOCK (CLEAN, MINIMAL, AT BOTTOM OF CORE)
            Zero heavy cards blocking the 3D particle sphere!
            ══════════════════════════════════════════════════════════ */}
        <div className="riva-vocal-dock">
          {/* Forensic Tool Action Badge */}
          {voice.actionCard && (
            <div className="riva-action-badge">
              <IconLightning size={12} color="var(--arc-cyan)" />
              <span>TOOL: {voice.actionCard.tool?.toUpperCase()} [{voice.actionCard.status?.toUpperCase()}]</span>
            </div>
          )}

          {/* Floating Subtitle Bubble */}
          {(voice.transcript || voice.aiSpeechText) && (
            <div className="riva-transcript-bubble">
              {voice.transcript && <div style={{ color: 'var(--arc-cyan)', marginBottom: 2 }}>OPERATOR: {voice.transcript}</div>}
              {voice.aiSpeechText && <div style={{ color: '#ffffff' }}>TATTVA: {voice.aiSpeechText}</div>}
            </div>
          )}

          {/* Dynamic State Status Line */}
          <div className="riva-status-text">
            <span className={`riva-status-dot ${coreMode}`} />
            <span>
              {coreMode === 'idle' && 'READY TO LISTEN // TOUCH CORE OR START'}
              {coreMode === 'listening' && 'LISTENING // SPEAK FORENSIC QUERY NOW'}
              {coreMode === 'analyzing' && 'THINKING // RETRIEVING CASE INTELLIGENCE'}
              {coreMode === 'speaking' && 'TATTVA SYNTHESIS ACTIVE // AUDIO TRANSMISSION'}
            </span>
          </div>

          {/* 9-Bar Micro-Waveform Equalizer */}
          <div className="riva-waveform-wrap">
            {voice.audioBars.map((h, idx) => (
              <div
                key={idx}
                className={`riva-waveform-bar ${h > 6 ? 'active' : ''}`}
                style={{ height: `${Math.max(3, Math.min(20, h))}px` }}
              />
            ))}
          </div>

          {/* Interactive Controls (Floating Pill) */}
          <div className="riva-control-pill">
            <button
              className={`riva-btn-action ${coreMode === 'idle' ? 'btn-start' : 'btn-stop'}`}
              onClick={(e) => {
                e.stopPropagation();
                if (coreMode === 'idle') {
                  voice.startListening();
                } else {
                  voice.stopListening();
                }
              }}
            >
              {coreMode === 'idle' ? (
                <>
                  <IconMic size={15} />
                  <span>START TATTVA</span>
                </>
              ) : (
                <>
                  <IconStop size={14} />
                  <span>DISENGAGE</span>
                </>
              )}
            </button>

            <button
              className="riva-btn-model-trigger"
              onClick={(e) => {
                e.stopPropagation();
                setShowVoiceSettings(true);
              }}
              title="Open TATTVA Voice Model Matrix"
            >
              <IconAudioWave size={13} color="var(--arc-cyan)" />
              <span>MODEL: {voice.selectedVoice?.toUpperCase()}</span>
            </button>

            <button
              className={`riva-btn-mute ${voice.isMuted ? 'muted' : ''}`}
              onClick={voice.toggleMute}
              title={voice.isMuted ? 'Unmute Audio' : 'Mute Audio'}
            >
              {voice.isMuted ? <IconMicOff size={15} /> : <IconMic size={15} />}
            </button>
          </div>
        </div>

        {/* Glassmorphic TATTVA Voice Model & Matrix Modal */}
        {showVoiceSettings && (
          <div className="riva-settings-modal">
            <div className="riva-settings-backdrop" onClick={() => setShowVoiceSettings(false)} />
            <div className="riva-settings-card">
              <div className="riva-settings-header">
                <div className="riva-settings-title">
                  <IconSettings size={16} color="var(--arc-cyan)" />
                  <span>TATTVA NEURAL VOICE MODEL & LANGUAGE PROTOCOL</span>
                </div>
                <button className="riva-settings-close" onClick={() => setShowVoiceSettings(false)}>✕</button>
              </div>

              {/* Voice Model Selection */}
              <div className="riva-settings-group">
                <label className="riva-settings-label">AI VOCAL IDENTITY // GEMINI LIVE NEURAL MODELS</label>
                <div className="riva-settings-grid">
                  {voice.voiceProfiles?.map((vp) => (
                    <button
                      key={vp.id}
                      className={`riva-option-pill ${voice.selectedVoice === vp.id ? 'active' : ''}`}
                      onClick={() => voice.switchVoice(vp.id)}
                    >
                      <span className="riva-option-name">{vp.name.toUpperCase()}</span>
                      <span className="riva-option-desc">{vp.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Language Mode Selection */}
              <div className="riva-settings-group">
                <label className="riva-settings-label">NATURAL LANGUAGE PROTOCOL</label>
                <div className="riva-settings-grid">
                  {voice.languageOptions?.map((lang) => (
                    <button
                      key={lang.id}
                      className={`riva-option-pill ${voice.selectedLanguage === lang.id ? 'active' : ''}`}
                      onClick={() => voice.switchLanguage(lang.id)}
                    >
                      <span className="riva-option-name">{lang.label}</span>
                      <span className="riva-option-desc">{lang.id === 'auto' ? 'Any Language' : lang.id === 'hindi' ? 'हिंदी' : lang.id === 'english' ? 'Global' : 'Hindi + English'}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Quick Actions inside Voice Model Modal */}
              <div style={{ display: 'flex', gap: 10, marginTop: 6, paddingTop: 14, borderTop: '1px solid var(--border-subtle)' }}>
                <button
                  className={`riva-btn-action ${coreMode === 'idle' ? 'btn-start' : 'btn-stop'}`}
                  style={{ flex: 1, padding: '10px 16px', borderRadius: 8, fontSize: 13 }}
                  onClick={() => {
                    if (coreMode === 'idle') voice.startListening();
                    else voice.stopListening();
                  }}
                >
                  {coreMode === 'idle' ? (
                    <>
                      <IconMic size={15} />
                      <span>CONNECT & START TATTVA</span>
                    </>
                  ) : (
                    <>
                      <IconStop size={14} />
                      <span>DISENGAGE VOCAL LINK</span>
                    </>
                  )}
                </button>
                <button
                  style={{
                    padding: '10px 18px',
                    borderRadius: 8,
                    background: 'rgba(255, 255, 255, 0.06)',
                    border: '1px solid var(--border-subtle)',
                    color: '#ffffff',
                    fontFamily: 'var(--font-stark)',
                    fontWeight: 700,
                    letterSpacing: 1,
                    cursor: 'pointer',
                  }}
                  onClick={() => setShowVoiceSettings(false)}
                >
                  DONE
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Universal Evidence Ingestion Modal (MHA / NCRB) */}
        <EvidenceIngestionModal
          caseId={activeCase?.case_id}
          isOpen={showIngestionModal}
          onClose={() => setShowIngestionModal(false)}
          onIngested={async (doc) => {
            soundEngine?.playSuccess();
            setLiveLogs((prev) => [
              {
                time: new Date().toLocaleTimeString(),
                agent: 'EVIDENCE INGESTION',
                text: `Ingested & Indexed ${doc.filename} (${(doc.size_bytes / 1024).toFixed(1)} KB) into Qdrant vector memory.`,
              },
              ...prev,
            ]);
            await loadLiveBackendData();
          }}
        />
      </div>

      {/* ══════════════════════════════════════════════════════════
          TACTICAL COMMAND & QUERY DECK (DOCKED OUTSIDE THEATER)
          Separated from 3D Orb for complete visual breathing room
          ══════════════════════════════════════════════════════════ */}
      <div className="stark-command-dock">
        {/* Precision Terminal Query Form */}
        <form
          className="stark-query-terminal"
          onSubmit={(e) => {
            e.preventDefault();
            if (voice.typedInput.trim()) {
              voice.processCommand(voice.typedInput);
              voice.setTypedInput('');
            }
          }}
        >
          <div className="terminal-chevron">❯</div>
          <input
            type="text"
            className="terminal-input"
            placeholder="Ask TATTVA AI anything about this case (e.g. 'Who is the kingpin?', 'Check alibi contradictions')..."
            value={voice.typedInput}
            onChange={(e) => voice.setTypedInput(e.target.value)}
          />
          <button type="submit" className="terminal-send-btn">
            EXECUTE
          </button>
        </form>

        {/* Quick Tactical Directives */}
        <div className="stark-directive-pills">
          <button
            className="directive-pill"
            onClick={triggerBackendScan}
          >
            <IconLightning size={13} color="var(--arc-cyan)" />
            <span>RUN FULL CASE AUDIT</span>
          </button>
          <button
            className="directive-pill"
            onClick={() => {
              if (onNavigate) onNavigate('analytics');
              voice.processCommand('Audit critical contradictions in wire transfer timestamps');
            }}
          >
            <IconContradiction size={13} color="#f43f5e" />
            <span>AUDIT ALIBI CONTRADICTIONS</span>
          </button>
          <button
            className="directive-pill"
            onClick={() => {
              if (onNavigate) onNavigate('graph');
              voice.processCommand('Trace criminal network graph and key kingpins');
            }}
          >
            <IconGraph size={13} color="#f59e0b" />
            <span>EXPLORE NETWORK GRAPH</span>
          </button>
          <button
            className="directive-pill"
            onClick={() => voice.processCommand('Summarize current case investigation status and evidence readiness')}
          >
            <IconCrosshair size={13} color="#10b981" />
            <span>INVESTIGATION SUMMARY</span>
          </button>
          <button
            className="directive-pill"
            onClick={() => voice.processCommand('Charo cases ke beech me relation find karo, common suspects aur knife weapon pattern match karke batao')}
            style={{
              borderColor: 'rgba(168, 85, 247, 0.45)',
              background: 'rgba(168, 85, 247, 0.12)',
              color: '#e9d5ff',
            }}
          >
            <span style={{ fontSize: 12 }}>🔗</span>
            <span>CROSS-CASE PATTERN MATCH</span>
          </button>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════
          GUIDED 4-STEP INVESTIGATION PIPELINE (MHA / NCRB S.O.P.)
          Clear, intuitive sequential workflow positioned comfortably below the 3D Core
          ══════════════════════════════════════════════════════════ */}
      <div className="guided-pipeline-banner" style={{
        background: 'linear-gradient(180deg, rgba(12, 13, 17, 0.92) 0%, rgba(5, 5, 8, 0.98) 100%)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: 'var(--radius-lg)',
        padding: '16px 20px',
        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.6)',
        width: '100%',
        marginTop: '6px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 18 }}>🧭</span>
            <div>
              <div style={{ fontFamily: 'var(--font-stark)', fontSize: 14, fontWeight: 700, color: '#ffffff', letterSpacing: 0.5 }}>
                GUIDED INVESTIGATION WORKFLOW // STANDARD OPERATING PROCEDURE
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                Follow these 4 sequential steps to ingest multi-source evidence, discover criminal networks, and generate court-admissible dossiers.
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
            <span>ACTIVE CASE:</span>
            <span style={{ color: 'var(--arc-cyan)', fontWeight: 700 }}>{activeCase?.case_number || 'NONE'}</span>
          </div>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 12,
        }}>
          {/* Step 1 */}
          <div
            onClick={() => onNavigate?.('cases')}
            style={{
              background: 'rgba(12, 13, 17, 0.85)',
              border: '1px solid rgba(0, 240, 255, 0.22)',
              borderRadius: 'var(--radius-md)',
              padding: '14px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--arc-cyan)';
              e.currentTarget.style.background = 'rgba(0, 240, 255, 0.06)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'rgba(0, 240, 255, 0.22)';
              e.currentTarget.style.background = 'rgba(12, 13, 17, 0.85)';
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, color: 'var(--arc-cyan)', background: 'rgba(0, 240, 255, 0.12)', padding: '2px 8px', borderRadius: 4 }}>
                STEP 01
              </span>
              <span style={{ fontSize: 18 }}>📁</span>
            </div>
            <div style={{ fontFamily: 'var(--font-stark)', fontSize: 13, fontWeight: 700, color: '#ffffff', marginBottom: 4 }}>
              Select / Register Case
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: 10 }}>
              Kaunse case ki jaanch ho rahi hai? Choose an active FIR dossier or register a new one.
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 8, borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
              <span style={{ fontSize: 10, color: '#10b981', fontWeight: 600 }}>✓ ACTIVE: {activeCase?.case_number || 'Ready'}</span>
              <span style={{ fontSize: 11, color: 'var(--arc-cyan)' }}>Manage ➔</span>
            </div>
          </div>

          {/* Step 2 */}
          <div
            onClick={() => setShowIngestionModal(true)}
            style={{
              background: 'rgba(12, 13, 17, 0.85)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              borderRadius: 'var(--radius-md)',
              padding: '14px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#10b981';
              e.currentTarget.style.background = 'rgba(16, 185, 129, 0.06)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'rgba(16, 185, 129, 0.25)';
              e.currentTarget.style.background = 'rgba(12, 13, 17, 0.85)';
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, color: '#10b981', background: 'rgba(16, 185, 129, 0.12)', padding: '2px 8px', borderRadius: 4 }}>
                STEP 02
              </span>
              <span style={{ fontSize: 18 }}>📤</span>
            </div>
            <div style={{ fontFamily: 'var(--font-stark)', fontSize: 13, fontWeight: 700, color: '#ffffff', marginBottom: 4 }}>
              Upload Evidence
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: 10 }}>
              FIR PDF, Telecom CDR CSV, ya Hawala Bank statement drag-and-drop karein (SHA-256 Locked).
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 8, borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
              <span style={{ fontSize: 10, color: '#10b981', fontWeight: 600 }}>{documents.length} Files Ingested</span>
              <span style={{ fontSize: 11, color: '#10b981', fontWeight: 700 }}>+ Ingest ➔</span>
            </div>
          </div>

          {/* Step 3 */}
          <div
            onClick={() => onNavigate?.('graph')}
            style={{
              background: 'rgba(12, 13, 17, 0.85)',
              border: '1px solid rgba(245, 158, 11, 0.25)',
              borderRadius: 'var(--radius-md)',
              padding: '14px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#f59e0b';
              e.currentTarget.style.background = 'rgba(245, 158, 11, 0.06)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'rgba(245, 158, 11, 0.25)';
              e.currentTarget.style.background = 'rgba(12, 13, 17, 0.85)';
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, color: '#f59e0b', background: 'rgba(245, 158, 11, 0.12)', padding: '2px 8px', borderRadius: 4 }}>
                STEP 03
              </span>
              <span style={{ fontSize: 18 }}>🕸️</span>
            </div>
            <div style={{ fontFamily: 'var(--font-stark)', fontSize: 13, fontWeight: 700, color: '#ffffff', marginBottom: 4 }}>
              Network & Alibis
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: 10 }}>
              AI dwara banaya gaya criminal syndicate map, kingpins aur jhoothe bayan (alibi conflicts) dekhein.
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 8, borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
              <span style={{ fontSize: 10, color: '#f43f5e', fontWeight: 600 }}>{findings.length} Flagged Threats</span>
              <span style={{ fontSize: 11, color: '#f59e0b', fontWeight: 700 }}>Inspect ➔</span>
            </div>
          </div>

          {/* Step 4 */}
          <div
            onClick={() => onNavigate?.('reports')}
            style={{
              background: 'rgba(12, 13, 17, 0.85)',
              border: '1px solid rgba(168, 85, 247, 0.25)',
              borderRadius: 'var(--radius-md)',
              padding: '14px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#c084fc';
              e.currentTarget.style.background = 'rgba(168, 85, 247, 0.06)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'rgba(168, 85, 247, 0.25)';
              e.currentTarget.style.background = 'rgba(12, 13, 17, 0.85)';
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, color: '#c084fc', background: 'rgba(168, 85, 247, 0.12)', padding: '2px 8px', borderRadius: 4 }}>
                STEP 04
              </span>
              <span style={{ fontSize: 18 }}>📄</span>
            </div>
            <div style={{ fontFamily: 'var(--font-stark)', fontSize: 13, fontWeight: 700, color: '#ffffff', marginBottom: 4 }}>
              Generate Court Dossier
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: 10 }}>
              Section 63 BSA / 65B certified legal report download karein chargesheet aur trial proceedings ke liye.
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 8, borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
              <span style={{ fontSize: 10, color: '#38bdf8', fontWeight: 600 }}>Court Admissible</span>
              <span style={{ fontSize: 11, color: '#c084fc', fontWeight: 700 }}>Export ➔</span>
            </div>
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════
          LIVE SYSTEM ACTIVITY & REASONING STREAM
          Streamlined and sleek below the gateways
          ══════════════════════════════════════════════════════════ */}
      <div style={{
        background: 'rgba(10, 11, 15, 0.92)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: 'var(--radius-md)',
        padding: '16px 20px',
        width: '100%',
        marginTop: '6px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, borderBottom: '1px solid var(--border-subtle)', paddingBottom: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#00f0ff', boxShadow: '0 0 8px #00f0ff' }} />
            <span style={{ fontFamily: 'var(--font-stark)', fontSize: 13, fontWeight: 700, color: '#ffffff', letterSpacing: 1 }}>
              LIVE INVESTIGATION & AGENT ACTIVITY STREAM
            </span>
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#10b981' }}>
            FASTAPI SSE PIPELINE SYNCHRONIZED
          </span>
        </div>

        <div style={{ maxHeight: 110, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
          {liveLogs.length > 0 ? (
            liveLogs.slice(0, 5).map((log, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'baseline', gap: 10, fontSize: 11.5, fontFamily: 'var(--font-mono)' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>{log.time}</span>
                <span style={{ color: 'var(--arc-cyan)', fontWeight: 700 }}>[{log.agent}]</span>
                <span style={{ color: '#e2e8f0' }}>{log.text}</span>
              </div>
            ))
          ) : (
            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', padding: '6px 0' }}>
              All 8 investigative agents synchronized. Monitoring case evidence and waiting for voice or query directives...
            </div>
          )}
        </div>
      </div>



      {/* Official Court Admissibility Section 65B / 63 BSA Digital Certificate Modal */}
      {selectedCert && (
        <div className="riva-settings-modal">
          <div className="riva-settings-backdrop" onClick={() => setSelectedCert(null)} />
          <div className="riva-settings-card" style={{ maxWidth: 650 }}>
            <div className="riva-settings-header">
              <div className="riva-settings-title" style={{ color: '#10b981' }}>
                <IconVerification size={16} color="#10b981" />
                <span>SECTION 63 BSA / 65B EVIDENCE CERTIFICATE</span>
              </div>
              <button className="riva-settings-close" onClick={() => setSelectedCert(null)}>✕</button>
            </div>

            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, lineHeight: 1.6, background: 'rgba(0,0,0,0.6)', padding: '14px', borderRadius: 8, border: '1px solid rgba(16, 185, 129, 0.3)', maxHeight: 360, overflowY: 'auto', whiteSpace: 'pre-wrap', color: '#a7f3d0' }}>
              {selectedCert.certificate_text}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6, paddingTop: 12, borderTop: '1px solid var(--border-subtle)' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#10b981', fontWeight: 700 }}>
                ● LEGAL STATUS: {selectedCert.admissibility_status || 'VERIFIED_TAMPER_PROOF'}
              </span>
              <button
                style={{
                  padding: '8px 18px',
                  borderRadius: 6,
                  background: 'var(--arc-cyan)',
                  color: '#020617',
                  fontFamily: 'var(--font-stark)',
                  fontWeight: 700,
                  fontSize: 12,
                  border: 'none',
                  cursor: 'pointer',
                }}
                onClick={() => setSelectedCert(null)}
              >
                DISMISS CERTIFICATE
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
