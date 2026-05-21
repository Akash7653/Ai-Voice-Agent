/**
 * Real-time waveform visualization
 */
'use client';

import React, { useEffect, useRef } from 'react';

export interface WaveformProps {
  audioLevel: number;
  isRecording: boolean;
  color?: string;
  height?: number;
}

export const Waveform: React.FC<WaveformProps> = ({
  audioLevel,
  isRecording,
  color = 'from-cyan-400 to-blue-500',
  height = 64,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const barsRef = useRef<number[]>(Array(32).fill(0));
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const update = () => {
      // Update bars
      barsRef.current = barsRef.current.map((bar, i) => {
        const newVal = i === Math.floor(Math.random() * 32)
          ? (audioLevel / 255) * height
          : bar * 0.9;
        return Math.max(8, newVal);
      });

      // Clear canvas
      ctx.fillStyle = 'rgba(0, 0, 0, 0)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw gradient
      const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
      gradient.addColorStop(0, 'rgba(34, 197, 94, 0.3)');
      gradient.addColorStop(0.5, 'rgba(59, 130, 246, 0.6)');
      gradient.addColorStop(1, 'rgba(168, 85, 247, 0.3)');

      // Draw bars
      const barWidth = canvas.width / 32;
      barsRef.current.forEach((bar, i) => {
        ctx.fillStyle = gradient;
        ctx.fillRect(i * barWidth + 2, height - bar, barWidth - 4, bar);
      });

      if (isRecording) {
        animationRef.current = requestAnimationFrame(update);
      }
    };

    update();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [audioLevel, isRecording, height]);

  return (
    <canvas
      ref={canvasRef}
      width={256}
      height={height}
      className="w-full h-16 rounded-lg border border-cyan-500/20"
    />
  );
};
