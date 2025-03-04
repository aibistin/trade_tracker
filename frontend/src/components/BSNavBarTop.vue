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
              All Trades
            </a>
            <ul class="dropdown-menu">
              <li v-for="[symbol, name] in currentStockSymbols" :key="symbol">
                <router-link class="dropdown-item" @click="logNavigation(symbol, 'all')" :to="`/trades/all/${symbol}`">
                  {{ symbol }} - {{ name }}
                </router-link>
              </li>
            </ul>
          </li>

          <li class="nav-item dropdown" size="3">
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
              Open Trades
            </a>
            <ul class="dropdown-menu">
              <li v-for="[symbol, name] in currentStockSymbols" :key="symbol">
                <router-link class="dropdown-item" @click="logNavigation(symbol, 'to')" :to="`/trades/open/${symbol}`">
                  {{ symbol }} - {{ name }}
                </router-link>
              </li>
            </ul>
          </li>
          <li class="nav-item dropdown" size="3">
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
              Closed Trades
            </a>
            <ul class="dropdown-menu">
              <li v-for="[symbol, name] in currentStockSymbols" :key="symbol">
                <router-link class="dropdown-item" @click="logNavigation(symbol, 'to')"
                  :to="`/trades/closed/${symbol}`">
                  {{ symbol }} - {{ name }}
                </router-link>
              </li>
            </ul>
          </li>
        </ul>

        <form class="d-flex" role="search">
          <input v-model="searchQuery" type="text" class="form-control" placeholder="View All Trades for ..."
            @input="filterSymbols" @focus="isDropdownOpen = true" />
          <!-- Dropdown Menu -->
          <ul v-if="isDropdownOpen" class="dropdown-menu show"
            style="width: 100%; max-height: 300px; overflow-y: auto;">
            <li v-for="[symbol, name] in filteredSymbols" :key="symbol">
              <a class="dropdown-item btn-outline-success" href="#" @click="selectAllTradesSymbol(symbol, 'all')">
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
import { computed, onMounted, ref, watch } from 'vue';
import { useFetchTrades } from '../composables/useFetchTrades';
import { useRouter } from 'vue-router';
const allSymbolsApiUrl = ref('http://localhost:5000/trade/symbols_json');
const currentSymbolsApiUrl = ref('http://localhost:5000/trade/current_holdings_symbols_json')
const searchQuery = ref('');
const isDropdownOpen = ref(false);
const router = useRouter();

// Create the useFetchTrades composable for fetching stock symbols
console.log(`[BSNavBarTop->Init] Creating useFetchTrades`);
const { data: stockSymbols, loading, error, fetchData } = useFetchTrades();
const { data: currentStockSymbols, loading: currentLoading, error: currentError, fetchData: fetchCurrentSymbols } = useFetchTrades();


/* Using Selector */
// Filter symbols based on search query
const filteredSymbols = computed(() => {
  if (!searchQuery.value) {
    return stockSymbols.value;
  }

  const query = searchQuery.value.toLowerCase();

  return stockSymbols.value.filter(([symbol, name]) => {
    return (
      symbol.toLowerCase().includes(query) ||
      name.toLowerCase().includes(query)
    );
  });
});


// Watch for changes in searchQuery
watch(isDropdownOpen, () => {
});


// Handle symbol selection
const selectAllTradesSymbol = (symbol, scope) => {
  searchQuery.value = ''; // Clear the search query
  isDropdownOpen.value = false; // Close the dropdown
  router.push(`/trades/${scope}/${symbol}`);
};

/* end Using Selector */


// Fetch data when the component mounts
onMounted(() => {
  console.log(`[BSNavBarTop->onMounted] fetchData with ${allSymbolsApiUrl.value}`);
  fetchData(allSymbolsApiUrl);
  fetchCurrentSymbols(currentSymbolsApiUrl);
});


const logNavigation = (symbol, type) => {
  console.log(`Navigating to ${type} trades for symbol: ${symbol}`);
};

</script>

<style scoped>
.navbar {
  margin-bottom: 20px;
}
</style>
