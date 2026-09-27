import type { JSX } from 'react';

export interface StreakBadgeProps {
  current: number;
}

/** Flame + count for the current streak; the number is announced with its meaning. */
export function StreakBadge({ current }: StreakBadgeProps): JSX.Element {
  const label = `Current streak: ${current} ${current === 1 ? 'day' : 'days'}`;
  return (
    <span className="streak-badge" role="img" aria-label={label} title={label}>
      <span aria-hidden="true">🔥</span>
      <span aria-hidden="true">{current}</span>
    </span>
  );
}
