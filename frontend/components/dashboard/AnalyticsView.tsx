'use client';

import React from  'react';
import PageHeader from  '@/components/layout/PageHeader';
import { LatencyStats } from  '@/types';

export default function AnalyticsView({
  latencyStats,
  loading,
}: {
  latencyStats: LatencyStats | null;
  loading: boolean;
}) {
  const target = 450;
  const avg = latencyStats?.avg_total_latency ?? 0;
  const ok = avg > 0 && avg < target;

  return (
    <div className="flex h-full flex-col">
      <PageHeader status={loading ? 'loading' : 'ready'} />
      <div className="flex-1 overflow-auto p-6">
        <h2 className="mb-4 text-lg font-semibold text-white">Latency analytics</h2>
        {latencyStats && latencyStats.metrics_count > 0 ? (
          <div className="grid max-w-lg gap-4 sm:grid-cols-2">
            <div className="glass-panel p-5">
              <p className="text-xs uppercase tracking-wider text-slate-500">Average</p>
              <p className={`mt-1 text-3xl font-bold ${ok ? 'text-emerald-400' : 'text-amber-400'}`}>
                {avg.toFixed(0)}ms
              </p>
              <p className="mt-1 text-[10px] text-slate-500">Target &lt; {target}ms</p>
            </div>
            <div className="glass-panel p-5">
              <p className="text-xs uppercase tracking-wider text-slate-500">Range</p>
              <p className="mt-1 text-lg text-white">
                {latencyStats.min_latency.toFixed(0)} – {latencyStats.max_latency.toFixed(0)}ms
              </p>
            </div>
            <div className="glass-panel p-5 sm:col-span-2">
              <p className="text-xs uppercase tracking-wider text-slate-500">Samples</p>
              <p className="mt-1 text-2xl font-bold text-cyan-300">{latencyStats.metrics_count}</p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-500">
            No aggregated latency data yet. Complete voice interactions to populate metrics.
          </p>
        )}
      </div>
    </div>
  );
}
