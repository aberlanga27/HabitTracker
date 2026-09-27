import type { JSX } from 'react';
import { Link, useSearchParams } from 'react-router';

import { useMe } from '@/features/auth';
import { CheckInRow, dateStatus, useCheckIns, type DateStatus } from '@/features/check-ins';
import { colorToken, useHabits } from '@/features/habits';
import { formatDayLabel, isIsoDate, localToday } from '@/shared/lib/dates';

import { DayNav } from './DayNav';

const DISABLED_REASON: Record<Exclude<DateStatus, 'editable'>, string> = {
  future: "You can't check in for future dates.",
  'too-old': 'Check-ins are limited to the last 30 days.',
};

// Interim day view: active habits with check-in toggles; spec 006 adds the day summary.
export function TodayPage(): JSX.Element {
  const me = useMe();
  const today = localToday(me.data?.timezone ?? 'UTC');
  const [params, setParams] = useSearchParams();
  const requested = params.get('date');
  const date = isIsoDate(requested) ? requested : today;
  const status = dateStatus(date, today);
  const habits = useHabits(false);
  const checkIns = useCheckIns(date);
  const loaded = !checkIns.isPlaceholderData;

  return (
    <section aria-labelledby="today-heading" className="stack">
      <h1 id="today-heading">{date === today ? 'Today' : formatDayLabel(date)}</h1>
      {date === today && <p className="date-label">{formatDayLabel(date)}</p>}
      <DayNav
        date={date}
        today={today}
        onChange={(next) => setParams(next === today ? {} : { date: next })}
      />
      {status !== 'editable' && <p className="notice">{DISABLED_REASON[status]}</p>}
      {habits.isPending || checkIns.isPending ? (
        <p className="page-loading">Loading habits…</p>
      ) : habits.data && habits.data.items.length > 0 ? (
        <ul className="habit-list" aria-label={`Habits for ${formatDayLabel(date)}`}>
          {habits.data.items.map((habit) => (
            <CheckInRow
              key={habit.id}
              habit={habit}
              colorToken={colorToken(habit.color)}
              date={date}
              state={
                loaded ? checkIns.data?.items.find((item) => item.habit_id === habit.id) : undefined
              }
              editable={status === 'editable' && loaded}
            />
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
