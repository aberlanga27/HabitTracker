import type { CSSProperties, JSX } from 'react';

import { useToggleCheckIn } from '../hooks/use-check-ins';
import type { CheckInState } from '../types';
import { CheckInButton } from './CheckInButton';
import { NoteEditor } from './NoteEditor';

export interface CheckInRowProps {
  habit: { id: string; name: string; icon: string | null };
  colorToken: string;
  date: string;
  state: CheckInState | undefined;
  editable: boolean;
}

export function CheckInRow({
  habit,
  colorToken,
  date,
  state,
  editable,
}: CheckInRowProps): JSX.Element {
  const toggle = useToggleCheckIn(date);
  const completed = state?.completed ?? false;

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
      {completed && (
        <NoteEditor
          key={state?.note ?? ''}
          habitId={habit.id}
          habitName={habit.name}
          date={date}
          note={state?.note ?? null}
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
