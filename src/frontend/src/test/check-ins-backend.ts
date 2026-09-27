import { http, HttpResponse } from 'msw';

import type { components } from '@/shared/types/api.generated';

import { API, errorBody } from './server';

type CheckInState = components['schemas']['CheckInState'];
type CheckInSet = components['schemas']['CheckInSet'];

/** In-memory check-ins API keyed by `${habitId}|${date}`, mirroring the backend contract. */
export function checkInsBackend(initial: CheckInState[] = []): {
  states: Map<string, CheckInState>;
  puts: { habitId: string; date: string; body: CheckInSet }[];
  handlers: ReturnType<typeof http.get>[];
} {
  const states = new Map(initial.map((s) => [`${s.habit_id}|${s.date}`, { ...s }]));
  const puts: { habitId: string; date: string; body: CheckInSet }[] = [];

  const handlers = [
    http.get(`${API}/check-ins`, ({ request }) => {
      const date = new URL(request.url).searchParams.get('date');
      const items = [...states.values()].filter((s) => s.date === date);
      return HttpResponse.json({ items, total: items.length });
    }),
    http.put(`${API}/habits/:habitId/check-ins/:date`, async ({ params, request }) => {
      const habitId = String(params.habitId);
      const date = String(params.date);
      const body = (await request.json()) as CheckInSet;
      puts.push({ habitId, date, body });
      const key = `${habitId}|${date}`;
      if (!body.completed) {
        states.delete(key);
        return HttpResponse.json({
          habit_id: habitId,
          date,
          completed: false,
          note: null,
          completed_at: null,
        });
      }
      const existing = states.get(key);
      const next: CheckInState = {
        habit_id: habitId,
        date,
        completed: true,
        note: 'note' in body ? (body.note ?? null) : (existing?.note ?? null),
        completed_at: existing?.completed_at ?? '2026-09-26T12:00:00Z',
      };
      states.set(key, next);
      return HttpResponse.json(next);
    }),
  ];
  return { states, puts, handlers };
}

export function failingCheckInPut(): ReturnType<typeof http.put> {
  return http.put(`${API}/habits/:habitId/check-ins/:date`, () =>
    HttpResponse.json(errorBody('ERROR', 'boom'), { status: 500 }),
  );
}
