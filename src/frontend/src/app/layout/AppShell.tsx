import type { JSX } from 'react';
import { Link, Outlet } from 'react-router';

import { useLogout, useMe } from '@/features/auth';

export function AppShell(): JSX.Element {
  const me = useMe();
  const logout = useLogout();

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="brand">
          Habitude
        </Link>
        <div className="app-header-user">
          <span className="user-email">{me.data?.email}</span>
          <button
            type="button"
            className="button"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
