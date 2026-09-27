import { addDays } from '@/shared/lib/dates';

/** Mirrors the server's editable window (spec 003 FR-002, FR-003). */
export const BACKFILL_DAYS = 30;

export type DateStatus = 'editable' | 'future' | 'too-old';

export function earliestEditable(today: string): string {
  return addDays(today, -BACKFILL_DAYS);
}

export function dateStatus(date: string, today: string): DateStatus {
  if (date > today) return 'future';
  if (date < earliestEditable(today)) return 'too-old';
  return 'editable';
}
