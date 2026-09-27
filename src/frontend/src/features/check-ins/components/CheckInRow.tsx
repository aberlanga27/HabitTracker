import type { CSSProperties, JSX } from 'react';

import { StreakBadge } from '@/features/streaks';

import { useToggleCheckIn } from '../hooks/use-check-ins';
import type { DayHabit } from '../types';
import { CheckInButton } from './CheckInButton';
import { NoteEditor } from './NoteEditor';

export interface CheckInRowProps {
  item: DayHabit;
  colorToken: string;
  date: string;
  editable: boolean;
}

export function CheckInRow({ item, colorToken, date, editable }: CheckInRowProps): JSX.Element {
  const { habit, completed, note, week, status } = item;
  const toggle = useToggleCheckIn(date);

  return (
    <li
      className={`habit-row card${completed ? ' is-complete' : ''}`}
      style={{ '--habit-color': colorToken } as CSSProperties}
    >
      <CheckInButton
        name={habit.name}
        icon={habit.icon}
        completed={completed}
        disabled={!editable || toggle.isPending}
        onToggle={() => toggle.mutate({ habitId: habit.id, completed: !completed })}
      />
      <StreakBadge current={habit.streak.current} />
      {status === 'done_for_week' ? (
        <span className="habit-meta">✓ Done for this week</span>
      ) : (
        week && (
          <span className="habit-meta">
            {week.completed} of {week.target} this week
          </span>
        )
      )}
      {completed && (
        <NoteEditor
          key={note ?? ''}
          habitId={habit.id}
          habitName={habit.name}
          date={date}
          note={note}
          editable={editable}
        />
      )}
      {toggle.isError && (
        <p role="alert" className="form-error">
          Could not save. Please try again.
        </p>
      )}
    </li>
  );
}
