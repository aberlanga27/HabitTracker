import { http, HttpResponse } from 'msw';

import type { components } from '@/shared/types/api.generated';

import { API, errorBody } from './server';

type HabitRead = components['schemas']['HabitRead'];
type CheckInState = components['schemas']['CheckInState'];
type CheckInSet = components['schemas']['CheckInSet'];
type DayHabit = components['schemas']['DayHabit'];

export interface DayStatus {
  status: DayHabit['status'];
  week?: DayHabit['week'];
}

/**
 * In-memory `/days/:date` + check-in PUT API. Due-ness is decided by the backend, so tests
 * pass `statusFor` to say which habits a date lists (default: every habit is due).
 */
export function dayBackend(
  habits: HabitRead[],
  options: {
    checkIns?: CheckInState[];
    statusFor?: (habit: HabitRead, date: string) => DayStatus | null;
  } = {},
): {
  states: Map<string, CheckInState>;
  puts: { habitId: string; date: string; body: CheckInSet }[];
  handlers: ReturnType<typeof http.get>[];
} {
  const states = new Map((options.checkIns ?? []).map((s) => [`${s.habit_id}|${s.date}`, s]));
  const puts: { habitId: string; date: string; body: CheckInSet }[] = [];
  const statusFor = options.statusFor ?? ((): DayStatus => ({ status: 'due' }));

  const handlers = [
    http.get(`${API}/days/:date`, ({ params }) => {
      const date = String(params.date);
      const items: DayHabit[] = [];
      for (const habit of habits.filter((h) => h.archived_at === null)) {
        const status = statusFor(habit, date);
        if (!status) continue;
        const state = states.get(`${habit.id}|${date}`);
        items.push({
          habit,
          status: status.status,
          completed: state !== undefined,
          note: state?.note ?? null,
          week: status.week ?? null,
        });
      }
      return HttpResponse.json({ date, items });
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
