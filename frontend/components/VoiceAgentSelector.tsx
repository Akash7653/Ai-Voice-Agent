"use client";

import React, { useState, useEffect } from  "react";

type Selection = {
  gender: "male" | "female";
  tone: "calm" | "energetic" | "neutral";
  style: "formal" | "casual";
};

const defaultSelection: Selection = { gender: "female", tone: "calm", style: "formal" };

const VoiceAgentSelector: React.FC<{ onChange?: (s: Selection) => void }> = ({ onChange }) => {
  const [sel, setSel] = useState<Selection>(defaultSelection);

  useEffect(() => {
    onChange?.(sel);
  }, [sel, onChange]);

  return (
    <div className="space-y-3">
      <div>
        <div className="text-xs text-slate-400 mb-1">Gender</div>
        <div className="flex gap-2">
          <button className={`px-2 py-1 text-xs rounded ${sel.gender === 'female' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-200'}`} onClick={() => setSel({...sel, gender: 'female'})}>Female</button>
          <button className={`px-2 py-1 text-xs rounded ${sel.gender === 'male' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-200'}`} onClick={() => setSel({...sel, gender: 'male'})}>Male</button>
        </div>
      </div>

      <div>
        <div className="text-xs text-slate-400 mb-1">Tone</div>
        <div className="flex gap-2">
          <button className={`px-2 py-1 text-xs rounded ${sel.tone === 'calm' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-200'}`} onClick={() => setSel({...sel, tone: 'calm'})}>Calm</button>
          <button className={`px-2 py-1 text-xs rounded ${sel.tone === 'energetic' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-200'}`} onClick={() => setSel({...sel, tone: 'energetic'})}>Energetic</button>
          <button className={`px-2 py-1 text-xs rounded ${sel.tone === 'neutral' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-200'}`} onClick={() => setSel({...sel, tone: 'neutral'})}>Neutral</button>
        </div>
      </div>

      <div>
        <div className="text-xs text-slate-400 mb-1">Style</div>
        <div className="flex gap-2">
          <button className={`px-2 py-1 text-xs rounded ${sel.style === 'formal' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-200'}`} onClick={() => setSel({...sel, style: 'formal'})}>Formal</button>
          <button className={`px-2 py-1 text-xs rounded ${sel.style === 'casual' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-200'}`} onClick={() => setSel({...sel, style: 'casual'})}>Casual</button>
        </div>
      </div>
    </div>
  );
};

export default VoiceAgentSelector;
