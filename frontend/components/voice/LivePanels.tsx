'use client';

import React from  'react';
import { LatencyMetrics as BackendLatency } from  '@/types';

export function latencyToPanel(metrics: BackendLatency | null) {
  if (!metrics) return null;
  const b = metrics.breakdown ?? {};
  return {
    total: metrics.total_latency_ms,
    stt: b.stt,
    llm: b.llm,
    tools: b.tools,
    tts: b.tts,
  };
}

export type PanelLatency = ReturnType<typeof latencyToPanel>;

export interface TranscriptPanelProps {
  userText: string;
  aiText: string;
  isStreaming: boolean;
}

export const TranscriptPanel: React.FC<TranscriptPanelProps> = ({
  userText,
  aiText,
  isStreaming,
}) => (
  <div className="glass-panel p-4 space-y-3">
    <h3 className="text-sm font-semibold uppercase tracking-wider text-cyan-300">Transcript</h3>
    {userText ? (
      <div className="space-y-1">
        <p className="text-xs text-cyan-400/70">You said</p>
        <p className="text-sm text-gray-300">{userText}</p>
      </div>
    ) : (
      <p className="text-xs text-slate-500">Waiting for speech…</p>
    )}
    {aiText && (
      <div className="space-y-1 border-t border-white/5 pt-3">
        <p className="text-xs text-emerald-400/70">AI response</p>
        <p className="text-sm text-gray-300">
          {aiText}
          {isStreaming && <span className="animate-pulse"> …</span>}
        </p>
      </div>
    )}
  </div>
);

export interface ReasoningPanelProps {
  intent?: string;
  confidence?: number;
  entities?: Record<string, unknown>;
  reasoning?: string;
}

export const ReasoningPanel: React.FC<ReasoningPanelProps> = ({
  intent,
  confidence = 0,
  entities,
  reasoning,
}) => (
  <div className="glass-panel p-4 space-y-3">
    <h3 className="text-sm font-semibold uppercase tracking-wider text-purple-300">Reasoning</h3>
    {intent && (
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-purple-400/70">Intent</span>
        <span className="text-sm font-semibold capitalize text-purple-200">
          {intent.replace(/_/g, ' ')}
        </span>
      </div>
    )}
    {confidence > 0 && (
      <div>
        <div className="mb-1 flex justify-between text-xs text-purple-400/70">
          <span>Confidence</span>
          <span>{(confidence * 100).toFixed(0)}%</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-purple-950">
          <div
            className="h-full bg-gradient-to-r from -emerald-400 to-purple-500"
            style={{ width: `${Math.min(confidence * 100, 100)}%` }}
          />
        </div>
      </div>
    )}
    {reasoning && <p className="text-xs leading-relaxed text-slate-400">{reasoning}</p>}
    {entities && Object.keys(entities).length > 0 && (
      <div className="space-y-1 rounded-lg border border-white/5 bg-white/5 p-2 text-xs">
        {Object.entries(entities)
          .filter(([, v]) => v != null && v !== '')
          .slice(0, 4)
          .map(([k, v]) => (
            <div key={k} className="flex justify-between gap-2">
              <span className="text-slate-500">{k.replace(/_/g, ' ')}</span>
              <span className="font-medium text-slate-200">{String(v)}</span>
            </div>
          ))}
      </div>
    )}
  </div>
);

export interface MemoryPanelProps {
  language?: string;
  patientId?: string;
  appointmentCount?: number;
}

export const MemoryPanel: React.FC<MemoryPanelProps> = ({
  language,
  patientId,
  appointmentCount = 0,
}) => (
  <div className="glass-panel p-4 space-y-3">
    <h3 className="text-sm font-semibold uppercase tracking-wider text-amber-300">Session</h3>
    {patientId && (
      <div className="flex justify-between text-xs">
        <span className="text-amber-400/70">Patient</span>
        <span className="font-mono text-amber-200">{patientId}</span>
      </div>
    )}
    {language && (
      <div className="flex justify-between text-xs">
        <span className="text-amber-400/70">Language</span>
        <span className="font-semibold uppercase text-amber-200">{language}</span>
      </div>
    )}
    <div className="flex justify-between text-xs">
      <span className="text-amber-400/70">Appointments</span>
      <span className="text-amber-200">{appointmentCount}</span>
    </div>
  </div>
);

export interface LatencyPanelProps {
  metrics: NonNullable<PanelLatency>;
}

export const LatencyPanel: React.FC<LatencyPanelProps> = ({ metrics }) => {
  const target = 450;
  const total = metrics.total ?? 0;
  const ok = total < target;

  return (
    <div className="glass-panel p-4 space-y-3">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-teal-300">Latency</h3>
      <div className={`text-2xl font-bold ${ok ? 'text-emerald-400' : 'text-amber-400'}`}>
        {total.toFixed(0)}ms
      </div>
      <p className="text-[10px] text-slate-500">Target &lt; {target}ms {ok ? '✓' : '⚠'}</p>
      <div className="space-y-1 text-xs text-slate-400">
        {metrics.stt != null && <p>STT: {metrics.stt.toFixed(0)}ms</p>}
        {metrics.llm != null && <p>LLM: {metrics.llm.toFixed(0)}ms</p>}
        {metrics.tools != null && <p>Tools: {metrics.tools.toFixed(0)}ms</p>}
        {metrics.tts != null && <p>TTS: {metrics.tts.toFixed(0)}ms</p>}
      </div>
    </div>
  );
};
