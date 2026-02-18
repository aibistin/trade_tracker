<!-- New Way  -->
<template>
  <div>
    <h1>Stock Trading App - Home</h1>
    <p>Select a stock symbol from the dropdown to view its trades.</p>

    <!-- Custom Dropdown for Stock Symbols -->
    <div class="mb-3">
      <label for="stockSymbol" class="form-label">Select a Stock:</label>
      <div class="dropdown">
        <!-- Search Input -->
        <input v-model="searchQuery" type="text" class="form-control" placeholder="Type to search..."
          @input="filterSymbols" @focus="isDropdownOpen = true" />
        <!-- Dropdown Menu -->
        <ul v-if="isDropdownOpen" class="dropdown-menu show" style="width: 100%; max-height: 300px; overflow-y: auto;">
          <li v-for="[symbol, name] in filteredSymbols" :key="symbol">
            <a class="dropdown-item" href="#" @click="selectSymbol(symbol)">
              {{ symbol }} - {{ name }}
            </a>
          </li>
          <li v-if="filteredSymbols.length === 0">
            <a class="dropdown-item disabled">No matching symbols found</a>
          </li>
        </ul>
      </div>
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

    <!-- Stock Holdings Table -->
    <div v-if="stockHoldings.length > 0" class="mt-4">
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
    <div v-if="optionHoldings.length > 0" class="mt-4">
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
import { useFetchTrades } from '../composables/useFetchTrades';
import { useSymbolSearch } from '../composables/useSymbolSearch';
import { formatCurrency, profitLossClass } from '../utils/tradeUtils';
import { API_BASE_URL } from '@/config.js';

const allSymbolsApiUrl = ref(`${API_BASE_URL}/trade/symbols_json`);
const { data: stockSymbols, loading, error, fetchData } = useFetchTrades();
const { searchQuery, isDropdownOpen, filteredSymbols, selectSymbol } = useSymbolSearch(stockSymbols);

const holdingsApiUrl = ref(`${API_BASE_URL}/trade/current_holdings_json`);
const { data: holdingsData, loading: holdingsLoading, error: holdingsError, fetchData: fetchHoldings } = useFetchTrades();

const stockHoldings = computed(() => {
  if (!holdingsData.value) return [];
  return holdingsData.value.filter(h => h.trade_type === 'L' || h.trade_type === 'S');
});

const optionHoldings = computed(() => {
  if (!holdingsData.value) return [];
  return holdingsData.value.filter(h => h.trade_type === 'C' || h.trade_type === 'P' || h.trade_type === 'O');
});

onMounted(() => {
  fetchData(allSymbolsApiUrl);
  fetchHoldings(holdingsApiUrl);
});
</script>


<style scoped>
.dropdown {
  position: relative;
}

.dropdown-menu {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 1000;
  background-color: white;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 0.25rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.175);
}

.dropdown-menu.show {
  display: block;
}

.dropdown-item {
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

.dropdown-item.disabled {
  color: #6c757d;
  pointer-events: none;
}
</style>
