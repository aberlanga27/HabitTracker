import { useState, type JSX } from 'react';

import { HabitForm } from './HabitForm';
import { HabitList } from './HabitList';
import { HabitRow } from './HabitRow';
import { useCreateHabit, useHabits } from '../hooks/use-habits';

export function HabitsPage(): JSX.Element {
  const active = useHabits(false);
  const archived = useHabits(true);
  const create = useCreateHabit();
  const [formKey, setFormKey] = useState(0);

  return (
    <div className="stack">
      <h1>Habits</h1>

      <section aria-labelledby="new-habit-heading" className="card stack">
        <h2 id="new-habit-heading">New habit</h2>
        <HabitForm
          key={formKey}
          idPrefix="new"
          submitLabel="Add habit"
          pending={create.isPending}
          errorMessage={create.error?.message}
          onSubmit={(body) =>
            create.mutate(body, {
              onSuccess: () => {
                create.reset();
                setFormKey((k) => k + 1);
              },
            })
          }
        />
      </section>

      <section aria-labelledby="active-heading" className="stack">
        <h2 id="active-heading">Active</h2>
        {active.isPending ? (
          <p className="page-loading">Loading habits…</p>
        ) : active.isError ? (
          <p role="alert" className="form-error">
            {active.error.message}
          </p>
        ) : (
          <HabitList habits={active.data.items} />
        )}
      </section>

      <section aria-labelledby="archived-heading" className="stack">
        <h2 id="archived-heading">Archived</h2>
        {archived.data && archived.data.items.length > 0 ? (
          <ul className="habit-list" aria-label="Archived habits">
            {archived.data.items.map((habit) => (
              <HabitRow key={habit.id} habit={habit} variant="archived" />
            ))}
          </ul>
        ) : (
          <p className="empty-state">No archived habits.</p>
        )}
      </section>
    </div>
  );
}
