import type { JSX } from 'react';

export interface SkeletonProps {
  label: string;
  rows?: number;
}

/** Placeholder rows that keep layout stable while content loads. */
export function Skeleton({ label, rows = 3 }: SkeletonProps): JSX.Element {
  return (
    <div role="region" aria-label={label} aria-busy="true" className="stack">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="skeleton-row" aria-hidden="true" />
      ))}
    </div>
  );
}
