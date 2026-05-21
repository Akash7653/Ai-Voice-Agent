'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AIOrb } from '@/components/AIOrb';
import { Waveform } from '@/components/Waveform';
import ControlBar from '@/components/voice/ControlBar';
import TranscriptPanel from '@/components/panels/TranscriptPanel';
import ReasoningPanel from '@/components/panels/ReasoningPanel';
import SessionMemoryPanel from '@/components/panels/SessionMemoryPanel';
import PersistentMemoryPanel from '@/components/panels/PersistentMemoryPanel';
import LatencyPanel from '@/components/panels/LatencyPanel';
import SchedulingPanel from '@/components/panels/SchedulingPanel';
import PipelineStatus from '@/components/panels/PipelineStatus';
import PageHeader from '@/components/layout/PageHeader';
import { useApp } from '@/context/AppContext';
import {
  useVoiceCapture,
  useVoiceWebSocket,
  useAudioPlayback,
  MIN_RECORDING_BYTES,
  MIN_RECORDING_MS,
} from '@/hooks/useVoice';
import { usePatientData } from '@/hooks/usePatientData';
import { extractSuggestedSlots } from '@/lib/languages';
import { PipelineStage, VoiceStatus } from '@/types';

export default function VoiceConsole() {
  const { apiUrl, patientId } = useApp();
  const { patient, refresh: refreshPatient } = usePatientData(apiUrl, patientId);

  const [status, setStatus] = useState<VoiceStatus>('initializing');
  const [autoListen, setAutoListen] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [language, setLanguage] = useState('en');
  const [userText, setUserText] = useState('');
  const [aiText, setAiText] = useState('');
  const [pipelineStage, setPipelineStage] = useState<PipelineStage>('idle');
  const [captureHint, setCaptureHint] = useState<string | null>(null);
  const autoTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const listeningRef = useRef(false);
  const statusRef = useRef<VoiceStatus>('initializing');

  const { startRecording, stopRecording, isRecording, audioLevel, getRecordingDurationMs } =
    useVoiceCapture();
  const { playAudio } = useAudioPlayback();

  const voice = useVoiceWebSocket(apiUrl, patientId);

  statusRef.current = status;
  listeningRef.current = isRecording;

  const clearAutoTimer = () => {
    if (autoTimerRef.current) {
      clearTimeout(autoTimerRef.current);
      autoTimerRef.current = null;
    }
  };

  const startListening = useCallback(async () => {
    if (listeningRef.current || statusRef.current === 'thinking') return;
    try {
      voice.resetTurn();
      setCaptureHint(null);
      setUserText('');
      setAiText('');
      setStatus('listening');
      setPipelineStage('speech');
      await startRecording();
    } catch {
      setStatus('error');
    }
  }, [voice, startRecording]);

  const stopListening = useCallback(async () => {
    if (!listeningRef.current) return;
    try {
      setStatus('thinking');
      setPipelineStage('stt');
      const audio = await stopRecording();
      const durationMs = getRecordingDurationMs();

      if (!audio || audio.byteLength < MIN_RECORDING_BYTES || durationMs < MIN_RECORDING_MS) {
        setCaptureHint(
          `Recording too short (${(durationMs / 1000).toFixed(1)}s). Speak for at least 2 seconds, then press Stop.`
        );
        setStatus('ready');
        setPipelineStage('idle');
        if (autoListen) {
          clearAutoTimer();
          autoTimerRef.current = setTimeout(() => startListening(), 1500);
        }
        return;
      }
      setCaptureHint(null);

      await voice.sendRecording(audio);
      await voice.endAudio();
    } catch {
      setStatus('error');
    }
  }, [voice, stopRecording]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setStatus('initializing');
        await voice.connect();
        if (!mounted) return;
        setStatus('ready');
        // User presses Listen — avoid auto-start before first successful turn
      } catch {
        if (mounted) setStatus('error');
      }
    })();
    return () => {
      mounted = false;
      clearAutoTimer();
      voice.disconnect();
    };
  }, [apiUrl, patientId]);

  useEffect(() => {
    if (voice.transcript) {
      setUserText(voice.transcript);
      setPipelineStage('language');
    }
  }, [voice.transcript]);

  useEffect(() => {
    if (voice.reasoning) {
      setPipelineStage('llm');
      if (voice.reasoning.intent && voice.reasoning.intent !== 'small_talk') {
        setPipelineStage('tools');
      }
    }
  }, [voice.reasoning]);

  useEffect(() => {
    if (!voice.responseText) return;
    setAiText(voice.responseText);
    setStatus('speaking');
    setPipelineStage('tts');

    const run = async () => {
      if (voice.responseAudio) {
        setPipelineStage('audio');
        try {
          await playAudio(voice.responseAudio);
        } catch {
          /* browser may block autoplay */
        }
      }
      setPipelineStage('idle');
      setStatus('ready');
      refreshPatient();
      if (autoListen) {
        clearAutoTimer();
        autoTimerRef.current = setTimeout(() => startListening(), 1200);
      }
    };
    run();
  }, [voice.responseText, voice.responseAudio]);

  useEffect(() => {
    if (voice.latencyMetrics) setPipelineStage('idle');
  }, [voice.latencyMetrics]);

  useEffect(() => {
    if (voice.error) {
      setStatus('error');
      setCaptureHint(null);
    }
  }, [voice.error]);

  useEffect(() => {
    if (!isRecording) {
      setRecordingSeconds(0);
      return;
    }
    const t0 = Date.now();
    const id = setInterval(() => setRecordingSeconds(Math.floor((Date.now() - t0) / 1000)), 200);
    return () => clearInterval(id);
  }, [isRecording]);

  const suggestedSlots = extractSuggestedSlots(aiText);
  const conflictHint =
    /already booked|not available|alternative|slot/i.test(aiText) ? aiText : undefined;

  const orbStatus =
    status === 'listening'
      ? 'listening'
      : status === 'speaking'
        ? 'speaking'
        : status === 'thinking'
          ? 'thinking'
          : 'idle';

  const headerStatus =
    status === 'error'
      ? { text: voice.error ?? 'error', tone: 'error' as const }
      : !voice.isConnected
        ? { text: 'disconnected', tone: 'warn' as const }
        : { text: status, tone: 'ok' as const };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader status={headerStatus.text} statusTone={headerStatus.tone} />

      <div className="flex-1 overflow-auto">
        <div className="grid-backdrop pointer-events-none fixed inset-0 opacity-30" />
        <div className="relative mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6">
          {(captureHint || (voice.error && status === 'error')) && (
            <div className="glass-panel border border-rose-500/30 p-4 text-sm text-rose-200">
              {captureHint ?? voice.error}
            </div>
          )}

          <div className="flex justify-center">
            <AIOrb status={orbStatus} audioLevel={audioLevel} pulse={status === 'thinking'} />
          </div>

          <div className="mx-auto max-w-2xl space-y-2">
            <Waveform audioLevel={audioLevel} isRecording={isRecording} />
            {isRecording && (
              <p className="text-center text-xs text-cyan-300/90">
                Recording… {recordingSeconds}s — speak clearly, then press <strong>Stop</strong>
              </p>
            )}
          </div>

          <ControlBar
            isRecording={isRecording}
            isThinking={status === 'thinking'}
            isConnected={voice.isConnected}
            autoListen={autoListen}
            language={language}
            onListen={startListening}
            onStop={stopListening}
            onToggleAuto={() => setAutoListen((a) => !a)}
            onLanguageChange={setLanguage}
          />

          <PipelineStatus activeStage={pipelineStage} />

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            <TranscriptPanel
              userText={userText}
              aiText={aiText}
              isStreaming={status === 'speaking'}
              detectedLanguage={voice.detectedLanguage}
              selectedLanguage={patient?.preferred_language ?? language}
            />
            <ReasoningPanel trace={voice.reasoning} />
            <SessionMemoryPanel
              sessionId={voice.sessionId}
              intent={voice.reasoning?.intent}
              state={status === 'thinking' ? 'processing' : status}
            />
            <PersistentMemoryPanel patient={patient} />
            <LatencyPanel metrics={voice.latencyMetrics} />
            <SchedulingPanel suggestedSlots={suggestedSlots} conflictMessage={conflictHint} />
          </div>
        </div>
      </div>
    </div>
  );
}
