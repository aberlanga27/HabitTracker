import type { JSX } from 'react';

import { COLORS } from '../palette';
import type { HabitColor } from '../types';

export interface ColorPickerProps {
  name: string;
  value: HabitColor;
  onChange: (value: HabitColor) => void;
}

export function ColorPicker({ name, value, onChange }: ColorPickerProps): JSX.Element {
  return (
    <fieldset className="choice-group" role="radiogroup" aria-label="Color">
      <legend>Color</legend>
      {COLORS.map((color) => (
        <label key={color.value} className="choice">
          <input
            type="radio"
            name={name}
            value={color.value}
            checked={value === color.value}
            onChange={() => onChange(color.value)}
          />
          <span className="swatch" style={{ background: color.token }} aria-hidden="true" />
          <span className="visually-hidden">{color.label}</span>
        </label>
      ))}
    </fieldset>
  );
}
