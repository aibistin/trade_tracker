<template>
  <div class="trade-home">
    <h1 class="home-title">Trade Tracker</h1>
    <p class="home-subtitle">Select a stock symbol from the dropdown to view its trades.</p>

    <!-- Symbol Search -->
    <div class="search-section">
      <label class="search-label">Select a Stock:</label>
      <SymbolSearchDropdown
        :symbols="stockSymbols ?? []"
        placeholder="Type to search..."
        @select="selectSymbol"
      />
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border" role="status"></div>
      <p class="mt-2 text-muted">Loading stock symbols...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="alert alert-danger">
      Error loading stock symbols: {{ error }}
    </div>

    <!-- Holdings Loading State -->
    <div v-if="holdingsLoading" class="text-center py-4">
      <div class="spinner-border" role="status"></div>
      <p class="mt-2 text-muted">Loading holdings...</p>
    </div>

    <!-- Holdings Error State -->
    <div v-if="holdingsError" class="alert alert-danger">
      Error loading holdings: {{ holdingsError }}
    </div>

    <!-- Holdings Filter Toggle -->
    <div v-if="holdingsData && holdingsData.length > 0" class="filter-bar">
      <div class="btn-group btn-group-sm">
        <button v-for="f in holdingsFilters" :key="f.value" type="button"
          class="btn" :class="holdingsFilter === f.value ? 'btn-success' : 'btn-outline-success'"
          @click="holdingsFilter = f.value">
          {{ f.label }}
        </button>
      </div>
    </div>

    <!-- Stock Holdings Table -->
    <div v-if="holdingsFilter !== 'option' && stockHoldings.length > 0" class="holdings-section">
      <h4 class="section-title">Stock Holdings</h4>
      <div class="table-responsive">
        <table class="table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Name</th>
              <th class="text-end">Shares</th>
              <th class="text-end">Avg Price</th>
              <th class="text-end">Cost Basis</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="holding in stockHoldings" :key="holding.symbol + holding.trade_type">
              <td>
                <router-link :to="`/trades/all/${holding.symbol}`" class="symbol-link">{{ holding.symbol }}</router-link>
              </td>
              <td class="text-muted">{{ holding.name }}</td>
              <td class="text-end">{{ holding.shares }}</td>
              <td class="text-end">{{ formatCurrency(holding.average_price) }}</td>
              <td class="text-end" :class="profitLossClass(holding.profit_loss)">
                {{ formatCurrency(holding.profit_loss) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Option Holdings Table -->
    <div v-if="holdingsFilter !== 'stock' && optionHoldings.length > 0" class="holdings-section">
      <h4 class="section-title">Option Holdings</h4>
      <div class="table-responsive">
        <table class="table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Name</th>
              <th class="text-end">Contracts</th>
              <th class="text-end">Avg Price</th>
              <th class="text-end">Cost Basis</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="holding in optionHoldings" :key="holding.symbol + holding.trade_type">
              <td>
                <router-link :to="`/trades/all/${holding.symbol}`" class="symbol-link">{{ holding.symbol }}</router-link>
              </td>
              <td class="text-muted">{{ holding.name }}</td>
              <td class="text-end">{{ holding.shares }}</td>
              <td class="text-end">{{ formatCurrency(holding.average_price) }}</td>
              <td class="text-end" :class="profitLossClass(holding.profit_loss)">
                {{ formatCurrency(holding.profit_loss) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useFetchTrades } from '@/composables/useFetchTrades.js';
import { useSymbolSearch } from '@/composables/useSymbolSearch.js';
import { formatCurrency, profitLossClass } from '@/utils/tradeUtils.js';
import { API_BASE_URL } from '@/config.js';
import SymbolSearchDropdown from '@/components/SymbolSearchDropdown.vue';

const { data: stockSymbols, loading, error, fetchData } = useFetchTrades();
const { data: holdingsData, loading: holdingsLoading, error: holdingsError, fetchData: fetchHoldings } = useFetchTrades();
const { selectSymbol } = useSymbolSearch();

const holdingsFilters = [
  { value: 'all', label: 'All' },
  { value: 'stock', label: 'Stocks' },
  { value: 'option', label: 'Options' },
];
const holdingsFilter = ref('all');

const stockHoldings = computed(() => {
  if (!holdingsData.value) return [];
  return holdingsData.value.filter((h) => h.trade_type === 'L' || h.trade_type === 'S');
});

const optionHoldings = computed(() => {
  if (!holdingsData.value) return [];
  return holdingsData.value.filter((h) => h.trade_type === 'C' || h.trade_type === 'P' || h.trade_type === 'O');
});

onMounted(() => {
  fetchData(`${API_BASE_URL}/trade/symbols_json`);
  fetchHoldings(`${API_BASE_URL}/trade/current_holdings_json`);
});
</script>

<style scoped>
.trade-home {
  max-width: 1000px;
  margin: 0 auto;
}

.home-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--color-terminal-text);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 4px;
}

.home-subtitle {
  color: var(--color-terminal-text-muted);
  font-size: 0.82rem;
  margin-bottom: 20px;
}

.search-section {
  margin-bottom: 20px;
}

.search-label {
  display: block;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-terminal-text-muted);
  margin-bottom: 6px;
}

.filter-bar {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.holdings-section {
  margin-top: 20px;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-terminal-text);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 10px;
}

.symbol-link {
  font-weight: 600;
  color: var(--color-accent-cyan);
}

.symbol-link:hover {
  color: var(--color-accent-blue);
}

.text-center { text-align: center; }
.py-4 { padding: 1rem 0; }
.mt-2 { margin-top: 0.5rem; }
</style>
