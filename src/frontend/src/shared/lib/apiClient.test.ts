import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { API, server } from '@/test/server';

import { ApiError, apiRequest } from './apiClient';

describe('apiClient', () => {
  it('sends JSON with credentials and the X-Requested-With header', async () => {
    let seen: Request | undefined;
    server.use(
      http.post(`${API}/echo`, async ({ request }) => {
        seen = request.clone();
        return HttpResponse.json(await request.json());
      }),
    );
    const body = await apiRequest<{ a: number }>('POST', '/echo', { a: 1 });
    expect(body).toEqual({ a: 1 });
    expect(seen?.headers.get('X-Requested-With')).toBe('XMLHttpRequest');
    expect(seen?.headers.get('Content-Type')).toBe('application/json');
    expect(seen?.credentials).toBe('include');
  });

  it('returns undefined for 204 responses', async () => {
    server.use(http.post(`${API}/empty`, () => new HttpResponse(null, { status: 204 })));
    await expect(apiRequest('POST', '/empty')).resolves.toBeUndefined();
  });

  it('throws ApiError with the envelope code and message', async () => {
    server.use(
      http.get(`${API}/fail`, () =>
        HttpResponse.json(
          { error: { code: 'NOT_FOUND', message: 'Nope', details: { id: 'x' } } },
          { status: 404 },
        ),
      ),
    );
    const error = await apiRequest('GET', '/fail').catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 404, code: 'NOT_FOUND', message: 'Nope' });
  });

  it('maps network failures to ApiError with code NETWORK_ERROR', async () => {
    server.use(http.get(`${API}/down`, () => HttpResponse.error()));
    const error = await apiRequest('GET', '/down').catch((e: unknown) => e);
    expect(error).toMatchObject({ status: 0, code: 'NETWORK_ERROR' });
  });

  it('maps non-envelope errors to a generic ApiError', async () => {
    server.use(http.get(`${API}/html`, () => new HttpResponse('<h1>oops</h1>', { status: 500 })));
    const error = await apiRequest('GET', '/html').catch((e: unknown) => e);
    expect(error).toMatchObject({ status: 500, code: 'UNKNOWN_ERROR' });
  });
});
