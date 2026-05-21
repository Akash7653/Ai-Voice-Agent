'use client';

import GlassCard from  '@/components/ui/GlassCard';
import { ReasoningTrace } from  '@/types';

export default function ReasoningPanel({ trace }: { trace: ReasoningTrace | null }) {
  if (!trace) {
    return (
      <GlassCard title="Reasoning Trace" icon="⚡" highlight="purple">
        <p className="text-xs text-slate-500">
          Agent reasoning appears here after each utterance — intent, confidence, entities, and chain-of-thought (evaluation requirement).
        </p>
      </GlassCard>
    );
  }

  const pct = Math.round((trace.confidence ?? 0) * 100);

  return (
    <GlassCard title="Reasoning Trace" icon="⚡" highlight="purple">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-400">Intent</span>
        <span className="font-semibold text-purple-200 capitalize">
          {trace.intent?.replace(/_/g, ' ') ?? '—'}
        </span>
      </div>
      <div>
        <div className="flex justify-between text-xs text-slate-400 mb-1">
          <span>Confidence</span>
          <span>{pct}%</span>
        </div>
        <div className="h-2 rounded-full bg-purple-950 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from -emerald-400 to-purple-500 transition-all"
            style={{ width: `${Math.min(100, pct)}%` }}
          />
        </div>
      </div>
      {trace.reasoning && (
        <p className="text-xs text-slate-400 leading-relaxed border-l-2 border-purple-500/40 pl-3">
          {trace.reasoning}
        </p>
      )}
      {trace.entities && Object.keys(trace.entities).length > 0 && (
        <div className="rounded-lg border border-white/5 bg-white/5 p-2 space-y-1 text-xs max-h-32 overflow-auto">
          {Object.entries(trace.entities).map(([k, v]) =>
            v != null && v !== '' ? (
              <div key={k} className="flex justify-between gap-2">
                <span className="text-slate-500 capitalize">{k.replace(/_/g, ' ')}</span>
                <span className="text-slate-200 font-medium text-right">{String(v)}</span>
              </div>
            ) : null
          )}
        </div>
      )}
    </GlassCard>
  );
}
