import type { JSX } from 'react';
import { Link, useSearchParams } from 'react-router';

import { useMe } from '@/features/auth';
import { CheckInRow, dateStatus, type DateStatus, type DayHabit } from '@/features/check-ins';
import { colorToken } from '@/features/habits';
import { formatDayLabel, isIsoDate } from '@/shared/lib/dates';
import { Skeleton } from '@/shared/ui';

import { DayNav } from './DayNav';
import { DayProgress } from './DayProgress';
import { useDay } from './use-day';
import { useLocalToday } from './use-local-today';

const DISABLED_REASON: Record<Exclude<DateStatus, 'editable'>, string> = {
  future: "You can't check in for future dates.",
  'too-old': 'Check-ins are limited to the last 30 days.',
};

function isDone(item: DayHabit): boolean {
  return item.completed || item.status === 'done_for_week';
}

interface HabitSectionProps {
  label: string;
  items: DayHabit[];
  date: string;
  editable: boolean;
}

function HabitSection({ label, items, date, editable }: HabitSectionProps): JSX.Element | null {
  if (items.length === 0) return null;
  return (
    <section className="stack" aria-labelledby={`${label}-heading`}>
      <h2 id={`${label}-heading`}>{label}</h2>
      <ul className="habit-list" aria-label={label}>
        {items.map((item) => (
          <CheckInRow
            key={item.habit.id}
            item={item}
            colorToken={colorToken(item.habit.color)}
            date={date}
            editable={editable}
          />
        ))}
      </ul>
    </section>
  );
}

/** Home dashboard: due habits for a local date with progress and check-ins (spec 006). */
export function TodayPage(): JSX.Element {
  const me = useMe();
  const today = useLocalToday(me.data?.timezone ?? 'UTC');
  const [params, setParams] = useSearchParams();
  const requested = params.get('date');
  const date = isIsoDate(requested) ? requested : today;
  const status = dateStatus(date, today);
  const day = useDay(date);
  const editable = status === 'editable' && !day.isPlaceholderData;
  const isToday = date === today;

  function body(): JSX.Element {
    if (day.isPending) return <Skeleton label="Loading habits" />;
    if (day.isError) {
      return (
        <p role="alert" className="form-error">
          {day.error.message}
        </p>
      );
    }
    const { items, due_count: due, completed_count: completed, habit_count: habits } = day.data;
    if (habits === 0) {
      return (
        <div className="empty-state stack">
          <p>No habits yet.</p>
          <Link to="/habits" className="button button-primary">
            Create your first habit
          </Link>
        </div>
      );
    }
    if (items.length === 0) {
      return <p className="empty-state">Nothing is scheduled for this day.</p>;
    }
    return (
      <>
        <DayProgress completed={completed} due={due} />
        {due > 0 && completed === due && (
          <p className="celebration">
            <span aria-hidden="true">🎉 </span>
            All done for {isToday ? 'today' : 'this day'}!
          </p>
        )}
        <HabitSection
          label="To do"
          items={items.filter((item) => !isDone(item))}
          date={date}
          editable={editable}
        />
        <HabitSection label="Done" items={items.filter(isDone)} date={date} editable={editable} />
      </>
    );
  }

  return (
    <section aria-labelledby="today-heading" className="stack">
      <h1 id="today-heading">{isToday ? 'Today' : formatDayLabel(date)}</h1>
      {isToday && <p className="date-label">{formatDayLabel(date)}</p>}
      <DayNav
        date={date}
        today={today}
        onChange={(next) => setParams(next === today ? {} : { date: next })}
      />
      {status !== 'editable' && <p className="notice">{DISABLED_REASON[status]}</p>}
      {body()}
    </section>
  );
}
