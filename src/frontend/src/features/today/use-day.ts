import { keepPreviousData, useQuery, type UseQueryResult } from '@tanstack/react-query';

import { apiRequest, type ApiError } from '@/shared/lib/apiClient';
import { queryKeys } from '@/shared/lib/queryKeys';

import type { DaySummary } from './types';

export function fetchDay(date: string): Promise<DaySummary> {
  return apiRequest<DaySummary>('GET', `/days/${date}`);
}

export function useDay(date: string): UseQueryResult<DaySummary, ApiError> {
  return useQuery<DaySummary, ApiError>({
    queryKey: queryKeys.day(date),
    queryFn: () => fetchDay(date),
    // Keeps the list mounted while another day loads; controls stay disabled meanwhile.
    placeholderData: keepPreviousData,
  });
}
