'use client';

import GlassCard from '@/components/ui/GlassCard';
export default function SessionMemoryPanel({
  sessionId,
  intent,
  state,
  contextSummary,
}: {
  sessionId: string | null;
  intent?: string;
  state?: string;
  contextSummary?: string;
}) {
  return (
    <GlassCard title="Session Memory" icon="🧠" highlight="amber">
      <p className="text-[10px] text-slate-500 leading-relaxed">
        Redis-backed context for the active call — current intent, pending confirmations, conversation state.
      </p>
      <div className="space-y-2 text-xs">
        <Row label="Session ID" value={sessionId ? `${sessionId.slice(0, 8)}…` : '—'} mono />
        <Row label="State" value={state ?? 'listening'} />
        <Row label="Pending intent" value={intent?.replace(/_/g, ' ') ?? '—'} />
      </div>
      {contextSummary && (
        <p className="text-xs text-amber-200/80 border-t border-white/5 pt-2">{contextSummary}</p>
      )}
    </GlassCard>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-slate-500">{label}</span>
      <span className={`text-slate-200 ${mono ? 'font-mono' : ''}`}>{value}</span>
    </div>
  );
}
