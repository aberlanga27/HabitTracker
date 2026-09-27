import { useState, type FormEvent, type JSX } from 'react';

import { useSaveNote } from '../hooks/use-check-ins';

const MAX_NOTE = 280;

export interface NoteEditorProps {
  habitId: string;
  habitName: string;
  date: string;
  note: string | null;
  editable: boolean;
}

/** Shows a check-in's note and lets the user add or edit it (spec 003 FR-005). */
export function NoteEditor({
  habitId,
  habitName,
  date,
  note,
  editable,
}: NoteEditorProps): JSX.Element {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(note ?? '');
  const save = useSaveNote(date);
  const fieldId = `note-${habitId}`;

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    save.mutate({ habitId, note: draft.trim() || null }, { onSuccess: () => setOpen(false) });
  }

  if (open) {
    return (
      <form className="stack note-editor" onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor={fieldId}>Note for {habitName}</label>
          <textarea
            id={fieldId}
            maxLength={MAX_NOTE}
            rows={2}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
          />
          <p className="field-hint">
            {draft.length}/{MAX_NOTE}
          </p>
        </div>
        {save.isError && (
          <p role="alert" className="form-error">
            {save.error.message}
          </p>
        )}
        <div className="row">
          <button type="submit" className="button button-primary" disabled={save.isPending}>
            Save note
          </button>
          <button type="button" className="button" onClick={() => setOpen(false)}>
            Cancel
          </button>
        </div>
      </form>
    );
  }

  return (
    <div className="row note">
      {note && <p className="habit-description">{note}</p>}
      {editable && (
        <button
          type="button"
          className="button button-small"
          aria-label={`${note ? 'Edit' : 'Add'} note for ${habitName}`}
          onClick={() => {
            setDraft(note ?? '');
            setOpen(true);
          }}
        >
          {note ? 'Edit note' : 'Add note'}
        </button>
      )}
    </div>
  );
}
