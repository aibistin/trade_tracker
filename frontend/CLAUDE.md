# frontend/CLAUDE.md

Frontend-specific guidance for the Vue 3 + Vite application in this directory.
This file is loaded in addition to the root `CLAUDE.md` when working inside `frontend/`.

## Commands

```bash
pnpm install              # Install dependencies
pnpm dev                  # Vite dev server (http://localhost:5173, proxies to backend at :5000)
pnpm build                # Production build (reads frontend/.env.production)
pnpm preview              # Serve the production build locally on port 4173
pnpm lint                 # ESLint with auto-fix
pnpm test:unit            # Vitest unit tests (run once)
pnpm test:unit:watch      # Vitest in watch mode
pnpm test:unit:coverage   # Vitest with coverage report
pnpm test:e2e             # Playwright end-to-end tests
```

## Architecture

**Vue 3 + Vite + Bootstrap 5 + Axios. No Vuex/Pinia — state is router-based or component-local.**

### API Config
`src/config.js` exports `API_BASE_URL` read from `VITE_API_BASE_URL` env var (default: `http://localhost:5000/api`).
Set via `frontend/.env` (gitignored). Production uses `frontend/.env.production` → `http://localhost:3000/api`.

### Directory Structure
```
src/
  components/         # Reusable components (not page-level views)
    AppContainer.vue          — Bootstrap .container wrapper
    BSNavBarTop.vue           — Top navbar: symbol dropdown, scope/asset-type toggles, search
    SymbolSearchDropdown.vue  — Self-contained search input + filtered dropdown; emits @select
    TradeCard.vue             — Expandable buy-trade card with inline edit form
    TransactionSummary.vue    — Trade stats summary table
  composables/
    useFetchTrades.js   — Generic GET fetch: fetchData(url: string) → { data, loading, error }
    useSymbolSearch.js  — Navigation helper: selectSymbol(symbol, scope) → router.push
  utils/
    tradeUtils.js       — Pure formatting functions (no Vue deps): formatCurrency, formatDate,
                          profitLossClass, formatValue, formatTradeType, formatAction, rowClass
  views/              # Page-level components registered in the router
    AllTrades.vue   — Trade detail view for a symbol+scope
    TradeHome.vue   — Home page: symbol search + current holdings tables
    NotFound.vue    — 404 page
  router/index.js   — Route definitions (lazy-loaded)
  config.js         — API base URL
  main.js           — App bootstrap (Bootstrap injection)
  tests/            — Vitest unit tests
```

### Component Conventions
- **Always use `<script setup>`** (Composition API). Never Options API or the `export default { setup() }` hybrid.
- Props down, events up — never mutate props. Use `defineEmits` and emit to the parent.
- `TradeCard` emits `@trade-updated(tradeId, fields)` after a successful PATCH; `AllTrades` handles it via `updateTrade()` to keep source data in sync without a re-fetch.
- Use `axios` for all HTTP calls (not raw `fetch`). The `useFetchTrades` composable covers all GET requests.

### Composable Conventions
- `useFetchTrades()` — call once per endpoint per component. Returns `{ data, loading, error, fetchData }`. Pass a plain string URL to `fetchData`, not a ref.
- `useSymbolSearch()` — provides only `selectSymbol(symbol, scope)` for navigation. Search/filter logic lives in `SymbolSearchDropdown.vue`.

### Routing
Routes: `/home` (TradeHome) and `/trades/:scope/:stockSymbol` (AllTrades). All lazy-loaded.
Scope (`all`/`open`/`closed`) and `asset_type` query param are stored in the URL — treat the URL as the source of truth for filter state.

### `tradeUtils.js` Reference
| Function | Notes |
|---|---|
| `formatCurrency(value)` | Returns `''` for null/undefined. Format: `-$x.xx` (no parentheses). |
| `formatDate(dateString)` | Returns `''` for null/empty. Appends `T00:00:00` to date-only strings to prevent UTC shift. |
| `profitLossClass(value)` | `text-success` for ≥ 0, `text-danger` for < 0. |
| `formatValue(value)` | `.toFixed(2)` or `''` for null/undefined. |
| `formatTradeType(trade)` | Maps `trade.trade_type` code → label (L→Long, S→Short, C→Call, P→Put, O→Other). |
| `formatAction(trade)` | Maps `trade.action` code → label. Returns raw code for unknowns. |

## Testing

### Framework
Vitest + `@vue/test-utils`. Tests live in `src/tests/`. Config: `vitest.config.js`.

### What to test
- **Pure functions** (`tradeUtils.js`) — no mocking needed, highest ROI.
- **Composables** — mock `axios` with `vi.mock('axios')` for `useFetchTrades`; mock `vue-router` for `useSymbolSearch`.
- **Components** — mount with `@vue/test-utils`, test props, emits, computed filtering, and user interactions.

### Patterns
```js
// Mocking axios
import { vi } from 'vitest'
import axios from 'axios'
vi.mock('axios')
axios.get.mockResolvedValueOnce({ data: [...] })

// Mocking vue-router
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useRoute: () => ({ query: {}, params: {} }),
}))

// Mounting a component
import { mount } from '@vue/test-utils'
const wrapper = mount(MyComponent, { props: { ... } })
await wrapper.find('input').setValue('AAPL')
expect(wrapper.emitted('select')).toBeTruthy()
```
