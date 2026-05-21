'use client';

import GlassCard from '@/components/ui/GlassCard';
import { LatencyMetrics } from '@/types';

const TARGET_MS = 450;
const STAGES = [
  { key: 'stt', label: 'STT' },
  { key: 'llm', label: 'LLM' },
  { key: 'tools', label: 'Tools' },
  { key: 'tts', label: 'TTS' },
] as const;

export default function LatencyPanel({ metrics }: { metrics: LatencyMetrics | null }) {
  if (!metrics) {
    return (
      <GlassCard title="Latency" icon="⏱️" highlight="teal">
        <p className="text-xs text-slate-500">
          Target: &lt;{TARGET_MS}ms speech-end → first audio. Metrics log after each turn.
        </p>
      </GlassCard>
    );
  }

  const total = metrics.total_latency_ms ?? 0;
  const pass = total > 0 && total < TARGET_MS;
  const breakdown = metrics.breakdown ?? {};

  return (
    <GlassCard title="Latency" icon="⏱️" highlight="teal">
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs text-slate-400">Total (speech end → response)</p>
          <p className={`text-2xl font-bold ${pass ? 'text-emerald-300' : total > TARGET_MS ? 'text-amber-300' : 'text-slate-200'}`}>
            {total.toFixed(0)}ms
          </p>
        </div>
        <span
          className={`text-xs font-semibold px-2 py-1 rounded-full ${
            pass ? 'bg-emerald-500/20 text-emerald-300' : total > 0 ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-700 text-slate-400'
          }`}
        >
          {total === 0 ? '—' : pass ? `✓ &lt;${TARGET_MS}ms` : `⚠ &gt;${TARGET_MS}ms`}
        </span>
      </div>
      <div className="space-y-2">
        {STAGES.map(({ key, label }) => {
          const ms = breakdown[key] ?? 0;
          const pct = total > 0 ? Math.min(100, (ms / total) * 100) : 0;
          return (
            <div key={key}>
              <div className="flex justify-between text-xs mb-0.5">
                <span className="text-slate-400">{label}</span>
                <span className="text-slate-200">{ms.toFixed(0)}ms</span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 to-teal-400 transition-all"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
}
