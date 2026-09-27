export const queryKeys = {
  me: () => ['me'] as const,
  habits: {
    all: () => ['habits'] as const,
    list: (filter: { archived: boolean }) => ['habits', 'list', filter] as const,
  },
  checkIns: {
    all: () => ['check-ins'] as const,
    day: (date: string) => ['check-ins', date] as const,
  },
};
