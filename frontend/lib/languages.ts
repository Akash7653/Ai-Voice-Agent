export const LANGUAGES = [
  { code: 'en', label: 'English', native: 'English' },
  { code: 'hi', label: 'Hindi', native: 'हिन्दी' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்' },
] as const;

export type LanguageCode = (typeof LANGUAGES)[number]['code'];

export function languageLabel(code: string | undefined): string {
  if (!code || code === 'auto') return 'Auto-detect';
  const found = LANGUAGES.find((l) => l.code === code || l.label.toLowerCase() === code.toLowerCase());
  return found ? `${found.label} (${found.native})` : code;
}

export function extractSuggestedSlots(text: string): string[] {
  if (!text) return [];
  const slots: string[] = [];
  const patterns = [
    /\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\b/g,
    /\b(\d{1,2}\s*(?:AM|PM|am|pm))\b/g,
  ];
  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      slots.push(match[1].trim());
    }
  }
  return [...new Set(slots)].slice(0, 6);
}
