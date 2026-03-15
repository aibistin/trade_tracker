<template>
  <div>
    <h1>Stock Trading App - Home</h1>
    <p>Select a stock symbol from the dropdown to view its trades.</p>

    <!-- Symbol Search -->
    <div class="mb-3">
      <label class="form-label">Select a Stock:</label>
      <SymbolSearchDropdown
        :symbols="stockSymbols ?? []"
        placeholder="Type to search..."
        @select="selectSymbol"
      />
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Loading stock symbols...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="alert alert-danger">
      Error loading stock symbols: {{ error }}
    </div>

    <!-- Holdings Loading State -->
    <div v-if="holdingsLoading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Loading holdings...</p>
    </div>

    <!-- Holdings Error State -->
    <div v-if="holdingsError" class="alert alert-danger">
      Error loading holdings: {{ holdingsError }}
    </div>

    <!-- Holdings Filter Toggle -->
    <div v-if="holdingsData && holdingsData.length > 0" class="mt-4 d-flex align-items-center gap-2">
      <div class="btn-group btn-group-sm" role="group" aria-label="Holdings filter">
        <button v-for="f in holdingsFilters" :key="f.value" type="button"
          class="btn" :class="holdingsFilter === f.value ? 'btn-success' : 'btn-outline-success'"
          @click="holdingsFilter = f.value">
          {{ f.label }}
        </button>
      </div>
    </div>

    <!-- Stock Holdings Table -->
    <div v-if="holdingsFilter !== 'option' && stockHoldings.length > 0" class="mt-3">
      <h4>Stock Holdings</h4>
      <table class="table table-striped table-hover">
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
              <router-link :to="`/trades/all/${holding.symbol}`">{{ holding.symbol }}</router-link>
            </td>
            <td>{{ holding.name }}</td>
            <td class="text-end">{{ holding.shares }}</td>
            <td class="text-end">{{ formatCurrency(holding.average_price) }}</td>
            <td class="text-end" :class="profitLossClass(holding.profit_loss)">
              {{ formatCurrency(holding.profit_loss) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Option Holdings Table -->
    <div v-if="holdingsFilter !== 'stock' && optionHoldings.length > 0" class="mt-4">
      <h4>Option Holdings</h4>
      <table class="table table-striped table-hover">
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
              <router-link :to="`/trades/all/${holding.symbol}`">{{ holding.symbol }}</router-link>
            </td>
            <td>{{ holding.name }}</td>
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
