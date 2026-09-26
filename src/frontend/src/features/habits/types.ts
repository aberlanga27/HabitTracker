import type { components } from '@/shared/types/api.generated';

export type HabitRead = components['schemas']['HabitRead'];
export type HabitCreate = components['schemas']['HabitCreate'];
export type HabitUpdate = components['schemas']['HabitUpdate'];
export type HabitList = components['schemas']['HabitList'];
export type HabitColor = HabitRead['color'];
