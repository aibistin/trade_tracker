<template>
  <nav class="navbar navbar-expand-lg bg-body-tertiary">
    <div class="container-fluid">
      <router-link class="navbar-brand" to="/home">Trade Track</router-link>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item">
            <router-link class="nav-link active" aria-current="page" to="/home">Home</router-link>
          </li>

          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
              Symbols
            </a>
            <ul class="dropdown-menu" style="max-height: 400px; overflow-y: auto;">
              <li v-for="[symbol, name] in currentStockSymbols" :key="symbol">
                <router-link class="dropdown-item" :to="{ path: `/trades/${activeScope}/${symbol}`, query: route.query }">
                  {{ symbol }} - {{ name }}
                </router-link>
              </li>
            </ul>
          </li>

          <li v-if="route.name !== 'Home'" class="nav-item d-flex align-items-center ms-2">
            <div class="btn-group btn-group-sm" role="group" aria-label="Trade scope">
              <button v-for="s in scopes" :key="s.value" type="button"
                class="btn" :class="activeScope === s.value ? 'btn-primary' : 'btn-outline-primary'"
                @click="setScope(s.value)">
                {{ s.label }}
              </button>
            </div>
          </li>

          <li v-if="route.name !== 'Home'" class="nav-item d-flex align-items-center ms-2">
            <div class="btn-group btn-group-sm" role="group" aria-label="Asset type">
              <button v-for="t in assetTypes" :key="t.value" type="button"
                class="btn" :class="activeAssetType === t.value ? 'btn-success' : 'btn-outline-success'"
                @click="setAssetType(t.value)">
                {{ t.label }}
              </button>
            </div>
          </li>
        </ul>

        <form class="d-flex" role="search">
          <input v-model="searchQuery" type="text" class="form-control" placeholder="Search symbols..."
            @input="filterSymbols" @focus="isDropdownOpen = true" />
          <!-- Dropdown Menu -->
          <ul v-if="isDropdownOpen" class="dropdown-menu show"
            style="width: 100%; max-height: 300px; overflow-y: auto;">
            <li v-for="[symbol, name] in filteredSymbols" :key="symbol">
              <a class="dropdown-item btn-outline-success" href="#" @click="selectSymbolWithScope(symbol)">
                {{ symbol }} - {{ name }}
              </a>
            </li>
            <li v-if="filteredSymbols.length === 0">
              <a class="dropdown-item disabled">No matching symbols found</a>
            </li>
          </ul>
        </form>

      </div>
    </div>
  </nav>

  <!-- Loading State -->
  <div v-if="loading" class="text-center py-4">
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">Loading all symbols...</span>
    </div>
    <p class="mt-2">Loading all stock symbols...</p>
  </div>

  <div v-if="currentLoading" class="text-center py-4">
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">Loading current symbols...</span>
    </div>
    <p class="mt-2">Loading current stock symbols...</p>
  </div>

  <!-- Error State -->
  <div v-if="error" class="alert alert-danger">
    Error loading all stock symbols: {{ error }}
  </div>
  <!-- Error State -->
  <div v-if="currentError" class="alert alert-danger">
    Error loading open stock symbols: {{ error }}
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useFetchTrades } from '../composables/useFetchTrades';
import { useSymbolSearch } from '../composables/useSymbolSearch';
import { API_BASE_URL } from '@/config.js';

const route = useRoute();
const router = useRouter();

const scopes = [
  { value: 'all', label: 'All' },
  { value: 'open', label: 'Open' },
  { value: 'closed', label: 'Closed' },
];

const assetTypes = [
  { value: 'all', label: 'All' },
  { value: 'stock', label: 'Stock' },
  { value: 'option', label: 'Option' },
];

const activeScope = computed(() => route.params.scope || 'all');
const activeAssetType = computed(() => route.query.asset_type || 'all');

const setScope = (scope) => {
  const symbol = route.params.stockSymbol;
  if (symbol) {
    router.push({ path: `/trades/${scope}/${symbol}`, query: route.query });
  }
};

const setAssetType = (type) => {
  const symbol = route.params.stockSymbol;
  if (symbol) {
    const query = { ...route.query };
    if (type && type !== 'all') {
      query.asset_type = type;
    } else {
      delete query.asset_type;
    }
    router.push({ path: route.path, query });
  }
};

const allSymbolsApiUrl = ref(`${API_BASE_URL}/trade/symbols_json`);
const currentSymbolsApiUrl = ref(`${API_BASE_URL}/trade/current_holdings_symbols_json`);

const { data: stockSymbols, loading, error, fetchData } = useFetchTrades();
const { data: currentStockSymbols, loading: currentLoading, error: currentError, fetchData: fetchCurrentSymbols } = useFetchTrades();
const { searchQuery, isDropdownOpen, filteredSymbols, selectSymbol } = useSymbolSearch(stockSymbols);

const selectSymbolWithScope = (symbol) => {
  selectSymbol(symbol, activeScope.value);
};

onMounted(() => {
  fetchData(allSymbolsApiUrl);
  fetchCurrentSymbols(currentSymbolsApiUrl);
});
</script>

<style scoped>
.navbar {
  margin-bottom: 20px;
}
</style>
