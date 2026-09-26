import type { RouteObject } from 'react-router';

import { RegisterPage, SignInPage } from '@/features/auth';
import { TodayPage } from '@/features/today';

import { AppShell } from './layout/AppShell';
import { GuestRoute } from './layout/GuestRoute';
import { ProtectedRoute } from './layout/ProtectedRoute';

export const routes: RouteObject[] = [
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [{ path: '/', element: <TodayPage /> }],
      },
    ],
  },
  {
    element: <GuestRoute />,
    children: [
      { path: '/sign-in', element: <SignInPage /> },
      { path: '/register', element: <RegisterPage /> },
    ],
  },
];
