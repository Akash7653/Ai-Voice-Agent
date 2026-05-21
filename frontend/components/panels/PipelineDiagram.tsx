'use client';

import GlassCard from  '@/components/ui/GlassCard';

const FLOW = [
  'User Speech',
  'STT',
  'Language Detection',
  'LLM Agent',
  'Tool Orchestration',
  'Appointment Service',
  'TTS',
  'Audio Response',
];

export default function PipelineDiagram() {
  return (
    <GlassCard title="Architecture Pipeline" icon="◇" highlight="cyan" className="lg:col-span-2">
      <p className="text-xs text-slate-500 mb-3">
        Real-time conversational pipeline — target &lt;450ms from  speech end to first audio response.
      </p>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        {FLOW.map((step, i) => (
          <span key={step} className="flex items-center gap-2">
            <span className="rounded-md border border-cyan-500/20 bg-cyan-500/10 px-2 py-1 text-cyan-200">
              {step}
            </span>
            {i < FLOW.length - 1 && <span className="text-slate-600">↓</span>}
          </span>
        ))}
      </div>
    </GlassCard>
  );
}
