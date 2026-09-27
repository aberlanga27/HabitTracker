import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { StreakBadge } from './StreakBadge';

describe('spec 004 US1 - StreakBadge', () => {
  it('shows the flame and count with a spoken label', () => {
    render(<StreakBadge current={3} />);
    const badge = screen.getByText('3');
    expect(badge.closest('[aria-label]')).toHaveAttribute('aria-label', 'Current streak: 3 days');
  });

  it('uses the singular for one day', () => {
    render(<StreakBadge current={1} />);
    expect(screen.getByLabelText('Current streak: 1 day')).toBeInTheDocument();
  });

  it('still renders a zero streak', () => {
    render(<StreakBadge current={0} />);
    expect(screen.getByLabelText('Current streak: 0 days')).toBeInTheDocument();
  });
});
