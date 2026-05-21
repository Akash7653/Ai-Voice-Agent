'use client';

import GlassCard from  '@/components/ui/GlassCard';
import { languageLabel } from  '@/lib/languages';

export default function TranscriptPanel({
  userText,
  aiText,
  isStreaming,
  detectedLanguage,
  selectedLanguage,
}: {
  userText: string;
  aiText: string;
  isStreaming: boolean;
  detectedLanguage?: string;
  selectedLanguage?: string;
}) {
  return (
    <GlassCard title="Live Transcript" icon="📝" highlight="cyan">
      <div className="flex flex-wrap gap-2 text-xs">
        {detectedLanguage && (
          <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 text-cyan-200">
            Detected: {languageLabel(detectedLanguage)}
          </span>
        )}
        {selectedLanguage && selectedLanguage !== 'auto' && (
          <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-slate-300">
            Preference: {languageLabel(selectedLanguage)}
          </span>
        )}
      </div>
      {userText ? (
        <div>
          <p className="text-xs text-cyan-400/70 mb-1">You</p>
          <p className="text-sm text-slate-200">{userText}</p>
        </div>
      ) : (
        <p className="text-xs text-slate-500 italic">Waiting for speech…</p>
      )}
      {aiText ? (
        <div>
          <p className="text-xs text-emerald-400/70 mb-1">Agent</p>
          <p className="text-sm text-slate-200">
            {aiText}
            {isStreaming && <span className="animate-pulse ml-1">▌</span>}
          </p>
        </div>
      ) : null}
    </GlassCard>
  );
}
