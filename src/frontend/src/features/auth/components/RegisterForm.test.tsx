import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { axeViolations, renderApp } from '@/test/render';
import { ana, API, emptyDataHandlers, errorBody, server, sessionHandlers } from '@/test/server';

describe('spec 001 US1 - Register a new account', () => {
  it('given a password shorter than 10 characters, when submitted, then an inline error shows and nothing is sent', async () => {
    let called = false;
    server.use(
      ...sessionHandlers(null),
      http.post(`${API}/auth/register`, () => {
        called = true;
        return HttpResponse.json(ana, { status: 201 });
      }),
    );
    renderApp('/register');
    await userEvent.type(await screen.findByLabelText(/email/i), 'ana@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'short');
    await userEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(screen.getByText(/at least 10 characters/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toHaveAttribute('aria-invalid', 'true');
    expect(called).toBe(false);
  });

  it('given valid details, when submitted, then the user lands on the dashboard with their email in the header', async () => {
    let sent: unknown;
    let registered = false;
    server.use(
      http.get(`${API}/auth/me`, () =>
        registered
          ? HttpResponse.json(ana)
          : HttpResponse.json(errorBody('UNAUTHENTICATED', 'Not signed in'), { status: 401 }),
      ),
      http.post(`${API}/auth/register`, async ({ request }) => {
        sent = await request.json();
        registered = true;
        return HttpResponse.json(ana, { status: 201 });
      }),
      ...emptyDataHandlers(),
    );
    renderApp('/register');
    await userEvent.type(await screen.findByLabelText(/email/i), 'ana@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'twelve-chars');
    await userEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByRole('heading', { name: /today/i })).toBeInTheDocument();
    expect(screen.getByText('ana@example.com')).toBeInTheDocument();
    expect(sent).toMatchObject({
      email: 'ana@example.com',
      password: 'twelve-chars',
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    });
  });

  it('given the server rejects registration, when submitted, then "Could not register" is announced', async () => {
    server.use(
      ...sessionHandlers(null),
      http.post(`${API}/auth/register`, () =>
        HttpResponse.json(errorBody('REGISTRATION_FAILED', 'Could not register'), { status: 400 }),
      ),
    );
    renderApp('/register');
    await userEvent.type(await screen.findByLabelText(/email/i), 'ana@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'twelve-chars');
    await userEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not register');
  });

  it('has no detectable accessibility violations', async () => {
    server.use(...sessionHandlers(null));
    const { container } = renderApp('/register');
    await screen.findByLabelText(/email/i);
    expect(await axeViolations(container)).toEqual([]);
  });
});
