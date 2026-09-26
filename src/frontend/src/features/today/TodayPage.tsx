import type { JSX } from 'react';

// Placeholder empty dashboard; spec 006 replaces it with the day summary.
export function TodayPage(): JSX.Element {
  return (
    <section aria-labelledby="today-heading" className="stack">
      <h1 id="today-heading">Today</h1>
      <p className="empty-state">No habits yet.</p>
    </section>
  );
}
