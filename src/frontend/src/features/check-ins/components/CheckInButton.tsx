import type { JSX } from 'react';

export interface CheckInButtonProps {
  name: string;
  icon: string | null;
  completed: boolean;
  disabled: boolean;
  onToggle: () => void;
}

/** One-tap completion toggle; state is exposed via `aria-pressed` and a ✓ glyph (FR-001). */
export function CheckInButton({
  name,
  icon,
  completed,
  disabled,
  onToggle,
}: CheckInButtonProps): JSX.Element {
  return (
    <button
      type="button"
      className="check-in-button"
      aria-pressed={completed}
      aria-label={name}
      disabled={disabled}
      onClick={onToggle}
    >
      <span className="check-in-mark" aria-hidden="true">
        {completed ? '✓' : ''}
      </span>
      {icon && (
        <span className="habit-icon" aria-hidden="true">
          {icon}
        </span>
      )}
      <span className="check-in-name">{name}</span>
    </button>
  );
}
