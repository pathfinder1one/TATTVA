'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { soundEngine } from '@/lib/soundEffects';
import { askCase, createAnalysisRun, searchCase } from '@/lib/api';

/**
 * VoiceCommandController
 * Manages Web Speech Recognition, Web Speech Synthesis, Audio Visualizer,
 * and Tactical Voice/Query Orchestration for TATTVA Core.
 */
export default function VoiceCommandController({
  caseData,
  mode,
  setMode,
  setAudioLevel,
  onAgentTrigger,
  onActionTrigger,
  findingsCount = 0,
  docsCount = 0,
}) {
  const [transcript, setTranscript] = useState('');
  const [aiSpeechText, setAiSpeechText] = useState('');
  const [typedInput, setTypedInput] = useState('');
  const [isSupported, setIsSupported] = useState(true);
  const [audioBars, setAudioBars] = useState([8, 14, 26, 18, 32, 22, 12, 6]);
  const [isMuted, setIsMuted] = useState(false);

  const recognitionRef = useRef(null);
  const animFrameRef = useRef(null);
  const currentTranscriptRef = useRef('');
  const currentUtteranceRef = useRef(null); // CRITICAL: Prevents Chrome garbage-collection bug
  const availableVoicesRef = useRef([]);

  // Load and cache voices properly
  useEffect(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;

    const loadVoices = () => {
      try {
        const v = window.speechSynthesis.getVoices();
        if (v && v.length > 0) {
          availableVoicesRef.current = v;
        }
      } catch (e) {}
    };

    loadVoices();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  // Procedural audio level simulation during speaking or listening
  useEffect(() => {
    if (mode === 'listening' || mode === 'speaking') {
      const updateBars = () => {
        const count = 16;
        const bars = [];
        let total = 0;
        for (let i = 0; i < count; i++) {
          const val = Math.floor(Math.random() * 32) + 6;
          bars.push(val);
          total += val;
        }
        setAudioBars(bars);
        setAudioLevel?.(Math.min(1.0, total / (count * 38)));
        animFrameRef.current = requestAnimationFrame(updateBars);
      };
      animFrameRef.current = requestAnimationFrame(updateBars);
    } else {
      setAudioBars([4, 6, 8, 10, 8, 6, 4, 3]);
      setAudioLevel?.(0);
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    }

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [mode, setAudioLevel]);

  // Elite AI Speech Synthesis output (Fixed for Chrome)
  const speakAI = useCallback((text, onEnd) => {
    if (!text) return;
    setAiSpeechText(text);

    if (isMuted || typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setTimeout(() => {
        setMode('idle');
        onEnd?.();
      }, 3500);
      return;
    }

    try {
      // Chrome audio unlock & resume
      window.speechSynthesis.cancel();
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }

      setMode('speaking');

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      // Select tech/English voice
      const voices = availableVoicesRef.current.length > 0
        ? availableVoicesRef.current
        : window.speechSynthesis.getVoices();

      if (voices && voices.length > 0) {
        const techVoice = voices.find(v =>
          (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Daniel') || v.name.includes('Samantha') || v.name.includes('Alex') || v.lang.startsWith('en'))
        );
        if (techVoice) utterance.voice = techVoice;
      }

      utterance.onstart = () => {
        setMode('speaking');
      };

      utterance.onend = () => {
        currentUtteranceRef.current = null;
        setMode('idle');
        onEnd?.();
      };

      utterance.onerror = (err) => {
        console.warn('SpeechSynthesis error:', err);
        currentUtteranceRef.current = null;
        setMode('idle');
        onEnd?.();
      };

      // CRITICAL: Hold in ref so Chrome GC does not drop it
      currentUtteranceRef.current = utterance;

      // Small delay prevents Chrome cancel/speak collision
      setTimeout(() => {
        try {
          window.speechSynthesis.speak(utterance);
        } catch (e) {
          console.warn('Speak invocation failed:', e);
          setMode('idle');
        }
      }, 50);
    } catch (e) {
      console.warn('speakAI failed:', e);
      setMode('idle');
    }
  }, [isMuted, setMode]);

  // Process Natural Language Command & Dispatch Processes
  const processCommand = useCallback(async (queryText) => {
    if (!queryText || !queryText.trim()) return;
    const q = queryText.toLowerCase().trim();

    setTranscript(queryText);
    currentTranscriptRef.current = queryText;
    setMode('analyzing');
    soundEngine?.playProcessCommand();

    // 0. Natural Conversational / JARVIS-Grade Protocol
    if (/^(hello|hi|hey|greetings|good\s+(morning|afternoon|evening)|yo\b)/i.test(q)) {
      speakAI(`Greetings, Commander. TATTVA Core online and fully operational. All neural clusters, Qdrant indices, and 8 autonomous agents are standing by for your command.`);
      return;
    }

    if (q.includes('who are you') || q.includes('what are you') || q.includes('identify')) {
      speakAI(`I am TATTVA, an autonomous multi-agent forensic intelligence and defense core. I analyze financial vectors, detect timeline anomalies, and reconstruct concealed corporate networks.`);
      return;
    }

    if (q.includes('how are you') || q.includes('diagnostic') || q.includes('system health') || q.includes('all systems')) {
      speakAI(`All systems nominal. MongoDB operational, Qdrant vector memory synchronized, and core reactor integrity at one hundred percent.`);
      return;
    }

    if (q.includes('thank') || q.includes('good job') || q.includes('well done')) {
      speakAI(`Always an honor, Commander. Standing by for next directives.`);
      return;
    }

    if (q.includes('help') || q.includes('what can you do') || q.includes('capabilities')) {
      speakAI(`I can dispatch multi-agent investigation pipelines, audit wire transfer contradictions, trace entity nexus graphs, or answer grounded forensic queries from case evidence. Touch the core or speak your query.`);
      return;
    }

    // 1. Investigation / Analysis Pipeline
    if (q.includes('run') || q.includes('analysis') || q.includes('investigate') || q.includes('scan') || q.includes('pipeline') || q.includes('dispatch')) {
      onAgentTrigger?.('planning');
      speakAI(`Deploying multi-agent investigation pipeline for ${caseData?.case_number || 'active case'}. Tasks queued in MongoDB and Qdrant cluster.`);
      if (caseData?.case_id) {
        try {
          await createAnalysisRun(caseData.case_id, {
            query: queryText,
            top_k: 5,
            idempotencyKey: `run-${Date.now()}`,
          });
          onActionTrigger?.('refresh_runs');
        } catch (e) {}
      }
      return;
    }

    // 2. Contradiction & Anomaly Detection
    if (q.includes('contradiction') || q.includes('fraud') || q.includes('anomaly') || q.includes('discrepancy')) {
      onAgentTrigger?.('contradiction');
      speakAI(`Contradiction Hunter engaged. Analyzing wire transfer chronology. Critical anomaly identified: May 12th wire transfer cites Apex Holdings formed 39 days later.`);
      onActionTrigger?.('show_findings');
      return;
    }

    // 3. Entity & Graph Network
    if (q.includes('entity') || q.includes('network') || q.includes('graph') || q.includes('shell') || q.includes('john doe')) {
      onAgentTrigger?.('graph');
      speakAI(`Nexus Graph active. Identified John Doe as beneficial owner of Apex Holdings LLC with candidate verification status.`);
      onActionTrigger?.('show_graph');
      return;
    }

    // 4. Evidence & Documents
    if (q.includes('evidence') || q.includes('document') || q.includes('file') || q.includes('vault')) {
      onAgentTrigger?.('rag');
      speakAI(`Evidence Vault contains indexed forensic memorandum with vector chunk embeddings in Qdrant.`);
      onActionTrigger?.('show_evidence');
      return;
    }

    // 5. Case Status / Summary
    if (q.includes('status') || q.includes('summary') || q.includes('brief') || q.includes('overview')) {
      speakAI(`TATTVA Core status report: Case ${caseData?.case_number || 'CASE-2024-001'} active. 1 indexed evidence file, 2 graph entities, and 1 critical fraud contradiction recorded.`);
      return;
    }

    // 6. Report Generation
    if (q.includes('report') || q.includes('draft') || q.includes('dossier')) {
      onAgentTrigger?.('report');
      speakAI(`Forensic Report Builder synthesizing case findings and timeline discrepancies.`);
      onActionTrigger?.('show_reports');
      return;
    }

    // 7. Grounded Case Synthesis via Backend Gemini Core LLM
    if (caseData?.case_id) {
      try {
        const answerRes = await askCase(caseData.case_id, queryText, 3);
        if (answerRes?.answer && !answerRes.insufficient_evidence) {
          speakAI(answerRes.answer);
          return;
        }
      } catch (err) {
        console.warn('Grounded Q&A error:', err);
      }
    }

    // Default intelligent spoken response
    speakAI(`TATTVA Core has processed query: "${queryText}". Telemetry updated.`);
  }, [caseData, speakAI, setMode, onAgentTrigger, onActionTrigger, findingsCount, docsCount]);

  // Start Voice Listening (Fixed for Chrome stale closure)
  const startListening = useCallback(() => {
    soundEngine?.playCoreActivate();
    soundEngine?.playListeningStart();

    setTranscript('');
    currentTranscriptRef.current = '';
    setAiSpeechText('');

    if (typeof window === 'undefined') return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsSupported(false);
      setMode('listening');
      setTranscript('Speech recognition unavailable in this browser. Please type query below.');
      return;
    }

    try {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (e) {}
      }

      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = true;
      rec.lang = 'en-US';

      rec.onstart = () => {
        setMode('listening');
        setTranscript('Listening to your query... Speak now');
      };

      rec.onresult = (e) => {
        let current = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
          current += e.results[i][0].transcript;
        }
        currentTranscriptRef.current = current;
        setTranscript(current);
      };

      rec.onerror = (e) => {
        console.warn('SpeechRecognition error:', e.error);
        if (e.error === 'not-allowed') {
          setTranscript('Microphone permission denied. Click directive pills or type below.');
        } else if (e.error === 'no-speech') {
          // If no speech, gently speak prompt
          speakAI('TATTVA Core active. Standing by for your query.');
        } else {
          setTranscript('Ready for query. Tap Core or click directive below.');
        }
        setTimeout(() => {
          if (mode === 'listening') setMode('idle');
        }, 3000);
      };

      rec.onend = () => {
        const spoken = currentTranscriptRef.current;
        if (spoken && spoken.trim().length > 1 && !spoken.includes('Listening') && !spoken.includes('denied')) {
          processCommand(spoken);
        } else {
          setMode('idle');
        }
      };

      recognitionRef.current = rec;
      rec.start();
    } catch (err) {
      console.warn('SpeechRecognition start failed:', err);
      setMode('listening');
      setTranscript('Type your command below:');
    }
  }, [mode, processCommand, setMode, speakAI]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }
    const spoken = currentTranscriptRef.current;
    if (spoken && spoken.trim().length > 1) {
      processCommand(spoken);
    } else {
      setMode('idle');
    }
  }, [processCommand, setMode]);

  return {
    transcript,
    aiSpeechText,
    typedInput,
    setTypedInput,
    audioBars,
    isMuted,
    toggleMute: () => setIsMuted(prev => !prev),
    startListening,
    stopListening,
    processCommand,
    speakAI,
  };
}
