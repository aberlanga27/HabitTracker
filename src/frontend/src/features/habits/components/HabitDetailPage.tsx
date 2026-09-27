import type { JSX } from 'react';
import { Link, useParams } from 'react-router';

import { StreakBadge } from '@/features/streaks';
import { formatDayLabel } from '@/shared/lib/dates';

import { useHabit } from '../hooks/use-habits';
import { scheduleLabel } from '../schedule-label';

function dayRange(start: string, end: string): string {
  const label = (iso: string): string => formatDayLabel(iso).replace(/^\w+, /, '');
  return `${label(start)} – ${label(end)}`;
}

/** Habit detail with current and longest streak (spec 004 US2). */
export function HabitDetailPage(): JSX.Element {
  const { habitId = '' } = useParams();
  const habit = useHabit(habitId);

  if (habit.isPending) return <p className="page-loading">Loading habit…</p>;
  if (habit.isError) {
    return (
      <div className="stack">
        <p role="alert" className="form-error">
          {habit.error.message}
        </p>
        <Link to="/habits">Back to habits</Link>
      </div>
    );
  }

  const { name, icon, schedule, streak } = habit.data;
  const days = (n: number): string => `${n} ${n === 1 ? 'day' : 'days'}`;
  return (
    <article className="stack" aria-labelledby="habit-heading">
      <Link to="/habits">← All habits</Link>
      <h1 id="habit-heading">
        {icon && <span aria-hidden="true">{icon} </span>}
        {name}
      </h1>
      <p className="habit-meta">{scheduleLabel(schedule)}</p>
      <div className="row">
        <StreakBadge current={streak.current} />
        {streak.current_start && (
          <span className="habit-meta">since {formatDayLabel(streak.current_start)}</span>
        )}
      </div>
      <section role="group" aria-label="Longest streak" className="card stack">
        <h2>Longest streak</h2>
        {streak.longest > 0 && streak.longest_start && streak.longest_end ? (
          <p>
            <strong>{days(streak.longest)}</strong>{' '}
            <span className="habit-meta">
              ({dayRange(streak.longest_start, streak.longest_end)})
            </span>
          </p>
        ) : (
          <p className="empty-state">No streak yet.</p>
        )}
      </section>
    </article>
  );
}
