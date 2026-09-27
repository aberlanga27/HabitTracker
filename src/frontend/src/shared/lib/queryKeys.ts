export const queryKeys = {
  me: () => ['me'] as const,
  habits: {
    all: () => ['habits'] as const,
    list: (filter: { archived: boolean }) => ['habits', 'list', filter] as const,
    detail: (id: string) => ['habits', 'detail', id] as const,
  },
  days: () => ['day'] as const,
  day: (date: string) => ['day', date] as const,
};
