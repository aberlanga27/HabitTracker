import type { JSX } from 'react';
import { Link } from 'react-router';

import { earliestEditable } from '@/features/check-ins';
import { addDays } from '@/shared/lib/dates';

export interface DayNavProps {
  date: string;
  today: string;
  onChange: (date: string) => void;
}

/** Previous / next day within the editable window, plus a jump back to today (spec 003 US2). */
export function DayNav({ date, today, onChange }: DayNavProps): JSX.Element {
  return (
    <nav aria-label="Day" className="row day-nav">
      <button
        type="button"
        className="button"
        disabled={date <= earliestEditable(today)}
        onClick={() => onChange(addDays(date, -1))}
      >
        ← Previous day
      </button>
      {date !== today && (
        <Link to="/" className="button">
          Jump to today
        </Link>
      )}
      <button
        type="button"
        className="button"
        disabled={date >= today}
        onClick={() => onChange(addDays(date, 1))}
      >
        Next day →
      </button>
    </nav>
  );
}
