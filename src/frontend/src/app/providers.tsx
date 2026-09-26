import { QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { JSX, ReactNode } from 'react';

import { ApiError } from '@/shared/lib/apiClient';
import { queryKeys } from '@/shared/lib/queryKeys';

export function createQueryClient(options: { retry?: boolean } = {}): QueryClient {
  const queryClient: QueryClient = new QueryClient({
    queryCache: new QueryCache({
      onError: (error) => {
        // Any 401 means the session is gone; ProtectedRoute then redirects to sign-in.
        if (error instanceof ApiError && error.status === 401) {
          queryClient.setQueryData(queryKeys.me(), null);
        }
      },
    }),
    defaultOptions: {
      queries: {
        retry: options.retry === false ? false : 1,
        refetchOnWindowFocus: false,
      },
    },
  });
  return queryClient;
}

export interface ProvidersProps {
  client: QueryClient;
  children: ReactNode;
}

export function Providers({ client, children }: ProvidersProps): JSX.Element {
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
