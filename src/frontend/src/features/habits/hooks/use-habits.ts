import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from '@tanstack/react-query';

import type { ApiError } from '@/shared/lib/apiClient';
import { queryKeys } from '@/shared/lib/queryKeys';

import * as habitsApi from '../api';
import type { HabitCreate, HabitList, HabitRead, HabitUpdate } from '../types';

export function useHabits(archived = false): UseQueryResult<HabitList, ApiError> {
  return useQuery<HabitList, ApiError>({
    queryKey: queryKeys.habits.list({ archived }),
    queryFn: () => habitsApi.listHabits(archived),
  });
}

function useInvalidatingMutation<TData, TVars>(
  mutationFn: (vars: TVars) => Promise<TData>,
): UseMutationResult<TData, ApiError, TVars> {
  const queryClient = useQueryClient();
  return useMutation<TData, ApiError, TVars>({
    mutationFn,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.habits.all() }),
  });
}

export function useCreateHabit(): UseMutationResult<HabitRead, ApiError, HabitCreate> {
  return useInvalidatingMutation(habitsApi.createHabit);
}

export function useUpdateHabit(): UseMutationResult<
  HabitRead,
  ApiError,
  { id: string; body: HabitUpdate }
> {
  return useInvalidatingMutation(({ id, body }) => habitsApi.updateHabit(id, body));
}

export function useArchiveHabit(): UseMutationResult<HabitRead, ApiError, string> {
  return useInvalidatingMutation(habitsApi.archiveHabit);
}

export function useRestoreHabit(): UseMutationResult<HabitRead, ApiError, string> {
  return useInvalidatingMutation(habitsApi.restoreHabit);
}

export function useDeleteHabit(): UseMutationResult<void, ApiError, string> {
  return useInvalidatingMutation(habitsApi.deleteHabit);
}

export function useReorderHabits(): UseMutationResult<HabitList, ApiError, string[]> {
  const queryClient = useQueryClient();
  return useMutation<HabitList, ApiError, string[]>({
    mutationFn: habitsApi.reorderHabits,
    onSuccess: (list) => {
      queryClient.setQueryData(queryKeys.habits.list({ archived: false }), list);
      void queryClient.invalidateQueries({ queryKey: queryKeys.habits.all() });
    },
  });
}
