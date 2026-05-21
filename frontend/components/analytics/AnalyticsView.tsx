'use client';

import React from 'react';
import PageHeader from '@/components/layout/PageHeader';
import GlassCard from '@/components/ui/GlassCard';
import LatencyPanel from '@/components/panels/LatencyPanel';
import { useApp } from '@/context/AppContext';
import { usePatientData } from '@/hooks/usePatientData';

const TARGET = 450;

export default function AnalyticsView() {
  const { apiUrl, patientId } = useApp();
  const { latencyStats, loading } = usePatientData(apiUrl, patientId);

  const avg = latencyStats?.avg_total_latency ?? 0;
  const pass = avg > 0 && avg < TARGET;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader status="latency" />
      <div className="flex-1 overflow-auto px-4 py-8 sm:px-6">
        <div className="mx-auto max-w-4xl space-y-6">
          <GlassCard title="Latency evaluation" icon="📊" highlight="teal">
            <p className="text-xs text-slate-400 mb-4">
              Assignment target: &lt;{TARGET}ms from speech end to first audio response. STT, LLM, Tools, and TTS
              are measured per turn via WebSocket <code className="text-teal-300">latency_metrics</code> and logged server-side.
            </p>
            {loading ? (
              <p className="text-slate-500 text-sm">Loading stats…</p>
            ) : latencyStats ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                <Metric label="Average" value={`${avg.toFixed(0)}ms`} highlight={pass} />
                <Metric label="Min" value={`${latencyStats.min_latency.toFixed(0)}ms`} />
                <Metric label="Max" value={`${latencyStats.max_latency.toFixed(0)}ms`} />
                <Metric label="Samples" value={String(latencyStats.metrics_count)} />
              </div>
            ) : (
              <p className="text-sm text-slate-500">
                No historical stats yet. Complete a voice turn to populate metrics.
              </p>
            )}
          </GlassCard>

          <div className="grid md:grid-cols-2 gap-4">
            <LatencyPanel metrics={null} />
            <GlassCard title="Component targets" icon="◎" highlight="cyan">
              <ul className="text-xs text-slate-400 space-y-2">
                <li>STT (Whisper): ~100–150ms</li>
                <li>LLM (GPT-4o-mini): ~150–250ms</li>
                <li>Tools: ~50–100ms</li>
                <li>TTS: ~100–150ms</li>
              </ul>
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="rounded-lg border border-white/5 bg-white/5 p-3">
      <p className={`text-lg font-bold ${highlight ? 'text-emerald-300' : 'text-white'}`}>{value}</p>
      <p className="text-[10px] text-slate-500">{label}</p>
    </div>
  );
}
