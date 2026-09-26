import { useState, type FormEvent, type JSX } from 'react';

import { TextField } from '@/shared/ui';

import type { HabitColor, HabitCreate } from '../types';
import { ColorPicker } from './ColorPicker';
import { EmojiPicker } from './EmojiPicker';

const MAX_NAME = 80;
const MAX_DESCRIPTION = 500;

export interface HabitFormValues {
  name: string;
  description: string;
  icon: string | null;
  color: HabitColor;
}

const EMPTY: HabitFormValues = { name: '', description: '', icon: null, color: 'coral' };

export interface HabitFormProps {
  idPrefix: string;
  initial?: HabitFormValues;
  submitLabel: string;
  pending?: boolean;
  errorMessage?: string;
  onSubmit: (body: Required<HabitCreate>) => void;
  onCancel?: () => void;
}

interface FieldErrors {
  name?: string;
  description?: string;
}

function validate(values: HabitFormValues): FieldErrors {
  const errors: FieldErrors = {};
  const name = values.name.trim();
  if (!name) errors.name = 'Enter a name.';
  else if (name.length > MAX_NAME) errors.name = `Name must be at most ${MAX_NAME} characters.`;
  if (values.description.trim().length > MAX_DESCRIPTION) {
    errors.description = `Description must be at most ${MAX_DESCRIPTION} characters.`;
  }
  return errors;
}

/** Create/edit form for a habit's name, description, icon, and color (spec 002 FR-001, FR-002). */
export function HabitForm({
  idPrefix,
  initial = EMPTY,
  submitLabel,
  pending = false,
  errorMessage,
  onSubmit,
  onCancel,
}: HabitFormProps): JSX.Element {
  const [values, setValues] = useState<HabitFormValues>(initial);
  const [errors, setErrors] = useState<FieldErrors>({});

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const next = validate(values);
    setErrors(next);
    if (next.name || next.description) return;
    const description = values.description.trim();
    onSubmit({
      name: values.name.trim(),
      description: description || null,
      icon: values.icon,
      color: values.color,
    });
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="stack">
      <TextField
        id={`${idPrefix}-name`}
        label="Name"
        value={values.name}
        onChange={(e) => setValues({ ...values, name: e.target.value })}
        error={errors.name}
      />
      <TextField
        id={`${idPrefix}-description`}
        label="Description (optional)"
        value={values.description}
        onChange={(e) => setValues({ ...values, description: e.target.value })}
        error={errors.description}
      />
      <EmojiPicker
        name={`${idPrefix}-icon`}
        value={values.icon}
        onChange={(icon) => setValues({ ...values, icon })}
      />
      <ColorPicker
        name={`${idPrefix}-color`}
        value={values.color}
        onChange={(color) => setValues({ ...values, color })}
      />
      {errorMessage && (
        <p role="alert" className="form-error">
          {errorMessage}
        </p>
      )}
      <div className="row">
        <button type="submit" className="button button-primary" disabled={pending}>
          {submitLabel}
        </button>
        {onCancel && (
          <button type="button" className="button" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
