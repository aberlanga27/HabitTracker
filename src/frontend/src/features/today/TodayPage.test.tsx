import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { dayBackend, failingCheckInPut, type DayStatus } from '@/test/day-backend';
import { habit, habitsBackend } from '@/test/habits-backend';
import { axeViolations, renderApp } from '@/test/render';
import { ana, server, sessionHandlers } from '@/test/server';

const read = habit({ name: 'Read 10 pages', position: 0 });

type CheckIns = NonNullable<Parameters<typeof dayBackend>[1]>['checkIns'];

function setup(
  checkIns: CheckIns = [],
  habits = [read],
  statusFor?: (h: (typeof habits)[number], date: string) => DayStatus | null,
): ReturnType<typeof dayBackend> {
  const backend = dayBackend(habits, { checkIns, statusFor });
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

    await userEvent.click(screen.getByRole('link', { name: /jump to today/i }));
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
    expect(await screen.findByRole('button', { name: 'Read 10 pages' })).toBeEnabled();
    expect(screen.getByRole('button', { name: /previous day/i })).toBeDisabled();
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

    const list = screen.getByRole('list', { name: 'Done' });
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

describe('spec 004 US1 - Current streak on Today', () => {
  it('shows the current streak next to the habit', async () => {
    const streaky = habit({
      name: 'Meditate',
      streak: {
        current: 3,
        current_start: '2026-09-24',
        longest: 3,
        longest_start: '2026-09-24',
        longest_end: '2026-09-26',
      },
    });
    setup([], [streaky]);
    renderApp('/');
    expect(await screen.findByLabelText('Current streak: 3 days')).toBeInTheDocument();
  });
});

describe('spec 005 - Schedules on Today', () => {
  const gym = habit({
    name: 'Gym',
    position: 1,
    schedule: {
      type: 'weekdays',
      weekdays: ['mon', 'wed', 'fri'],
      times_per_week: null,
      effective_from: '2026-09-21',
    },
  });

  it('US2-S1: a Mon/Wed/Fri habit is not listed on a day the server says it is not due', async () => {
    setup([], [read, gym], (h, date) =>
      h.id === gym.id && date === '2026-09-22' ? null : { status: 'due' },
    );
    renderApp('/?date=2026-09-22');
    expect(await screen.findByRole('button', { name: 'Read 10 pages' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Gym' })).not.toBeInTheDocument();
  });

  it('US3-S1: a 3x/week habit with 2 check-ins shows "2 of 3 this week"', async () => {
    setup([], [read], () => ({ status: 'due', week: { completed: 2, target: 3 } }));
    renderApp('/');
    const list = await screen.findByRole('list', { name: 'To do' });
    expect(await within(list).findByText('2 of 3 this week')).toBeInTheDocument();
  });

  it('US3-S2: a 3x/week habit with 3 check-ins shows "Done for this week"', async () => {
    setup([], [read], () => ({ status: 'done_for_week', week: { completed: 3, target: 3 } }));
    renderApp('/');
    const list = await screen.findByRole('list', { name: 'Done' });
    expect(await within(list).findByText(/done for this week/i)).toBeInTheDocument();
  });
});

function fiveHabits(): ReturnType<typeof habit>[] {
  return ['A', 'B', 'C', 'D', 'E'].map((name, position) =>
    habit({ name: `Habit ${name}`, position }),
  );
}

function doneOn(habits: ReturnType<typeof habit>[], date = '2026-09-26'): CheckIns {
  return habits.map((h) => ({
    habit_id: h.id,
    date,
    completed: true,
    note: null,
    completed_at: `${date}T08:00:00Z`,
  }));
}

describe('spec 006 US1 - See today at a glance', () => {
  it('given 5 due habits with 3 complete, then progress shows "3 of 5" and 60%', async () => {
    const habits = fiveHabits();
    setup(doneOn(habits.slice(0, 3)), habits);
    renderApp('/');
    expect(await screen.findByText('3 of 5 habits done')).toHaveAttribute('aria-live', 'polite');
    expect(screen.getByRole('progressbar', { name: /daily progress/i })).toHaveAttribute(
      'aria-valuenow',
      '60',
    );
  });

  it('given zero habits, then an empty state with "Create your first habit" is shown', async () => {
    setup([], []);
    renderApp('/');
    expect(await screen.findByRole('link', { name: /create your first habit/i })).toBeVisible();
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });

  it('given all habits complete, then "All done for today" is shown', async () => {
    const habits = fiveHabits().slice(0, 2);
    setup(doneOn(habits), habits);
    renderApp('/');
    expect(await screen.findByText(/all done for today/i)).toBeVisible();
  });

  it('given habits but none due, then it says nothing is scheduled', async () => {
    setup([], [read], () => null);
    renderApp('/');
    expect(await screen.findByText(/nothing is scheduled for this day/i)).toBeVisible();
  });

  it('FR-006: toggling announces the new progress immediately', async () => {
    const habits = fiveHabits();
    setup(doneOn(habits.slice(0, 3)), habits);
    renderApp('/');
    await screen.findByText('3 of 5 habits done');
    await userEvent.click(screen.getByRole('button', { name: 'Habit D' }));
    expect(screen.getByText('4 of 5 habits done')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '80');
  });

  it('shows skeleton rows while loading instead of a spinner', () => {
    setup();
    renderApp('/');
    // The session query resolves first; the skeleton appears while the day loads.
    return vi.waitFor(() =>
      expect(screen.getByRole('region', { name: 'Loading habits' })).toHaveAttribute(
        'aria-busy',
        'true',
      ),
    );
  });

  it('has no detectable accessibility violations with progress and sections', async () => {
    const habits = fiveHabits();
    setup(doneOn(habits.slice(0, 2)), habits);
    const { container } = renderApp('/');
    await screen.findByText('2 of 5 habits done');
    expect(await axeViolations(container)).toEqual([]);
  });
});

describe('spec 006 US3 - Group by completion', () => {
  it('given a due habit, when completed, then it moves to the Done section without reload', async () => {
    setup();
    renderApp('/');
    const todo = await screen.findByRole('list', { name: 'To do' });
    await userEvent.click(within(todo).getByRole('button', { name: 'Read 10 pages' }));
    const done = await screen.findByRole('list', { name: 'Done' });
    expect(within(done).getByRole('button', { name: 'Read 10 pages' })).toBeInTheDocument();
    expect(screen.queryByRole('list', { name: 'To do' })).not.toBeInTheDocument();
  });
});

describe('spec 006 edge - midnight rollover', () => {
  it('given the tab stays open, when local midnight passes, then the header shows the new day', async () => {
    vi.useFakeTimers({ toFake: ['Date', 'setInterval', 'clearInterval'] });
    vi.setSystemTime(new Date('2026-09-26T23:59:50Z'));
    setup();
    renderApp('/');
    expect(await screen.findByText('Saturday, 26 September 2026')).toBeInTheDocument();
    await vi.advanceTimersByTimeAsync(30_000);
    expect(await screen.findByText('Sunday, 27 September 2026')).toBeInTheDocument();
  });

  it('keeps an explicitly chosen date when midnight passes', async () => {
    vi.useFakeTimers({ toFake: ['Date', 'setInterval', 'clearInterval'] });
    vi.setSystemTime(new Date('2026-09-26T23:59:50Z'));
    setup();
    renderApp('/?date=2026-09-25');
    const heading = await screen.findByRole('heading', { name: 'Friday, 25 September 2026' });
    await vi.advanceTimersByTimeAsync(30_000);
    expect(heading).toHaveTextContent('Friday, 25 September 2026');
  });
});
