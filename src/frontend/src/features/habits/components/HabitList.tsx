import type { JSX } from 'react';

import { useReorderHabits } from '../hooks/use-habits';
import type { HabitRead } from '../types';
import { HabitRow } from './HabitRow';

export interface HabitListProps {
  habits: HabitRead[];
}

/** Active habits in order, with keyboard- and pointer-operable reordering (spec 002 FR-005). */
export function HabitList({ habits }: HabitListProps): JSX.Element {
  const reorder = useReorderHabits();

  function move(index: number, direction: -1 | 1): void {
    const ids = habits.map((h) => h.id);
    const target = index + direction;
    const current = ids[index];
    const other = ids[target];
    if (current === undefined || other === undefined) return;
    ids[index] = other;
    ids[target] = current;
    reorder.mutate(ids);
  }

  if (habits.length === 0) {
    return <p className="empty-state">No active habits.</p>;
  }

  return (
    <>
      <ul className="habit-list" aria-label="Active habits">
        {habits.map((habit, index) => (
          <HabitRow
            key={habit.id}
            habit={habit}
            variant="active"
            canMoveUp={index > 0}
            canMoveDown={index < habits.length - 1}
            movePending={reorder.isPending}
            onMove={(direction) => move(index, direction)}
          />
        ))}
      </ul>
      {reorder.isError && (
        <p role="alert" className="form-error">
          {reorder.error.message}
        </p>
      )}
    </>
  );
}
