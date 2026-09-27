import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

import type { components } from '@/shared/types/api.generated';

export const server = setupServer();

export const API = '*/api/v1';

type UserRead = components['schemas']['UserRead'];

export const ana: UserRead = {
  id: '0192f000-0000-7000-8000-000000000001',
  email: 'ana@example.com',
  timezone: 'UTC',
  created_at: '2026-09-26T12:00:00Z',
};

export function errorBody(code: string, message: string): { error: object } {
  return { error: { code, message, details: {} } };
}

/** Handlers for a signed-in or signed-out session. */
export function sessionHandlers(user: UserRead | null): ReturnType<typeof http.get>[] {
  return [
    http.get(`${API}/auth/me`, () =>
      user
        ? HttpResponse.json(user)
        : HttpResponse.json(errorBody('UNAUTHENTICATED', 'Not signed in'), { status: 401 }),
    ),
  ];
}

/** Empty data endpoints for tests that only need the dashboard to render. */
export function emptyDataHandlers(): ReturnType<typeof http.get>[] {
  return [
    http.get(`${API}/habits`, () => HttpResponse.json({ items: [], total: 0 })),
    http.get(`${API}/days/:date`, ({ params }) =>
      HttpResponse.json({
        date: String(params.date),
        items: [],
        due_count: 0,
        completed_count: 0,
        habit_count: 0,
      }),
    ),
  ];
}
