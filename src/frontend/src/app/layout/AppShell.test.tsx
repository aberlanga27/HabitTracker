import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { renderApp } from '@/test/render';
import { ana, API, errorBody, server } from '@/test/server';

describe('spec 001 US3 - Sign out', () => {
  it('given a signed-in user, when choosing "Sign out", then the session is ended and sign-in is shown', async () => {
    let signedIn = true;
    let logoutCalls = 0;
    server.use(
      http.get(`${API}/auth/me`, () =>
        signedIn
          ? HttpResponse.json(ana)
          : HttpResponse.json(errorBody('UNAUTHENTICATED', 'Not signed in'), { status: 401 }),
      ),
      http.post(`${API}/auth/logout`, () => {
        logoutCalls += 1;
        signedIn = false;
        return new HttpResponse(null, { status: 204 });
      }),
      http.get(`${API}/habits`, () => HttpResponse.json({ items: [], total: 0 })),
    );
    const { router } = renderApp('/');
    await userEvent.click(await screen.findByRole('button', { name: /sign out/i }));

    expect(await screen.findByRole('heading', { name: /sign in/i })).toBeInTheDocument();
    expect(logoutCalls).toBe(1);
    expect(router.state.location.pathname).toBe('/sign-in');
    expect(screen.queryByText('ana@example.com')).not.toBeInTheDocument();
  });
});
