import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from '@tanstack/react-query';

import type { ApiError } from '@/shared/lib/apiClient';
import { queryKeys } from '@/shared/lib/queryKeys';

import * as checkInsApi from '../api';
import type { CheckInList, CheckInState } from '../types';

export function useCheckIns(date: string): UseQueryResult<CheckInList, ApiError> {
  return useQuery<CheckInList, ApiError>({
    queryKey: queryKeys.checkIns.day(date),
    queryFn: () => checkInsApi.listCheckIns(date),
    // Keeps the list mounted while another day loads; callers disable controls meanwhile.
    placeholderData: keepPreviousData,
  });
}

interface ToggleVars {
  habitId: string;
  completed: boolean;
}

interface ToggleContext {
  previous: CheckInList | undefined;
}

function applyToggle(list: CheckInList | undefined, date: string, vars: ToggleVars): CheckInList {
  const items = (list?.items ?? []).filter((item) => item.habit_id !== vars.habitId);
  if (vars.completed) {
    const existing = list?.items.find((item) => item.habit_id === vars.habitId);
    items.push({
      habit_id: vars.habitId,
      date,
      completed: true,
      note: existing?.note ?? null,
      completed_at: existing?.completed_at ?? new Date().toISOString(),
    });
  }
  return { items, total: items.length };
}

/**
 * Optimistically toggles a habit for `date` and rolls back on failure (spec 003 FR-006).
 * Callers disable the control while `isPending` to de-duplicate rapid taps.
 */
export function useToggleCheckIn(
  date: string,
): UseMutationResult<CheckInState, ApiError, ToggleVars, ToggleContext> {
  const queryClient = useQueryClient();
  const key = queryKeys.checkIns.day(date);
  return useMutation<CheckInState, ApiError, ToggleVars, ToggleContext>({
    mutationFn: ({ habitId, completed }) => checkInsApi.setCheckIn(habitId, date, { completed }),
    onMutate: async (vars) => {
      await queryClient.cancelQueries({ queryKey: key });
      const previous = queryClient.getQueryData<CheckInList>(key);
      queryClient.setQueryData<CheckInList>(key, (old) => applyToggle(old, date, vars));
      return { previous };
    },
    onError: (_error, _vars, context) => {
      queryClient.setQueryData(key, context?.previous);
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.checkIns.all() });
      void queryClient.invalidateQueries({ queryKey: queryKeys.habits.all() });
    },
  });
}

export function useSaveNote(
  date: string,
): UseMutationResult<CheckInState, ApiError, { habitId: string; note: string | null }> {
  const queryClient = useQueryClient();
  return useMutation<CheckInState, ApiError, { habitId: string; note: string | null }>({
    mutationFn: ({ habitId, note }) =>
      checkInsApi.setCheckIn(habitId, date, { completed: true, note }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.checkIns.day(date) }),
  });
}
