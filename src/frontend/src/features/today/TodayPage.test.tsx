import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { checkInsBackend, failingCheckInPut } from '@/test/check-ins-backend';
import { habit, habitsBackend } from '@/test/habits-backend';
import { axeViolations, renderApp } from '@/test/render';
import { ana, server, sessionHandlers } from '@/test/server';

const read = habit({ name: 'Read 10 pages', position: 0 });

function setup(
  checkIns: Parameters<typeof checkInsBackend>[0] = [],
  habits = [read],
): ReturnType<typeof checkInsBackend> {
  const backend = checkInsBackend(checkIns);
  server.use(...sessionHandlers(ana), ...habitsBackend(habits).handlers, ...backend.handlers);
  return backend;
}

function toggle(name: string): HTMLElement {
  return screen.getByRole('button', { name });
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-09-26T12:00:00Z'));
});

afterEach(() => {
  vi.useRealTimers();
});

describe('spec 002 interim Today list', () => {
  it('given zero habits, then a "Create your first habit" call-to-action links to /habits', async () => {
    setup([], []);
    renderApp('/');
    const cta = await screen.findByRole('link', { name: /create your first habit/i });
    expect(cta).toHaveAttribute('href', '/habits');
  });

  it('given active and archived habits, then only active habits are shown (US3-S1)', async () => {
    setup(
      [],
      [
        habit({ name: 'Active one', position: 0 }),
        habit({ name: 'Archived one', archived_at: '2026-09-25T12:00:00Z' }),
      ],
    );
    renderApp('/');
    expect(await screen.findByRole('button', { name: 'Active one' })).toBeInTheDocument();
    expect(screen.queryByText('Archived one')).not.toBeInTheDocument();
  });
});

describe('spec 003 US1 - Check in for today', () => {
  it('given an uncompleted habit, when tapped, then it is marked complete immediately and persisted', async () => {
    const backend = setup();
    renderApp('/');
    const button = await screen.findByRole('button', { name: 'Read 10 pages' });
    expect(button).toHaveAttribute('aria-pressed', 'false');
    await userEvent.click(button);

    expect(toggle('Read 10 pages')).toHaveAttribute('aria-pressed', 'true');
    await vi.waitFor(() => expect(backend.puts).toHaveLength(1));
    expect(backend.puts[0]).toEqual({
      habitId: read.id,
      date: '2026-09-26',
      body: { completed: true },
    });
  });

  it('given a completed habit, when tapped, then the completion is removed', async () => {
    const backend = setup([
      {
        habit_id: read.id,
        date: '2026-09-26',
        completed: true,
        note: null,
        completed_at: '2026-09-26T08:00:00Z',
      },
    ]);
    renderApp('/');
    const button = await screen.findByRole('button', { name: 'Read 10 pages', pressed: true });
    await userEvent.click(button);
    expect(toggle('Read 10 pages')).toHaveAttribute('aria-pressed', 'false');
    await vi.waitFor(() => expect(backend.states.size).toBe(0));
  });

  it('given a failing save, when tapped, then the UI rolls back and shows a non-blocking error', async () => {
    setup();
    server.use(failingCheckInPut());
    renderApp('/');
    await userEvent.click(await screen.findByRole('button', { name: 'Read 10 pages' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/could not save/i);
    expect(toggle('Read 10 pages')).toHaveAttribute('aria-pressed', 'false');
  });

  it('has no detectable accessibility violations', async () => {
    setup();
    const { container } = renderApp('/');
    await screen.findByRole('button', { name: 'Read 10 pages' });
    expect(await axeViolations(container)).toEqual([]);
  });
});

describe('spec 003 US2 - Backfill a past day', () => {
  it('given Today, when "Previous day" is pressed, then yesterday shows its own state and can be checked in', async () => {
    const backend = setup([
      {
        habit_id: read.id,
        date: '2026-09-26',
        completed: true,
        note: null,
        completed_at: '2026-09-26T08:00:00Z',
      },
    ]);
    const { router } = renderApp('/');
    await screen.findByRole('button', { name: 'Read 10 pages', pressed: true });
    await userEvent.click(screen.getByRole('button', { name: /previous day/i }));

    expect(
      await screen.findByRole('heading', { name: /friday, 25 september 2026/i }),
    ).toBeVisible();
    expect(router.state.location.search).toBe('?date=2026-09-25');
    const button = await screen.findByRole('button', { name: 'Read 10 pages', pressed: false });
    await userEvent.click(button);
    await vi.waitFor(() => expect(backend.states.has(`${read.id}|2026-09-25`)).toBe(true));

    await userEvent.click(screen.getByRole('link', { name: /^today$/i }));
    expect(await screen.findByRole('heading', { name: /^today$/i })).toBeVisible();
  });

  it('disables "Next day" on today', async () => {
    setup();
    renderApp('/');
    expect(await screen.findByRole('button', { name: /next day/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /previous day/i })).toBeEnabled();
  });

  it('disables "Previous day" 30 days back', async () => {
    setup();
    renderApp('/?date=2026-08-27');
    expect(await screen.findByRole('button', { name: /previous day/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Read 10 pages' })).toBeEnabled();
  });

  it.each([
    ['more than 30 days ago', '2026-08-26', /last 30 days/i],
    ['in the future', '2026-09-27', /future/i],
  ])(
    'given a date %s, then check-in controls are disabled with an explanation',
    async (_label, date, message) => {
      setup();
      renderApp(`/?date=${date}`);
      expect(await screen.findByRole('button', { name: 'Read 10 pages' })).toBeDisabled();
      expect(screen.getByText(message)).toBeInTheDocument();
    },
  );
});

describe('spec 003 US3 - Add a note', () => {
  it('given a completed check-in, when a note is added, then it is saved and shown', async () => {
    const backend = setup([
      {
        habit_id: read.id,
        date: '2026-09-26',
        completed: true,
        note: null,
        completed_at: '2026-09-26T08:00:00Z',
      },
    ]);
    renderApp('/');
    await userEvent.click(
      await screen.findByRole('button', { name: 'Add note for Read 10 pages' }),
    );
    const field = screen.getByLabelText('Note for Read 10 pages');
    expect(field).toHaveAttribute('maxlength', '280');
    await userEvent.type(field, 'ran 5k in the rain');
    await userEvent.click(screen.getByRole('button', { name: /save note/i }));

    const list = screen.getByRole('list', { name: /habits for/i });
    expect(await within(list).findByText('ran 5k in the rain')).toBeInTheDocument();
    expect(backend.states.get(`${read.id}|2026-09-26`)?.note).toBe('ran 5k in the rain');
  });

  it('does not offer a note for an uncompleted habit', async () => {
    setup();
    renderApp('/');
    await screen.findByRole('button', { name: 'Read 10 pages' });
    expect(screen.queryByRole('button', { name: /add note/i })).not.toBeInTheDocument();
  });
});
