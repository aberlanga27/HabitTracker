import { describe, expect, it } from 'vitest';

import { addDays, formatDayLabel, isIsoDate, localToday } from './dates';

describe('dates', () => {
  it('localToday uses the given timezone: 23:59 in Mexico City is still that local date', () => {
    expect(localToday('America/Mexico_City', new Date('2026-09-27T05:59:00Z'))).toBe('2026-09-26');
  });

  it('localToday rolls forward east of UTC', () => {
    expect(localToday('Asia/Tokyo', new Date('2026-09-26T22:30:00Z'))).toBe('2026-09-27');
  });

  it('addDays crosses month and year boundaries', () => {
    expect(addDays('2026-03-01', -1)).toBe('2026-02-28');
    expect(addDays('2026-12-31', 1)).toBe('2027-01-01');
    expect(addDays('2026-09-26', -30)).toBe('2026-08-27');
  });

  it('addDays is not affected by DST transitions', () => {
    expect(addDays('2026-03-28', 1)).toBe('2026-03-29');
    expect(addDays('2026-03-29', 1)).toBe('2026-03-30');
  });

  it('formatDayLabel renders a readable calendar date', () => {
    expect(formatDayLabel('2026-09-26')).toBe('Saturday, 26 September 2026');
  });

  it('isIsoDate accepts only real YYYY-MM-DD dates', () => {
    expect(isIsoDate('2026-09-26')).toBe(true);
    expect(isIsoDate('2026-02-30')).toBe(false);
    expect(isIsoDate('26/09/2026')).toBe(false);
    expect(isIsoDate(null)).toBe(false);
  });
});
