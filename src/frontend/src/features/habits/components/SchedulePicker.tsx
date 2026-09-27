import type { JSX } from 'react';

import type { ScheduleIn, Weekday } from '../types';

const DAYS: { value: Weekday; label: string }[] = [
  { value: 'mon', label: 'Monday' },
  { value: 'tue', label: 'Tuesday' },
  { value: 'wed', label: 'Wednesday' },
  { value: 'thu', label: 'Thursday' },
  { value: 'fri', label: 'Friday' },
  { value: 'sat', label: 'Saturday' },
  { value: 'sun', label: 'Sunday' },
];

const TYPES: { value: ScheduleIn['type']; label: string }[] = [
  { value: 'daily', label: 'Every day' },
  { value: 'weekdays', label: 'Specific days' },
  { value: 'times_per_week', label: 'Times per week' },
];

export interface ScheduleValue {
  type: ScheduleIn['type'];
  weekdays: Weekday[];
  timesPerWeek: number;
}

export interface SchedulePickerProps {
  idPrefix: string;
  value: ScheduleValue;
  error?: string;
  onChange: (value: ScheduleValue) => void;
}

/** Daily / specific weekdays / N times per week (spec 005 FR-001..FR-003). */
export function SchedulePicker({
  idPrefix,
  value,
  error,
  onChange,
}: SchedulePickerProps): JSX.Element {
  const errorId = `${idPrefix}-schedule-error`;

  function toggleDay(day: Weekday): void {
    const weekdays = value.weekdays.includes(day)
      ? value.weekdays.filter((d) => d !== day)
      : DAYS.map((d) => d.value).filter((d) => d === day || value.weekdays.includes(d));
    onChange({ ...value, weekdays });
  }

  return (
    <fieldset className="stack schedule-picker" aria-describedby={error ? errorId : undefined}>
      <legend>Schedule</legend>
      <div className="row">
        {TYPES.map((type) => (
          <label key={type.value} className="inline-choice">
            <input
              type="radio"
              name={`${idPrefix}-schedule-type`}
              checked={value.type === type.value}
              onChange={() => onChange({ ...value, type: type.value })}
            />
            {type.label}
          </label>
        ))}
      </div>
      {value.type === 'weekdays' && (
        <fieldset className="row" role="group" aria-label="Days">
          {DAYS.map((day) => (
            <label key={day.value} className="inline-choice">
              <input
                type="checkbox"
                checked={value.weekdays.includes(day.value)}
                onChange={() => toggleDay(day.value)}
              />
              <abbr title={day.label} aria-hidden="true">
                {day.label.slice(0, 3)}
              </abbr>
              <span className="visually-hidden">{day.label}</span>
            </label>
          ))}
        </fieldset>
      )}
      {value.type === 'times_per_week' && (
        <div className="field">
          <label htmlFor={`${idPrefix}-times`}>Times each week</label>
          <input
            id={`${idPrefix}-times`}
            type="number"
            min={1}
            max={7}
            value={value.timesPerWeek}
            onChange={(e) => onChange({ ...value, timesPerWeek: Number(e.target.value) })}
          />
        </div>
      )}
      {error && (
        <p id={errorId} className="field-error">
          {error}
        </p>
      )}
    </fieldset>
  );
}
