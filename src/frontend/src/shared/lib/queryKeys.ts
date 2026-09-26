export const queryKeys = {
  me: () => ['me'] as const,
  habits: {
    all: () => ['habits'] as const,
    list: (filter: { archived: boolean }) => ['habits', 'list', filter] as const,
  },
};
