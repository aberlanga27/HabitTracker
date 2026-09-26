import { useState, type FormEvent, type JSX } from 'react';
import { useNavigate, useSearchParams } from 'react-router';

import { TextField } from '@/shared/ui';

import { useLogin } from '../hooks/use-auth';
import { safeNext } from '../safe-next';

interface FieldErrors {
  email?: string;
  password?: string;
}

export function SignInForm(): JSX.Element {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<FieldErrors>({});
  const loginMutation = useLogin();
  const navigate = useNavigate();
  const [params] = useSearchParams();

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const next: FieldErrors = {};
    if (!email.trim()) next.email = 'Enter your email.';
    if (!password) next.password = 'Enter your password.';
    setErrors(next);
    if (next.email || next.password) return;

    loginMutation.mutate(
      { email, password },
      { onSuccess: () => void navigate(safeNext(params.get('next')), { replace: true }) },
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="stack">
      <TextField
        id="sign-in-email"
        label="Email"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={errors.email}
      />
      <TextField
        id="sign-in-password"
        label="Password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={errors.password}
      />
      {loginMutation.isError && (
        <p role="alert" className="form-error">
          {loginMutation.error.message}
        </p>
      )}
      <button type="submit" className="button button-primary" disabled={loginMutation.isPending}>
        Sign in
      </button>
    </form>
  );
}
