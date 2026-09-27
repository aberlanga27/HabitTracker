import { useState, type CSSProperties, type JSX } from 'react';

import {
  useArchiveHabit,
  useDeleteHabit,
  useRestoreHabit,
  useUpdateHabit,
} from '../hooks/use-habits';
import { colorToken } from '../palette';
import { scheduleLabel } from '../schedule-label';
import type { HabitRead } from '../types';
import { DeleteHabitConfirm } from './DeleteHabitConfirm';
import { DEFAULT_SCHEDULE, HabitForm } from './HabitForm';

export interface HabitRowProps {
  habit: HabitRead;
  variant: 'active' | 'archived';
  canMoveUp?: boolean;
  canMoveDown?: boolean;
  onMove?: (direction: -1 | 1) => void;
  movePending?: boolean;
}

type Mode = 'view' | 'edit' | 'delete';

export function HabitRow({
  habit,
  variant,
  canMoveUp = false,
  canMoveDown = false,
  onMove,
  movePending = false,
}: HabitRowProps): JSX.Element {
  const [mode, setMode] = useState<Mode>('view');
  const update = useUpdateHabit();
  const archive = useArchiveHabit();
  const restore = useRestoreHabit();
  const remove = useDeleteHabit();
  const style = { '--habit-color': colorToken(habit.color) } as CSSProperties;

  if (mode === 'edit') {
    return (
      <li className="habit-row card">
        <HabitForm
          idPrefix="edit"
          submitLabel="Save"
          initial={{
            name: habit.name,
            description: habit.description ?? '',
            icon: habit.icon,
            color: habit.color,
            schedule: {
              type: habit.schedule.type,
              weekdays: habit.schedule.weekdays,
              timesPerWeek: habit.schedule.times_per_week ?? DEFAULT_SCHEDULE.timesPerWeek,
            },
          }}
          pending={update.isPending}
          errorMessage={update.error?.message}
          onSubmit={(body) =>
            update.mutate({ id: habit.id, body }, { onSuccess: () => setMode('view') })
          }
          onCancel={() => setMode('view')}
        />
      </li>
    );
  }

  if (mode === 'delete') {
    return (
      <li className="habit-row card">
        <DeleteHabitConfirm
          habit={habit}
          pending={remove.isPending}
          errorMessage={remove.error?.message}
          onConfirm={() => remove.mutate(habit.id)}
          onCancel={() => setMode('view')}
        />
      </li>
    );
  }

  const actionError = archive.error ?? restore.error;
  return (
    <li className="habit-row card" style={style}>
      <div className="habit-summary">
        <span className="habit-swatch" aria-hidden="true" />
        {habit.icon && (
          <span className="habit-icon" aria-hidden="true">
            {habit.icon}
          </span>
        )}
        <div className="habit-text">
          <h3>{habit.name}</h3>
          <p className="habit-meta">{scheduleLabel(habit.schedule)}</p>
          {habit.description && <p className="habit-description">{habit.description}</p>}
        </div>
      </div>
      <div className="row habit-actions">
        {variant === 'active' ? (
          <>
            <button
              type="button"
              className="button"
              aria-label={`Move ${habit.name} up`}
              disabled={!canMoveUp || movePending}
              onClick={() => onMove?.(-1)}
            >
              ↑
            </button>
            <button
              type="button"
              className="button"
              aria-label={`Move ${habit.name} down`}
              disabled={!canMoveDown || movePending}
              onClick={() => onMove?.(1)}
            >
              ↓
            </button>
            <button
              type="button"
              className="button"
              aria-label={`Edit ${habit.name}`}
              onClick={() => setMode('edit')}
            >
              Edit
            </button>
            <button
              type="button"
              className="button"
              aria-label={`Archive ${habit.name}`}
              disabled={archive.isPending}
              onClick={() => archive.mutate(habit.id)}
            >
              Archive
            </button>
          </>
        ) : (
          <button
            type="button"
            className="button"
            aria-label={`Restore ${habit.name}`}
            disabled={restore.isPending}
            onClick={() => restore.mutate(habit.id)}
          >
            Restore
          </button>
        )}
        <button
          type="button"
          className="button"
          aria-label={`Delete ${habit.name}`}
          onClick={() => setMode('delete')}
        >
          Delete
        </button>
      </div>
      {actionError && (
        <p role="alert" className="form-error">
          {actionError.message}
        </p>
      )}
    </li>
  );
}
