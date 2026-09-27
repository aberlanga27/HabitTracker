import type { ScheduleRead } from './types';

const SHORT_DAY: Record<ScheduleRead['weekdays'][number], string> = {
  mon: 'Mon',
  tue: 'Tue',
  wed: 'Wed',
  thu: 'Thu',
  fri: 'Fri',
  sat: 'Sat',
  sun: 'Sun',
};

export function scheduleLabel(schedule: ScheduleRead): string {
  if (schedule.type === 'weekdays') return schedule.weekdays.map((d) => SHORT_DAY[d]).join(', ');
  if (schedule.type === 'times_per_week') return `${schedule.times_per_week ?? 0}× per week`;
  return 'Every day';
}
