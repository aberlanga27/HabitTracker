import { ApiError, apiRequest } from '@/shared/lib/apiClient';

import type { LoginRequest, RegisterRequest, UserRead } from './types';

/** Returns the signed-in user, or null when there is no valid session. */
export async function fetchMe(): Promise<UserRead | null> {
  try {
    return await apiRequest<UserRead>('GET', '/auth/me');
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}

export function register(body: RegisterRequest): Promise<UserRead> {
  return apiRequest<UserRead>('POST', '/auth/register', body);
}

export function login(body: LoginRequest): Promise<UserRead> {
  return apiRequest<UserRead>('POST', '/auth/login', body);
}

export function logout(): Promise<void> {
  return apiRequest<void>('POST', '/auth/logout');
}
