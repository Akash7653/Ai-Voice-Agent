'use client';

import GlassCard from '@/components/ui/GlassCard';

export default function SchedulingPanel({
  suggestedSlots,
  conflictMessage,
}: {
  suggestedSlots: string[];
  conflictMessage?: string;
}) {
  const hasSlots = suggestedSlots.length > 0;

  return (
    <GlassCard title="Scheduling" icon="📅" highlight="rose">
      {conflictMessage && (
        <p className="text-xs text-amber-200/90 leading-relaxed">{conflictMessage}</p>
      )}
      {hasSlots ? (
        <div>
          <p className="text-xs text-rose-400/70 mb-2">Alternative slots (from agent response)</p>
          <ul className="space-y-1">
            {suggestedSlots.map((slot) => (
              <li key={slot} className="text-sm text-rose-200">
                • {slot}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="text-xs text-slate-500">
          Conflict detection and alternative slots appear when the agent suggests them in the response.
        </p>
      )}
    </GlassCard>
  );
}
