'use client';

import React from  'react';

export default function GlassCard({
  title,
  icon,
  children,
  className = '',
  highlight,
}: {
  title: string;
  icon?: string;
  children: React.ReactNode;
  className?: string;
  highlight?: 'cyan' | 'purple' | 'amber' | 'teal' | 'rose' | 'emerald';
}) {
  const accent =
    highlight === 'purple'
      ? 'text-purple-300'
      : highlight === 'amber'
        ? 'text-amber-300'
        : highlight === 'teal'
          ? 'text-teal-300'
          : highlight === 'rose'
            ? 'text-rose-300'
            : highlight === 'emerald'
              ? 'text-emerald-300'
              : 'text-cyan-300';

  return (
    <div className={`glass-panel p-4 space-y-3 ${className}`}>
      <h3 className={`text-sm font-semibold uppercase tracking-wider ${accent}`}>
        {icon ? `${icon} ` : ''}
        {title}
      </h3>
      {children}
    </div>
  );
}
