import { defineConfig, devices } from '@playwright/test';

const BACKEND_PORT = 8001;
const FRONTEND_PORT = 5174;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    trace: 'retain-on-failure',
  },
  // PLAYWRIGHT_CHANNEL=chrome uses an installed Chrome when the bundled browser is unavailable.
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], channel: process.env.PLAYWRIGHT_CHANNEL },
    },
  ],
  webServer: [
    {
      command: `rm -f e2e.db && HABITUDE_DATABASE_URL=sqlite:///./e2e.db ../../.venv/bin/alembic upgrade head && HABITUDE_DATABASE_URL=sqlite:///./e2e.db ../../.venv/bin/uvicorn app.main:app --port ${BACKEND_PORT}`,
      cwd: '../backend',
      url: `http://localhost:${BACKEND_PORT}/api/v1/openapi.json`,
      reuseExistingServer: false,
    },
    {
      command: `npx vite --port ${FRONTEND_PORT} --strictPort`,
      url: `http://localhost:${FRONTEND_PORT}`,
      env: { VITE_PROXY_TARGET: `http://localhost:${BACKEND_PORT}` },
      reuseExistingServer: false,
    },
  ],
});
