import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from '@tanstack/react-query';

import type { ApiError } from '@/shared/lib/apiClient';
import { queryKeys } from '@/shared/lib/queryKeys';

import * as authApi from '../api';
import type { LoginRequest, RegisterRequest, UserRead } from '../types';

export function useMe(): UseQueryResult<UserRead | null> {
  return useQuery({ queryKey: queryKeys.me(), queryFn: authApi.fetchMe, staleTime: 60_000 });
}

export function useRegister(): UseMutationResult<UserRead, ApiError, RegisterRequest> {
  const queryClient = useQueryClient();
  return useMutation<UserRead, ApiError, RegisterRequest>({
    mutationFn: authApi.register,
    onSuccess: (user) => queryClient.setQueryData(queryKeys.me(), user),
  });
}

export function useLogin(): UseMutationResult<UserRead, ApiError, LoginRequest> {
  const queryClient = useQueryClient();
  return useMutation<UserRead, ApiError, LoginRequest>({
    mutationFn: authApi.login,
    onSuccess: (user) => queryClient.setQueryData(queryKeys.me(), user),
  });
}

export function useLogout(): UseMutationResult<void, ApiError, void> {
  const queryClient = useQueryClient();
  return useMutation<void, ApiError, void>({
    mutationFn: authApi.logout,
    onSettled: () => {
      queryClient.setQueryData(queryKeys.me(), null);
      // Drop every other cached resource so no user data survives sign-out.
      queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== 'me' });
    },
  });
}
