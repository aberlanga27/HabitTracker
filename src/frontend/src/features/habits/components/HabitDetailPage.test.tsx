import { screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { habit } from '@/test/habits-backend';
import { axeViolations, renderApp } from '@/test/render';
import { ana, API, errorBody, server, sessionHandlers } from '@/test/server';

const read = habit({
  name: 'Read 10 pages',
  streak: {
    current: 2,
    current_start: '2026-09-25',
    longest: 5,
    longest_start: '2026-09-01',
    longest_end: '2026-09-05',
  },
});

describe('spec 004 US2 - See longest streak', () => {
  it('given streaks of 5 and 2, when viewing habit detail, then longest shows 5 with its dates', async () => {
    server.use(
      ...sessionHandlers(ana),
      http.get(`${API}/habits/:id`, () => HttpResponse.json(read)),
    );
    const { container } = renderApp(`/habits/${read.id}`);

    expect(await screen.findByRole('heading', { name: 'Read 10 pages', level: 1 })).toBeVisible();
    expect(screen.getByLabelText('Current streak: 2 days')).toBeInTheDocument();
    const longest = screen.getByRole('group', { name: /longest streak/i });
    expect(longest).toHaveTextContent('5 days');
    expect(longest).toHaveTextContent('1 September 2026 – 5 September 2026');
    expect(await axeViolations(container)).toEqual([]);
  });

  it('shows a placeholder when there is no streak yet', async () => {
    server.use(
      ...sessionHandlers(ana),
      http.get(`${API}/habits/:id`, () => HttpResponse.json(habit({ name: 'New habit' }))),
    );
    renderApp('/habits/any');
    const longest = await screen.findByRole('group', { name: /longest streak/i });
    expect(longest).toHaveTextContent(/no streak yet/i);
  });

  it('shows not found for an unknown habit', async () => {
    server.use(
      ...sessionHandlers(ana),
      http.get(`${API}/habits/:id`, () =>
        HttpResponse.json(errorBody('NOT_FOUND', 'Habit not found'), { status: 404 }),
      ),
    );
    renderApp('/habits/missing');
    expect(await screen.findByRole('alert')).toHaveTextContent('Habit not found');
  });
});
