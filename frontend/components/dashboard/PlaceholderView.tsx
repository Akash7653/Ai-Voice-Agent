'use client';

import React from 'react';
import PageHeader from '@/components/layout/PageHeader';

export default function PlaceholderView({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="flex h-full flex-col">
      <PageHeader status="ready" />
      <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
        <h2 className="mb-2 text-xl font-semibold text-white">{title}</h2>
        <p className="max-w-md text-sm text-slate-400">{description}</p>
      </div>
    </div>
  );
}
