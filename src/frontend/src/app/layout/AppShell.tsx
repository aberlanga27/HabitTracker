import type { JSX } from 'react';
import { Link, NavLink, Outlet } from 'react-router';

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
        <nav aria-label="Main" className="app-nav">
          <NavLink to="/" end>
            Today
          </NavLink>
          <NavLink to="/habits">Habits</NavLink>
        </nav>
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
