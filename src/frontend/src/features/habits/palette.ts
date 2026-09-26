import type { HabitColor } from './types';

export interface ColorOption {
  value: HabitColor;
  label: string;
  token: string;
}

export const COLORS: readonly ColorOption[] = [
  { value: 'coral', label: 'Coral', token: 'var(--habit-1)' },
  { value: 'amber', label: 'Amber', token: 'var(--habit-2)' },
  { value: 'lime', label: 'Lime', token: 'var(--habit-3)' },
  { value: 'teal', label: 'Teal', token: 'var(--habit-4)' },
  { value: 'sky', label: 'Sky', token: 'var(--habit-5)' },
  { value: 'indigo', label: 'Indigo', token: 'var(--habit-6)' },
  { value: 'violet', label: 'Violet', token: 'var(--habit-7)' },
  { value: 'rose', label: 'Rose', token: 'var(--habit-8)' },
];

export interface EmojiOption {
  value: string;
  label: string;
}

export const EMOJIS: readonly EmojiOption[] = [
  { value: '📚', label: 'Books' },
  { value: '💧', label: 'Water' },
  { value: '🏃', label: 'Running' },
  { value: '🧘', label: 'Meditation' },
  { value: '🥗', label: 'Salad' },
  { value: '😴', label: 'Sleep' },
  { value: '💪', label: 'Strength' },
  { value: '✍️', label: 'Writing' },
  { value: '🎸', label: 'Music' },
  { value: '🌱', label: 'Plant' },
  { value: '🧹', label: 'Cleaning' },
  { value: '💊', label: 'Medicine' },
];

export function colorToken(color: HabitColor): string {
  return COLORS.find((c) => c.value === color)?.token ?? 'var(--habit-1)';
}
