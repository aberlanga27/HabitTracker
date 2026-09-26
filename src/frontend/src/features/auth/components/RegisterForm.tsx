import { useState, type FormEvent, type JSX } from 'react';
import { useNavigate, useSearchParams } from 'react-router';

import { TextField } from '@/shared/ui';

import { useRegister } from '../hooks/use-auth';
import { safeNext } from '../safe-next';

const MIN_PASSWORD = 10;

interface FieldErrors {
  email?: string;
  password?: string;
}

export function RegisterForm(): JSX.Element {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<FieldErrors>({});
  const registerMutation = useRegister();
  const navigate = useNavigate();
  const [params] = useSearchParams();

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const next: FieldErrors = {};
    if (!email.trim()) next.email = 'Enter your email.';
    if (password.length < MIN_PASSWORD) {
      next.password = `Password must be at least ${MIN_PASSWORD} characters.`;
    }
    setErrors(next);
    if (next.email || next.password) return;

    registerMutation.mutate(
      { email, password, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone },
      { onSuccess: () => void navigate(safeNext(params.get('next')), { replace: true }) },
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="stack">
      <TextField
        id="register-email"
        label="Email"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={errors.email}
      />
      <TextField
        id="register-password"
        label="Password"
        type="password"
        autoComplete="new-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={errors.password}
      />
      {registerMutation.isError && (
        <p role="alert" className="form-error">
          {registerMutation.error.message}
        </p>
      )}
      <button type="submit" className="button button-primary" disabled={registerMutation.isPending}>
        Create account
      </button>
    </form>
  );
}
