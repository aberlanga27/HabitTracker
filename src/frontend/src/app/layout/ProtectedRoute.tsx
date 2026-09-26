import type { JSX } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router';

import { useMe } from '@/features/auth';

export function ProtectedRoute(): JSX.Element {
  const me = useMe();
  const location = useLocation();

  if (me.isPending) {
    return <p className="page-loading">Loading…</p>;
  }
  if (!me.data) {
    const next = encodeURIComponent(`${location.pathname}${location.search}`);
    return <Navigate to={`/sign-in?next=${next}`} replace />;
  }
  return <Outlet />;
}
