import { useEffect, useRef, useState, type FormEvent, type JSX } from 'react';

import type { HabitRead } from '../types';

export interface DeleteHabitConfirmProps {
  habit: HabitRead;
  pending: boolean;
  errorMessage?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

/** Inline typed-name confirmation before permanent deletion (spec 002 FR-004). */
export function DeleteHabitConfirm({
  habit,
  pending,
  errorMessage,
  onConfirm,
  onCancel,
}: DeleteHabitConfirmProps): JSX.Element {
  const [typed, setTyped] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const inputId = `delete-${habit.id}`;

  useEffect(() => inputRef.current?.focus(), []);

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (typed === habit.name) onConfirm();
  }

  return (
    <form className="stack delete-confirm" onSubmit={handleSubmit}>
      <p>
        This permanently deletes <strong>{habit.name}</strong> and all of its history.
      </p>
      <div className="field">
        <label htmlFor={inputId}>
          Type <strong>{habit.name}</strong> to confirm
        </label>
        <input
          id={inputId}
          ref={inputRef}
          value={typed}
          autoComplete="off"
          onChange={(e) => setTyped(e.target.value)}
        />
      </div>
      {errorMessage && (
        <p role="alert" className="form-error">
          {errorMessage}
        </p>
      )}
      <div className="row">
        <button
          type="submit"
          className="button button-danger"
          disabled={typed !== habit.name || pending}
        >
          Delete permanently
        </button>
        <button type="button" className="button" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
