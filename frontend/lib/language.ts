const LABELS: Record<string, string> = {
  en: 'English',
  hi: 'Hindi',
  ta: 'Tamil',
  te: 'Telugu',
  auto: 'Auto-detect',
};

export function formatLanguage(code?: string): string {
  if (!code) return 'Auto-detect';
  return LABELS[code.toLowerCase()] ?? code;
}
