import { describe, expect, it } from 'vitest';

import { safeNext } from './safe-next';

describe('safeNext', () => {
  it.each([
    ['/habits', '/habits'],
    ['/?date=2026-09-25', '/?date=2026-09-25'],
    [null, '/'],
    ['https://evil.example', '/'],
    ['//evil.example', '/'],
    ['javascript:alert(1)', '/'],
  ])('maps %s to %s', (input, expected) => {
    expect(safeNext(input)).toBe(expected);
  });
});
