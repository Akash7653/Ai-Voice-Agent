import type { Metadata } from  'next';
import './globals.css';
import AppShell from  '@/components/layout/AppShell';

export const metadata: Metadata = {
  title: 'Voice Healthcare Agent',
  description: 'Real-time multilingual voice AI agent for appointment booking',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
