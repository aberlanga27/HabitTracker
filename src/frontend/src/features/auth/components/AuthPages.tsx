import type { JSX } from 'react';
import { Link, useSearchParams } from 'react-router';

import { RegisterForm } from './RegisterForm';
import { SignInForm } from './SignInForm';

function withNext(path: string, next: string | null): string {
  return next ? `${path}?next=${encodeURIComponent(next)}` : path;
}

export function SignInPage(): JSX.Element {
  const [params] = useSearchParams();
  return (
    <main className="auth-page">
      <div className="card auth-card">
        <h1>Sign in</h1>
        <SignInForm />
        <p>
          New here? <Link to={withNext('/register', params.get('next'))}>Create an account</Link>
        </p>
      </div>
    </main>
  );
}

export function RegisterPage(): JSX.Element {
  const [params] = useSearchParams();
  return (
    <main className="auth-page">
      <div className="card auth-card">
        <h1>Create your account</h1>
        <RegisterForm />
        <p>
          Already have an account?{' '}
          <Link to={withNext('/sign-in', params.get('next'))}>Sign in</Link>
        </p>
      </div>
    </main>
  );
}
