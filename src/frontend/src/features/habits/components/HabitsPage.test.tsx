import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it, vi } from 'vitest';

import { habit, habitsBackend } from '@/test/habits-backend';
import { axeViolations, renderApp } from '@/test/render';
import { ana, API, errorBody, server, sessionHandlers } from '@/test/server';

function setup(
  initial = [habit({ name: 'Read 10 pages', position: 0 })],
): ReturnType<typeof habitsBackend> {
  const backend = habitsBackend(initial);
  server.use(...sessionHandlers(ana), ...backend.handlers);
  return backend;
}

function activeList(): HTMLElement {
  return screen.getByRole('list', { name: /active habits/i });
}

describe('spec 002 US1 - Create a habit', () => {
  it('given the new-habit form, when submitted with a name, then the habit is listed', async () => {
    const backend = setup([]);
    renderApp('/habits');
    await userEvent.type(await screen.findByLabelText(/^name/i), 'Drink 2L of water');
    await userEvent.click(screen.getByRole('radio', { name: 'Water' }));
    await userEvent.click(screen.getByRole('radio', { name: 'Teal' }));
    await userEvent.click(screen.getByRole('button', { name: /add habit/i }));

    expect(await within(activeList()).findByText('Drink 2L of water')).toBeInTheDocument();
    expect(backend.habits[0]).toMatchObject({
      name: 'Drink 2L of water',
      icon: '💧',
      color: 'teal',
    });
    expect(screen.getByLabelText(/^name/i)).toHaveValue('');
  });

  it.each([
    ['blank', '   ', /enter a name/i],
    ['81 characters', 'a'.repeat(81), /at most 80 characters/i],
  ])(
    'given a %s name, when submitted, then an inline error shows and nothing is saved',
    async (_label, name, message) => {
      const backend = setup([]);
      renderApp('/habits');
      await userEvent.type(await screen.findByLabelText(/^name/i), name);
      await userEvent.click(screen.getByRole('button', { name: /add habit/i }));
      expect(screen.getByText(message)).toBeInTheDocument();
      expect(backend.habits).toHaveLength(0);
    },
  );

  it('given 50 habits, when creating a 51st, then "Habit limit reached (50)" is announced', async () => {
    setup([]);
    server.use(
      http.post(`${API}/habits`, () =>
        HttpResponse.json(errorBody('HABIT_LIMIT_REACHED', 'Habit limit reached (50)'), {
          status: 409,
        }),
      ),
    );
    renderApp('/habits');
    await userEvent.type(await screen.findByLabelText(/^name/i), 'One too many');
    await userEvent.click(screen.getByRole('button', { name: /add habit/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Habit limit reached (50)');
  });

  it('exposes icon and color pickers as labelled radio groups', async () => {
    setup([]);
    renderApp('/habits');
    expect(await screen.findByRole('radiogroup', { name: /icon/i })).toBeInTheDocument();
    expect(screen.getByRole('radiogroup', { name: /color/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Coral' })).toBeChecked();
  });

  it('has no detectable accessibility violations', async () => {
    setup();
    const { container } = renderApp('/habits');
    await screen.findByText('Read 10 pages');
    expect(await axeViolations(container)).toEqual([]);
  });
});

describe('spec 002 US2 - Edit a habit', () => {
  it('given an existing habit, when renamed and saved, then the new name shows', async () => {
    const backend = setup();
    renderApp('/habits');
    await userEvent.click(await screen.findByRole('button', { name: 'Edit Read 10 pages' }));
    const name = screen.getByLabelText(/^name/i, { selector: '#edit-name' });
    await userEvent.clear(name);
    await userEvent.type(name, 'Read 20 pages');
    await userEvent.click(screen.getByRole('button', { name: /^save/i }));

    expect(await within(activeList()).findByText('Read 20 pages')).toBeInTheDocument();
    expect(backend.habits[0]?.name).toBe('Read 20 pages');
  });

  it('given an edit form, when cancelled, then nothing is persisted', async () => {
    let patched = false;
    setup();
    server.use(
      http.patch(`${API}/habits/:id`, () => {
        patched = true;
        return HttpResponse.json({});
      }),
    );
    renderApp('/habits');
    await userEvent.click(await screen.findByRole('button', { name: 'Edit Read 10 pages' }));
    const name = screen.getByLabelText(/^name/i, { selector: '#edit-name' });
    await userEvent.clear(name);
    await userEvent.type(name, 'Changed');
    await userEvent.click(screen.getByRole('button', { name: /cancel/i }));

    expect(within(activeList()).getByText('Read 10 pages')).toBeInTheDocument();
    expect(patched).toBe(false);
  });
});

describe('spec 002 US3 - Archive and restore', () => {
  it('given an active habit, when archived, then it is listed under Archived; when restored, it returns', async () => {
    setup();
    renderApp('/habits');
    await userEvent.click(await screen.findByRole('button', { name: 'Archive Read 10 pages' }));
    const archived = await screen.findByRole('list', { name: /archived habits/i });
    expect(await within(archived).findByText('Read 10 pages')).toBeInTheDocument();
    expect(screen.getByText(/no active habits/i)).toBeInTheDocument();

    await userEvent.click(within(archived).getByRole('button', { name: 'Restore Read 10 pages' }));
    expect(await within(activeList()).findByText('Read 10 pages')).toBeInTheDocument();
  });
});

describe('spec 002 US4 - Delete a habit', () => {
  it('given the delete panel, when the exact name is typed and confirmed, then the habit is removed', async () => {
    const backend = setup();
    renderApp('/habits');
    await userEvent.click(await screen.findByRole('button', { name: 'Delete Read 10 pages' }));
    const confirm = screen.getByRole('button', { name: /delete permanently/i });
    expect(confirm).toBeDisabled();
    const input = screen.getByLabelText(/type .*read 10 pages.* to confirm/i);
    expect(input).toHaveFocus();
    await userEvent.type(input, 'Read 10 page');
    expect(confirm).toBeDisabled();
    await userEvent.type(input, 's');
    expect(confirm).toBeEnabled();
    await userEvent.click(confirm);

    expect(await screen.findByText(/no active habits/i)).toBeInTheDocument();
    expect(backend.habits).toHaveLength(0);
  });

  it('given the delete panel, when cancelled, then nothing is removed', async () => {
    const backend = setup();
    renderApp('/habits');
    await userEvent.click(await screen.findByRole('button', { name: 'Delete Read 10 pages' }));
    await userEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(within(activeList()).getByText('Read 10 pages')).toBeInTheDocument();
    expect(backend.habits).toHaveLength(1);
  });
});

describe('spec 005 - Habit schedules', () => {
  it('US1: the schedule defaults to "Every day" and the list shows it', async () => {
    const backend = setup([]);
    renderApp('/habits');
    expect(await screen.findByRole('radio', { name: 'Every day' })).toBeChecked();
    await userEvent.type(screen.getByLabelText(/^name/i), 'Drink water');
    await userEvent.click(screen.getByRole('button', { name: /add habit/i }));

    expect(await within(activeList()).findByText('Every day')).toBeInTheDocument();
    expect(backend.habits[0]?.schedule.type).toBe('daily');
  });

  it('US2: specific days sends the chosen weekdays and the list shows them', async () => {
    const backend = setup([]);
    renderApp('/habits');
    await userEvent.type(await screen.findByLabelText(/^name/i), 'Gym');
    await userEvent.click(screen.getByRole('radio', { name: 'Specific days' }));
    const days = screen.getByRole('group', { name: /days/i });
    await userEvent.click(within(days).getByRole('checkbox', { name: 'Monday' }));
    await userEvent.click(within(days).getByRole('checkbox', { name: 'Wednesday' }));
    await userEvent.click(within(days).getByRole('checkbox', { name: 'Friday' }));
    await userEvent.click(screen.getByRole('button', { name: /add habit/i }));

    expect(await within(activeList()).findByText('Mon, Wed, Fri')).toBeInTheDocument();
    expect(backend.habits[0]?.schedule).toMatchObject({
      type: 'weekdays',
      weekdays: ['mon', 'wed', 'fri'],
    });
  });

  it('US2-S2: specific days with none selected shows an error and saves nothing', async () => {
    const backend = setup([]);
    renderApp('/habits');
    await userEvent.type(await screen.findByLabelText(/^name/i), 'Gym');
    await userEvent.click(screen.getByRole('radio', { name: 'Specific days' }));
    await userEvent.click(screen.getByRole('button', { name: /add habit/i }));
    expect(screen.getByText(/choose at least one day/i)).toBeInTheDocument();
    expect(backend.habits).toHaveLength(0);
  });

  it('US3: times per week sends the target and the list shows "3× per week"', async () => {
    const backend = setup([]);
    renderApp('/habits');
    await userEvent.type(await screen.findByLabelText(/^name/i), 'Run');
    await userEvent.click(screen.getByRole('radio', { name: 'Times per week' }));
    const times = screen.getByLabelText(/times each week/i);
    await userEvent.clear(times);
    await userEvent.type(times, '3');
    await userEvent.click(screen.getByRole('button', { name: /add habit/i }));

    expect(await within(activeList()).findByText('3× per week')).toBeInTheDocument();
    expect(backend.habits[0]?.schedule).toMatchObject({
      type: 'times_per_week',
      times_per_week: 3,
    });
  });

  it('US4: editing the schedule sends it in the update', async () => {
    let sent: unknown;
    setup();
    server.use(
      http.patch(`${API}/habits/:id`, async ({ request }) => {
        sent = await request.json();
        return HttpResponse.json(habit({ name: 'Read 10 pages' }));
      }),
    );
    renderApp('/habits');
    await userEvent.click(await screen.findByRole('button', { name: 'Edit Read 10 pages' }));
    await userEvent.click(within(activeList()).getByRole('radio', { name: 'Times per week' }));
    await userEvent.click(screen.getByRole('button', { name: /^save/i }));
    await vi.waitFor(() =>
      expect(sent).toMatchObject({ schedule: { type: 'times_per_week', times_per_week: 3 } }),
    );
  });
});

describe('spec 002 US5 - Reorder habits', () => {
  it('given three habits, when the third is moved up twice with the keyboard, then it is first', async () => {
    const backend = setup([
      habit({ name: 'First', position: 0 }),
      habit({ name: 'Second', position: 1 }),
      habit({ name: 'Third', position: 2 }),
    ]);
    renderApp('/habits');
    const moveUp = await screen.findByRole('button', { name: 'Move Third up' });
    moveUp.focus();
    await userEvent.keyboard('{Enter}');
    await within(activeList()).findByText('Third');
    await screen.findByRole('button', { name: 'Move Third up' });
    screen.getByRole('button', { name: 'Move Third up' }).focus();
    await userEvent.keyboard('{Enter}');

    await expect
      .poll(() =>
        within(activeList())
          .getAllByRole('heading')
          .map((h) => h.textContent),
      )
      .toEqual(['Third', 'First', 'Second']);
    expect([...backend.habits].sort((a, b) => a.position - b.position).map((h) => h.name)).toEqual([
      'Third',
      'First',
      'Second',
    ]);
  });

  it('disables "Move up" on the first habit and "Move down" on the last', async () => {
    setup([habit({ name: 'First', position: 0 }), habit({ name: 'Last', position: 1 })]);
    renderApp('/habits');
    expect(await screen.findByRole('button', { name: 'Move First up' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Move Last down' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Move First down' })).toBeEnabled();
  });
});
