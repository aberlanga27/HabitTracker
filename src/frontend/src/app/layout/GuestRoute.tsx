import type { JSX } from 'react';
import { Navigate, Outlet, useSearchParams } from 'react-router';

import { safeNext, useMe } from '@/features/auth';

export function GuestRoute(): JSX.Element {
  const me = useMe();
  const [params] = useSearchParams();

  if (me.isPending) {
    return <p className="page-loading">Loading…</p>;
  }
  if (me.data) {
    return <Navigate to={safeNext(params.get('next'))} replace />;
  }
  return <Outlet />;
}
