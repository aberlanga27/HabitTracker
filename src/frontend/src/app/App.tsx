import type { JSX } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router';

import { createQueryClient, Providers } from './providers';
import { routes } from './routes';

const queryClient = createQueryClient();
const router = createBrowserRouter(routes);

export function App(): JSX.Element {
  return (
    <Providers client={queryClient}>
      <RouterProvider router={router} />
    </Providers>
  );
}
