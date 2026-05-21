'use client';

import React from  'react';
import GlassCard from  '@/components/ui/GlassCard';
import { PipelineStage } from  '@/types';

const STAGES: { id: PipelineStage; label: string }[] = [
  { id: 'speech', label: 'Speech' },
  { id: 'stt', label: 'STT' },
  { id: 'language', label: 'Language' },
  { id: 'llm', label: 'LLM' },
  { id: 'tools', label: 'Tools' },
  { id: 'tts', label: 'TTS' },
  { id: 'audio', label: 'Audio' },
];

export default function PipelineStatus({ activeStage }: { activeStage: PipelineStage }) {
  const activeIdx = STAGES.findIndex((s) => s.id === activeStage);

  return (
    <GlassCard title="Pipeline" icon="⟳" highlight="cyan" className="lg:col-span-2">
      <div className="flex flex-wrap items-center gap-1 text-[10px] sm:text-xs">
        {STAGES.map((stage, i) => {
          const done = activeIdx > i;
          const active = stage.id === activeStage;
          return (
            <React.Fragment key={stage.id}>
              <span
                className={`px-2 py-1 rounded-md border transition ${
                  active
                    ? 'border-cyan-400/50 bg-cyan-500/20 text-cyan-200 animate-pulse'
                    : done
                      ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                      : 'border-white/5 bg-white/5 text-slate-500'
                }`}
              >
                {stage.label}
              </span>
              {i < STAGES.length - 1 && <span className="text-slate-600">→</span>}
            </React.Fragment>
          );
        })}
      </div>
    </GlassCard>
  );
}
