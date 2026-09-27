import type { JSX } from 'react';

export interface DayProgressProps {
  completed: number;
  due: number;
}

/** "3 of 5 habits done" with a progress bar; the text is a polite live region (FR-002, FR-006). */
export function DayProgress({ completed, due }: DayProgressProps): JSX.Element {
  const percent = due === 0 ? 0 : Math.round((100 * completed) / due);
  return (
    <div className="day-progress stack">
      <p aria-live="polite" className="day-progress-text">
        {completed} of {due} habits done
      </p>
      <div
        role="progressbar"
        aria-label="Daily progress"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        className="progress-track"
      >
        <div className="progress-fill" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
