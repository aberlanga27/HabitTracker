import type { JSX } from 'react';

import { EMOJIS } from '../palette';

export interface EmojiPickerProps {
  name: string;
  value: string | null;
  onChange: (value: string | null) => void;
}

export function EmojiPicker({ name, value, onChange }: EmojiPickerProps): JSX.Element {
  return (
    <fieldset className="choice-group" role="radiogroup" aria-label="Icon">
      <legend>Icon</legend>
      <label className="choice">
        <input type="radio" name={name} checked={value === null} onChange={() => onChange(null)} />
        <span className="choice-text">None</span>
      </label>
      {EMOJIS.map((emoji) => (
        <label key={emoji.value} className="choice">
          <input
            type="radio"
            name={name}
            value={emoji.value}
            checked={value === emoji.value}
            onChange={() => onChange(emoji.value)}
          />
          <span className="choice-emoji" aria-hidden="true">
            {emoji.value}
          </span>
          <span className="visually-hidden">{emoji.label}</span>
        </label>
      ))}
    </fieldset>
  );
}
