import { apiRequest } from '@/shared/lib/apiClient';

import type { HabitCreate, HabitList, HabitRead, HabitUpdate } from './types';

export function listHabits(archived: boolean): Promise<HabitList> {
  return apiRequest<HabitList>('GET', `/habits?archived=${archived}`);
}

export function getHabit(id: string): Promise<HabitRead> {
  return apiRequest<HabitRead>('GET', `/habits/${id}`);
}

export function createHabit(body: HabitCreate): Promise<HabitRead> {
  return apiRequest<HabitRead>('POST', '/habits', body);
}

export function updateHabit(id: string, body: HabitUpdate): Promise<HabitRead> {
  return apiRequest<HabitRead>('PATCH', `/habits/${id}`, body);
}

export function archiveHabit(id: string): Promise<HabitRead> {
  return apiRequest<HabitRead>('POST', `/habits/${id}/archive`);
}

export function restoreHabit(id: string): Promise<HabitRead> {
  return apiRequest<HabitRead>('POST', `/habits/${id}/restore`);
}

export function deleteHabit(id: string): Promise<void> {
  return apiRequest<void>('DELETE', `/habits/${id}`);
}

export function reorderHabits(habitIds: string[]): Promise<HabitList> {
  return apiRequest<HabitList>('PUT', '/habits/order', { habit_ids: habitIds });
}
