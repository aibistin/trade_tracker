# Trade Tracker — Frontend

Vue 3 + Vite + Bootstrap 5 frontend for the Trade Tracker application.

## Setup

```bash
pnpm install
```

## Development

```bash
pnpm dev        # Vite dev server with hot reload (http://localhost:5173)
pnpm build      # Production build (output: dist/)
pnpm preview    # Serve the production build on port 4173
pnpm lint       # ESLint with auto-fix
```

## Testing

### Unit tests (Vitest + @vue/test-utils)

Tests live in `src/tests/`. Cover utility functions, composables, and components.

```bash
pnpm test:unit            # run once
pnpm test:unit:watch      # watch mode during development
pnpm test:unit:coverage   # run with coverage report
```

### End-to-end tests (Playwright)

```bash
npx playwright install    # first run only — installs browsers
pnpm test:e2e             # run all E2E tests (headless)
pnpm test:e2e --project=chromium  # Chromium only
pnpm test:e2e --debug     # debug mode with inspector
```

E2E tests are in `e2e/`. The Playwright config auto-starts the dev server locally and uses the preview server (`pnpm preview`) on CI.

## Environment

API base URL is read from `VITE_API_BASE_URL` (default: `http://localhost:5000/api`).
Set it in `frontend/.env` (gitignored) for local overrides, or `frontend/.env.production` for production builds.
