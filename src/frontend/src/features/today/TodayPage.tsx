import type { CSSProperties, JSX } from 'react';
import { Link } from 'react-router';

import { colorToken, useHabits } from '@/features/habits';

// Interim list of active habits; spec 006 replaces it with the day summary.
export function TodayPage(): JSX.Element {
  const habits = useHabits(false);

  return (
    <section aria-labelledby="today-heading" className="stack">
      <h1 id="today-heading">Today</h1>
      {habits.isPending ? (
        <p className="page-loading">Loading habits…</p>
      ) : habits.data && habits.data.items.length > 0 ? (
        <ul className="habit-list" aria-label="Today's habits">
          {habits.data.items.map((habit) => (
            <li
              key={habit.id}
              className="habit-row card"
              style={{ '--habit-color': colorToken(habit.color) } as CSSProperties}
            >
              <div className="habit-summary">
                <span className="habit-swatch" aria-hidden="true" />
                {habit.icon && <span aria-hidden="true">{habit.icon}</span>}
                <span>{habit.name}</span>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <div className="empty-state stack">
          <p>No habits yet.</p>
          <Link to="/habits" className="button button-primary">
            Create your first habit
          </Link>
        </div>
      )}
    </section>
  );
}
