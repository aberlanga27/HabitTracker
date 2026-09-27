import { useState, type FormEvent, type JSX } from 'react';

import { TextField } from '@/shared/ui';

import type { HabitColor, HabitCreate, ScheduleIn } from '../types';
import { ColorPicker } from './ColorPicker';
import { EmojiPicker } from './EmojiPicker';
import { SchedulePicker, type ScheduleValue } from './SchedulePicker';

const MAX_NAME = 80;
const MAX_DESCRIPTION = 500;

export interface HabitFormValues {
  name: string;
  description: string;
  icon: string | null;
  color: HabitColor;
  schedule: ScheduleValue;
}

export const DEFAULT_SCHEDULE: ScheduleValue = { type: 'daily', weekdays: [], timesPerWeek: 3 };

const EMPTY: HabitFormValues = {
  name: '',
  description: '',
  icon: null,
  color: 'coral',
  schedule: DEFAULT_SCHEDULE,
};

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
  schedule?: string;
}

function validate(values: HabitFormValues): FieldErrors {
  const errors: FieldErrors = {};
  const name = values.name.trim();
  if (!name) errors.name = 'Enter a name.';
  else if (name.length > MAX_NAME) errors.name = `Name must be at most ${MAX_NAME} characters.`;
  if (values.description.trim().length > MAX_DESCRIPTION) {
    errors.description = `Description must be at most ${MAX_DESCRIPTION} characters.`;
  }
  const { type, weekdays, timesPerWeek } = values.schedule;
  if (type === 'weekdays' && weekdays.length === 0) errors.schedule = 'Choose at least one day.';
  if (
    type === 'times_per_week' &&
    !(Number.isInteger(timesPerWeek) && timesPerWeek >= 1 && timesPerWeek <= 7)
  ) {
    errors.schedule = 'Choose between 1 and 7 times per week.';
  }
  return errors;
}

function toScheduleIn({ type, weekdays, timesPerWeek }: ScheduleValue): ScheduleIn {
  if (type === 'weekdays') return { type, weekdays };
  if (type === 'times_per_week') return { type, times_per_week: timesPerWeek };
  return { type };
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
    if (next.name || next.description || next.schedule) return;
    const description = values.description.trim();
    onSubmit({
      name: values.name.trim(),
      description: description || null,
      icon: values.icon,
      color: values.color,
      schedule: toScheduleIn(values.schedule),
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
      <SchedulePicker
        idPrefix={idPrefix}
        value={values.schedule}
        error={errors.schedule}
        onChange={(schedule) => setValues({ ...values, schedule })}
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
