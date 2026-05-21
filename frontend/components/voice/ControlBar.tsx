'use client';

import React from 'react';
import { LANGUAGES } from '@/lib/languages';

export default function ControlBar({
  isRecording,
  isThinking,
  isConnected,
  autoListen,
  language,
  onListen,
  onStop,
  onToggleAuto,
  onLanguageChange,
}: {
  isRecording: boolean;
  isThinking: boolean;
  isConnected: boolean;
  autoListen: boolean;
  language: string;
  onListen: () => void;
  onStop: () => void;
  onToggleAuto: () => void;
  onLanguageChange: (code: string) => void;
}) {
  return (
    <div className="flex flex-col items-center gap-4">
      <div className="flex flex-wrap justify-center gap-2">
        {LANGUAGES.map((lang) => (
          <button
            key={lang.code}
            type="button"
            onClick={() => onLanguageChange(lang.code)}
            className={`px-3 py-1.5 text-xs rounded-lg border transition ${
              language === lang.code
                ? 'border-cyan-400/50 bg-cyan-500/20 text-cyan-100'
                : 'border-white/10 bg-white/5 text-slate-400 hover:text-white'
            }`}
          >
            {lang.native}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap justify-center gap-3">
        <button
          type="button"
          onClick={onListen}
          disabled={!isConnected || isRecording || isThinking}
          className="btn btn-primary px-6 py-3 disabled:opacity-40"
        >
          Listen
        </button>
        <button
          type="button"
          onClick={onStop}
          disabled={!isRecording}
          className="px-6 py-3 rounded-lg bg-gradient-to-r from-amber-500/80 to-orange-600/80 text-white font-semibold disabled:opacity-40"
        >
          Stop
        </button>
        <button
          type="button"
          onClick={onToggleAuto}
          className={`px-6 py-3 rounded-lg font-semibold text-sm ${
            autoListen
              ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-200'
              : 'bg-slate-800 border border-white/10 text-slate-400'
          }`}
        >
          {autoListen ? 'Auto-listen on' : 'Auto-listen off'}
        </button>
      </div>

      <p className="text-[10px] text-slate-500">
        {isConnected ? 'WebSocket connected' : 'Connecting…'} · Press Listen → speak 2+ seconds → Stop
      </p>
    </div>
  );
}
