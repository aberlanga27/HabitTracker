import { apiRequest } from '@/shared/lib/apiClient';

import type { CheckInSet, CheckInState } from './types';

export function setCheckIn(habitId: string, date: string, body: CheckInSet): Promise<CheckInState> {
  return apiRequest<CheckInState>('PUT', `/habits/${habitId}/check-ins/${date}`, body);
}
