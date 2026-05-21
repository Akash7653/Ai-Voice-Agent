"use client";

import React, { useState, useEffect } from  "react";

const ModeSwitcher: React.FC = () => {
  const [dark, setDark] = useState(true);

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.classList.toggle('dark', dark);
      document.documentElement.classList.toggle('light', !dark);
    }
  }, [dark]);

  return (
    <button
      onClick={() => setDark((d) => !d)}
      className="px-3 py-1 bg-slate-700 text-slate-200 rounded text-xs"
    >
      {dark ? 'Dark' : 'Light'}
    </button>
  );
};

export default ModeSwitcher;
