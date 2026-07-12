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

**Vue 3 + Vite + Tailwind CSS v4 + Axios + chart.js (via vue-chartjs + chartjs-chart-treemap). No Vuex/Pinia — state is router-based or component-local.**

### Design System — Dark Terminal Theme
CSS custom properties in `src/assets/base.css` define a Bloomberg/trading-terminal dark theme. Use these exact values for any new chart, canvas, or hardcoded color (Chart.js options can't consume CSS variables directly):
- Profit/positive: `#00c896` — Loss/negative: `#ff4060` — Highlight: `#ffd700`
- Accent blue: `#4d9fff` — Accent cyan: `#00d4e8`
- Chart tooltip bg: `#1a1e27`, title/body text: `#dce4f0`, border: `#262b38`
- Chart grid lines: `rgba(255,255,255,0.04)` — tick color: `#6b7a96`

### API Config
`src/config.js` exports `API_BASE_URL` read from `VITE_API_BASE_URL` env var (default: `http://localhost:5000/api`).
Set via `frontend/.env` (gitignored). Production uses `frontend/.env.production` → `http://localhost:3000/api`.

### Directory Structure
```
src/
  components/         # Reusable components (not page-level views)
    NavBar.vue                — Top navbar: symbol dropdown, scope/asset-type toggles, search (no Bootstrap JS)
    SymbolSearchDropdown.vue  — Self-contained search input + filtered dropdown; emits @select
    TradeCard.vue             — Expandable buy-trade card; lazy-fetches live price on expand (open trades only).
                                Stock trades use useStockPrice; option trades use useOptionPrice (×100 multiplier).
                                Metrics bar shows: Live/Option Price | Cost | Mkt Value | Diff | Diff%.
    TransactionSummary.vue    — Trade stats summary table
    WinLossBar.vue            — Horizontal W/L bar: accepts wins/losses props, shows win rate %
    PortfolioHeatmap.vue      — Treemap visualization of portfolio positions, sized by weight, colored by P&L
    CumulativePnlChart.vue    — Cumulative P&L line chart computed from monthly/quarterly buckets
    SparklineChart.vue        — Canvas-based sparkline with buy/sell annotation markers
  composables/
    useFetchTrades.js   — Generic GET fetch: fetchData(url: string) → { data, loading, error }
    useSymbolSearch.js  — Navigation helper: selectSymbol(symbol, scope) → router.push
    useStockPrice.js    — Live stock price: fetchPrice(symbol) → { price, loading, error }. Module-level
                          Map cache (5-min TTL) so repeated calls within a tab skip the API.
    useOptionPrice.js   — Live option price: fetchPrice(label) → { price, bid, ask, occTicker, loading, error }.
                          Passes the raw Schwab label to GET /api/option/price; OCC conversion happens server-side.
                          Module-level Map cache (5-min TTL) keyed by label.
    usePriceHistory.js  — Fetches sparkline price history: fetchHistory(symbol, period) → { prices, annotations }.
                          Module-level Map cache. Silently skips on error (endpoint may not exist yet).
  utils/
    tradeUtils.js       — Pure formatting functions (no Vue deps): formatCurrency, formatDate,
                          profitLossClass, formatValue, formatTradeType, formatAction, rowClass
  views/              # Page-level components registered in the router
    AllTrades.vue   — Trade detail view for a symbol+scope; shows WinLossBar below each TransactionSummary
    Dashboard.vue   — Performance dashboard: summary cards, P&L/cumulative/win-rate charts (hidden by
                      default, toggle to show), stock holdings table (one aggregated row per ticker),
                      options holdings table (grouped by underlying with expand/collapse per contract),
                      portfolio heatmap. Holdings data from GET /api/holdings.
    SymbolHistory.vue — "By Symbol — Closed Trade History" page (/history): per-symbol closed-trade
                      stats from GET /api/dashboard/summary, click-to-sort columns (default P&L desc),
                      totals footer row.
    TradeHome.vue   — Home page: symbol search + current holdings tables
    NotFound.vue    — 404 page
  router/index.js   — Route definitions (lazy-loaded)
  config.js         — API base URL
  main.js           — App bootstrap (Tailwind CSS via @tailwindcss/vite plugin)
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
Routes: `/home` (TradeHome), `/dashboard` (Dashboard), `/history` (SymbolHistory), and `/trades/:scope/:stockSymbol` (AllTrades). All lazy-loaded.
NavBar's scope/asset-type toggles only show on trade views — new page-level routes must be added to the exclusion list in `NavBar.vue`'s `isTradeView`.
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
