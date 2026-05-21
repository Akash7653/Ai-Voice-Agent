/**
 * Animated AI Orb component - central voice interface
 */
'use client';

import React from 'react';

export interface AIorbProps {
  status: 'listening' | 'speaking' | 'thinking' | 'idle';
  audioLevel?: number;
  pulse?: boolean;
}

export const AIOrb: React.FC<AIorbProps> = ({ status, audioLevel = 0, pulse = true }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'listening':
        return 'from-cyan-400 via-blue-500 to-purple-600';
      case 'speaking':
        return 'from-emerald-400 via-teal-500 to-cyan-600';
      case 'thinking':
        return 'from-amber-400 via-orange-500 to-red-600';
      default:
        return 'from-blue-400 via-purple-500 to-pink-600';
    }
  };

  const getGlowIntensity = () => {
    if (status === 'listening' || status === 'speaking') {
      return Math.min(100, 60 + (audioLevel || 0) / 2.55);
    }
    return 60;
  };

  const pulseScale = status === 'thinking' ? 1.1 : 1.0;
  const orbScale = Math.min(1.2, 1.0 + (audioLevel || 0) / 255 * 0.2);

  return (
    <div className="relative flex items-center justify-center w-64 h-64 mx-auto">
      {/* Outer glow ring */}
      <div
        className={`absolute inset-0 rounded-full bg-gradient-to-r ${getStatusColor()} opacity-20 blur-3xl transition-all duration-200`}
        style={{
          filter: `blur(${30 + getGlowIntensity() / 5}px)`,
        }}
      />

      {/* Animated rings (3 layers) */}
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="absolute inset-0 rounded-full border-2 border-transparent bg-gradient-to-r"
          style={{
            backgroundImage: `conic-gradient(from 0deg, rgb(34 197 94 / ${0.1 + i * 0.15}), transparent)`,
            animation: `spin ${8 - i * 2}s linear infinite`,
            opacity: status !== 'idle' ? 1 : 0.3,
            transition: 'opacity 0.3s ease',
          }}
        />
      ))}

      {/* Center orb */}
      <div
        className={`relative z-10 w-40 h-40 rounded-full bg-gradient-to-br ${getStatusColor()} shadow-2xl transition-transform duration-200`}
        style={{
          transform: `scale(${orbScale})`,
          animation: pulse && status === 'thinking' ? `pulse 2s ease-in-out infinite` : 'none',
          boxShadow: `0 0 ${getGlowIntensity()}px rgba(99, 102, 241, ${0.5 + (audioLevel || 0) / 255 * 0.5})`,
        }}
      >
        {/* Inner shine effect */}
        <div className="absolute inset-2 rounded-full bg-gradient-to-br from-white/30 to-transparent opacity-50" />

        {/* Status indicator */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-white text-sm font-bold tracking-widest uppercase">
            {status === 'listening' && '🎤 Listening'}
            {status === 'speaking' && '🔊 Speaking'}
            {status === 'thinking' && '⚡ Thinking'}
            {status === 'idle' && '✨ Ready'}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
      `}</style>
    </div>
  );
};
