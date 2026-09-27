import { apiRequest } from '@/shared/lib/apiClient';

import type { CheckInList, CheckInSet, CheckInState } from './types';

export function listCheckIns(date: string): Promise<CheckInList> {
  return apiRequest<CheckInList>('GET', `/check-ins?date=${date}`);
}

export function setCheckIn(habitId: string, date: string, body: CheckInSet): Promise<CheckInState> {
  return apiRequest<CheckInState>('PUT', `/habits/${habitId}/check-ins/${date}`, body);
}
