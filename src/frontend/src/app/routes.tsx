import type { RouteObject } from 'react-router';

import { RegisterPage, SignInPage } from '@/features/auth';
import { HabitDetailPage, HabitsPage } from '@/features/habits';
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
        children: [
          { path: '/', element: <TodayPage /> },
          { path: '/habits', element: <HabitsPage /> },
          { path: '/habits/:habitId', element: <HabitDetailPage /> },
        ],
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
