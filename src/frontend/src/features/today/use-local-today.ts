import { useSyncExternalStore } from 'react';

import { localToday } from '@/shared/lib/dates';

const CHECK_EVERY_MS = 30_000;

function subscribe(onChange: () => void): () => void {
  const id = setInterval(onChange, CHECK_EVERY_MS);
  return () => clearInterval(id);
}

/** The user's local date, updated when local midnight passes while the tab stays open. */
export function useLocalToday(timeZone: string): string {
  return useSyncExternalStore(subscribe, () => localToday(timeZone));
}
