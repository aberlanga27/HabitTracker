/** Only same-app paths are allowed as post-auth redirects (prevents open redirects). */
export function safeNext(next: string | null): string {
  return next && next.startsWith('/') && !next.startsWith('//') ? next : '/';
}
