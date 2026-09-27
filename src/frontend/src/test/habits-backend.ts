import { http, HttpResponse } from 'msw';

import type { components } from '@/shared/types/api.generated';

import { API, errorBody } from './server';

type HabitRead = components['schemas']['HabitRead'];
type HabitCreate = components['schemas']['HabitCreate'];
type HabitUpdate = components['schemas']['HabitUpdate'];
type ScheduleIn = components['schemas']['ScheduleIn'];
type ScheduleRead = components['schemas']['ScheduleRead'];

export const DAILY: ScheduleRead = {
  type: 'daily',
  weekdays: [],
  times_per_week: null,
  effective_from: '2026-09-26',
};

export const NO_STREAK: HabitRead['streak'] = {
  current: 0,
  current_start: null,
  longest: 0,
  longest_start: null,
  longest_end: null,
};

function toRead(schedule: ScheduleIn | null | undefined): ScheduleRead {
  if (!schedule) return DAILY;
  return {
    type: schedule.type,
    weekdays: schedule.weekdays ?? [],
    times_per_week: schedule.times_per_week ?? null,
    effective_from: '2026-09-26',
  };
}

let counter = 0;

export function habit(overrides: Partial<HabitRead> = {}): HabitRead {
  counter += 1;
  return {
    id: `0192f000-0000-7000-8000-${String(counter).padStart(12, '0')}`,
    name: `Habit ${counter}`,
    description: null,
    icon: null,
    color: 'coral',
    position: counter,
    archived_at: null,
    created_at: '2026-09-26T12:00:00Z',
    schedule: DAILY,
    streak: NO_STREAK,
    ...overrides,
  };
}

/** A tiny in-memory stand-in for the habits API, mirroring the backend contract. */
export function habitsBackend(initial: HabitRead[] = []): {
  habits: HabitRead[];
  handlers: ReturnType<typeof http.get>[];
} {
  const state = { habits: initial.map((h) => ({ ...h })) };
  const active = (): HabitRead[] =>
    state.habits.filter((h) => h.archived_at === null).sort((a, b) => a.position - b.position);
  const nextPosition = (): number => Math.max(-1, ...active().map((h) => h.position)) + 1;
  const find = (id: unknown): HabitRead | undefined => state.habits.find((h) => h.id === id);
  const notFound = (): Response =>
    HttpResponse.json(errorBody('NOT_FOUND', 'Habit not found'), { status: 404 });

  const handlers = [
    http.get(`${API}/habits`, ({ request }) => {
      const archived = new URL(request.url).searchParams.get('archived') === 'true';
      const items = archived ? state.habits.filter((h) => h.archived_at !== null) : active();
      return HttpResponse.json({ items, total: items.length });
    }),
    http.post(`${API}/habits`, async ({ request }) => {
      const body = (await request.json()) as HabitCreate;
      if (active().length >= 50) {
        return HttpResponse.json(errorBody('HABIT_LIMIT_REACHED', 'Habit limit reached (50)'), {
          status: 409,
        });
      }
      const created = habit({
        name: body.name.trim(),
        description: body.description ?? null,
        icon: body.icon ?? null,
        color: body.color ?? 'coral',
        position: nextPosition(),
        schedule: toRead(body.schedule),
      });
      state.habits.push(created);
      return HttpResponse.json(created, { status: 201 });
    }),
    http.put(`${API}/habits/order`, async ({ request }) => {
      const { habit_ids } = (await request.json()) as { habit_ids: string[] };
      habit_ids.forEach((id, position) => {
        const h = find(id);
        if (h) h.position = position;
      });
      const items = active();
      return HttpResponse.json({ items, total: items.length });
    }),
    http.patch(`${API}/habits/:id`, async ({ params, request }) => {
      const h = find(params.id);
      if (!h) return notFound();
      const { schedule, ...rest } = (await request.json()) as HabitUpdate;
      Object.assign(h, rest, schedule ? { schedule: toRead(schedule) } : {});
      return HttpResponse.json(h);
    }),
    http.delete(`${API}/habits/:id`, ({ params }) => {
      if (!find(params.id)) return notFound();
      state.habits = state.habits.filter((h) => h.id !== params.id);
      return new HttpResponse(null, { status: 204 });
    }),
    http.post(`${API}/habits/:id/archive`, ({ params }) => {
      const h = find(params.id);
      if (!h) return notFound();
      h.archived_at ??= '2026-09-26T12:00:00Z';
      return HttpResponse.json(h);
    }),
    http.post(`${API}/habits/:id/restore`, ({ params }) => {
      const h = find(params.id);
      if (!h) return notFound();
      if (h.archived_at !== null) {
        h.position = nextPosition();
        h.archived_at = null;
      }
      return HttpResponse.json(h);
    }),
  ];
  return {
    get habits() {
      return state.habits;
    },
    handlers,
  };
}
