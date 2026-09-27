import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { axeViolations, renderApp } from '@/test/render';
import { ana, API, emptyDataHandlers, errorBody, server, sessionHandlers } from '@/test/server';

async function fillAndSubmit(email: string, password: string): Promise<void> {
  await userEvent.type(await screen.findByLabelText(/email/i), email);
  await userEvent.type(screen.getByLabelText(/password/i), password);
  await userEvent.click(screen.getByRole('button', { name: /sign in/i }));
}

describe('spec 001 US2 - Sign in', () => {
  it('given wrong credentials, when submitted, then "Invalid email or password" is shown', async () => {
    server.use(
      ...sessionHandlers(null),
      http.post(`${API}/auth/login`, () =>
        HttpResponse.json(errorBody('INVALID_CREDENTIALS', 'Invalid email or password'), {
          status: 401,
        }),
      ),
    );
    renderApp('/sign-in');
    await fillAndSubmit('ana@example.com', 'wrong-password');
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password');
  });

  it('given a locked-out email, when submitted, then the lockout message is shown', async () => {
    server.use(
      ...sessionHandlers(null),
      http.post(`${API}/auth/login`, () =>
        HttpResponse.json(errorBody('LOCKED_OUT', 'Too many failed attempts.'), { status: 429 }),
      ),
    );
    renderApp('/sign-in');
    await fillAndSubmit('ana@example.com', 'whatever-123');
    expect(await screen.findByRole('alert')).toHaveTextContent(/too many failed attempts/i);
  });

  it('given correct credentials, when submitted, then the user is sent to the "next" page', async () => {
    let signedIn = false;
    server.use(
      http.get(`${API}/auth/me`, () =>
        signedIn
          ? HttpResponse.json(ana)
          : HttpResponse.json(errorBody('UNAUTHENTICATED', 'Not signed in'), { status: 401 }),
      ),
      http.post(`${API}/auth/login`, () => {
        signedIn = true;
        return HttpResponse.json(ana);
      }),
      ...emptyDataHandlers(),
    );
    const { router } = renderApp('/sign-in?next=%2F');
    await fillAndSubmit('ana@example.com', 'correct-horse-battery');
    expect(await screen.findByRole('heading', { name: /today/i })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/');
  });

  it('given empty fields, when submitted, then inline errors show', async () => {
    server.use(...sessionHandlers(null));
    renderApp('/sign-in');
    await userEvent.click(await screen.findByRole('button', { name: /sign in/i }));
    expect(screen.getByText(/enter your email/i)).toBeInTheDocument();
    expect(screen.getByText(/enter your password/i)).toBeInTheDocument();
  });

  it('given a signed-in user, when visiting sign-in, then they are redirected to the dashboard', async () => {
    server.use(...sessionHandlers(ana), ...emptyDataHandlers());
    const { router } = renderApp('/sign-in');
    expect(await screen.findByRole('heading', { name: /today/i })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/');
  });

  it('has no detectable accessibility violations', async () => {
    server.use(...sessionHandlers(null));
    const { container } = renderApp('/sign-in');
    await screen.findByLabelText(/email/i);
    expect(await axeViolations(container)).toEqual([]);
  });
});
