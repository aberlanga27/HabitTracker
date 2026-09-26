import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { renderApp } from '@/test/render';
import { server, sessionHandlers } from '@/test/server';

describe('spec 001 FR-006 - Protected routes', () => {
  it('given no session, when opening a protected page, then it redirects to sign-in with next', async () => {
    server.use(...sessionHandlers(null));
    const { router } = renderApp('/');
    expect(await screen.findByRole('heading', { name: /sign in/i })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/sign-in');
    expect(router.state.location.search).toBe('?next=%2F');
  });
});
