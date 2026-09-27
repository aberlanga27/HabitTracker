import { QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { describe, expect, it } from 'vitest';

import { createQueryClient } from '@/app/providers';
import { habit } from '@/test/habits-backend';

import { HabitList } from './HabitList';

describe('spec 002 SC-003 - render budget', () => {
  it('renders 50 habits in under 100 ms after data arrives', () => {
    const habits = Array.from({ length: 50 }, (_, i) => habit({ name: `Habit ${i}`, position: i }));
    const start = performance.now();
    render(
      <QueryClientProvider client={createQueryClient({ retry: false })}>
        <MemoryRouter>
          <HabitList habits={habits} />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    const elapsed = performance.now() - start;
    expect(screen.getAllByRole('listitem')).toHaveLength(50);
    expect(elapsed).toBeLessThan(100);
  });
});
