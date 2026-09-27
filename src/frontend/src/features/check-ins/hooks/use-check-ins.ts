import { useMutation, useQueryClient, type UseMutationResult } from '@tanstack/react-query';

import type { ApiError } from '@/shared/lib/apiClient';
import { queryKeys } from '@/shared/lib/queryKeys';

import * as checkInsApi from '../api';
import type { CheckInState, DaySummary } from '../types';

interface ToggleVars {
  habitId: string;
  completed: boolean;
}

interface ToggleContext {
  previous: DaySummary | undefined;
}

function applyToggle(day: DaySummary | undefined, vars: ToggleVars): DaySummary | undefined {
  if (!day) return day;
  return {
    ...day,
    items: day.items.map((item) =>
      item.habit.id === vars.habitId
        ? { ...item, completed: vars.completed, note: vars.completed ? item.note : null }
        : item,
    ),
  };
}

function invalidateAfterCheckIn(queryClient: ReturnType<typeof useQueryClient>): void {
  void queryClient.invalidateQueries({ queryKey: queryKeys.days() });
  void queryClient.invalidateQueries({ queryKey: queryKeys.habits.all() });
}

/**
 * Optimistically toggles a habit on the day summary for `date` and rolls back on failure
 * (spec 003 FR-006). Callers disable the control while `isPending` to de-duplicate taps.
 */
export function useToggleCheckIn(
  date: string,
): UseMutationResult<CheckInState, ApiError, ToggleVars, ToggleContext> {
  const queryClient = useQueryClient();
  const key = queryKeys.day(date);
  return useMutation<CheckInState, ApiError, ToggleVars, ToggleContext>({
    mutationFn: ({ habitId, completed }) => checkInsApi.setCheckIn(habitId, date, { completed }),
    onMutate: async (vars) => {
      await queryClient.cancelQueries({ queryKey: key });
      const previous = queryClient.getQueryData<DaySummary>(key);
      queryClient.setQueryData<DaySummary>(key, (old) => applyToggle(old, vars));
      return { previous };
    },
    onError: (_error, _vars, context) => {
      queryClient.setQueryData(key, context?.previous);
    },
    onSettled: () => invalidateAfterCheckIn(queryClient),
  });
}

export function useSaveNote(
  date: string,
): UseMutationResult<CheckInState, ApiError, { habitId: string; note: string | null }> {
  const queryClient = useQueryClient();
  return useMutation<CheckInState, ApiError, { habitId: string; note: string | null }>({
    mutationFn: ({ habitId, note }) =>
      checkInsApi.setCheckIn(habitId, date, { completed: true, note }),
    onSuccess: () => invalidateAfterCheckIn(queryClient),
  });
}
