import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { habit, habitsBackend } from '@/test/habits-backend';
import { renderApp } from '@/test/render';
import { ana, server, sessionHandlers } from '@/test/server';

describe('spec 002 interim Today list', () => {
  it('given zero habits, then a "Create your first habit" call-to-action links to /habits', async () => {
    server.use(...sessionHandlers(ana), ...habitsBackend([]).handlers);
    renderApp('/');
    const cta = await screen.findByRole('link', { name: /create your first habit/i });
    expect(cta).toHaveAttribute('href', '/habits');
  });

  it('given active and archived habits, then only active habits are shown (US3-S1)', async () => {
    server.use(
      ...sessionHandlers(ana),
      ...habitsBackend([
        habit({ name: 'Active one', position: 0 }),
        habit({ name: 'Archived one', archived_at: '2026-09-25T12:00:00Z' }),
      ]).handlers,
    );
    renderApp('/');
    expect(await screen.findByText('Active one')).toBeInTheDocument();
    expect(screen.queryByText('Archived one')).not.toBeInTheDocument();
  });
});
